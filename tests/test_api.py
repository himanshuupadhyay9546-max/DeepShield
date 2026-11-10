import os
import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.session import init_db

# Ensure all database tables exist
init_db()
client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_auth_workflow():
    random_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "secretpassword123"

    # Register short password error
    r_short = client.post("/api/v1/auth/register", json={"email": random_email, "password": "123"})
    assert r_short.status_code == 400

    # Register success
    r_reg = client.post("/api/v1/auth/register", json={"email": random_email, "password": password})
    assert r_reg.status_code == 201
    data = r_reg.json()
    assert "access_token" in data
    assert data["email"] == random_email

    # Duplicate register error
    r_dup = client.post("/api/v1/auth/register", json={"email": random_email, "password": password})
    assert r_dup.status_code == 409

    # Login invalid password error
    r_bad_login = client.post("/api/v1/auth/login", json={"email": random_email, "password": "wrong"})
    assert r_bad_login.status_code == 401

    # Login success
    r_login = client.post("/api/v1/auth/login", json={"email": random_email, "password": password})
    assert r_login.status_code == 200
    token = r_login.json()["access_token"]
    assert token

    headers = {"Authorization": f"Bearer {token}"}

    # Fetch /me profile
    r_me = client.get("/api/v1/auth/me", headers=headers)
    assert r_me.status_code == 200
    assert r_me.json()["email"] == random_email
    assert r_me.json()["role"] == "analyst"
    assert "X-Content-Type-Options" in r_me.headers
    assert r_me.headers["X-Content-Type-Options"] == "nosniff"

    # Stats initially 0 for new user
    r_stats = client.get("/api/v1/stats", headers=headers)
    assert r_stats.status_code == 200
    stats = r_stats.json()
    assert stats["total"] == 0
    assert stats["fake"] == 0
    assert stats["real"] == 0
    assert "daily_trends" in stats
    assert len(stats["daily_trends"]) == 7

    # Empty history
    r_hist = client.get("/api/v1/detect/history", headers=headers)
    assert r_hist.status_code == 200
    assert r_hist.json()["total"] == 0
    assert r_hist.json()["items"] == []

    # Invalid image format validation
    r_bad_fmt = client.post(
        "/api/v1/detect/image",
        files={"file": ("malicious.exe", b"fake binary data", "application/octet-stream")},
        headers=headers,
    )
    assert r_bad_fmt.status_code == 400

    # Image detection with auth
    sample_img = "test_samples/images/real/musk_real.jpg"
    det_id = None
    if os.path.exists(sample_img):
        with open(sample_img, "rb") as f:
            r_detect = client.post(
                "/api/v1/detect/image",
                files={"file": ("musk.jpg", f, "image/jpeg")},
                headers=headers,
            )
        assert r_detect.status_code == 200
        det_data = r_detect.json()
        assert det_data["label"] in ["REAL", "FAKE"]
        assert "confidence" in det_data
        assert "heatmap_b64" in det_data
        assert "processing_time_ms" in det_data
        assert "id" in det_data
        det_id = det_data["id"]

        # Verify stats updated with real telemetry
        r_stats_after = client.get("/api/v1/stats", headers=headers)
        assert r_stats_after.status_code == 200
        stats_after = r_stats_after.json()
        assert stats_after["total"] == 1
        assert stats_after["media_distribution"]["image"] == 1
        assert stats_after["avg_confidence"] > 0

        # Verify history has the record
        r_hist_after = client.get("/api/v1/detect/history", headers=headers)
        assert r_hist_after.status_code == 200
        hist_data = r_hist_after.json()
        assert hist_data["total"] == 1
        assert hist_data["items"][0]["filename"] == "musk.jpg"
        assert hist_data["items"][0]["media_type"] == "image"

        # Verify single item fetch
        if det_id:
            r_single = client.get(f"/api/v1/detect/{det_id}", headers=headers)
            assert r_single.status_code == 200
            assert r_single.json()["id"] == det_id


def test_unauthenticated_stats():
    r = client.get("/api/v1/stats")
    assert r.status_code == 401
