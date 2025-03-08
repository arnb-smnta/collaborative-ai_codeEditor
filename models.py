from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db import Base
import datetime


from sqlalchemy import (
    Boolean,
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)  # Added admin flag
    created_at = Column(TIMESTAMP, server_default=func.now())

    files = relationship("CodeFile", back_populates="owner")


class CodeFile(Base):
    __tablename__ = "code_files"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, default="")
    last_updated = Column(DateTime, default=datetime.datetime.now)

    owner = relationship(
        "User", back_populates="files"
    )  # Ensure back_populates matches User.files
