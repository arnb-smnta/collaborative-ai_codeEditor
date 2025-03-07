from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from pydantic import BaseModel, Field
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
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    is_admin: Optional[bool] = False


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8)
    is_admin: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    created_at: int


@router.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Register a new regular (non-admin) user.
    try:
        existing_user = (
            db.query(User).filter(User.username == user_data.username).first()
        )
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
            content={
                "message": "User created successfully",
                "user_id": new_user.id,
                "username": new_user.username,
            },
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.post("/signup-admin")
def create_admin_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Allow an authenticated admin to create new users with admin privileges.
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can create new users with admin privileges",
            )

        existing_user = (
            db.query(User).filter(User.username == user_data.username).first()
        )
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
                "username": new_user.username,
                "is_admin": new_user.is_admin,
            },
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    try:
        user = db.query(User).filter(User.username == form_data.username).first()

        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        # Convert datetime to timestamp
        created_at_timestamp = (
            int(user.created_at.timestamp())
            if isinstance(user.created_at, datetime)
            else user.created_at
        )

        user_data = {
            "id": user.id,
            "username": user.username,
            "is_admin": bool(user.is_admin),  # Ensure proper boolean conversion
            "created_at": created_at_timestamp,
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
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        user_to_update = db.query(User).filter(User.id == user_id).first()

        if not user_to_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Check permissions: must be admin or the user themselves
        is_current_user_admin = bool(current_user.is_admin)
        if not is_current_user_admin and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this user",
            )

        # Only admins can change admin status
        if user_data.is_admin is not None and not is_current_user_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can change admin status",
            )

        # Update username if provided
        if user_data.username is not None:
            # Check if username is already taken by someone else
            existing_user = (
                db.query(User).filter(User.username == user_data.username).first()
            )
            if existing_user is not None and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken",
                )
            user_to_update.username = user_data.username

        # Update password if provided
        if user_data.password is not None:
            user_to_update.hashed_password = get_password_hash(user_data.password)

        # Update admin status if provided and current user is admin
        if user_data.is_admin is not None and is_current_user_admin:
            user_to_update.is_admin = user_data.is_admin

        db.commit()
        db.refresh(user_to_update)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "User updated successfully",
                "user": {
                    "id": user_to_update.id,
                    "username": user_to_update.username,
                    "is_admin": bool(user_to_update.is_admin),
                },
            },
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a user. Users can delete themselves, admins can delete any user."""
    try:
        user_to_delete = db.query(User).filter(User.id == user_id).first()

        if not user_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        is_current_user_admin = bool(current_user.is_admin)
        if not is_current_user_admin and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this user",
            )

        # Prevent deletion of the last admin
        if user_to_delete.is_admin:
            admin_count = db.query(User).filter(User.is_admin == True).count()
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the last admin user",
                )

        db.delete(user_to_delete)
        db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "User deleted successfully", "user_id": user_id},
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.post("/initial-admin")
def create_initial_admin(user_data: UserCreate, db: Session = Depends(get_db)):
    # Create the first admin user when the system is empty.Only works if no users exist in the database.

    try:
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
                "username": new_admin.username,
            },
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
