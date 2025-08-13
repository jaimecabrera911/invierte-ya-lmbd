from datetime import timedelta, datetime
from decimal import Decimal
from typing import List

import boto3
from fastapi import FastAPI, HTTPException, Depends, status
from mangum import Mangum
from dotenv import load_dotenv

# Importar servicios
from .services.auth_service import AuthService
from .services.user_service import UserService
from .services.fund_service import FundService
from .services.transaction_service import TransactionService
from .services.notification_service import NotificationService

# Importar modelos
from .models.schemas import (
    UserCreate, UserLogin, Token, User, Fund,
    SubscriptionRequest, CancellationRequest, DepositRequest
)
# Removed unused enum imports
from .config.settings import settings
from .utils.auth import get_current_user

# Cargar variables de entorno
load_dotenv()

# Constantes
INITIAL_BALANCE = Decimal('500000')  # Balance inicial de 500,000 COP

# Configurar DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
users_table = dynamodb.Table(settings.USERS_TABLE_NAME)

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION
)




@app.get("/")
def read_root():
    return {
        "message": "Bienvenido a Invierte Ya - Sistema de Fondos",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "description": settings.APP_DESCRIPTION
    }


@app.get("/health")
def health_check():
    """Endpoint de salud para verificar el estado de la API y DynamoDB"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "tables_configured": {
            "users": settings.USERS_TABLE_NAME is not None,
            "funds": settings.FUNDS_TABLE_NAME is not None,
            "user_funds": settings.USER_FUNDS_TABLE_NAME is not None,
            "transactions": settings.TRANSACTIONS_TABLE_NAME is not None,
            "notifications": settings.NOTIFICATIONS_TABLE_NAME is not None
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
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
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
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthService.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
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
            email=current_user,
            new_balance=new_balance
        )
        
        # Cancelar suscripción
        FundService.cancel_user_subscription(
            user_id=current_user,
            fund_id=cancellation.fund_id,
            transaction_id=transaction_id
        )
        
        # Registrar transacción
        TransactionService.create_transaction(
            user_id=current_user,
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
        # Obtener balance actual del usuario
        user = UserService.get_user_by_email(current_user)
        current_balance = Decimal(str(user['balance']))
        
        # Procesar depósito usando el servicio
        result = TransactionService.process_deposit(
            user_id=current_user,
            amount=deposit.amount,
            current_balance=current_balance
        )
        
        # Obtener información del usuario para la notificación
        user = UserService.get_user_by_email(current_user)
        
        # Crear notificación
        NotificationService.create_deposit_notification(
            user_id=current_user,
            transaction_id=result['transaction_id'],
            amount=deposit.amount,
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
