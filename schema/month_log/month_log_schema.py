from typing import List, Dict, Any
from pydantic import BaseModel


class MonthLogSchema(BaseModel):
    _id: int
    time: str
    description: str
    amount: float

    class Config:
        form_attributes = {
            "_id": "id",
            "time": "time",
            "description": "description",
            "amount": "amount"
        }