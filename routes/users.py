from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from auth import get_db, get_current_user
from models import User
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta


router = APIRouter()


class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: Optional[bool] = False


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None


@router.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Allows anyone to create an account, but all users will be non-admin.
    """
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    new_user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        is_admin=False,  # Force all registered users to be non-admin
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "User created successfully", "user_id": new_user.id},
    )


@router.post("/signup-admin")
def signup(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Allows an authenticated admin to create new users.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create new users",
        )

    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    new_user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        is_admin=user_data.is_admin,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "User created successfully",
            "user_id": new_user.id,
            "username": user_data.username,
        },
    )


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    user_data = {
        "id": user.id,
        "username": user.username,
        "is_admin": user.is_admin
        is True,  # Convert SQLAlchemy boolean to Python boolean
        "created_at": int(user.created_at.timestamp())
        if isinstance(user.created_at, datetime)
        else user.created_at,
    }

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "message": "User logged in successfully",
            "user": user_data,
        },
    )


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_to_update = db.query(User).filter(User.id == user_id).first()

    if not user_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not bool(current_user.is_admin) and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user",
        )

    # Only admins can change admin status
    if user_data.is_admin is not None and current_user.is_admin is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can change admin status",
        )

    if user_data.username is not None:
        # Check if username is already taken
        existing_user = (
            db.query(User).filter(User.username == user_data.username).first()
        )
        if existing_user is not None and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
            )
        user_to_update.username = user_data.username

    if user_data.password is not None:
        user_to_update.hashed_password = get_password_hash(user_data.password)

    if user_data.is_admin is not None and current_user.is_admin is True:
        user_to_update.is_admin = user_data.is_admin

    db.commit()
    db.refresh(user_to_update)

    return JSONResponse(
        status_code=status.HTTP_200_OK, content={"message": "User updated successfully"}
    )


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get the user to delete
    user_to_delete = db.query(User).filter(User.id == user_id).first()

    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if bool(current_user.is_admin) is not True and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user",
        )

    if user_to_delete.is_admin is True:
        admin_count = db.query(User).filter(User.is_admin == True).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last admin user",
            )

    db.delete(user_to_delete)
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK, content={"message": "User deleted successfully"}
    )


@router.post("/initial-admin")
def create_initial_admin(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Special endpoint to create the first admin user when the system is empty.
    Only works if no users exist in the database.
    """

    user_count = db.query(User).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Initial admin can only be created when no users exist",
        )

    hashed_password = get_password_hash(user_data.password)
    new_admin = User(
        username=user_data.username,
        hashed_password=hashed_password,
        is_admin=True,  # Force admin status
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "Initial admin user created successfully",
            "user_id": new_admin.id,
        },
    )
