# month_log/schemas.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List

from schema.list_schema import PaginationDetails


# --- Monthly Salary Schemas ---
class MonthlySalaryBase(BaseModel):
    salary_amount: Decimal = Field(..., gt=0,
                                   description="The amount of monthly salary.")
    month_year: date

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
    user_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Expense Schemas ---


class ExpenseBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Amount spent.")
    description: str = Field(..., min_length=1, max_length=255)
    date_logged: Optional[datetime] = Field(default_factory=datetime.now)


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0)
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    date_logged: Optional[datetime] = Field(None)


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


class ExpenseFilterInputSchema(BaseModel):  # Input from View to Service
    filter_date: Optional[date] = None
    filter_month_year: Optional[str] = None
    page: int = Field(1, gt=0)
    page_size: int = Field(10, gt=0, le=100)
    sort_by: Optional[str] = None  # e.g., "date_logged", "-amount"

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


class MonthlyLogContextData(BaseModel):  # Output from Service to View
    current_salary: Optional[MonthlySalarySchema] = None
    total_spent_for_period: Decimal = Decimal('0.00')  # Renamed for clarity
    saved_amount_for_period: Decimal = Decimal('0.00')  # Renamed for clarity
    expenses: List[ExpenseSchema] = []
    date_filters: List[DateFilterSchema] = []
    pagination: PaginationDetails
    # For templates, direct access to current filters might be useful
    current_filters_applied: ExpenseFilterInputSchema
