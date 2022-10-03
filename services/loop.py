from services.lightning import create_invoice, decode_invoice
from services.bitcoin import bitcoin, get_balance, get_estimate_fee, get_new_address
from helpers.helpers import sats_to_btc, btc_to_sats
from services.redis import redis
from services.lnd import lnd

from database import db
from configs import SERVICE_FEE_RATE, SERVICE_MIN_FEE_RATE, LOOP_MIN_BTC

from tinydb import Query
from time import time
from json import dumps, loads

def create_loop_out(address: str, amount: float, feerate: float = 0, webhook=None) -> dict:
    if (feerate < 1):
        return {"message": "Ferrate minimum is 1 sats / vbytes."}

    if (bitcoin.validate_address(address)["isvalid"] == False):
        return {"message": "Address invalid."}

    if (amount < LOOP_MIN_BTC):
        return {"message": f"The minimum value is {LOOP_MIN_BTC:.8f}"}
    
    balance = sats_to_btc(get_balance()["confirmed_balance"])
    if (amount > balance):
        return {"message": "We are short of liquidity at the moment."}

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
    timestamp = time()
    metadata = {
        "address": address, 
        "amount": amount, 
        "feerate": feerate, 
        "created_at": timestamp,
        "updated_at": timestamp
    }
    payment_request = create_invoice(
        amount=service_fee_and_tx_amount, 
        expiry=expiry, 
        metadata=metadata, 
        typeof="loop-out"
    )
    
    txid = payment_request["payment_hash"]
    tx = {
        "id": txid,
        "from": {
            "invoice": payment_request["payment_request"], 
            "amount": service_fee_and_tx_amount,
            "expiry": timestamp + expiry,
            "status": "pending"
        },
        "type": "loop-out"
    }
    tx["to"] = metadata
    tx["to"]["txid"] = None
    tx["to"]["status"] = "pending"

    tx["webhook"] = webhook
    tx["created_at"] = timestamp
    tx["updated_at"] = timestamp
    
    del tx["to"]["updated_at"]
    del tx["to"]["created_at"]

    redis.set(f"torch.light.tx.{txid}", dumps(tx))
    redis.expire(f"torch.light.tx.{txid}", expiry)
    return tx

def create_loop_in(invoice: str, webhook=None) -> dict:
    try:
        dec_invoice = decode_invoice(invoice)
    except:
        return {"message": "Invoice invalid."}

    if (lnd.lookup_invoice(dec_invoice["payment_hash"]).get("settled")):
        return {"message": "The invoice has already been paid."}

    timestamp = int(dec_invoice["timestamp"])
    expiry = int(dec_invoice["expiry"])
    if (time() > (timestamp + expiry)):
        return {"message": "Invoice expired."}
    
    if (expiry > 86400):
        return {"message": "Invoice invalid."}
    
    amount = sats_to_btc(dec_invoice["num_satoshis"])
    if (amount < LOOP_MIN_BTC):
        return {"message": f"The minimum value is {LOOP_MIN_BTC:.8f}"}

    balance = sats_to_btc(lnd.channels_balance()["local_balance"]["sat"])
    if (amount > balance):
        return {"message": "We are short of liquidity at the moment."}

    service_fee_amount = (amount * SERVICE_FEE_RATE / 100)
    if (service_fee_amount < SERVICE_MIN_FEE_RATE):
        service_fee_amount = SERVICE_MIN_FEE_RATE

    address = get_new_address()["address"]
    estimate_fee = get_estimate_fee(address, btc_to_sats(amount + service_fee_amount), target_conf=6)
    feerate_sat_per_byte = float(estimate_fee["feerate_sat_per_byte"])
    
    timestamp = time()

    txid = dec_invoice["payment_hash"]
    metadata = {
        "id": txid, 
        "amount": amount, 
        "invoice": invoice, 
        "created_at": timestamp,
        "updated_at": timestamp
    }

    redis.set(f"torch.light.address.{address}", dumps(metadata))
    redis.expire(f"torch.light.address.{address}", expiry)

    txid = metadata["id"]
    tx = {
        "id": txid,
        "from": {
            "address": address, 
            "amount": amount + service_fee_amount,
            "feerate": feerate_sat_per_byte,
            "expiry": timestamp + expiry,
            "status": "pending"
        },
        "type": "loop-in"
    }

    tx["to"] = metadata
    tx["to"]["txid"] = None
    tx["to"]["status"] = "pending"
    
    tx["webhook"] = webhook
    tx["created_at"] = timestamp
    tx["updated_at"] = timestamp

    del tx["to"]["updated_at"]
    del tx["to"]["created_at"]
    del tx["to"]["id"]
    
    redis.set(f"torch.light.tx.{txid}", dumps(tx))
    redis.expire(f"torch.light.tx.{txid}", expiry)
    return tx

def get_transaction(txid: str) -> dict:
    tx = db.get(Query().id == txid)
    if (tx == None):
        tx = redis.get(f"torch.light.tx.{txid}")
        if (tx == None):
            return {"message": "TxID not found."}
        else:
            return loads(tx)
    else:
        return tx