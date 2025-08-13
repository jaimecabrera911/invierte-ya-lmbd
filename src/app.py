import os
from datetime import timedelta
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from mangum import Mangum
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from dotenv import load_dotenv

# Importar servicios
from .services.auth_service import AuthService
from .services.user_service import UserService
from .services.fund_service import FundService
from .services.transaction_service import TransactionService
from .services.notification_service import NotificationService

# Cargar variables de entorno
load_dotenv()

app = FastAPI(
    title="Invierte Ya - Sistema de Fondos API",
    version="1.0.0",
    description="API para gestión de fondos de inversión FPV y FIC"
)

# Configuración de autenticación
security = HTTPBearer()


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


# Modelos Pydantic
class UserCreate(BaseModel):
    email: str
    phone: str
    password: str
    notification_preference: NotificationType = (
        NotificationType.EMAIL
    )


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


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


class SubscriptionRequest(BaseModel):
    fund_id: str
    amount: Optional[Decimal] = None  # Si no se especifica, usa el mínimo


class CancellationRequest(BaseModel):
    fund_id: str


class DepositRequest(BaseModel):
    amount: Decimal


# Funciones de utilidad
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    return AuthService.get_current_user(credentials)


@app.get("/")
def read_root():
    return {
        "message": "Bienvenido a Invierte Ya - Sistema de Fondos",
        "version": "1.0.0",
        "environment": os.environ.get('ENVIRONMENT', 'unknown'),
        "description": (
            "API para gestión de Fondos Voluntarios de Pensión "
            "(FPV) y Fondos de Inversión Colectiva (FIC)"
        )
    }


