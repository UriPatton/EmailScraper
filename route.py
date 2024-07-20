from fastapi import FastAPI, APIRouter

from auth import CreateUserRequest
from database import User
from model import EmailScraperRequest, Emails


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


#@router.get("/auth")
#async def get_user():
    #return {'user': 'authenticated'}


@router.post("/auth")
async def create_user(create_user_request: CreateUserRequest):
    create_user_model = User(
        email=create_user_request.email,
        hashed_password=create_user_request.password,
        role=create_user_request.role,
        password=create_user_request.password
    )

    return create_user_model














