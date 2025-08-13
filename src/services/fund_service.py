import boto3
from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException, status
from botocore.exceptions import ClientError
from typing import Dict, Any, List, Optional
from ..config.settings import settings

# Configuración de DynamoDB
dynamodb = boto3.resource('dynamodb')
funds_table = dynamodb.Table(settings.FUNDS_TABLE_NAME)
user_funds_table = dynamodb.Table(settings.USER_FUNDS_TABLE_NAME)


class FundService:
    @staticmethod
    def get_all_funds() -> List[Dict[str, Any]]:
        """Obtener todos los fondos disponibles."""
        try:
            response = funds_table.scan()
            funds = []
            for item in response['Items']:
                funds.append({
                    'fund_id': item['fund_id'],
                    'name': item['name'],
                    'minimum_amount': float(item['minimum_amount']),
                    'category': item['category'],
                    'is_active': item.get('is_active', True),
                    'created_at': item['created_at']
                })
            return funds
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener fondos: {str(e)}"
            )
    
    @staticmethod
    def get_fund_by_id(fund_id: str) -> Dict[str, Any]:
        """Obtener fondo por ID."""
        try:
            response = funds_table.get_item(Key={'fund_id': fund_id})
            if 'Item' not in response:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Fondo no encontrado"
                )
            
            fund = response['Item']
            return {
                'fund_id': fund['fund_id'],
                'name': fund['name'],
                'minimum_amount': fund['minimum_amount'],
                'category': fund['category'],
                'is_active': fund.get('is_active', True),
                'created_at': fund['created_at']
            }
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener fondo: {str(e)}"
            )
    
    @staticmethod
    def subscribe_user_to_fund(user_id: str, fund_id: str, amount: Decimal, transaction_id: str) -> Dict[str, Any]:
        """Suscribir usuario a un fondo."""
        timestamp = datetime.utcnow().isoformat()
        subscription_id = str(uuid.uuid4())
        
        subscription_item = {
            'user_id': user_id,
            'fund_id': fund_id,
            'subscription_id': subscription_id,
            'invested_amount': amount,
            'subscription_date': timestamp,
            'status': 'active',
            'transaction_id': transaction_id
        }
        
        try:
            user_funds_table.put_item(Item=subscription_item)
            return subscription_item
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear suscripción: {str(e)}"
            )
    
    @staticmethod
    def get_user_subscription(user_id: str, fund_id: str) -> Optional[Dict[str, Any]]:
        """Obtener suscripción activa del usuario a un fondo."""
        try:
            response = user_funds_table.query(
                KeyConditionExpression='user_id = :user_id',
                FilterExpression='fund_id = :fund_id AND #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':user_id': user_id,
                    ':fund_id': fund_id,
                    ':status': 'active'
                }
            )
            
            if response['Items']:
                return response['Items'][0]
            return None
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al verificar suscripción: {str(e)}"
            )
    
    @staticmethod
    def cancel_user_subscription(user_id: str, fund_id: str, transaction_id: str) -> Dict[str, Any]:
        """Cancelar suscripción del usuario a un fondo."""
        timestamp = datetime.utcnow().isoformat()
        
        # Buscar la suscripción activa
        subscription = FundService.get_user_subscription(user_id, fund_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tienes una suscripción activa a este fondo"
            )
        
        try:
            # Actualizar el estado de la suscripción
            user_funds_table.update_item(
                Key={
                    'user_id': user_id,
                    'subscription_id': subscription['subscription_id']
                },
                UpdateExpression='SET #status = :status, cancellation_date = :date, cancellation_transaction_id = :transaction_id',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'cancelled',
                    ':date': timestamp,
                    ':transaction_id': transaction_id
                }
            )
            
            return subscription
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al cancelar suscripción: {str(e)}"
            )
    
    @staticmethod
    def get_user_subscriptions(user_id: str) -> List[Dict[str, Any]]:
        """Obtener todas las suscripciones del usuario."""
        try:
            response = user_funds_table.query(
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id}
            )
            
            subscriptions = []
            for item in response['Items']:
                # Obtener información del fondo
                fund = FundService.get_fund_by_id(item['fund_id'])
                
                subscription = {
                    'user_id': item['user_id'],
                    'fund_id': item['fund_id'],
                    'fund_name': fund['name'],
                    'invested_amount': float(item['invested_amount']),
                    'subscription_date': item['subscription_date'],
                    'status': item['status'],
                    'transaction_id': item['transaction_id']
                }
                
                if 'cancellation_date' in item:
                    subscription['cancellation_date'] = item['cancellation_date']
                if 'cancellation_transaction_id' in item:
                    subscription['cancellation_transaction_id'] = item['cancellation_transaction_id']
                
                subscriptions.append(subscription)
            
            return subscriptions
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener suscripciones: {str(e)}"
            )
    
    @staticmethod
    def initialize_default_funds():
        """Inicializar fondos predefinidos"""
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
    
    @staticmethod
    def get_user_active_subscriptions(user_id: str):
        """Obtener suscripciones activas del usuario"""
        try:
            response = user_funds_table.query(
                KeyConditionExpression='user_id = :user_id',
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':user_id': user_id,
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
            
            return subscriptions
            
        except Exception as e:
             raise Exception(f"Error al obtener suscripciones activas: {str(e)}")
    
    @staticmethod
    def subscribe_user_to_fund(user_id: str, fund_id: str, amount: Decimal, transaction_id: str):
        """Crear suscripción del usuario al fondo"""
        try:
            timestamp = datetime.utcnow().isoformat()
            subscription_item = {
                'user_id': user_id,
                'fund_id': fund_id,
                'invested_amount': amount,
                'subscription_date': timestamp,
                'status': 'active',
                'transaction_id': transaction_id
            }
            user_funds_table.put_item(Item=subscription_item)
            
        except Exception as e:
            raise Exception(f"Error al crear suscripción: {str(e)}")
    
    @staticmethod
    def cancel_user_subscription(user_id: str, fund_id: str):
        """Cancelar suscripción del usuario"""
        try:
            user_funds_table.update_item(
                Key={
                    'user_id': user_id,
                    'fund_id': fund_id
                },
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': 'cancelled'}
            )
            
        except Exception as e:
            raise Exception(f"Error al cancelar suscripción: {str(e)}")