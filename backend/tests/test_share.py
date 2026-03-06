import pytest
import fakeredis.aioredis
from httpx import AsyncClient, ASGITransport
import io

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
class TestShareText:
    async def test_share_text_success(self, client, fake_redis):
        resp = await client.post("/api/share/text", json={"text": "hello world", "type": "text"})
        assert resp.status_code == 200
        data = resp.json()
        assert "code" in data
        assert len(data["code"]) == 6
        assert data["code"].isdigit()
        assert data["expires_in"] == 600
        assert data["type"] == "text"

    async def test_share_text_empty_text(self, client, fake_redis):
        resp = await client.post("/api/share/text", json={"text": "", "type": "text"})
        assert resp.status_code == 422

    async def test_share_text_whitespace_only(self, client, fake_redis):
        resp = await client.post("/api/share/text", json={"text": "   ", "type": "text"})
        assert resp.status_code == 422

    async def test_share_text_oversized(self, client, fake_redis):
        big_text = "a" * (101 * 1024)
        resp = await client.post("/api/share/text", json={"text": big_text, "type": "text"})
        assert resp.status_code == 422

    async def test_share_text_max_allowed(self, client, fake_redis):
        text = "a" * (100 * 1024)
        resp = await client.post("/api/share/text", json={"text": text, "type": "text"})
        assert resp.status_code == 200

    async def test_share_text_missing_body(self, client, fake_redis):
        resp = await client.post("/api/share/text", json={})
        assert resp.status_code == 422

    async def test_share_text_returns_unique_codes(self, client, fake_redis):
        codes = []
        for _ in range(5):
            resp = await client.post("/api/share/text", json={"text": "test", "type": "text"})
            assert resp.status_code == 200
            codes.append(resp.json()["code"])
        for code in codes:
            assert len(code) == 6
            assert code.isdigit()


@pytest.mark.asyncio
class TestShareFile:
    async def test_share_file_valid_pdf(self, client, fake_redis):
        files = {"file": ("test.pdf", io.BytesIO(b"PDF content"), "application/pdf")}
        resp = await client.post("/api/share/file", files=files)
        assert resp.status_code == 200
        data = resp.json()
        assert "code" in data
        assert data["type"] == "file"

    async def test_share_file_invalid_extension_exe(self, client, fake_redis):
        files = {"file": ("evil.exe", io.BytesIO(b"MZ malware"), "application/octet-stream")}
        resp = await client.post("/api/share/file", files=files)
        assert resp.status_code == 400

    async def test_share_file_invalid_extension_php(self, client, fake_redis):
        files = {"file": ("shell.php", io.BytesIO(b"<?php system($_GET['cmd']); ?>"), "text/plain")}
        resp = await client.post("/api/share/file", files=files)
        assert resp.status_code == 400

    async def test_share_file_invalid_extension_sh(self, client, fake_redis):
        files = {"file": ("backdoor.sh", io.BytesIO(b"#!/bin/bash\nrm -rf /"), "text/plain")}
        resp = await client.post("/api/share/file", files=files)
        assert resp.status_code == 400

    async def test_share_file_png_valid(self, client, fake_redis):
        png_header = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
        files = {"file": ("image.png", io.BytesIO(png_header), "image/png")}
        resp = await client.post("/api/share/file", files=files)
        assert resp.status_code == 200

    async def test_share_file_docx_valid(self, client, fake_redis):
        files = {"file": ("doc.docx", io.BytesIO(b"PK fake docx"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        resp = await client.post("/api/share/file", files=files)
        assert resp.status_code == 200
