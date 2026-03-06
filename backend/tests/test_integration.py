import pytest
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
class TestFullTextFlow:
    async def test_send_receive_text_roundtrip(self, client, fake_redis):
        original_text = "This is my secret message"
        share_resp = await client.post("/api/share/text", json={"text": original_text, "type": "text"})
        assert share_resp.status_code == 200
        code = share_resp.json()["code"]
        assert len(code) == 6
        get_resp = await client.get(f"/api/receive/{code}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["type"] == "text"
        assert data["content"] == original_text
        assert data["expires_in"] > 0

    async def test_wrong_code_returns_404(self, client, fake_redis):
        resp = await client.get("/api/receive/000001")
        assert resp.status_code == 404

    async def test_ttl_is_set_correctly(self, client, fake_redis):
        resp = await client.post("/api/share/text", json={"text": "ttl check", "type": "text"})
        code = resp.json()["code"]
        ttl = await fake_redis.ttl(f"share:{code}")
        assert 595 <= ttl <= 600

    async def test_multiple_shares_independent(self, client, fake_redis):
        r1 = await client.post("/api/share/text", json={"text": "message one", "type": "text"})
        r2 = await client.post("/api/share/text", json={"text": "message two", "type": "text"})
        c1 = r1.json()["code"]
        c2 = r2.json()["code"]
        g1 = await client.get(f"/api/receive/{c1}")
        g2 = await client.get(f"/api/receive/{c2}")
        assert g1.json()["content"] == "message one"
        assert g2.json()["content"] == "message two"


@pytest.mark.asyncio
class TestFullFileFlow:
    async def test_send_receive_file_roundtrip(self, client, fake_redis):
        file_content = b"Binary file data \x00\x01\x02\x03"
        files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
        share_resp = await client.post("/api/share/file", files=files)
        assert share_resp.status_code == 200
        code = share_resp.json()["code"]
        assert len(code) == 6
        meta_resp = await client.get(f"/api/receive/{code}")
        assert meta_resp.status_code == 200
        meta = meta_resp.json()
        assert meta["type"] == "file"
        assert meta["filename"] is not None
        assert meta["download_url"] == f"/api/receive/{code}/download"
        dl_resp = await client.get(f"/api/receive/{code}/download")
        assert dl_resp.status_code == 200
        assert dl_resp.content == file_content

    async def test_file_ttl_set_correctly(self, client, fake_redis):
        files = {"file": ("image.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")}
        resp = await client.post("/api/share/file", files=files)
        code = resp.json()["code"]
        ttl = await fake_redis.ttl(f"share:{code}")
        assert 595 <= ttl <= 600


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health_returns_ok(self, client, fake_redis):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
