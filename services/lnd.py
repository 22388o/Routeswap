from helpers.helpers import btc_to_sats, sats_to_btc
from services.redis import redis
from database import db
from configs import LN_BACKEND, LND_HOST, LND_MACAROON, LND_CERTIFICATE

from base64 import b64decode
from json import dumps, loads
from time import time
from lnd import Lnd

lnd = Lnd(LND_HOST, LND_MACAROON, LND_CERTIFICATE)

def start():
    if (LN_BACKEND != "lnd"):
        return
    
    for data in lnd.invoice_subscribe().iter_lines():
        data = loads(data).get("result")
        if not (data) or (data["state"] != "SETTLED"):
            continue
        
        # Decode base64 and encode the bytes in hex.
        payment_hash = b64decode(data["r_hash"]).hex()

        # Fetch hash payment information.
        lookup_invoice = lnd.lookup_invoice(payment_hash)
        if (lookup_invoice["state"] != "SETTLED"):
            continue
                
        # Get the user_id of payment_hash in redis.
        payload = redis.get(f"torch.light.invoice.{payment_hash}")
        if (payload == None):
            continue
        else:
            payload = loads(payload)
        
        metadata = payload["metadata"]
        amount = btc_to_sats(metadata["amount"])
        if (amount > int(lookup_invoice["value"])):
            continue
            
        address = metadata["address"]
        feerate = metadata["feerate"]

        redis.delete(f"torch.light.invoice.{payment_hash}")

        # Create an unchain transaction with address 
        # specified in the contract.
        send_coins = lnd.send_coins(address, amount, sat_per_vbyte=feerate)

        tx = loads(redis.get(f"torch.light.tx.{payment_hash}"))
        tx["from"]["status"] = "settled"
        tx["to"]["status"] = "settled"
        tx["to"]["txid"] = send_coins["txid"]
        tx["updated_at"] = time()
        db.insert(tx)

        redis.delete(f"torch.light.tx.{payment_hash}")

def create_invoice(amount: float, memo="", expiry=86400, metadata={}, typeof="loop-out") -> dict:
    amount = round(amount * pow(10, 8))

    # Generate lightning invoice.
    invoice = lnd.create_invoice(amount, memo, expiry)
    if invoice.get("error"):
        return {"message": "There was a problem trying to create a new invoice."}
    
    # Relate a user to a payment has and 
    # add an expiration time. 
    payload = {"type": typeof, "metadata": metadata}
    
    # Get the hashed payment.
    payment_hash = b64decode(invoice["r_hash"]).hex()
    
    # Relate payment_hash to user id.
    redis.set(f"torch.light.invoice.{payment_hash}", dumps(payload))
    redis.expire(f"torch.light.invoice.{payment_hash}", expiry)
    return {"payment_hash": payment_hash, "payment_request": invoice["payment_request"], "expiry": expiry}