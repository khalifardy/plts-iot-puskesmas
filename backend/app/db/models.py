from app.db.db_config import Base, engine
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    is_super_user = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    update_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    
    @property  # Fixed typo from "oroperty"
    def hashed_password(self):
        raise AttributeError("Password is not a readable attribute")
    
    @hashed_password.setter
    def hashed_password(self, password):
        self.password = pwd_context.hash(password)
        
    def verify_password(self, password):
        return pwd_context.verify(password, self.password)

class Profile(Base):
    __tablename__ = "profile"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), unique=True)
    
    user = relationship("User", back_populates="profile")

def create_tables():
    Base.metadata.create_all(bind=engine)