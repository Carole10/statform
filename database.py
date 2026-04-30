# import os
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base
# from dotenv import load_dotenv

# load_dotenv()
# DATABASE_URL = os.getenv("DATABASE_URL")
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#        db.close()


# import os
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
# from sqlalchemy.orm import DeclarativeBase
# from dotenv import load_dotenv

# load_dotenv()

# # Convertir l'URL postgres → asyncpg
# DATABASE_URL = os.getenv("DATABASE_URL", "").replace(
#     "postgresql://", "postgresql+asyncpg://"
# ).split("?")[0]  # asyncpg ne supporte pas tous les params SSL en URL

# engine = create_async_engine(DATABASE_URL, echo=False)
# async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# class Base(DeclarativeBase):
#     pass

# async def get_async_session() -> AsyncSession:
#     async with async_session_maker() as session:
#         yield session


import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

# Conversion URL : postgresql:// → postgresql+asyncpg://
# On retire les params SSL incompatibles avec asyncpg
DATABASE_URL = os.getenv("DATABASE_URL", "").replace(
    "postgresql://", "postgresql+asyncpg://"
)#.split("?")[0]

engine = create_async_engine(DATABASE_URL, echo=False, poolclass=NullPool)  # ← recommandé pour Neon)

AsyncSessionLocal = async_sessionmaker(
    engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

Base = declarative_base()

# Equivalent de ton get_db() mais async
async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