@app.get("/health")
def health_check():
    """Endpoint de salud para verificar el estado de la API y DynamoDB"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.environ.get('ENVIRONMENT', 'unknown'),
        "tables_configured": {
            "users": (
                os.environ.get('USERS_TABLE_NAME') is not None
            ),
            "funds": (
                os.environ.get('FUNDS_TABLE_NAME') is not None
            ),
            "user_funds": (
                os.environ.get('USER_FUNDS_TABLE_NAME') is not None
            ),
            "transactions": (
                os.environ.get('TRANSACTIONS_TABLE_NAME') is not None
            ),
            "notifications": (
                os.environ.get('NOTIFICATIONS_TABLE_NAME') is not None
            )
        }
    }
    return health_status


@app.post("/auth/register", response_model=Token)
def register_user(user_data: UserCreate):
    """Registrar un nuevo usuario."""
    try:
        # Crear hash de la contraseña
        hashed_password = AuthService.get_password_hash(user_data.password)
        
        # Crear usuario usando el servicio
        UserService.create_user(
            email=user_data.email,
            phone=user_data.phone,
            hashed_password=hashed_password,
            notification_preference=user_data.notification_preference.value
        )
        
        # Crear token de acceso
        access_token_expires = timedelta(minutes=30)
        access_token = AuthService.create_access_token(
            data={"sub": user_data.email}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@app.post("/auth/login", response_model=Token)
def login_user(user_credentials: UserLogin):
    """Autenticar usuario y retornar token de acceso"""
    try:
        # Buscar usuario por email
        user = UserService.get_user_with_password(user_credentials.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verificar contraseña
        if not AuthService.verify_password(user_credentials.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Crear token de acceso
        access_token_expires = timedelta(minutes=30)
        access_token = AuthService.create_access_token(
            data={"sub": user['email']}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@app.post("/users", response_model=User)
def create_user(user_data: UserCreate):
    """Crear un nuevo usuario con saldo inicial"""
    try:
        timestamp = datetime.utcnow().isoformat()
        
        user_item = {
            'user_id': user_data.user_id,
            'balance': INITIAL_BALANCE,
            'email': user_data.email,
            'phone': user_data.phone,
            'notification_preference': (
                 user_data.notification_preference.value
             ),
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        users_table.put_item(Item=user_item)
        
        return User(**user_item)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear usuario: {str(e)}"
        )


@app.get("/users/me", response_model=User)
def get_user(current_user: str = Depends(get_current_user)):
    """Obtener información del usuario autenticado."""
    try:
        return UserService.get_user_by_email(current_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener usuario: {str(e)}"
        )


@app.get("/funds", response_model=List[Fund])
def get_funds():
    """Obtener lista de fondos disponibles."""
    try:
        return FundService.get_all_funds()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener fondos: {str(e)}"
        )


@app.post("/funds/subscribe")
def subscribe_to_fund(
    subscription: SubscriptionRequest,
    current_user: str = Depends(get_current_user)
):
    """Suscribirse a un fondo."""
    try:
        # Obtener información del usuario
        user = UserService.get_user_by_email(current_user)
        current_balance = Decimal(str(user['balance']))
        
        # Obtener información del fondo
        fund = FundService.get_fund_by_id(subscription.fund_id)
        minimum_amount = Decimal(str(fund['minimum_amount']))
        
        # Determinar monto de inversión
        investment_amount = subscription.amount or minimum_amount
        
        # Verificar que el monto sea suficiente
        if investment_amount < minimum_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El monto mínimo para este fondo es COP ${minimum_amount:,.0f}"
            )
        
        # Verificar saldo disponible
        if current_balance < investment_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No tiene saldo disponible para vincularse al fondo"
            )
        
        # Verificar si ya está suscrito
        existing_subscription = FundService.get_user_subscription(current_user, subscription.fund_id)
        if existing_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya está suscrito a este fondo"
            )
        
        # Calcular nuevo balance
        new_balance = current_balance - investment_amount
        
        # Crear transacción
        transaction_id = TransactionService.create_transaction(
            user_id=current_user,
            fund_id=subscription.fund_id,
            transaction_type="subscription",
            amount=investment_amount,
            balance_before=current_balance,
            balance_after=new_balance
        )
        
        # Actualizar saldo del usuario
        UserService.update_user_balance(current_user, new_balance)
        
        # Crear suscripción
        FundService.subscribe_user_to_fund(
            user_id=current_user,
            fund_id=subscription.fund_id,
            amount=investment_amount,
            transaction_id=transaction_id
        )
        
        # Crear notificación
        NotificationService.create_subscription_notification(
            user_id=current_user,
            transaction_id=transaction_id,
            fund_name=fund['name'],
            amount=investment_amount,
            notification_type=user['notification_preference']
        )
        
        return {
            "message": "Suscripción exitosa",
            "transaction_id": transaction_id,
            "fund_name": fund['name'],
            "invested_amount": float(investment_amount),
            "new_balance": float(new_balance),
            "notification_sent": user['notification_preference']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar suscripción: {str(e)}"
        )


@app.post("/funds/cancel")
def cancel_fund_subscription(
    cancellation: CancellationRequest,
    current_user: str = Depends(get_current_user)
):
    """Cancelar suscripción a un fondo"""
    try:
        # Verificar suscripción activa
        subscription = FundService.get_user_subscription(
            user_id=current_user,
            fund_id=cancellation.fund_id
        )
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró suscripción a este fondo"
            )
        
        if subscription['status'] != 'active':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La suscripción ya está cancelada"
            )
        
        # Obtener información del usuario
        user = UserService.get_user_by_email(current_user)
        current_balance = Decimal(str(user['balance']))
        invested_amount = Decimal(str(subscription['invested_amount']))
        
        # Obtener información del fondo
        fund = FundService.get_fund_by_id(cancellation.fund_id)
        
        # Generar ID de transacción
        transaction_id = TransactionService.generate_transaction_id()
        
        # Devolver dinero al usuario
        new_balance = current_balance + invested_amount
        UserService.update_user_balance(
            user_id=current_user,
            new_balance=new_balance
        )
        
        # Cancelar suscripción
        FundService.cancel_user_subscription(
            user_id=current_user,
            fund_id=cancellation.fund_id
        )
        
        # Registrar transacción
        TransactionService.create_transaction(
            user_id=current_user,
            transaction_id=transaction_id,
            fund_id=cancellation.fund_id,
            transaction_type='cancellation',
            amount=invested_amount,
            balance_before=current_balance,
            balance_after=new_balance
        )
        
        # Crear notificación
        NotificationService.create_cancellation_notification(
            user_id=current_user,
            transaction_id=transaction_id,
            fund_name=fund['name'],
            amount=invested_amount,
            notification_type=user['notification_preference']
        )
        
        return {
            "message": "Cancelación exitosa",
            "transaction_id": transaction_id,
            "fund_name": fund['name'],
            "returned_amount": float(invested_amount),
            "new_balance": float(new_balance),
            "notification_sent": user['notification_preference']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar cancelación: {str(e)}"
        )


@app.get("/users/me/transactions")
def get_user_transactions(
    current_user: str = Depends(get_current_user),
    limit: int = 20
):
    """Obtener historial de transacciones del usuario autenticado"""
    try:
        transactions = TransactionService.get_user_transactions(
            user_id=current_user,
            limit=limit
        )
        
        return {
            "transactions": transactions
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener transacciones: {str(e)}"
        )


@app.get("/users/me/subscriptions")
def get_user_subscriptions(
    current_user: str = Depends(get_current_user)
):
    """Obtener suscripciones activas del usuario autenticado"""
    try:
        subscriptions = FundService.get_user_active_subscriptions(
            user_id=current_user
        )
        
        return {
            "user_id": current_user,
            "active_subscriptions": subscriptions,
            "count": len(subscriptions)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener suscripciones: {str(e)}"
        )


@app.post("/users/me/deposit")
def deposit_money(
    deposit: DepositRequest,
    current_user: str = Depends(get_current_user)
):
    """Depositar dinero en la cuenta del usuario"""
    try:
        # Procesar depósito usando el servicio
        result = TransactionService.process_deposit(
            user_id=current_user,
            amount=deposit.amount
        )
        
        # Obtener información del usuario para la notificación
        user = UserService.get_user_by_email(current_user)
        
        # Crear notificación
        NotificationService.create_deposit_notification(
            user_id=current_user,
            transaction_id=result['transaction_id'],
            amount=deposit.amount,
            new_balance=result['new_balance'],
            notification_type=user['notification_preference']
        )
        
        return {
            'message': 'Depósito realizado exitosamente',
            'transaction_id': result['transaction_id'],
            'amount_deposited': float(deposit.amount),
            'previous_balance': float(result['previous_balance']),
            'new_balance': float(result['new_balance']),
            'timestamp': result['timestamp']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar depósito: {str(e)}"
        )


@app.post("/init-funds")
def initialize_funds():
    """Inicializar fondos predefinidos (solo para desarrollo)"""
    try:
        result = FundService.initialize_default_funds()
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al inicializar fondos: {str(e)}"
        )


handler = Mangum(app)
