from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from jose import JWTError, jwt
from passlib.context import CryptContext

# Schemas for Validation
class ViolationCreate(BaseModel):
    timestamp: str
    violation_type: int
    confidence_score: float
    video_directory: str
    camera_id: str

class ViolationLog(BaseModel):
    id: str
    timestamp: str
    violation_name: str
    video_url: str

    class Config:
        from_attributes = True

class ViolationResponse(BaseModel):
    status: str
    data_count: int
    logs: List[ViolationLog]

class LoginRequest(BaseModel):
    username: str
    password: str