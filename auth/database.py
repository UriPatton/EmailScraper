from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


SQLALCHEMY_DATABASE_URL = 'sqlite:///database.db'

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    email = Column(String, unique=True, nullable=False, primary_key=True)
    password = Column(String)
    hashed_password = Column(String)
    role = Column(String)
