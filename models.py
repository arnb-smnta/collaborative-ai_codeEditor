from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from db import Base
import datetime


class User(Base):
    _tablename_ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class CodeFile(Base):
    __tablename__ = "code_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    content = Column(Text, default="")
    last_updated = Column(DateTime, default=datetime.datetime.now)
    owner = relationship("User", back_populates="owner")


User.files = relationship("CodeFile", back_populates="owner")
