from fastapi.middleware.cors import CORSMiddleware
from services.bitcoin import get_estimate_fee, get_new_address, bitcoin
from helpers.helpers import sats_to_btc
from models.schemas import LoopinSchema, LoopoutSchema
from services.lnd import lnd
from services import loop
from configs import API_HOST, API_PORT, LOOP_MIN_BTC, SERVICE_FEE_RATE, SERVICE_MIN_FEE_RATE
from fastapi import FastAPI, HTTPException

import uvicorn

api = FastAPI()
api.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@api.post("/api/v1/loop/out")
def loop_out(data: LoopoutSchema):
    address = data.address
    feerate = data.feerate
    amount = data.amount

    loop_out = loop.create_loop_out(address, amount, feerate=feerate)
    if (loop_out.get("message") != None):
        raise HTTPException(500, detail=loop_out["message"])
    else:
        return loop_out

@api.post("/api/v1/loop/in")
def loop_in(data: LoopinSchema):
    loop_in = loop.create_loop_in(data.invoice)
    if (loop_in.get("message") != None):
        raise HTTPException(500, detail=loop_in["message"])
    else:
        return loop_in

@api.get("/api/v1/tx/{txid}")
def get_transaction(txid: str):
    tx = loop.get_transaction(txid)
    if (tx.get("message") != None):
        raise HTTPException(500, detail=tx["message"])
    else:
        return tx

@api.get("/api/v1/info")
def info():
    return {"LOOP_MIN_BTC": LOOP_MIN_BTC, "SERVICE_FEE_RATE": SERVICE_FEE_RATE, "SERVICE_MIN_FEE_RATE": SERVICE_MIN_FEE_RATE,}

@api.get("/api/v1/estimate/fee")
def estimate_fee(address: str = None, amount: float = 0, feerate: float = 1):
    if (address == None) or (amount <= 0) or (feerate <= 0):
        raise HTTPException(500)

    if (bitcoin.validate_address(address)["isvalid"] == False):
        address = get_new_address()["address"]

    amount = int(amount * pow(10, 8))
    estimate_fee = get_estimate_fee(address, amount)
    if not (estimate_fee.get("fee_sat")):
        raise HTTPException(500)
    
    fee_sat = int(estimate_fee["fee_sat"])
    feerate_sat_per_byte = int(estimate_fee["feerate_sat_per_byte"])
    
    fee_sat = int((fee_sat / feerate_sat_per_byte) * feerate)
    fee_btc = sats_to_btc(fee_sat)
    return {"fee_sats": fee_sat, "fee_btc": fee_btc}

@api.get("/api/v1/decode/invoice/{payment_request}")
def decode_invoice(payment_request: str):
    decode_invoice = lnd.decode_invoice(payment_request)
    if (decode_invoice.get("destination") == None):
        raise HTTPException(500, "Invoice invalid.")
    else:
        return decode_invoice

def start():
    uvicorn.run(api, host=API_HOST, port=API_PORT)