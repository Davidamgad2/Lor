from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import UUID
import uuid_utils as uuid


def utcnow():
    return datetime.utcnow()


class BaseModel(SQLModel):
    __abstract__ = True

    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True, index=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
