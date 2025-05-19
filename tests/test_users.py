import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.config import Settings
import os


is_ci = os.getenv("GITHUB_ACTIONS") == "true"
test_settings = Settings(_env_file=None if is_ci else ".env.test")
DATABASE_URL_TEST = test_settings.db_url

# 🔄 Do NOT use shared engine/session outside of test scope
@pytest_asyncio.fixture()
async def test_db():
    engine = create_async_engine(DATABASE_URL_TEST, echo=False)
    TestSession = async_sessionmaker(bind=engine, expire_on_commit=False)

    async def override_get_db():
        async with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    # Create schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_user(test_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/users/", json={"name": "John", "email": "john@example.com"})
    assert response.status_code == 200
    assert response.json()["email"] == "john@example.com"


@pytest.mark.asyncio
async def test_read_users(test_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
