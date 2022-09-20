from services.redis import redis
from configs import LND_HOST, LND_MACAROON, LND_CERTIFICATE
from base64 import b64decode
from json import dumps
from lnd import Lnd

lnd = Lnd(LND_HOST, LND_MACAROON, LND_CERTIFICATE)

def create_invoice(amount: float, memo="", expiry=86400, metadata={}) -> dict:
    amount = round(amount * pow(10, 8))

    # Generate lightning invoice.
    invoice = lnd.create_invoice(amount, memo, expiry)
    if invoice.get("error"):
        return {"message": "There was a problem trying to create a new invoice."}
    
    # Relate a user to a payment has and 
    # add an expiration time. 
    payload = {"metadata": metadata}
    
    # Get the hashed payment.
    payment_hash = b64decode(invoice["r_hash"]).hex()

    # Relate payment_hash to user id.
    redis.set(f"torch.light.invoice.{payment_hash}", dumps(payload))
    redis.expire(f"torch.light.invoice.{payment_hash}", expiry)
    return {"payment_hash": payment_hash, "payment_request": invoice["payment_request"], "expiry": expiry}