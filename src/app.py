import os
import boto3
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from mangum import Mangum
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = FastAPI(
    title="Invierte Ya - Sistema de Fondos API",
    version="1.0.0",
    description="API para gestión de fondos de inversión FPV y FIC"
)

# Configuración de DynamoDB
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ.get('USERS_TABLE_NAME'))
funds_table = dynamodb.Table(os.environ.get('FUNDS_TABLE_NAME'))
user_funds_table = dynamodb.Table(os.environ.get('USER_FUNDS_TABLE_NAME'))
transactions_table = dynamodb.Table(os.environ.get('TRANSACTIONS_TABLE_NAME'))
notifications_table = dynamodb.Table(
    os.environ.get('NOTIFICATIONS_TABLE_NAME')
)

# Constantes
INITIAL_BALANCE = Decimal('500000')  # COP $500.000

# Configuración de autenticación
SECRET_KEY = os.environ.get(
    'JWT_SECRET_KEY', 'your-secret-key-change-in-production'
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configuración de hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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


# Funciones de utilidad para autenticación
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # Verificar que el usuario existe en la base de datos
    try:
        response = users_table.scan(
            FilterExpression='email = :email',
            ExpressionAttributeValues={':email': token_data.email}
        )
        if not response['Items']:
            raise credentials_exception
        return response['Items'][0]['user_id']
    except Exception:
        raise credentials_exception


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
    """Registrar un nuevo usuario y retornar token de acceso"""
    try:
        # Verificar si el usuario ya existe por email
        response = users_table.scan(
            FilterExpression='email = :email',
            ExpressionAttributeValues={':email': user_data.email}
        )
        if response['Items']:
            raise HTTPException(
                status_code=409,
                detail="User already exists"
            )
        
        # Generar UID único para el usuario
        user_id = str(uuid.uuid4())
        
        # Hash de la contraseña
        hashed_password = get_password_hash(user_data.password)
        
        # Crear usuario en la base de datos
        timestamp = datetime.utcnow().isoformat()
        user_item = {
            'user_id': user_id,
            'balance': INITIAL_BALANCE,
            'email': user_data.email,
            'phone': user_data.phone,
            'password_hash': hashed_password,
            'notification_preference': user_data.notification_preference.value,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        users_table.put_item(Item=user_item)
        
        # Crear token de acceso usando el email
        access_token_expires = timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={"sub": user_data.email}, 
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating user: {str(e)}"
        )


@app.post("/auth/login", response_model=Token)
def login_user(user_credentials: UserLogin):
    """Autenticar usuario y retornar token de acceso"""
    try:
        # Buscar usuario por email en la base de datos
        response = users_table.scan(
            FilterExpression='email = :email',
            ExpressionAttributeValues={':email': user_credentials.email}
        )
        if not response['Items']:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
        
        user = response['Items'][0]
        
        # Verificar contraseña
        if not verify_password(
            user_credentials.password, 
            user['password_hash']
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )
        
        # Crear token de acceso usando el email
        access_token_expires = timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={"sub": user_credentials.email}, 
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during login: {str(e)}"
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
    """Obtener información del usuario autenticado"""
    try:
        response = users_table.get_item(Key={'user_id': current_user})
        
        if 'Item' not in response:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        return User(**response['Item'])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener usuario: {str(e)}"
        )


@app.get("/funds", response_model=List[Fund])
def get_funds():
    """Obtener todos los fondos disponibles"""
    try:
        response = funds_table.scan(
            FilterExpression='is_active = :active',
            ExpressionAttributeValues={':active': True}
        )
        
        funds = [Fund(**item) for item in response['Items']]
        return funds
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener fondos: {str(e)}"
        )


