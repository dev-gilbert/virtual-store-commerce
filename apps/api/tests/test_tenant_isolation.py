from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.main import Account, StoreTenant, SessionLocal, password_digest, issue_account_token, app

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_storefront_and_catalogue_are_isolated_by_tenant(client):
    suffix = uuid4().hex[:10]
    store_id = str(uuid4())
    with SessionLocal() as db:
        owner = Account(
            name="Tenant Isolation Owner",
            email=f"tenant-{suffix}@example.com",
            password_hash=password_digest("correct-horse-battery-7"),
            role="store_owner",
            store_name=f"Tenant {suffix}",
            store_id=store_id,
        )
        db.add(owner)
        db.flush()
        store = StoreTenant(
            id=store_id,
            name=f"Tenant {suffix}",
            slug=f"tenant-{suffix}",
            owner_account_id=owner.id,
            status="approved",
        )
        db.add(store)
        db.commit()
        token = issue_account_token(owner)

    sku = f"ISOLATED-{suffix.upper()}"
    created = client.post(
        "/api/v1/admin/products",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "sku": sku,
            "name": f"Private Product {suffix}",
            "category": "Tenant Test",
            "price": 1234,
            "stock_quantity": 8,
            "description": "Belongs only to one approved tenant",
        },
    )
    assert created.status_code == 201, created.text

    tenant_results = client.get(
        "/api/v1/products",
        params={"q": sku},
        headers={"X-Store-ID": store_id},
    )
    assert tenant_results.status_code == 200
    assert [item["sku"] for item in tenant_results.json()["items"]] == [sku]

    public_results = client.get("/api/v1/products", params={"q": sku})
    assert public_results.status_code == 200
    assert all(item["sku"] != sku for item in public_results.json()["items"])

    other_store_id = str(uuid4())
    with SessionLocal() as db:
        other_owner = Account(
            name="Other Tenant",
            email=f"other-{suffix}@example.com",
            password_hash=password_digest("correct-horse-battery-7"),
            role="store_owner",
            store_name=f"Other {suffix}",
            store_id=other_store_id,
        )
        db.add(other_owner)
        db.flush()
        db.add(StoreTenant(
            id=other_store_id,
            name=f"Other {suffix}",
            slug=f"other-{suffix}",
            owner_account_id=other_owner.id,
            status="approved",
        ))
        db.commit()

    other_results = client.get(
        "/api/v1/products",
        params={"q": sku},
        headers={"X-Store-ID": other_store_id},
    )
    assert other_results.status_code == 200
    assert other_results.json()["total"] == 0
