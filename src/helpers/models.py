from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import UUID
import uuid_utils as uuid
from pydantic import ConfigDict


def utcnow():
    return datetime.utcnow()


class BaseModel(SQLModel):
    """Base model class that provides common fields and functionality for SQLModel-based models.

    This abstract base class defines common fields that should be included in all database models:
    - id: A UUID primary key generated using UUID7
    - is_deleted: A soft deletion flag
    - created_at: Timestamp of when the record was created
    - updated_at: Timestamp of when the record was last updated

    All timestamps are in UTC.

    Attributes:
        id (UUID): Primary key UUID, auto-generated using UUID7
        is_deleted (bool): Soft deletion flag, defaults to False
        created_at (datetime): UTC timestamp of record creation
        updated_at (datetime): UTC timestamp of last update

    Note:
        This is an abstract base class and should not be instantiated directly.
        All model classes should inherit from this base class.
    """

    __abstract__ = True
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)
    id: UUID = Field(default_factory=uuid.uuid7, primary_key=True, index=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
