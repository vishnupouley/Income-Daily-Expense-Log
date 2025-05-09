# monthly_income/schemas.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List

# --- Monthly Salary Schemas ---
class MonthlySalaryBase(BaseModel):
    salary_amount: Decimal = Field(..., gt=0, description="The amount of monthly salary.")
    month_year: date # Expects YYYY-MM-DD, will represent the first day of the month.

    @field_validator('month_year')
    @classmethod
    def ensure_first_day_of_month(cls, v: date) -> date:
        if v.day != 1:
            return date(v.year, v.month, 1)
        return v

class MonthlySalaryCreate(MonthlySalaryBase):
    pass

class MonthlySalarySchema(MonthlySalaryBase):
    id: int
    user_id: int # Assuming you have a user model with an int PK
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Expense Schemas ---
class ExpenseBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Amount spent.")
    description: str = Field(..., min_length=1, max_length=255)
    date_logged: Optional[datetime] = Field(default_factory=datetime.now, description="Date and time of the expense. Defaults to now.")

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0, description="New amount spent.")
    description: Optional[str] = Field(None, min_length=1, max_length=255, description="New description.")
    date_logged: Optional[datetime] = Field(None, description="New date and time of the expense.")

class ExpenseSchema(ExpenseBase):
    id: int
    user_id: int
    date_logged: datetime 
    balance_after_this_expense_in_month: Optional[Decimal] = None 
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Filtering and Utility Schemas ---
class DateFilterSchema(BaseModel):
    id: int 
    date_value: str 
    display_text: str 

class ExpenseFilterInputSchema(BaseModel):
    filter_date: Optional[date] = None 
    filter_month_year: Optional[str] = None # Expects "YYYY-MM" format
    page: int = Field(1, gt=0)
    page_size: int = Field(10, gt=0, le=100) 
    sort_by: Optional[str] = None 

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
        
class MonthlyLogViewData(BaseModel):
    current_salary: Optional[MonthlySalarySchema] = None
    total_spent_this_month: Decimal = Decimal('0.00')
    saved_amount_this_month: Decimal = Decimal('0.00')
    expenses: List[ExpenseSchema] = []
    total_expense_count: int = 0
    date_filters: List[DateFilterSchema] = []
    current_page: int
    total_pages: int
    page_size: int
