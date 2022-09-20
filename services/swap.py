from services.lightning import create_invoice
from services.bitcoin import bitcoin, get_balance, get_estimate_fee
from helpers.helpers import sats_to_btc, btc_to_sats
from database import db
from configs import SERVICE_FEE_RATE, SERVICE_MIN_FEE_RATE
from tinydb import Query
from time import time

def create_swap(base: str, quote: str, address: str, amount: float, feerate: float):
    if ((base == "LN-BTC") and (quote == "BTC")):
        if (bitcoin.validate_address(address)["isvalid"] == False):
            return {"message": "Address invalid."}
        
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
        return {"payment_request": payment_request["payment_request"], "payment_hash": payment_request["payment_hash"], "expiry": timestamp + expiry}

def get_lookup(id: str) -> dict:
    tx = db.get(Query().id == id)
    if (tx == None):
        return {"message": "ID not found."}
    else:
        return tx