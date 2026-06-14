from pydantic import BaseModel

class DebtRequest(BaseModel):
    balance: float
    interest_rate: float

class ApiResponse(BaseModel):
    status: str
    message: str