@app.post("/funds/subscribe")
def subscribe_to_fund(
    subscription: SubscriptionRequest,
    current_user: str = Depends(get_current_user)
):
    """Suscribirse a un fondo"""
    try:
        # Obtener información del usuario autenticado
        user_response = users_table.get_item(
            Key={'user_id': current_user}
        )
        if 'Item' not in user_response:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        user = user_response['Item']
        current_balance = Decimal(str(user['balance']))
        
        # Obtener información del fondo
        fund_response = funds_table.get_item(
            Key={'fund_id': subscription.fund_id}
        )
        if 'Item' not in fund_response:
            raise HTTPException(
                status_code=404,
                detail="Fondo no encontrado"
            )
        
        fund = fund_response['Item']
        minimum_amount = Decimal(str(fund['minimum_amount']))
        
        # Determinar monto de inversión
        investment_amount = subscription.amount or minimum_amount
        
        # Verificar que el monto sea suficiente
        if investment_amount < minimum_amount:
            raise HTTPException(
                status_code=400,
                detail=(
                     f"El monto mínimo para este fondo es "
                     f"COP ${minimum_amount:,.0f}"
                 )
            )
        
        # Verificar saldo disponible
        if current_balance < investment_amount:
            raise HTTPException(
                status_code=400,
                detail=(
                     "No tiene saldo disponible para vincularse al fondo"
                 )
            )
        
        # Verificar si ya está suscrito
        existing_subscription = user_funds_table.get_item(
            Key={
                'user_id': current_user,
                'fund_id': subscription.fund_id
            }
        )
        
        if ('Item' in existing_subscription and
                existing_subscription['Item']['status'] == 'active'):
            raise HTTPException(
                status_code=400,
                detail="Ya está suscrito a este fondo"
            )
        
        # Generar ID de transacción
        transaction_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Actualizar saldo del usuario
        new_balance = current_balance - investment_amount
        users_table.update_item(
            Key={'user_id': current_user},
            UpdateExpression=(
                'SET balance = :balance, updated_at = :updated_at'
            ),
            ExpressionAttributeValues={
                ':balance': new_balance,
                ':updated_at': timestamp
            }
        )
        
        # Crear suscripción
        subscription_item = {
            'user_id': current_user,
            'fund_id': subscription.fund_id,
            'invested_amount': investment_amount,
            'subscription_date': timestamp,
            'status': 'active',
            'transaction_id': transaction_id
        }
        user_funds_table.put_item(Item=subscription_item)
        
        # Registrar transacción
        transaction_item = {
            'user_id': current_user,
            'transaction_id': transaction_id,
            'fund_id': subscription.fund_id,
            'transaction_type': 'subscription',
            'amount': investment_amount,
            'timestamp': timestamp,
            'status': 'completed',
            'balance_before': current_balance,
            'balance_after': new_balance
        }
        transactions_table.put_item(Item=transaction_item)
        
        # Crear notificación
        notification_id = str(uuid.uuid4())
        notification_content = (
             f"Se ha suscrito exitosamente al fondo {fund['name']} "
             f"con un monto de COP ${investment_amount:,.0f}"
         )
        
        notification_item = {
            'notification_id': notification_id,
            'user_id': current_user,
            'transaction_id': transaction_id,
            'type': user['notification_preference'],
            'status': 'pending',
            'content': notification_content,
            'created_at': timestamp
        }
        notifications_table.put_item(Item=notification_item)
        
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
            status_code=500,
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
        subscription_response = user_funds_table.get_item(
            Key={
                'user_id': current_user,
                'fund_id': cancellation.fund_id
            }
        )
        
        if 'Item' not in subscription_response:
            raise HTTPException(
                status_code=404,
                detail="No se encontró suscripción a este fondo"
            )
        
        subscription = subscription_response['Item']
        if subscription['status'] != 'active':
            raise HTTPException(
                status_code=400,
                detail="La suscripción ya está cancelada"
            )
        
        # Obtener información del usuario
        user_response = users_table.get_item(
            Key={'user_id': current_user}
        )
        user = user_response['Item']
        current_balance = Decimal(str(user['balance']))
        invested_amount = Decimal(str(subscription['invested_amount']))
        
        # Obtener información del fondo
        fund_response = funds_table.get_item(
            Key={'fund_id': cancellation.fund_id}
        )
        fund = fund_response['Item']
        
        # Generar ID de transacción
        transaction_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Devolver dinero al usuario
        new_balance = current_balance + invested_amount
        users_table.update_item(
            Key={'user_id': current_user},
            UpdateExpression=(
                'SET balance = :balance, updated_at = :updated_at'
            ),
            ExpressionAttributeValues={
                ':balance': new_balance,
                ':updated_at': timestamp
            }
        )
        
        # Actualizar suscripción
        user_funds_table.update_item(
            Key={
                'user_id': current_user,
                'fund_id': cancellation.fund_id
            },
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'cancelled'}
        )
        
        # Registrar transacción
        transaction_item = {
            'user_id': current_user,
            'transaction_id': transaction_id,
            'fund_id': cancellation.fund_id,
            'transaction_type': 'cancellation',
            'amount': invested_amount,
            'timestamp': timestamp,
            'status': 'completed',
            'balance_before': current_balance,
            'balance_after': new_balance
        }
        transactions_table.put_item(Item=transaction_item)
        
        # Crear notificación
        notification_id = str(uuid.uuid4())
        notification_content = (
             f"Se ha cancelado su suscripción al fondo {fund['name']}. "
             f"Se han devuelto COP ${invested_amount:,.0f} a su cuenta"
         )
        
        notification_item = {
            'notification_id': notification_id,
            'user_id': current_user,
            'transaction_id': transaction_id,
            'type': user['notification_preference'],
            'status': 'pending',
            'content': notification_content,
            'created_at': timestamp
        }
        notifications_table.put_item(Item=notification_item)
        
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
            status_code=500,
            detail=f"Error al procesar cancelación: {str(e)}"
        )


