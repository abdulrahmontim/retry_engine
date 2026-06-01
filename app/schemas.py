from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Literal, List
from uuid import UUID
from datetime import datetime


# req POST
class RequestCreate(BaseModel):
    url : HttpUrl
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    body: Optional[str] = None
    maxRetries: Optional[int] = Field(default=5, ge=0)
    backoffMs: Optional[int] = Field(default=1000, ge=0)


# req POST
class RequestResponse(BaseModel):
    id: UUID
    status: Literal["pending"]


class AttemptHistory(BaseModel):
    attemptNumber: int
    executedAt: datetime
    status: Optional[str] = None
    error: Optional[str] = None
    result: Optional[str] = None


# req/id
class RequestDetail(BaseModel):
    id: UUID
    url: HttpUrl
    method: str
    body: Optional[str] = None
    status: Literal["pending", "retrying", "completed", "failed"]

    attemptCount: int
    nextRetryAt: Optional[datetime] = None
    lastError: Optional[str] = None
    result: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    attempts: List[AttemptHistory] = []

