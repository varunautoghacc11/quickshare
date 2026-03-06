import pytest
import json
import io
import fakeredis.aioredis
from httpx import AsyncClient, ASGITransport

from app.main import app
import app.storage as storage_module


@pytest.fixture
async def fake_redis():
    server = fakeredis.aioredis.FakeRedis(decode_responses=True)
    storage_module._redis_client = server
    yield server
    await server.aclose()


@pytest.fixture
async def client(fake_redis):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
class TestReceive:
    async def test_retrieve_valid_text_code(self, client, fake_redis):
        resp = await client.post("/api/share/text", json={"text": "hello test", "type": "text"})
        assert resp.status_code == 200
        code = resp.json()["code"]
        resp2 = await client.get(f"/api/receive/{code}")
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["type"] == "text"
        assert data["content"] == "hello test"
        assert data["expires_in"] > 0

    async def test_retrieve_nonexistent_code(self, client, fake_redis):
        resp = await client.get("/api/receive/000000")
        assert resp.status_code == 404

    async def test_retrieve_invalid_format_alpha(self, client, fake_redis):
        resp = await client.get("/api/receive/abcdef")
        assert resp.status_code == 422

    async def test_retrieve_invalid_format_short(self, client, fake_redis):
        resp = await client.get("/api/receive/12345")
        assert resp.status_code == 422

    async def test_retrieve_invalid_format_long(self, client, fake_redis):
        resp = await client.get("/api/receive/1234567")
        assert resp.status_code == 422

    async def test_retrieve_expired_code(self, client, fake_redis):
        key = "share:777777"
        await fake_redis.setex(key, 1, json.dumps({
            "type": "text", "content": "expiring", "filename": None,
            "filepath": None, "created_at": "2024-01-01T00:00:00Z"
        }))
        await fake_redis.delete(key)
        resp = await client.get("/api/receive/777777")
        assert resp.status_code == 404

    async def test_download_text_share_returns_404(self, client, fake_redis):
        resp = await client.post("/api/share/text", json={"text": "test text", "type": "text"})
        code = resp.json()["code"]
        resp2 = await client.get(f"/api/receive/{code}/download")
        assert resp2.status_code == 404

    async def test_download_file_share(self, client, fake_redis):
        content = b"Hello file content"
        files = {"file": ("hello.txt", io.BytesIO(content), "text/plain")}
        resp = await client.post("/api/share/file", files=files)
        assert resp.status_code == 200
        code = resp.json()["code"]
        resp2 = await client.get(f"/api/receive/{code}")
        assert resp2.status_code == 200
        assert resp2.json()["type"] == "file"
        resp3 = await client.get(f"/api/receive/{code}/download")
        assert resp3.status_code == 200
        assert resp3.content == content
