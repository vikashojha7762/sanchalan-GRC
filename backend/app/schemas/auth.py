from pydantic import BaseModel, EmailStr
from typing import Optional


class UserSignup(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    company_industry: Optional[str] = None
    company_size: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    industry: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
