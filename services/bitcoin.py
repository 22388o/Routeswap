from services.lnd import lnd
from bitcoin import Bitcoin
from configs import BTC_HOST, BTC_PASS, BTC_USER

bitcoin = Bitcoin(BTC_HOST)
bitcoin.auth(BTC_USER, BTC_PASS)

def get_balance() -> dict:
    return lnd.wallet_balance()

def get_estimate_fee(address: str, amount: float, target_conf: int = 144) -> dict:
    return lnd.get_estimate_fee(address, amount, target_conf=target_conf)