from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .models import CategoryEnum

class UserCreate(BaseModel):
    username: str
    salary: Optional[float] = 0.0

class UserOut(BaseModel):
    user_id: int
    username: str
    salary: float

    class Config:
        orm_mode = True


class ExpenseCreate(BaseModel):
    user_id: int
    name: str
    amount: float = Field(gt=0)
    category: CategoryEnum


class ExpenseOut(BaseModel):
    expense_id: int
    user_id: int
    name: str
    amount: float
    category: CategoryEnum
    created_at: datetime

    class Config:
        orm_mode = True


class TotalOut(BaseModel):
    total_expense: float
    total_salary: float
    remaining_amount: float
    category_breakdown: dict
