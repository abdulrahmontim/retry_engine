import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import engine, Base
from app.models import Request, AttemptHistory
from app.routers import requests
from app.worker import run_worker_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    task = asyncio.create_task(run_worker_loop())
    print("Worker started")

    yield

    task.cancel()
    await task
    print("Worker stopped")

app = FastAPI(lifespan=lifespan)

app.include_router(requests.router)

@app.get("/")
async def index():
    return {"status": "healthy"}