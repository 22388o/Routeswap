from models.schemas import SwapSchema
from services import swap
from configs import API_HOST, API_PORT
from fastapi import FastAPI, HTTPException

import uvicorn

api = FastAPI()

@api.post("/api/v1/swap/create")
def create_new_swap(data: SwapSchema):
    swap_details_payment = swap.create_swap(data.base, data.quote, data.address, data.amount, data.feerate)
    if (swap_details_payment.get("message") != None):
        raise HTTPException(500, detail=swap_details_payment["message"])
    else:
        return swap_details_payment

@api.get("/api/v1/lookup/{txid}")
def get_lookup(txid):
    lookup = swap.get_lookup(txid)
    if (lookup.get("message") != None):
        raise HTTPException(500, detail=lookup["message"])
    else:
        return lookup
    
def start():
    uvicorn.run(api, host=API_HOST, port=API_PORT)
