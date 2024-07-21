from typing import List, Dict

from pydantic import BaseModel, AnyHttpUrl, Field


class Emails(BaseModel):
    emails: List[Dict[str, List]] = Field(..., title='Emails', description='List of emails scraped from webpages')

    def __str__(self):
        return f'Emails: {self.emails}'

    class Config:
        json_schema_extra = {
            "example": {
                "emails": [
                    {"https://www.google.com":
                         ["1@google.com", "2@gmail.com"]},
                    {"https://www.facebook.com": ["1@facebook.com", "2@facebook.com"]}
                ]
            }
        }


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


class JobStatus(BaseModel):
    job_id: str = Field(..., title='Job ID', description='ID of the job')
    status: str = Field(..., title='Status', description='Status of the job')
    percentage: int = Field(0, title='Percentage', description='Percentage of job completion')

    def __str__(self):
        return f'Job ID: {self.job_id}, Status: {self.status}, Percentage: {self.percentage}'

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "1",
                "status": "In Progress",
                "percentage": 10
            }
        }
