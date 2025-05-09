# bank_log/schemas.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List, Literal 

# --- Bank Account Schemas ---
class BankAccountBase(BaseModel):
    initial_balance: Decimal = Field(..., ge=0, description="The balance to set for the bank account.")

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
    amount: Decimal = Field(..., gt=0, description="Transaction amount, always positive.")
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

class BankLogViewData(BaseModel):
    bank_account: Optional[BankAccountSchema] = None
    transactions: List[BankTransactionSchema] = []
    total_transaction_count: int = 0
    date_filters: List[BankDateFilterSchema] = []
    current_page: int
    total_pages: int
    page_size: int
