from pydantic import BaseModel, EmailStr
from typing import Union


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Union[str, None] = None


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str

