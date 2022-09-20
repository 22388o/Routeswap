from services import lnd
from configs import LN_BACKEND

def create_invoice(amount: float, memo="", expiry=86400, metadata={}, typeof="loop-out") -> dict:
    if (LN_BACKEND == "lnd"):
        return lnd.create_invoice(amount, memo=memo, expiry=expiry, metadata=metadata, typeof=typeof)
