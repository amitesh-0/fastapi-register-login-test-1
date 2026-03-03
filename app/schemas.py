from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: int
    mob: str
    created_at: datetime
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    mob: str
    password: str
    otp: str#otp or code?

class UserLogin(BaseModel):
    mob: str
    password: str

class Token(BaseModel):
    refresh_token: str
    access_token: str
    token_type: str

class TokenRefresh(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    id: Optional[str] = None

class OTPSendRequest(BaseModel):
    mob: str 

class OTPVerifyRequest(BaseModel):
    mob: str
    code: str