@app.get("/users/me/transactions")
def get_user_transactions(
    current_user: str = Depends(get_current_user),
    limit: int = 20
):
    """Obtener historial de transacciones del usuario autenticado"""
    try:
        response = transactions_table.query(
            KeyConditionExpression='user_id = :user_id',
            ExpressionAttributeValues={':user_id': current_user},
            Limit=limit,
            ScanIndexForward=False  # Ordenar por fecha descendente
        )
        
        transactions = []
        for item in response['Items']:
            # Obtener nombre del fondo
            fund_response = funds_table.get_item(
                Key={'fund_id': item['fund_id']}
            )
            fund_name = fund_response.get('Item', {}).get(
                 'name', 'Fondo no encontrado'
             )
            
            transaction = {
                "transaction_id": item['transaction_id'],
                "fund_id": item['fund_id'],
                "fund_name": fund_name,
                "transaction_type": item['transaction_type'],
                "amount": float(item['amount']),
                "timestamp": item['timestamp'],
                "status": item['status'],
                "balance_before": float(item['balance_before']),
                "balance_after": float(item['balance_after'])
            }
            transactions.append(transaction)
        
        return {
            "user_id": current_user,
            "transactions": transactions,
            "count": len(transactions)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener transacciones: {str(e)}"
        )


@app.get("/users/me/subscriptions")
def get_user_subscriptions(
    current_user: str = Depends(get_current_user)
):
    """Obtener suscripciones activas del usuario autenticado"""
    try:
        response = user_funds_table.query(
            KeyConditionExpression='user_id = :user_id',
            FilterExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':user_id': current_user,
                ':status': 'active'
            }
        )
        
        subscriptions = []
        for item in response['Items']:
            # Obtener información del fondo
            fund_response = funds_table.get_item(
                Key={'fund_id': item['fund_id']}
            )
            fund = fund_response.get('Item', {})
            
            subscription = {
                "fund_id": item['fund_id'],
                "fund_name": fund.get('name', 'Fondo no encontrado'),
                "fund_category": fund.get('category', 'N/A'),
                "invested_amount": float(item['invested_amount']),
                "subscription_date": item['subscription_date'],
                "transaction_id": item['transaction_id']
            }
            subscriptions.append(subscription)
        
        return {
            "user_id": current_user,
            "active_subscriptions": subscriptions,
            "count": len(subscriptions)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener suscripciones: {str(e)}"
        )


