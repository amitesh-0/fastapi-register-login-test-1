from .. import schemas, utils, models
from fastapi import Body, Depends, FastAPI, HTTPException, Response, status, APIRouter
from sqlalchemy.orm import Session
from ..database import get_db  

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

def get_user_by_id(id: str, db: Session):
    return db.query(models.User).filter(models.User.id == id).first()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):

    phone_number = user.mob if str(user.mob).startswith("+") else f"+{user.mob}"

    is_valid_otp = utils.verify_otp_code(phone_number, user.otp)
    if not is_valid_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Invalid or expired OTP"
        )
    
    existing_user = db.query(models.User).filter(models.User.mob == phone_number).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this mobile number already exists"
        )

    hashed_password = utils.hash(user.password)
    new_user_data = user.model_dump(exclude={"otp"})
    new_user_data["mob"] = phone_number
    new_user_data["password"] = hashed_password
    new_user = models.User(**new_user_data)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/{id}", response_model=schemas.UserOut)
def get_user(id: int, response: Response, db: Session = Depends(get_db)):
    
    user = db.query(models.User).filter(models.User.id == id).first()

    if not user:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message": f"user with id: {id} was not found"}
    return user