# bank_balance_log/schemas.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List, Literal

from schema.list_schema import PaginationDetails

# --- Bank Account Schemas ---


class BankAccountBase(BaseModel):
    initial_balance: Decimal = Field(..., ge=0)


class BankAccountCreateOrUpdate(BankAccountBase):
    pass


class BankAccountSchema(BaseModel):
    id: int
    user_id: int
    current_balance: Decimal
    last_updated: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Bank Transaction Schemas ---


class BankTransactionBase(BaseModel):
    transaction_type: Literal['DEBIT', 'CREDIT']
    amount: Decimal = Field(..., gt=0)
    description: str = Field(..., min_length=1, max_length=255)
    date_logged: Optional[datetime] = Field(default_factory=datetime.now)


class BankTransactionCreateRequest(BankTransactionBase):
    pass


class BankTransactionSchema(BankTransactionBase):
    id: int
    user_id: int
    account_id: int
    date_logged: datetime
    balance_after_transaction: Decimal
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Filtering and Utility Schemas ---


class BankDateFilterSchema(BaseModel):
    id: int
    date_value: str
    display_text: str


# Input from View to Service
class BankTransactionFilterInputSchema(BaseModel):
    filter_date: Optional[date] = None
    filter_month_year: Optional[str] = None
    page: int = Field(1, gt=0)
    page_size: int = Field(10, gt=0, le=100)
    sort_by: Optional[str] = None
    transaction_type: Optional[Literal['DEBIT', 'CREDIT']] = None

    @field_validator('filter_month_year')
    @classmethod
    def validate_month_year_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m")
            return v
        except ValueError:
            raise ValueError("filter_month_year must be in YYYY-MM format")


class BankLogContextData(BaseModel):  # Output from Service to View
    bank_account: Optional[BankAccountSchema] = None
    transactions: List[BankTransactionSchema] = []
    date_filters: List[BankDateFilterSchema] = []
    pagination: PaginationDetails
    current_filters_applied: BankTransactionFilterInputSchema
