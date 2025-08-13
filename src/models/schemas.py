from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from .enums import FundCategory, TransactionType, NotificationType, TransactionStatus, SubscriptionStatus


# Modelos de autenticación
class UserCreate(BaseModel):
    email: str
    phone: str
    password: str
    notification_preference: NotificationType = NotificationType.EMAIL


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# Modelos de entidades
class User(BaseModel):
    user_id: str
    balance: Decimal
    email: str
    phone: str
    notification_preference: NotificationType
    created_at: str
    updated_at: str


class Fund(BaseModel):
    fund_id: str
    name: str
    minimum_amount: Decimal
    category: FundCategory
    is_active: bool = True
    created_at: str


class FundSubscription(BaseModel):
    user_id: str
    fund_id: str
    invested_amount: Decimal
    subscription_date: str
    status: SubscriptionStatus
    transaction_id: str


class Transaction(BaseModel):
    user_id: str
    transaction_id: str
    fund_id: str
    transaction_type: TransactionType
    amount: Decimal
    timestamp: str
    status: TransactionStatus
    balance_before: Decimal
    balance_after: Decimal


# Modelos de request
class SubscriptionRequest(BaseModel):
    fund_id: str
    amount: Optional[Decimal] = None  # Si no se especifica, usa el mínimo


class CancellationRequest(BaseModel):
    fund_id: str


class DepositRequest(BaseModel):
    amount: Decimal