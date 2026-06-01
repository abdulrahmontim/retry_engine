from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi import APIRouter, status
from app.database import get_db
from app.schemas import RequestCreate, RequestResponse, RequestDetail
from app.services import RequestService

router = APIRouter(tags=["Request"])


@router.post(
    "/request",
    response_model=RequestResponse,
    status_code=status.HTTP_202_ACCEPTED)
async def create_request(
    payload: RequestCreate,
    db: Session = Depends(get_db)
):
    req_job = await RequestService.create_request(db, payload)
    
    return {
        "id": req_job.id,
        "status": req_job.status
        }


@router.get("/requests/{req_id}", response_model=RequestDetail)
async def get_request(
    req_id: UUID,
    db: Session = Depends(get_db)
    ):
    
    res = await RequestService.get_request(req_id, db)
    
    return res


@router.get("/requests", response_model=RequestResponse)
async def list_requests(
    status: str | None,
    db: Session = Depends(get_db)
):
    queries = await RequestService.list_requests(status, db)
    
    return queries
