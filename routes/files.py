from email import message
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from auth import get_current_user, get_db
from models import CodeFile

router = APIRouter()


@router.post("/")
def create_file(db: Session = Depends(get_db), user=Depends(get_current_user)):
    new_file = CodeFile(user_id=user.id, content="")
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"newFile": new_file, "message": "File succesfully created"},
    )


@router.put("/{file_id}")
def update_file(
    file_id: int,
    content: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    file = (
        db.query(CodeFile)
        .filter(CodeFile.id == file_id, CodeFile.user_id == user)
        .first()
    )

    if not file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    file.content = content
    db.commit()
    db.refresh(file)
    return JSONResponse(
        status_code=status.HTTP_200_OK, content={"message": "File Successfully updated"}
    )


@router.get("/{file_id}")
def get_file(
    file_id: int,
    content: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    file = (
        db.query(CodeFile)
        .filter(CodeFile.id == file_id, CodeFile.user_id == user)
        .first()
    )

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not Found"
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"file": file, "message": "File fetched succesfully"},
    )


@router.get("/file")
def get_all_files(db: Session = Depends(get_db), user=Depends(get_current_user)):
    files = db.query(CodeFile).filter(CodeFile.user_id == user.id).all()
    if not files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No files Found"
        )

    file_ids = [{"id": file.id} for file in files]
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"files": file_ids, message: "Files fetched succesfully"},
    )
