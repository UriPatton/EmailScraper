from email_scraper.model import EmailScraperRequest, Emails
from fastapi import APIRouter, Depends, HTTPException, Response, status
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from auth.auth import (db_dependency, create_access_token, authenticate_user,
                       ACCESS_TOKEN_EXPIRE_MINUTES, oauth2_scheme)
from auth.model import Token
from datetime import timedelta
from redis import Redis
from rq import Queue
from tasks.scrap_email import scrap_emails

router = APIRouter()
redis_conn = Redis(host='redis', port=6379, db=0)  # Adjust connection parameters as needed
q = Queue(connection=redis_conn, name='default')


@router.post("/token",
             response_model=Token,
             status_code=status.HTTP_200_OK,
             tags=['auth'],
             summary='Login',
             description='Login to get access token',
             response_description='Access Token')
async def login_for_access_token(db: db_dependency,
                                 form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
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


@router.post("/email_scraper/", dependencies=[Depends(oauth2_scheme)],
             responses={200: {"job_id": "Job ID", "status": "In Progress"}},
             status_code=status.HTTP_200_OK,
             # dependencies=[Depends(oauth2_scheme)],
             tags=['email'],
             summary='Email Scraper',
             description='Scrapes emails from webpages',
             response_description='List of emails'
             )
async def email_scraper(email_scraper_request: EmailScraperRequest):
    # return scrap_emails(email_scraper_request, user)

    job = q.enqueue(scrap_emails,
                    email_scraper_request.webpages,
                    email_scraper_request.max_worker,
                    email_scraper_request.max_pages)
    return {"job_id": job.id, "status": "In Progress"}


@router.get("/email_scraper/{job_id}", dependencies=[Depends(oauth2_scheme)],
            response_model=Emails,
            responses={200: {"emails": ["jondoe@example.com"]}},
            status_code=status.HTTP_200_OK,
            tags=['email'],
            summary='Email Scraper Result',
            description='Get emails from email scraper job',
            response_description='List of emails')
async def email_scraper_result(job_id: str):
    job = q.fetch_job(job_id)
    if job is None:
        return Response(
            content='Job not found',
            status_code=status.HTTP_404_NOT_FOUND
        )
    if job.is_finished:
        return Emails(emails=job.return_value())
    return Response(
        content='Job is not finished yet',
        status_code=status.HTTP_202_ACCEPTED
    )


# @router.post("/create_user", status_code=status.HTTP_201_CREATED)
# async def create_user(db: db_dependency,
#                       create_user_request: CreateUserRequest):
#     create_user_model = User(
#         email=create_user_request.email,
#         hashed_password=bcrypt_context.hash(create_user_request.password),
#
#     )
#     # check if user already exists
#     if db.query(User).filter(User.email == create_user_request.email).first() is None:
#         db.add(create_user_model)
#         db.commit()
#         return 'User Created'
#     return Response(
#         content='Email Already exists',
#         status_code=status.HTTP_400_BAD_REQUEST
#     )
#
#
# @router.get("/all_users/")
# async def get_all_users(db: db_dependency):
#     users = db.query(User).all()
#     return users
#
#
# @router.delete("/delete_user/{email}", status_code=status.HTTP_200_OK)
# def delete_user(db: db_dependency, user_email: EmailStr):
#     user = db.query(User).filter(User.email == user_email).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     db.delete(user)
#     db.commit()
#     return 'User Deleted'
