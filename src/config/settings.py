import os
from decimal import Decimal

# Configuración de la aplicación
class Settings:
    # Información de la aplicación
    APP_TITLE = "Invierte Ya - Sistema de Fondos API"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "API para gestión de fondos de inversión FPV y FIC"
    
    # Configuración de autenticación
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # Configuración de AWS
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    
    # Configuración de DynamoDB
    USERS_TABLE_NAME = os.environ.get('USERS_TABLE_NAME')
    FUNDS_TABLE_NAME = os.environ.get('FUNDS_TABLE_NAME')
    USER_FUNDS_TABLE_NAME = os.environ.get('USER_FUNDS_TABLE_NAME')
    TRANSACTIONS_TABLE_NAME = os.environ.get('TRANSACTIONS_TABLE_NAME')
    NOTIFICATIONS_TABLE_NAME = os.environ.get('NOTIFICATIONS_TABLE_NAME')
    
    # Configuración de usuario
    INITIAL_USER_BALANCE = Decimal('500000')  # COP $500.000
    
    # Configuración de depósitos
    MIN_DEPOSIT_AMOUNT = Decimal('10000')  # COP $10,000
    MAX_DEPOSIT_AMOUNT = Decimal('10000000')  # COP $10,000,000
    
    # Configuración del entorno
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')


settings = Settings()