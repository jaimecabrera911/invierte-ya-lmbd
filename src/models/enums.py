from enum import Enum


class FundCategory(str, Enum):
    FPV = "FPV"
    FIC = "FIC"


class TransactionType(str, Enum):
    SUBSCRIPTION = "subscription"
    CANCELLATION = "cancellation"
    DEPOSIT = "deposit"


class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"


class TransactionStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"