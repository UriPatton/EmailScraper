from email_scraper.model import EmailScraperRequest, Emails
from fastapi import APIRouter, Depends, HTTPException, Response, status
from auth.database import User
from pydantic import EmailStr
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from auth.auth import (db_dependency, bcrypt_context, create_access_token, Token, authenticate_user,
                       ACCESS_TOKEN_EXPIRE_MINUTES, oauth2_scheme)
from auth.model import CreateUserRequest
from datetime import timedelta


router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Hello World"}


@router.post("/email_scraper/")
async def email_scraper(email_scraper_request: EmailScraperRequest) -> Emails:
    temp_emails = Emails(
        emails=[
            'example@google.com',
            'second@gmail.com'
        ]
    )
    return temp_emails


@router.post("/create_user", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency,
                      create_user_request: CreateUserRequest):
    create_user_model = User(
        email=create_user_request.email,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        role=create_user_request.role,
        password=create_user_request.password
    )
    # check if user already exists
    if db.query(User).filter(User.email == create_user_request.email).first() is None:
        db.add(create_user_model)
        db.commit()
        return 'User Created'
    return Response(
        content='Email Already exists',
        status_code=status.HTTP_400_BAD_REQUEST
    )


@router.post("/token")
async def login_for_access_token(db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")



@router.get("/all_users/", dependencies=[Depends(oauth2_scheme)])
async def get_all_users(db: db_dependency):
    users = db.query(User).all()
    return users


@router.delete("/delete_user/{email}", status_code=status.HTTP_200_OK, dependencies=[Depends(oauth2_scheme)])
def delete_user(db: db_dependency, user_email: EmailStr):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return 'User Deleted'











