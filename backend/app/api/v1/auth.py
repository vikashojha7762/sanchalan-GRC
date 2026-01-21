from datetime import datetime, timedelta
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User, Company, Role, Department
from app.schemas.auth import UserSignup, UserLogin, Token, TokenData
from typing import List
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    
    if email is None or user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id, User.email == email).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    """
    Sign up a new user. If company exists, user joins that company.
    If company doesn't exist, creates a new company and makes user admin.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if company exists (by name if provided)
    company = None
    is_first_user_in_company = False
    
    if user_data.company_name:
        company = db.query(Company).filter(Company.name == user_data.company_name).first()
        
        if company:
            # Company exists - check if it's the first user
            existing_users_count = db.query(User).filter(User.company_id == company.id).count()
            is_first_user_in_company = (existing_users_count == 0)
        else:
            # Company doesn't exist - create it
            company = Company(
                name=user_data.company_name,
                domain=user_data.company_domain,
                industry=user_data.company_industry,
                size=user_data.company_size,
                is_active=True
            )
            db.add(company)
            db.flush()
            is_first_user_in_company = True
    else:
        # No company name provided - create a default company
        # This shouldn't happen in normal flow, but handle it gracefully
        company = Company(
            name=f"Company_{user_data.email.split('@')[0]}",
            domain=user_data.company_domain,
            industry=user_data.company_industry,
            size=user_data.company_size,
            is_active=True
        )
        db.add(company)
        db.flush()
        is_first_user_in_company = True
    
    # Get or create roles
    admin_role = db.query(Role).filter(Role.name == "Admin").first()
    if not admin_role:
        admin_role = Role(
            name="Admin",
            description="Administrator role with full access",
            permissions="all",
            is_active=True
        )
        db.add(admin_role)
        db.flush()
    
    # Get or create Contributor role for regular users
    contributor_role = db.query(Role).filter(Role.name == "Contributor").first()
    if not contributor_role:
        contributor_role = Role(
            name="Contributor",
            description="Regular user role with standard access",
            permissions="read,write",
            is_active=True
        )
        db.add(contributor_role)
        db.flush()
    
    # Determine user role: Admin if first user, Contributor otherwise
    user_role = admin_role if is_first_user_in_company else contributor_role
    is_superuser = is_first_user_in_company
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        company_id=company.id,
        role_id=user_role.id,
        is_active=True,
        is_superuser=is_superuser
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access token
    access_token_expires = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires - datetime.utcnow()
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login endpoint. Returns JWT token on successful authentication.
    Accepts email, password, and optional industry in JSON body.
    Validates that the selected industry matches the user's company industry if provided.
    """
    # Log login attempt (without sensitive data)
    logger.info(f"Login attempt for email: {login_data.email}")
    
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user:
        logger.warning(f"Login failed: User not found for email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        logger.warning(f"Login failed: Invalid password for email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login failed: Inactive account for email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Validate industry matches user's company industry (if industry is provided)
    if login_data.industry and login_data.industry.strip():
        # Get user's company
        company = db.query(Company).filter(Company.id == user.company_id).first()
        if not company:
            logger.error(f"Login failed: Company not found for user: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User company not found"
            )
        
        # Check if selected industry matches company industry
        if company.industry and company.industry.upper() != login_data.industry.upper():
            logger.warning(f"Login failed: Industry mismatch for email: {login_data.email}. Expected: {company.industry}, Got: {login_data.industry}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Industry mismatch. Your account is registered with {company.industry} industry. Please select the correct industry to sign in."
            )
    # Note: Industry is now optional - if not provided, we skip validation
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token_expires = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires - datetime.utcnow()
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/departments")
async def get_departments_by_email(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Get departments for a company based on user email.
    Returns all departments in the user's company.
    This endpoint is public and doesn't require authentication.
    """
    if not email or '@' not in email:
        return []
    
    # Find user by email to get their company
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # User doesn't exist yet (new signup) - return empty list
        return []
    
    if not user.company_id:
        # User exists but has no company - return empty list
        return []
    
    # Get all departments for the user's company
    departments = db.query(Department).filter(
        Department.company_id == user.company_id,
        Department.is_active == True
    ).all()
    
    # Return department list
    return [
        {
            "id": dept.id,
            "name": dept.name,
            "description": dept.description or ""
        }
        for dept in departments
    ]
