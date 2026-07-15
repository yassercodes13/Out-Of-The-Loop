from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from contextlib import asynccontextmanager
from config import DATABASE_URL

engine = create_async_engine(
  DATABASE_URL,
  echo = False, 
  pool_size = 5,
  max_overflow = 10,
)

async_session_factory = async_sessionmaker(
  engine,
  expire_on_commit = False, 
  class_ = AsyncSession,
)

@asynccontextmanager
async def get_session():
  async with async_session_factory() as session:
    try:
      yield session
      await session.commit()
    except Exception:
      await session.rollback()
      raise