from typing import Optional
from pydantic import BaseModel, PositiveFloat, validator
from configs import SUPPORTED_CURRENCIES, TRADE_MIN_BTC

class SwapSchema(BaseModel):
    base: str
    quote: str
    address: str
    amount: PositiveFloat
    feerate: Optional[PositiveFloat]

    @validator("base")
    def validator_base(cls, base: str):
        if not (base in SUPPORTED_CURRENCIES):
            raise ValueError("Currency invalid.")
        return base
    
    @validator("quote")
    def validator_quote(cls, quote: str):
        if not (quote in SUPPORTED_CURRENCIES):
            raise ValueError("Currency invalid.")
        return quote
    
    @validator("amount")
    def validator_amount(cls, amount: float):
        if (amount < TRADE_MIN_BTC):
            raise ValueError(f"The minimum value is {TRADE_MIN_BTC:.8f}")
        return amount