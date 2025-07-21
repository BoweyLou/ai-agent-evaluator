from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime, Integer, Text, JSON, Boolean
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from ..core.config import settings

# Convert sync DATABASE_URL to async for SQLAlchemy
if settings.DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DATABASE_URL = settings.DATABASE_URL

# Create async engine
engine = create_async_engine(ASYNC_DATABASE_URL, echo=True if settings.NODE_ENV == "development" else False)

# Create async session maker
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create declarative base
Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50))
    config = Column(JSON)
    baseline_metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(String, primary_key=True)
    task_id = Column(String, nullable=False)
    agents = Column(JSON)  # List of agent names
    status = Column(String(50), default="pending")  # pending, active, completed, failed
    agent_status = Column(JSON, default=dict)  # {agent: status}
    results = Column(JSON, default=dict)  # {agent: results}
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentResult(Base):
    __tablename__ = "agent_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    evaluation_id = Column(String, nullable=False)
    agent_name = Column(String(50), nullable=False)
    score = Column(Integer)
    breakdown = Column(JSON)
    feedback = Column(Text)
    outputs = Column(JSON)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    status = Column(String(50), default="pending")


async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)