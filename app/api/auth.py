from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.user import (
    UserCreate,
    UserResponse,
)
from app.services.auth_service import (
    register_user,
    authenticate_user,
)
from app.core.security import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    return register_user(db, user)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    db_user = authenticate_user(
        db,
        form_data.username,   # Email or username
        form_data.password,
    )

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue token with UUID sub and canonical integer user_id
    access_token = create_access_token(
        data={
            "sub": str(db_user.user_uuid),
            "user_id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "user_uuid": db_user.user_uuid,
            "username": db_user.username,
            "email": db_user.email,
        }
    }