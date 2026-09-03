from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, ConfigDict, Field


# ---------- User schemas ----------

class UserCreate(BaseModel):
    """What the client sends to POST /register."""
    email: EmailStr
    password: str


class UserOut(BaseModel):
    """What the API sends back — note: no password field, ever."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


# ---------- Transaction schemas ----------

TransactionType = Literal["income", "recurring", "discretionary"]


class TransactionCreate(BaseModel):
    """What the client sends to POST /transactions."""
    type: TransactionType
    category: str
    description: str
    amount: Decimal = Field(gt=0, description="Must be positive; sign is implied by 'type'")
    txn_date: date


class TransactionOut(BaseModel):
    """What the API sends back for a single transaction."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: TransactionType
    category: str
    description: str
    amount: Decimal
    txn_date: date
    created_at: datetime
