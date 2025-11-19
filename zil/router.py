from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .models import User, Expense
from .schemas import UserCreate, UserOut, ExpenseCreate, ExpenseOut, TotalOut
from datetime import datetime
from sqlalchemy import func, extract



""" User Routes """

router_users = APIRouter(prefix="/users", tags=["Users"])


@router_users.post("/", response_model=UserOut)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(username=data.username, salary=data.salary)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


''''expenses Routes '''

router_expenses = APIRouter(prefix="/expenses", tags=["Expenses"])


@router_expenses.post("/", response_model=ExpenseOut)
async def create_expense(data: ExpenseCreate, db: AsyncSession = Depends(get_db)):

    user = await db.get(User, data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    expense = Expense(**data.dict())
    db.add(expense)
    await db.commit()
    await db.refresh(expense)

    return expense


@router_expenses.get("/{user_id}", response_model=list[ExpenseOut])
async def list_expenses(
    user_id: int,
    day: str = None,
    week: int = None,
    month: int = None,
    year: int = None,
    category: str = None,
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    query = select(Expense).where(Expense.user_id == user_id)

    if day:
        day_date = datetime.strptime(day, "%Y-%m-%d")
        query = query.where(
            extract("day", Expense.created_at) == day_date.day,
            extract("month", Expense.created_at) == day_date.month,
            extract("year", Expense.created_at) == day_date.year,
        )

    if week and year:
        query = query.where(
            extract("week", Expense.created_at) == week,
            extract("year", Expense.created_at) == year,
        )

    if month and year:
        query = query.where(
            extract("month", Expense.created_at) == month,
            extract("year", Expense.created_at) == year,
        )

    if category:
        query = query.where(Expense.category == category)

    result = await db.execute(query)
    return result.scalars().all()



''' totals Routes '''

router_totals = APIRouter(prefix="/totals", tags=["Totals"])


@router_totals.get("/{user_id}", response_model=TotalOut)
async def get_totals(user_id: int, db: AsyncSession = Depends(get_db)):

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total_expense = await db.execute(
        select(func.sum(Expense.amount)).where(Expense.user_id == user_id)
    )
    total_expense = total_expense.scalar() or 0.0

    category_breakdown = await db.execute(
        select(Expense.category, func.sum(Expense.amount))
        .where(Expense.user_id == user_id)
        .group_by(Expense.category)
    )

    breakdown_dict = {cat: amt for cat, amt in category_breakdown.all()}

    return TotalOut(
        total_expense=total_expense,
        total_salary=user.salary,
        remaining_amount=user.salary - total_expense,
        category_breakdown=breakdown_dict
    )