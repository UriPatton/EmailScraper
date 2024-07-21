from pydantic import BaseModel, EmailStr, AnyHttpUrl, Field
from typing import List


class Emails(BaseModel):

    emails: List[EmailStr]

    def __str__(self):
        return f'Emails: {self.emails}'

    class Config:
        json_schema_extra = {
            "example": {
                "emails": [
                    "jondoe@example.com",
            ]},}


class EmailScraperRequest(BaseModel):

    webpages: List[AnyHttpUrl] = Field(..., title='Webpages', description='List of webpages to scrape emails from')
    max_worker: int = Field(5, title='Max Worker', description='Max number of workers to scrape emails')
    max_pages: int = Field(5, title='Max Pages', description='Max number of pages to scrape emails from')

    def __str__(self):
        return f'Webpages: {self.webpages}, Max Worker: {self.max_worker}, Max Pages: {self.max_pages}'

    class Config:
        json_schema_extra = {
            "example": {
                "webpages": [
                    "https://www.google.com",
                    "https://www.facebook.com"
                ],
                "max_worker": 5,
                "max_pages": 5
            }
        }

