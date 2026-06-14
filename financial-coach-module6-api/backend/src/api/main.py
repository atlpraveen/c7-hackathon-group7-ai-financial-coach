from fastapi import FastAPI
from .routes import health, debt, savings, budget, investment, documents

app = FastAPI(title="Financial Coach API")

app.include_router(health.router)
app.include_router(debt.router, prefix="/debt", tags=["Debt"])
app.include_router(savings.router, prefix="/savings", tags=["Savings"])
app.include_router(budget.router, prefix="/budget", tags=["Budget"])
app.include_router(investment.router, prefix="/investment", tags=["Investment"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
