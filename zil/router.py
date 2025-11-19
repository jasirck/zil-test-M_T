from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from .database import get_db
from .models import User, Expense
from .schemas import UserCreate, UserOut, ExpenseCreate, ExpenseOut, TotalOut, Token
from .utils import verify_password, get_password_hash, create_access_token, decode_access_token
from .settings import ACCESS_TOKEN_EXPIRE
from datetime import datetime
from sqlalchemy import func, extract

"""auth Routes """
router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


@router.post("/register", response_model=Token)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check username exists
    q = await db.execute(select(User).where(User.username == user_in.username))
    existing = q.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed = get_password_hash(user_in.password)
    new_user = User(username=user_in.username, salary=user_in.salary, hashed_password=hashed)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    access_token = create_access_token({"sub": new_user.username}, expires_delta=ACCESS_TOKEN_EXPIRE)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(User).where(User.username == form_data.username))
    user = q.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    access_token = create_access_token({"sub": user.username}, expires_delta=ACCESS_TOKEN_EXPIRE)
    return {"access_token": access_token, "token_type": "bearer"}


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