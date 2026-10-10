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
    email: str  # plain str on output: never 500 on an unusual admin address
    is_admin: bool = False
    created_at: datetime


# ---------- Transaction schemas ----------

TransactionType = Literal["income", "recurring", "discretionary"]


class TransactionCreate(BaseModel):
    """What the client sends to POST /transactions."""
    type: TransactionType
    category: str
    description: str = Field(default="", max_length=200, description="Optional; defaults to the category name")
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


# ---------- Narrative report schemas (step 7) ----------

NarrativeTone = Literal["encouraging", "analyst", "blunt", "storyteller"]


class NarrativeRequest(BaseModel):
    """What the client sends to POST /narrative."""
    tone: NarrativeTone = "encouraging"
    language: Literal["en", "fa"] = "en"


class NarrativeResponse(BaseModel):
    """What the API sends back from POST /narrative."""
    narrative: str


# ---------- Admin schemas ----------

class AdminUserOut(BaseModel):
    """One row of the admin user table."""
    id: int
    email: str
    is_admin: bool
    created_at: datetime
    transaction_count: int


class CategoryTotal(BaseModel):
    category: str
    total: Decimal


class AdminStats(BaseModel):
    """Site-wide numbers for the admin panel."""
    total_users: int
    total_admins: int
    total_transactions: int
    total_income: Decimal
    total_expense: Decimal
    top_expense_categories: list[CategoryTotal]
