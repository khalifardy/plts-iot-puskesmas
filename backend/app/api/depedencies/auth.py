# app/api/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.security import SECRET_KEY, ALGORITHM
from app.db.db_config import get_db
from app.db.models.user import User
from typing import Optional

# Skema token
from pydantic import BaseModel
class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: str

# Definisikan OAuth2PasswordBearer untuk endpoint token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Dependency untuk mendapatkan user saat ini dari token JWT.
    
    Args:
        token: JWT token
        db: Database session
        
    Returns:
        User object
        
    Raises:
        HTTPException: Jika token tidak valid atau user tidak ditemukan
    """
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
        
        # Verifikasi tipe token
        if token_data.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if token_data.sub is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Cari user berdasarkan ID
    user = db.query(User).filter(User.id == int(token_data.sub)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency untuk memastikan user aktif.
    
    Args:
        current_user: User object dari get_current_user
        
    Returns:
        User object jika user aktif
        
    Raises:
        HTTPException: Jika user tidak aktif
    """
    # Periksa apakah user memiliki profile yang aktif
    if not current_user.profile.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user

def get_current_superuser(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency untuk memastikan user adalah superuser.
    
    Args:
        current_user: User object dari get_current_active_user
        
    Returns:
        User object jika user adalah superuser
        
    Raises:
        HTTPException: Jika user bukan superuser
    """
    if not current_user.is_super_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user