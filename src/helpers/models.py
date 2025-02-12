from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Boolean, DateTime, UUID
from datetime import datetime
import uuid_utils as uuid

Base = declarative_base()


def utcnow():
    return datetime.utcnow()


class BaseModel(Base):
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid7)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
