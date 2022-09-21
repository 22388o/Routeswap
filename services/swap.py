from services.lightning import create_invoice, decode_invoice
from services.bitcoin import bitcoin, get_balance, get_estimate_fee, get_new_address
from helpers.helpers import sats_to_btc, btc_to_sats
from services.redis import redis
from services.lnd import lnd

from database import db
from configs import SERVICE_FEE_RATE, SERVICE_MIN_FEE_RATE, TRADE_MIN_BTC

from tinydb import Query
from time import time
from json import dumps
from os import urandom

def create_swap(base: str, quote: str, address: str, amount: float, feerate: float = 0) -> dict:
    if ((base == "LN-BTC") and (quote == "BTC")) and (feerate >= 1):
        if (bitcoin.validate_address(address)["isvalid"] == False):
            return {"message": "Address invalid."}

        if (amount > TRADE_MIN_BTC):
            return {"message": f"The minimum value is {TRADE_MIN_BTC:.8f}"}
        
        balance = sats_to_btc(get_balance()["confirmed_balance"])
        if (amount > balance):
            return {"message": "internal server error."}

        amount_sats = btc_to_sats(amount)

        estimate_fee = get_estimate_fee(address, amount_sats)
        estimate_fee = (int(estimate_fee["fee_sat"]) / int(estimate_fee["feerate_sat_per_byte"]))
        estimate_fee = int(estimate_fee * feerate)

        service_fee_amount = amount * SERVICE_FEE_RATE / 100
        if (service_fee_amount < SERVICE_MIN_FEE_RATE):
            service_fee_amount = SERVICE_MIN_FEE_RATE
        
        estimate_fee_btc = sats_to_btc(estimate_fee)
        service_fee_and_tx_amount = (service_fee_amount + estimate_fee_btc + amount)
        
        expiry = (60 * 15)
        metadata = {"address": address, "amount": amount, "feerate": feerate, "base": "LN-BTC", "quote": "BTC"}
        timestamp = time()
        payment_request = create_invoice(service_fee_and_tx_amount, expiry=expiry, metadata=metadata, typeof="loop-out")
        return {"id": payment_request["payment_hash"], "payment_request": payment_request["payment_request"], "expiry": timestamp + expiry}
    
    elif ((base == "BTC") and (quote == "LN-BTC")):
        invoice = address
        try:
            dec_invoice = decode_invoice(invoice)
        except:
            return {"message": "Invoice invalid."}

        if lnd.lookup_invoice(dec_invoice["payment_hash"]).get("settled"):
            return {"message": "The invoice has already been paid."}
        
        timestamp = int(dec_invoice["timestamp"])
        expiry = int(dec_invoice["expiry"])
        if (time() > (timestamp + expiry)):
            return {"message": "Invoice expired."}

        amount = sats_to_btc(dec_invoice["num_satoshis"])
        if (amount > TRADE_MIN_BTC):
            return {"message": f"The minimum value is {TRADE_MIN_BTC:.8f}"}
        
        balance = sats_to_btc(lnd.channels_balance()["local_balance"]["sat"])
        if (amount > balance):
            return {"message": "internal server error."}

        service_fee_amount = amount * SERVICE_FEE_RATE / 100
        if (service_fee_amount < SERVICE_MIN_FEE_RATE):
            service_fee_amount = SERVICE_MIN_FEE_RATE

        address = get_new_address()["address"]

        payload = {"id": urandom(16).hex(), "amount": amount, "invoice": invoice, "fee": service_fee_amount, "base": base, "quote": quote, "type": "loop-in"}
        redis.set(f"torch.light.address.{address}", dumps(payload))
        redis.expire(f"torch.light.address.{address}", expiry)
        return {"id": payload["id"], "address": address, "amount": amount + service_fee_amount, "expiry": timestamp + expiry}
    else:
        return {"message": "internal server error."}

def get_lookup(id: str) -> dict:
    tx = db.get(Query().id == id)
    if (tx == None):
        return {"message": "ID not found."}
    else:
        return tx