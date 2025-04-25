# app/api/routes/auth.py
from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any,Optional
from pydantic import BaseModel, EmailStr
import datetime 
from datetime import timedelta

# Import model setelah create_tables() dipanggil di main.py
from app.db.db_config import get_db
from app.db.models.user import User as UserModel, Profile as ProfileModel
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

from app.api.depedencies.auth import get_current_user


router = APIRouter()

#token response Model
class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

# Pydantic models
class ProfileBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: Optional[str] = None
    is_active: Optional[bool] = True

class ProfileCreate(ProfileBase):
    pass

class Profile(ProfileBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    profile: ProfileCreate

class User(UserBase):
    id: int
    is_super_user: bool
    created_at: Optional[datetime.datetime] = None
    update_at: Optional[datetime.datetime] = None
    profile: Optional[Profile] = None

    class Config:
        orm_mode = True
        
# Login Endpoint
@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Endpoint untuk login dan mendapatkan token JWT.
    
    Args:
        form_data: Form dengan username dan password
        db: Database session
        
    Returns:
        Dictionary dengan access_token, refresh_token, dan token_type
        
    Raises:
        HTTPException: Jika kredensial tidak valid
    """
    
    #cari user berdasarkan username
    user = db.query(UserModel).filter(UserModel.username == form_data.username).first()
    
    #verifikasi user dan password
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    #verifikasi user aktif
    
    if not user.profile.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not active"
        )
    
    #buar access token dan refresh token
    access_token = create_access_token(subject=user.id)
    referesh_token = create_refresh_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": referesh_token,
        "token_type": "bearer",
        "username": user.username,
        "is_super_user": user.is_super_user,
    }

#referesh token endpoint
@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    Endpoint untuk memperbaharui access token dengan refresh token.
    
    Args:
        refresh_token: Refresh token yang masih valid
        db: Database session
        
    Returns:
        Dictionary dengan access_token, refresh_token, dan token_type
        
    Raises:
        HTTPException: Jika refresh token tidak valid
    """
    
    try:
        from jose import jwt
        from app.core.security import SECRET_KEY, ALGORITHM
        from app.api.depedencies.auth import TokenPayload
        
        #decode refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
        
        #periksa tipe token
        if token_data.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                
            )
        
        #cari user berdasarkan id
        user = db.query(UserModel).filter(UserModel.id == token_data.sub).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                
            )
        
        #periksa status user
        if not user.profile.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not active",
            )
        
        #buat token baru
        access_token = create_access_token(subject=user.id)
        new_refresh_token = create_refresh_token(subject=user.id)
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
#register user endpoint
@router.post("/register", response_model=User)
async def register_user(user: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Endpoint untuk registrasi user baru.
    
    Args:
        user_in: Data user baru
        db: Database session
        
    Returns:
        User yang baru dibuat
        
    Raises:
        HTTPException: Jika username atau email sudah terdaftar
    """
    
    # Import UserModel dan ProfileModel di level fungsi untuk menghindari import siklik
    from app.db.models.user import User as UserModel, Profile as ProfileModel
    
    # Cek apakah email sudah ada
    db_profile_email = db.query(ProfileModel).filter(ProfileModel.email == user.profile.email).first()
    if db_profile_email:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")
    
    # Cek apakah username sudah ada
    db_user_username = db.query(UserModel).filter(UserModel.username == user.username).first()
    if db_user_username:
        raise HTTPException(status_code=400, detail="Username sudah digunakan")
    
    # Buat user dengan hashing password
    db_user = UserModel(
        username=user.username,
        password=get_password_hash(user.password),
        is_super_user=False,
    )
    
    #db_user = UserModel(username=user.username)
    #db_user.hashed_password = user.password
    
    # Buat profile
    db_profile = ProfileModel(
        email=user.profile.email,
        first_name=user.profile.first_name,
        last_name=user.profile.last_name,
        phone_number=user.profile.phone_number,
        is_active=True
    )
    
    # Hubungkan profile ke user
    db_user.profile = db_profile
    
    # Tambahkan ke database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.get("/me", response_model=User)
async def read_users_me(
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """
    Endpoint untuk mendapatkan informasi user yang sedang login.
    
    Args:
        current_user: User yang sedang login
        
    Returns:
        User yang sedang login
    """
    
    return current_user