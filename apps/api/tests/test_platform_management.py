from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def register(client, suffix):
    response = client.post("/api/v1/auth/register", json={
        "name": "Tenant Owner",
        "email": f"owner-{suffix}@example.com",
        "password": "correct-horse-battery-7",
        "store_name": f"Tenant Market {suffix}",
    })
    assert response.status_code == 200
    return response.json()


def test_store_requires_platform_approval_before_retailer_actions():
    with TestClient(app) as client:
        account = register(client, uuid4().hex[:8])
        token = account["token"]
        assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).json()["store_status"] == "pending"
        denied = client.get("/api/v1/admin/summary", headers={"Authorization": f"Bearer {token}"})
        assert denied.status_code == 403

        # A platform admin is provisioned from environment configuration in deployment.
        from app.main import SessionLocal, Account, password_digest, issue_account_token
        from sqlalchemy import select
        admin_email = f"platform-{uuid4().hex[:8]}@example.com"
        with SessionLocal() as db:
            admin = Account(name="Test Platform Admin", email=admin_email, password_hash=password_digest("platform-test-password-9"), role="platform_admin")
            db.add(admin)
            db.commit()
            db.refresh(admin)
            admin_token = issue_account_token(admin)
            store_id = account["account"].get("store_id")
            # The store id is obtained from the persisted owner account.
            owner = db.scalar(select(Account).where(Account.email == account["account"]["email"]))
            store_id = owner.store_id
        headers = {"Authorization": f"Bearer {admin_token}"}
        stores = client.get("/api/v1/platform/stores", headers=headers)
        assert stores.status_code == 200
        target = next(item for item in stores.json()["items"] if item["id"] == store_id)
        approved = client.post(f"/api/v1/platform/stores/{store_id}/review", headers=headers, json={"status": "approved", "notes": "Test approved"})
        assert approved.status_code == 200
        allowed = client.get("/api/v1/admin/summary", headers={"Authorization": f"Bearer {token}"})
        assert allowed.status_code == 200


def test_platform_endpoints_reject_store_owner():
    with TestClient(app) as client:
        account = register(client, uuid4().hex[:8])
        response = client.get("/api/v1/platform/accounts", headers={"Authorization": f"Bearer {account['token']}"})
        assert response.status_code == 403
