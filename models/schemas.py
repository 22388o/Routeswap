from pydantic import BaseModel, PositiveFloat

class LoopoutSchema(BaseModel):
    address: str
    amount: PositiveFloat
    feerate: PositiveFloat

class LoopinSchema(BaseModel):
    invoice: str