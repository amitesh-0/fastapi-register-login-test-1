from datetime import timedelta
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm

from app.oauth2 import authenticate_user, create_access_token
from .. import schemas, models
from fastapi import Body, Depends, FastAPI, HTTPException, Response, status, APIRouter
from sqlalchemy.orm import Session
from .. database import get_db  

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
) -> schemas.Token:
    user = authenticate_user(form_data.id, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect id or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=1440)
    access_token = create_access_token(
        data={"user_id": user.id}, expires_delta = access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
