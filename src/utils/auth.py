"""Authentication utilities for FastAPI."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..services.auth_service import AuthService
from ..services.user_service import UserService
from ..models.schemas import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get the current user based on the JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verificar el token y obtener email
        email = AuthService.get_current_user(credentials.credentials)
    except Exception as exc:
        raise credentials_exception from exc

    # Obtener el usuario
    user = UserService.get_user_by_email(email)
    if user is None:
        raise credentials_exception

    return user