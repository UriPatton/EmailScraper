from fastapi import FastAPI

from auth.database import Base, engine
from route import router


app = FastAPI()
app.include_router(router)


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)

