from datetime import datetime, timedelta, timezone
from typing_extensions import Annotated
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi import Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.routers import user 
from app.routers.user import get_user_by_id
from app.utils import verify_password
from . import schemas, database, models
from app import schemas
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/login')

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def authenticate_user(id: str, password: str, db: Session = Depends(database.get_db)):
    if not get_user_by_id(id, db):
        return False
    if not verify_password(password,user.password): 
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    to_encode.update({"token_type": "access"})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    to_encode.update({"token_type": "refresh"}) 
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = str(payload.get("user_id"))
        token_type: str = payload.get("token_type")
        
        # Ensure it exists AND is strictly an access token
        if id is None or token_type != "access":
            raise credentials_exception
            
        token_data = schemas.TokenData(id=id)
        return token_data
    except JWTError:
        raise credentials_exception

def verify_refresh_token(token: str, credentials_exception, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id")
        token_type: str = payload.get("token_type")
        
        # Ensure it's actually a refresh token
        if id is None or token_type != "refresh":
            raise credentials_exception
            
        token_data = schemas.TokenData(id=id)
    except JWTError:
        raise credentials_exception

    user = get_user_by_id(id=token_data.id, db=db)
    if user is None:
        raise credentials_exception
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id")
        if id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=id)
    except JWTError:
        raise credentials_exception

    user = get_user_by_id(id=token_data.id, db=db)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Annotated[schemas.UserOut, Depends(get_current_user)]):
    return current_user