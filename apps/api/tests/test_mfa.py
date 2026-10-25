import pyotp
from fastapi.testclient import TestClient
from app.main import app


def test_optional_totp_mfa_is_enforced_during_login():
    with TestClient(app) as client:
        registered = client.post("/api/v1/customer/register", json={
            "name": "MFA Test",
            "email": "mfa-test@example.com",
            "password": "correct-horse-battery-7",
        })
        assert registered.status_code == 200, registered.text
        token = registered.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        setup = client.post("/api/v1/auth/mfa/setup", headers=headers)
        assert setup.status_code == 200, setup.text
        secret = setup.json()["secret"]
        code = pyotp.TOTP(secret).now()
        enabled = client.post("/api/v1/auth/mfa/enable", headers=headers, json={"otp": code})
        assert enabled.status_code == 200 and enabled.json()["enabled"] is True

        denied = client.post("/api/v1/auth/login", json={
            "email": "mfa-test@example.com",
            "password": "correct-horse-battery-7",
        })
        assert denied.status_code == 401
        valid_code = pyotp.TOTP(secret).now()
        accepted = client.post("/api/v1/auth/login", json={
            "email": "mfa-test@example.com",
            "password": "correct-horse-battery-7",
            "otp": valid_code,
        })
        assert accepted.status_code == 200, accepted.text
