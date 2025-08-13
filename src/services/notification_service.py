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
notifications_table = dynamodb.Table(settings.NOTIFICATIONS_TABLE_NAME)


class NotificationService:
    @staticmethod
    def create_subscription_notification(
        user_id: str,
        transaction_id: str,
        fund_name: str,
        amount: Decimal,
        notification_type: str
    ) -> str:
        """Crear notificación de suscripción."""
        notification_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        notification_content = (
            f"Tu suscripción al fondo {fund_name} por COP ${amount:,.0f} "
            f"ha sido procesada exitosamente. ID de transacción: {transaction_id}"
        )
        
        notification_item = {
            'notification_id': notification_id,
            'user_id': user_id,
            'transaction_id': transaction_id,
            'type': notification_type,
            'status': 'pending',
            'content': notification_content,
            'created_at': timestamp
        }
        
        try:
            notifications_table.put_item(Item=notification_item)
            return notification_id
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear notificación: {str(e)}"
            )
    
    @staticmethod
    def create_cancellation_notification(
        user_id: str,
        transaction_id: str,
        fund_name: str,
        amount: Decimal,
        notification_type: str
    ) -> str:
        """Crear notificación de cancelación."""
        notification_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        notification_content = (
            f"Tu cancelación del fondo {fund_name} por COP ${amount:,.0f} "
            f"ha sido procesada exitosamente. ID de transacción: {transaction_id}"
        )
        
        notification_item = {
            'notification_id': notification_id,
            'user_id': user_id,
            'transaction_id': transaction_id,
            'type': notification_type,
            'status': 'pending',
            'content': notification_content,
            'created_at': timestamp
        }
        
        try:
            notifications_table.put_item(Item=notification_item)
            return notification_id
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear notificación: {str(e)}"
            )
    
    @staticmethod
    def create_deposit_notification(
        user_id: str,
        transaction_id: str,
        amount: Decimal,
        notification_type: str
    ) -> str:
        """Crear notificación de depósito."""
        notification_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        notification_content = (
            f"Tu depósito por COP ${amount:,.0f} ha sido procesado exitosamente. "
            f"ID de transacción: {transaction_id}"
        )
        
        notification_item = {
            'notification_id': notification_id,
            'user_id': user_id,
            'transaction_id': transaction_id,
            'type': notification_type,
            'status': 'pending',
            'content': notification_content,
            'created_at': timestamp
        }
        
        try:
            notifications_table.put_item(Item=notification_item)
            return notification_id
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear notificación: {str(e)}"
            )