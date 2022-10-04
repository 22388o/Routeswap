from pydantic import BaseModel, PositiveFloat
from typing import Optional

class LoopoutSchema(BaseModel):
    address: str
    amount: PositiveFloat
    feerate: PositiveFloat
    webhook: Optional[str]

class LoopinSchema(BaseModel):
    invoice: str
    webhook: Optional[str]
