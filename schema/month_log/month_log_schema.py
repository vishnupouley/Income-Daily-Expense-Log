from typing import Optional
from pydantic import BaseModel, field_validator, Field
from datetime import datetime, date, time


class MonthLogCreateSchema(BaseModel):
    expense: float = Field(..., description="Expense amount")
    description: Optional[str] = Field(
        "Daily expenses", description="Description of expense")

    @field_validator("expense", mode="after")
    def validate_expense(cls, v):
        return float(v)

    class Config:
        form_attributes = True


class MonthLogResponseSchema(BaseModel):
    _id: int
    date_of_expense: date = Field(..., description="Date of expense")
    time_of_expense: time = Field(..., description="Time of expense")
    expense: float = Field(..., description="Expense amount")
    description: str = Field(..., description="Description of expense")
    balance: float = Field(..., description="Balance amount")

    class Config:
        form_attributes = True


class MonthLogDeleteSchema(BaseModel):
    _id: int

    class Config:
        form_attributes = True


class MonthSalaryCreateSchema(BaseModel):
    salary: float = Field(..., description="Salary amount")
    date_of_salary: str = Field(..., description="Date of salary")

    @field_validator("salary", mode="after")
    def validate_salary(cls, v):
        return float(v)

    @field_validator("date_of_salary", mode="after")
    def validate_date_of_salary(cls, v):
        return datetime.strptime(v, "%Y-%m-%d")

    class Config:
        form_attributes = True


class MonthSalaryResponseSchema(BaseModel):
    _id: int
    salary: float = Field(..., description="Salary amount")
    date_of_salary: str = Field(..., description="Date of salary")

    class Config:
        form_attributes = True
