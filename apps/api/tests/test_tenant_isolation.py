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

    auth_headers = {"Authorization": f"Bearer {token}"}
    draft = client.post(
        "/api/v1/admin/layout-versions",
        headers=auth_headers,
        json={"items":[{"id":"draft-shelf","name":"Tenant Fresh Shelf","kind":"shelf","x":0,"z":0,"products":[created.json()["id"]]}]},
    )
    assert draft.status_code == 200, draft.text
    validated = client.post(f"/api/v1/admin/layout-versions/{draft.json()['id']}/validate", headers=auth_headers)
    assert validated.status_code == 200 and validated.json()["valid"] is True
    published = client.post(f"/api/v1/admin/layout-versions/{draft.json()['id']}/publish", headers=auth_headers)
    assert published.status_code == 200, published.text
    live_layout = client.get("/api/v1/store-layout", headers=auth_headers)
    assert live_layout.status_code == 200 and live_layout.json()["total"] == 1
    fixture = live_layout.json()["items"][0]
    assert fixture["products"][0]["product_id"] == created.json()["id"]

    empty_shelf_draft = client.post(
        "/api/v1/admin/layout-versions",
        headers=auth_headers,
        json={"items":[{"id":fixture["id"],"name":fixture["name"],"kind":"shelf","x":0,"z":0,"products":[]}]},
    )
    assert empty_shelf_draft.status_code == 200, empty_shelf_draft.text
    assert client.post(f"/api/v1/admin/layout-versions/{empty_shelf_draft.json()['id']}/publish", headers=auth_headers).status_code == 200
    restored = client.post(f"/api/v1/admin/layout-versions/{draft.json()['id']}/rollback", headers=auth_headers)
    assert restored.status_code == 200, restored.text
    assert client.get("/api/v1/store-layout", headers=auth_headers).json()["items"][0]["products"][0]["product_id"] == created.json()["id"]

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

    tenant_headers = {"X-Store-ID": store_id}
    order_session = "tenant-order-" + suffix
    added = client.post(
        "/api/v1/cart/items?session_id=" + order_session,
        headers=tenant_headers,
        json={"product_id": created.json()["id"], "quantity": 1},
    )
    assert added.status_code == 200, added.text
    order = client.post(
        "/api/v1/checkout",
        headers={**tenant_headers, "Idempotency-Key": "tenant-order-" + suffix},
        json={
            "session_id": order_session,
            "customer_name": "Tenant Shopper",
            "customer_phone": "+250788123456",
            "delivery_address": "Tenant delivery address",
        },
    )
    assert order.status_code == 200, order.text
    cross_tenant_order = client.get(
        f"/api/v1/orders/{order.json()['id']}",
        params={"session_id": order_session},
        headers={"X-Store-ID": other_store_id},
    )
    assert cross_tenant_order.status_code == 404
