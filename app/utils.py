import random
import redis
from twilio.rest import Client
from bcrypt import hashpw, gensalt, checkpw
from .config import settings

# decode_responses=True ensures Redis returns strings instead of bytes
redis_client = redis.Redis(
    host=settings.REDIS_HOST, 
    port=settings.REDIS_PORT, 
    db=0, 
    decode_responses=True
)

twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

def verify_password(plain_password, hashed_password) -> bool:
    try:
        return checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False
    

def hash(password: str):
    return hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')


def send_otp_sms(phone_number: str) -> bool:
    try:
        otp_code = str(random.randint(100000, 999999))
        
        # setex (set with expiration). 300 seconds = 5 minutes TTL
        redis_client.setex(name=phone_number, time=300, value=otp_code)
        
        twilio_client.messages.create(
            body=f"Your verification code is {otp_code}. It will expire in 5 minutes.",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return True
    except Exception as e:
        print(f"Failed to send OTP: {e}")
        return False

def verify_otp_code(phone_number: str, user_provided_code: str) -> bool:
    # 1. Fetch the stored code from Redis
    stored_code = redis_client.get(phone_number)
    
    if stored_code and stored_code == user_provided_code:
        redis_client.delete(phone_number)
        return True
        
    return False
