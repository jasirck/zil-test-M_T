from fastapi import FastAPI
from .database import engine, Base
from .database import get_db
from .router import router_users, router_expenses, router_totals

app = FastAPI(title="Expense & Budget Management API")

# Create tables on startup
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(router_users)
app.include_router(router_expenses)
app.include_router(router_totals)
