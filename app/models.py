import os
import time
import uuid
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc)

def generate_uuid_v7() -> uuid.UUID:
    """Generate a UUID v7 (time-ordered, millisecond precision)."""
    timestamp_ms = int(time.time() * 1000)
    uuid_int = (timestamp_ms & 0xFFFFFFFFFFFF) << 80
    uuid_int |= 0x7000 << 64
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF
    uuid_int |= rand_a << 64
    uuid_int |= 0x8000000000000000
    rand_b = int.from_bytes(os.urandom(8), "big") & 0x3FFFFFFFFFFFFFFF
    uuid_int |= rand_b
    return uuid.UUID(int=uuid_int)


class Request(Base):
    __tablename__ = "requests"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(generate_uuid_v7()))
    url = Column(String, nullable=False)
    method = Column(String, nullable=False)
    body = Column(Text, nullable=True)
    maxRetries = Column(Integer, default=5)
    backoffMs = Column(Integer, default=1000)
    
    # state
    status = Column(String, default="pending", index=True)
    attemptCount = Column(Integer, default=0)
    nextRetryAt = Column(DateTime, nullable=True, index=True)
    lastError = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    
    # attempts = Column(JSON, default=list)

    #timestamp
    createdAt = Column(DateTime, default=_now)
    updatedAt = Column(DateTime, default=_now, onupdate=_now)
    
    attempts = relationship("AttemptHistory", back_populates="request", cascade="all, delete-orphan")
    

class AttemptHistory(Base):
    __tablename__ = "attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, ForeignKey("requests.id", ondelete="CASCADE"), nullable=False)

    attemptNumber = Column(Integer, nullable=False)
    executedAt = Column(DateTime, default=_now)
    error = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    
    request = relationship("Request", back_populates="attempts")


