import pytest
import asyncio
import fakeredis.aioredis
import app.storage as storage_module


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def fake_redis():
    server = fakeredis.aioredis.FakeRedis(decode_responses=True)
    storage_module._redis_client = server
    yield server
    await server.aclose()
