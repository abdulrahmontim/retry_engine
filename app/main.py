from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import engine, Base
from app.models import Request, AttemptHistory
from app.routers import requests


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created!")
    
    yield
    
    print("🛑 Server shutting down.")

app = FastAPI(lifespan=lifespan)

app.include_router(requests.router)

@app.get("/")
async def index():
    return {"status": "healthy"}