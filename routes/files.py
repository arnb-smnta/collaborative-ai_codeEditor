from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
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
                "message": "File successfully created",
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
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
            )

        if file.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this file",
            )

        file.content = file_data.content
        db.commit()
        db.refresh(file)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "File successfully updated"},
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
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
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
                "message": "File fetched successfully",
            },
        )
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get("/")
def get_all_files(db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        files = db.query(CodeFile).filter(CodeFile.user_id == user.id).all()

        if not files:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"files": [], "message": "No files found"},
            )

        file_list = [{"id": file.id, "content": file.content} for file in files]
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"files": file_list, "message": "Files fetched successfully"},
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
    try:
        file = db.query(CodeFile).filter(CodeFile.id == file_id).first()

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
            )

        if file.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this file",
            )

        db.delete(file)
        db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "File successfully deleted"},
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
