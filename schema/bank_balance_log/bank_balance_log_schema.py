from typing import Optional
from pydantic import BaseModel, field_validator, Field
from datetime import time, date


class BankBalanceLogCreateSchema(BaseModel):
    transaction_type: str = Field(..., description="Transaction type")
    amount: float = Field(..., description="Amount")
    description: Optional[str] = Field("Transaction", description="Description")

    @field_validator("amount", mode="after")
    def validate_amount(cls, v):
        return float(v)

    class Config:
        form_attributes = True

class BankBalanceLogResponseSchema(BaseModel):
    _id: int
    date_of_transaction: date = Field(..., description="Date of transaction")
    time_of_transaction: time = Field(..., description="Time of transaction")
    transaction_type: str = Field(..., description="Transaction type")
    amount: float = Field(..., description="Amount")
    description: Optional[str] = Field("Basic Transaction", description="Description")

    class Config:
        form_attributes = True


class BankBalanceLogDeleteSchema(BaseModel):
    _id: int

    class Config:
        form_attributes = True


class BankBalanceUpdateSchema(BaseModel):
    bank_balance: float = Field(..., description="Bank balance")

    @field_validator("bank_balance", mode="after")
    def validate_bank_balance(cls, v):
        return float(v)

    class Config:
        form_attributes = True


class BankBalanceResponseSchema(BaseModel):
    _id: int
    bank_balance: float = Field(..., description="Bank balance")

    class Config:
        form_attributes = True