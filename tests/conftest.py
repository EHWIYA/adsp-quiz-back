"""테스트 설정 및 픽스처"""
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base, get_db
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
async def test_db_session():
    """테스트용 DB 세션"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def client(test_db_session):
    """FastAPI 테스트 클라이언트 (DB 의존성 오버라이드)"""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    client_instance = TestClient(app)
    yield client_instance
    app.dependency_overrides.clear()
