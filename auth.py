from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import User, SessionLocal
from passlib.context import CryptContext
from typing import Annotated
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter()

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")




class CreateUserRequest(BaseModel):
    email: str
    password: str
    role: str
    hashed_password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def authenticate_user(email: str, password: str, db):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.password):
        return False
    return True


@router.post("/auth", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency,
                      create_user_request: CreateUserRequest):
    create_user_model = User(
        email=create_user_request.email,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        role=create_user_request.role,
        password=create_user_request.password
    )

    db.add(create_user_model)
    db.commit()



@router.post("/token")
async def login_for_access_token(from_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    user = authenticate_user(from_data.username, from_data.password, db)
    if not user:
        return 'failed Authentication' #status.HTTP_403_FORBIDDEN
    return 'Successfully Authenticated'





















