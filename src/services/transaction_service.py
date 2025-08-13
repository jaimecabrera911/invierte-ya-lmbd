import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from ..config.settings import settings

# Configuración de DynamoDB
dynamodb = boto3.resource('dynamodb')
transactions_table = dynamodb.Table(settings.TRANSACTIONS_TABLE_NAME)


class TransactionService:
    @staticmethod
    def generate_transaction_id() -> str:
        """Generar un ID único para transacción."""
        return str(uuid.uuid4())
    
    @staticmethod
    def create_transaction(
        user_id: str,
        fund_id: str,
        transaction_type: str,
        amount: Decimal,
        balance_before: Decimal,
        balance_after: Decimal,
        transaction_status: str = "completed"
    ) -> str:
        """Crear una nueva transacción."""
        transaction_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        transaction_item = {
            'user_id': user_id,
            'transaction_id': transaction_id,
            'fund_id': fund_id,
            'transaction_type': transaction_type,
            'amount': amount,
            'timestamp': timestamp,
            'status': transaction_status,
            'balance_before': balance_before,
            'balance_after': balance_after
        }
        
        try:
            transactions_table.put_item(Item=transaction_item)
            return transaction_id
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al crear transacción: {str(e)}"
            )
    
    @staticmethod
    def get_user_transactions(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtener transacciones del usuario."""
        try:
            response = transactions_table.query(
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id},
                ScanIndexForward=False,  # Orden descendente por timestamp
                Limit=limit
            )
            
            transactions = []
            for item in response['Items']:
                transactions.append({
                    'user_id': item['user_id'],
                    'transaction_id': item['transaction_id'],
                    'fund_id': item['fund_id'],
                    'transaction_type': item['transaction_type'],
                    'amount': float(item['amount']),
                    'timestamp': item['timestamp'],
                    'status': item['status'],
                    'balance_before': float(item['balance_before']),
                    'balance_after': float(item['balance_after'])
                })
            
            return transactions
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener transacciones: {str(e)}"
            )
    
    @staticmethod
    def process_deposit(
        user_id: str,
        amount: Decimal,
        current_balance: Decimal
    ) -> Dict[str, Any]:
        """Procesar un depósito de dinero."""
        # Validaciones
        min_deposit = settings.MIN_DEPOSIT_AMOUNT
        max_deposit = settings.MAX_DEPOSIT_AMOUNT
        
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El monto debe ser positivo"
            )
        
        if amount < min_deposit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El monto mínimo de depósito es COP ${min_deposit:,.0f}"
            )
        
        if amount > max_deposit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El monto máximo de depósito es COP ${max_deposit:,.0f}"
            )
        
        # Calcular nuevo balance
        new_balance = current_balance + amount
        
        # Crear transacción
        transaction_id = TransactionService.create_transaction(
            user_id=user_id,
            fund_id="DEPOSIT",
            transaction_type="deposit",
            amount=amount,
            balance_before=current_balance,
            balance_after=new_balance
        )
        
        return {
            'transaction_id': transaction_id,
            'amount': amount,
            'balance_before': current_balance,
            'balance_after': new_balance,
            'timestamp': datetime.utcnow().isoformat()
        }