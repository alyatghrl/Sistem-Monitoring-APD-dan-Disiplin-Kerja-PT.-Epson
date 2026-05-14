from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from jose import JWTError, jwt
from passlib.context import CryptContext

# Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./violations.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy Models
class DBViolation(Base):
    __tablename__ = "violations"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String)
    violation_type = Column(Integer)
    confidence_score = Column(Float)
    video_directory = Column(String)
    camera_id = Column(String)

class DBUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String)
    permissions = Column(String)

Base.metadata.create_all(bind=engine)