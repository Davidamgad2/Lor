from helpers.models import BaseModel
from sqlmodel import Column, String, Boolean


class User(BaseModel):
    __tablename__ = "users"

    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
