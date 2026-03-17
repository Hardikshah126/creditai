"""
Basic auth endpoint tests using an in-memory SQLite database.
Run: pytest tests/ -v
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession,
                                       expire_on_commit=False, autoflush=False)

    async def override_get_db():
        async with SessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    yield
    await engine.dispose()
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(db_session):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.anyio
async def test_signup(client):
    r = await client.post("/api/v1/auth/signup", json={
        "name": "Test User",
        "phone": "+1111111111",
        "country": "Ghana",
        "email": "test@example.com",
        "password": "secret123",
    })
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert data["user"]["name"] == "Test User"


@pytest.mark.anyio
async def test_signup_duplicate(client):
    payload = {
        "name": "Dup User",
        "phone": "+2222222222",
        "country": "India",
        "email": "dup@example.com",
        "password": "secret123",
    }
    await client.post("/api/v1/auth/signup", json=payload)
    r = await client.post("/api/v1/auth/signup", json=payload)
    assert r.status_code == 409


@pytest.mark.anyio
async def test_login(client):
    await client.post("/api/v1/auth/signup", json={
        "name": "Login User",
        "phone": "+3333333333",
        "country": "Nigeria",
        "email": "login@example.com",
        "password": "mypassword",
    })
    r = await client.post("/api/v1/auth/login", json={
        "identifier": "login@example.com",
        "password": "mypassword",
    })
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.anyio
async def test_me(client):
    # Signup and use token
    r = await client.post("/api/v1/auth/signup", json={
        "name": "Me User",
        "phone": "+4444444444",
        "country": "Kenya",
        "email": "me@example.com",
        "password": "password1",
    })
    token = r.json()["access_token"]
    r2 = await client.get("/api/v1/auth/me",
                           headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["email"] == "me@example.com"