@app.post("/users/me/deposit")
def deposit_money(
    deposit: DepositRequest,
    current_user: str = Depends(get_current_user)
):
    """Depositar dinero en la cuenta del usuario"""
    try:
        # Validar que el monto sea positivo
        if deposit.amount <= 0:
            raise HTTPException(
                status_code=400,
                detail="El monto del depósito debe ser mayor a cero"
            )
        
        # Validar monto mínimo de depósito (ej: $10,000 COP)
        min_deposit = Decimal('10000')
        if deposit.amount < min_deposit:
            raise HTTPException(
                status_code=400,
                detail=f"El monto mínimo de depósito es COP ${min_deposit:,.0f}"
            )
        
        # Validar monto máximo de depósito (ej: $10,000,000 COP)
        max_deposit = Decimal('10000000')
        if deposit.amount > max_deposit:
            raise HTTPException(
                status_code=400,
                detail=f"El monto máximo de depósito es COP ${max_deposit:,.0f}"
            )
        
        # Obtener información actual del usuario
        user_response = users_table.get_item(Key={'user_id': current_user})
        if 'Item' not in user_response:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        user = user_response['Item']
        current_balance = Decimal(str(user['balance']))
        new_balance = current_balance + deposit.amount
        
        # Crear ID de transacción
        transaction_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Actualizar balance del usuario
        users_table.update_item(
            Key={'user_id': current_user},
            UpdateExpression='SET balance = :new_balance, updated_at = :timestamp',
            ExpressionAttributeValues={
                ':new_balance': new_balance,
                ':timestamp': timestamp
            }
        )
        
        # Registrar transacción de depósito
        transaction_data = {
            'user_id': current_user,
            'transaction_id': transaction_id,
            'fund_id': 'DEPOSIT',  # Identificador especial para depósitos
            'transaction_type': TransactionType.DEPOSIT.value,
            'amount': deposit.amount,
            'timestamp': timestamp,
            'status': TransactionStatus.COMPLETED.value,
            'balance_before': current_balance,
            'balance_after': new_balance
        }
        
        transactions_table.put_item(Item=transaction_data)
        
        # Crear notificación
        notification_data = {
            'user_id': current_user,
            'notification_id': str(uuid.uuid4()),
            'type': 'deposit_confirmation',
            'message': f'Depósito exitoso de COP ${deposit.amount:,.0f}. Nuevo balance: COP ${new_balance:,.0f}',
            'timestamp': timestamp,
            'sent': False
        }
        
        notifications_table.put_item(Item=notification_data)
        
        return {
            'message': 'Depósito realizado exitosamente',
            'transaction_id': transaction_id,
            'amount_deposited': float(deposit.amount),
            'previous_balance': float(current_balance),
            'new_balance': float(new_balance),
            'timestamp': timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar depósito: {str(e)}"
        )


@app.post("/init-funds")
def initialize_funds():
    """Inicializar fondos predefinidos (solo para desarrollo)"""
    try:
        funds_data = [
            {
                "fund_id": "1",
                "name": "FPV_EL CLIENTE_RECAUDADORA",
                "minimum_amount": Decimal('75000'),
                "category": "FPV",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "fund_id": "2",
                "name": "FPV_EL CLIENTE_ECOPETROL",
                "minimum_amount": Decimal('125000'),
                "category": "FPV",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "fund_id": "3",
                "name": "DEUDAPRIVADA",
                "minimum_amount": Decimal('50000'),
                "category": "FIC",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "fund_id": "4",
                "name": "FDO-ACCIONES",
                "minimum_amount": Decimal('250000'),
                "category": "FIC",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "fund_id": "5",
                "name": "FPV_EL CLIENTE_DINAMICA",
                "minimum_amount": Decimal('100000'),
                "category": "FPV",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        for fund_data in funds_data:
            funds_table.put_item(Item=fund_data)
        
        return {
            "message": "Fondos inicializados exitosamente",
            "funds_created": len(funds_data)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al inicializar fondos: {str(e)}"
        )


handler = Mangum(app)
