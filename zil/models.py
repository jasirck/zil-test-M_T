from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime, func
from sqlalchemy.orm import relationship
from .database import Base
import enum

class CategoryEnum(str, enum.Enum):
    Food = "Food"
    Transport = "Transport"
    Entertainment = "Entertainment"
    Utilities = "Utilities"
    Other = "Other"

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    salary = Column(Float, default=0.0)
    hashed_password = Column(String, nullable=False) 
    expenses = relationship("Expense", back_populates="user")


class Expense(Base):
    __tablename__ = "expenses"

    expense_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(Enum(CategoryEnum), nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="expenses")
