from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, status, Depends, Response
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
    db: AsyncSession = Depends(get_db)
):
    req_job = await RequestService.create_request(db=db, payload=payload)
    
    return {
        "id": req_job.id,
        "status": req_job.status
        }


@router.get("/requests/{req_id}", response_model=RequestDetail)
async def get_request(
    req_id: UUID,
    db: AsyncSession = Depends(get_db)
    ):
    
    res = await RequestService.get_request(req_id, db)
    
    return res


@router.get("/requests", response_model=list[RequestDetail])
async def list_requests(
    status: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    queries = await RequestService.list_requests(status, db)
    
    return queries



mock_attempt_counter = 0
@router.get("/mock-target")
async def mock_target():
    global mock_attempt_counter
    mock_attempt_counter += 1
    
    # 500 failure
    if mock_attempt_counter <= 3:
        return Response(content="Simulated Server Overload", status_code=500)
    
    # 200
    mock_attempt_counter = 0 
    return {"message": "Success on attempt 4!"}
