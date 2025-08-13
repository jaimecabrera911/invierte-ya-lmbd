import boto3
import uuid
from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException, status
from botocore.exceptions import ClientError
from typing import Dict, Any
from ..config.settings import settings

# Configuración de DynamoDB
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(settings.USERS_TABLE_NAME)


class UserService:
    @staticmethod
    def create_user(email: str, phone: str, hashed_password: str, notification_preference: str) -> Dict[str, Any]:
        """Crear un nuevo usuario en la base de datos."""
        user_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Verificar si el usuario ya existe
        try:
            response = users_table.get_item(Key={'user_id': email})
            if 'Item' in response:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El usuario ya existe"
                )
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error al verificar usuario existente"
                )
        
        # Crear nuevo usuario
        user_item = {
            'user_id': email,
            'internal_id': user_id,
            'email': email,
            'phone': phone,
            'password_hash': hashed_password,
            'balance': settings.INITIAL_USER_BALANCE,
            'notification_preference': notification_preference,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        try:
            users_table.put_item(Item=user_item)
            return {
                'user_id': email,
                'balance': float(settings.INITIAL_USER_BALANCE),
                'email': email,
                'phone': phone,
                'notification_preference': notification_preference,
                'created_at': timestamp,
                'updated_at': timestamp
            }
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear usuario: {str(e)}"
            )
    
    @staticmethod
    def get_user_by_email(email: str) -> Dict[str, Any]:
        """Obtener usuario por email."""
        try:
            response = users_table.get_item(Key={'user_id': email})
            if 'Item' not in response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado"
                )
            
            user = response['Item']
            return {
                'user_id': user['user_id'],
                'balance': float(user['balance']),
                'email': user['email'],
                'phone': user['phone'],
                'notification_preference': user['notification_preference'],
                'created_at': user['created_at'],
                'updated_at': user['updated_at']
            }
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener usuario: {str(e)}"
            )
    
    @staticmethod
    def get_user_with_password(email: str) -> Dict[str, Any]:
        """Obtener usuario con contraseña para autenticación."""
        try:
            response = users_table.get_item(Key={'user_id': email})
            if 'Item' not in response:
                return None
            return response['Item']
        except ClientError:
            return None
    
    @staticmethod
    def update_user_balance(email: str, new_balance: Decimal) -> None:
        """Actualizar el balance del usuario."""
        timestamp = datetime.utcnow().isoformat()
        
        try:
            users_table.update_item(
                Key={'user_id': email},
                UpdateExpression='SET balance = :balance, updated_at = :updated_at',
                ExpressionAttributeValues={
                    ':balance': new_balance,
                    ':updated_at': timestamp
                }
            )
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al actualizar balance: {str(e)}"
            )