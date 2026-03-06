from fastapi import Depends, status, APIRouter, HTTPException
from sqlalchemy.orm import Session
from app import  models, utils, oauth2, schemas
from app.database import get_db
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

router = APIRouter()

@router.post("/login")
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.mob == user_credentials.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
    if not utils.verify_password(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    access_token = oauth2.create_access_token(data={"user_id": user.id})
    refresh_token = oauth2.create_refresh_token(data={"user_id": user.id})

    return {"access_token": access_token,
            "refresh_token": refresh_token,
             "token_type": "bearer"}

@router.post("/refresh", response_model=schemas.Token)
def refresh_token(token_data: schemas.TokenRefresh, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify the incoming refresh token
    user = oauth2.verify_refresh_token(token_data.refresh_token, credentials_exception, db)
    
    # Issue a new pair of tokens
    new_access_token = oauth2.create_access_token(data={"user_id": user.id})
    new_refresh_token = oauth2.create_refresh_token(data={"user_id": user.id})
    
    return {
        "access_token": new_access_token, 
        "token_type": "bearer",
        "refresh_token": new_refresh_token
    }

@router.post("/send-otp")
def request_otp(otp_request: schemas.OTPSendRequest):
    # Twilio requires E.164 format (must start with '+'). 
    # Add a '+' if the frontend forgot to include it.
    phone_number = otp_request.mob if str(otp_request.mob).startswith("+") else f"+{otp_request.mob}"
    
    success = utils.send_otp_sms(phone_number)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to generate or send OTP"
        )
        
    return {"message": "OTP sent successfully. It expires in 5 minutes."}


@router.post("/verify-otp")
def validate_otp(otp_verify: schemas.OTPVerifyRequest):
    phone_number = otp_verify.mob if str(otp_verify.mob).startswith("+") else f"+{otp_verify.mob}"
    
    is_valid = utils.verify_otp_code(phone_number, otp_verify.code)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid or expired OTP"
        )
        
    return {"message": "Phone number successfully verified!"}