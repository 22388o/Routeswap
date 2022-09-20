from models.schemas import SwapSchema
from services import swap
from configs import API_HOST, API_PORT
from fastapi import FastAPI, HTTPException

import uvicorn

api = FastAPI()

@api.post("/api/v1/swap/create")
def create_new_swap(data: SwapSchema):
    payment_request = swap.create_swap(
        data.base, 
        data.quote, 
        data.address, 
        data.amount,
        data.feerate
    )
    if (payment_request.get("message") != None):
        raise HTTPException(500, detail=payment_request)
    else:
        return payment_request

def start():
    uvicorn.run(api, host=API_HOST, port=API_PORT)
