from helpers.helpers import btc_to_sats, sats_to_btc
from services.redis import redis
from services.lnd import lnd

from database import db
from bitcoin import Bitcoin
from configs import BTC_HOST, BTC_PASS, BTC_USER, SERVICE_FEE_RATE
from json import loads
from time import time

bitcoin = Bitcoin(BTC_HOST)
bitcoin.auth(BTC_USER, BTC_PASS)

def start():
    for data in lnd.transactions_subscribe().iter_lines():
        data = loads(data).get("result")
        if (data == None) or ("-" in data["amount"]):
            continue
        
        num_confirmations = int(data["num_confirmations"])
        if (num_confirmations < 1):
            continue
        
        txid = data["tx_hash"]
        amount = float(data["amount"])
        for address in data["dest_addresses"]:
            # Get the user_id of payment_hash in redis.
            payload = redis.get(f"torch.light.address.{address}")
            if (payload == None):
                continue
            else:
                payload = loads(payload)

            redis.delete(f"torch.light.address.{address}")

            tx = loads(redis.get("torch.light.tx." + payload["id"]))
            if (sats_to_btc(amount) < (tx["from"]["amount"])):
                continue
            
            feerate = (SERVICE_FEE_RATE * 25 / 100)
            fee_limit_sat = btc_to_sats((tx["from"]["amount"] - amount) * feerate / 100)

            invoice = payload["invoice"]
            pay = lnd.pay_invoice(invoice, fee_limit_sat=fee_limit_sat)
            if (pay == None) or (pay["status"] != "SUCCEEDED"):
                continue
            
            redis.delete("torch.light.tx." + payload["id"])
            
            tx["from"]["status"] = "settled"
            tx["to"]["status"] = "settled"
            tx["to"]["txid"] = txid
            tx["updated_at"] = time()
            db.insert(tx)

def get_balance() -> dict:
    return lnd.wallet_balance()

def get_estimate_fee(address: str, amount: float, target_conf: int = 144) -> dict:
    return lnd.get_estimate_fee(address, amount, target_conf=target_conf)

def get_new_address() -> dict:
    return lnd.get_address()