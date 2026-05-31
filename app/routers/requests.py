from uuid import UUID
import uuid7

from fastapi import APIRouter, status
from app.schemas import * #update

router = APIRouter(tags=["Request"])


@router.post("/request", status_code=status.HTTP_202_ACCEPTED)
async def submit_request(
    url,
    method,
    body,
    maxRetries,
    backoffMs
):
    return {"message": "submitting..."}


@router.get("/requests/{req_id}")
async def request_by_id(
    req_id: UUID
    ):
    return {"message": "requesting by {req_id}..."}


@router.get("/requests")
async def get_requests(
    status
):
    return {"message": "getting requests with status={status}..."}
