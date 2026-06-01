
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Request as RequestModel
from app.schemas import RequestCreate


class RequestService:
    
    @staticmethod
    async def create_request(payload: RequestCreate, db: AsyncSession):
        req_job = RequestModel(
            url=str(payload.url),
            method=payload.method,
            body=payload.body,
            maxRetries=payload.maxRetries,
            backoffMs=payload.backoffMs,
            status="pending"
        )
        
        db.add(req_job)
        await db.commit()
        await db.refresh(req_job)

        return req_job
    
    
    @staticmethod
    async def get_request(req_id: UUID, db: AsyncSession):
        stmt = select(RequestModel).options(selectinload(RequestModel.attempts)).where(RequestModel.id == str(req_id))
        result = await db.execute(stmt)

        req_job = result.scalar_one_or_none()
        
        if not req_job:
            raise HTTPException(status_code=404, detail="Request not found")
        
        return req_job


    @staticmethod
    async def list_requests(status: str | None, db: AsyncSession):
        stmt = select(RequestModel).options(selectinload(RequestModel.attempts))
        
        if status:
            stmt = stmt.where(RequestModel.status == status)
            
        result = await db.execute(stmt)
        return list(result.scalars().all())