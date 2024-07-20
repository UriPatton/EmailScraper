from pydantic import BaseModel, EmailStr, AnyHttpUrl
from typing import List


class Emails(BaseModel):

    emails: List[EmailStr]


class EmailScraperRequest(BaseModel):
    webpages: List[AnyHttpUrl]
    max_worker: int = None
    max_pages: int = None


