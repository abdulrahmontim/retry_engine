from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base


DATABASE_URL = "sqlite+aiosqlite:///./requests.db"

engine = create_async_engine(DATABASE_URL, echo=False)

Base = declarative_base()

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

async def get_db():
    async with SessionLocal() as session:
        yield session