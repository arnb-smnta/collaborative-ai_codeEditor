from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from pydantic import BaseModel
from auth import get_current_user, get_db
from models import CodeFile

router = APIRouter()


class FileContent(BaseModel):
    content: str


class FileResponse(BaseModel):
    id: int
    content: str
    user_id: int


class FileListResponse(BaseModel):
    id: int
    content: str


class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 100


@router.post("/")
def create_file(db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        new_file = CodeFile(user_id=user.id, content="")
        db.add(new_file)
        db.commit()
        db.refresh(new_file)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "newFile": {
                    "id": new_file.id,
                    "content": new_file.content,
                    "user_id": new_file.user_id,
                },
                "message": "Code File successfully created",
            },
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.put("/{file_id}")
def update_file(
    file_id: int,
    file_data: FileContent,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        file = db.query(CodeFile).filter(CodeFile.id == file_id).first()

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Code File not found"
            )

        if file.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authorized to update this file",
            )

        file.content = file_data.content
        db.commit()
        db.refresh(file)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "file": {
                    "id": file.id,
                    "content": file.content,
                    "user_id": file.user_id,
                },
                "message": "Code File successfully updated",
            },
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get("/{file_id}")
def get_file(
    file_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    try:
        file = db.query(CodeFile).filter(CodeFile.id == file_id).first()

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Code File not found"
            )

        if file.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this file",
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "file": {
                    "id": file.id,
                    "content": file.content,
                    "user_id": file.user_id,
                },
                "message": "Code File fetched successfully",
            },
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get("/")
def get_all_files(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # pagination suppotred
    try:
        query = db.query(CodeFile).filter(CodeFile.user_id == user.id)
        total_count = query.count()

        files = query.offset(skip).limit(limit).all()

        if not files:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "files": [],
                    "total": 0,
                    "skip": skip,
                    "limit": limit,
                    "message": "No code files found",
                },
            )

        file_list = [{"id": file.id, "content": file.content} for file in files]
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "files": file_list,
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "message": "Files fetched successfully",
            },
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Delete a specific file if owned by the authenticated user.
    try:
        file = db.query(CodeFile).filter(CodeFile.id == file_id).first()

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Code File not found"
            )

        if file.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authorized to delete this file",
            )

        db.delete(file)
        db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "id": file_id,
                "message": "Code File successfully deleted",
            },
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
