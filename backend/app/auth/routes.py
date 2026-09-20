from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.auth.schemas import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.auth.security import create_access_token, hash_password, verify_password
from app.database.models import AuditLog, User
from app.database.session import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])
Database = Annotated[Session, Depends(get_db)]


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Database) -> TokenResponse:
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    db.add(AuditLog(user_id=user.id, action="auth.register"))
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(str(user.id)), user=user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Database) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    db.add(AuditLog(user_id=user.id, action="auth.login"))
    db.commit()
    return TokenResponse(access_token=create_access_token(str(user.id)), user=user)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUser) -> User:
    return current_user


@router.post("/logout", response_model=MessageResponse)
def logout(current_user: CurrentUser, db: Database) -> MessageResponse:
    db.add(AuditLog(user_id=current_user.id, action="auth.logout"))
    db.commit()
    return MessageResponse(message="Logged out; discard the bearer token on the client")
