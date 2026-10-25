from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import Account, StoreTenant, SessionLocal, app, password_digest, issue_account_token


def test_store_manager_has_explicit_limited_write_permissions():
    suffix = uuid4().hex[:8]
    store_id = str(uuid4())
    with SessionLocal() as db:
        owner = Account(
            name="Permission Owner",
            email=f"permission-owner-{suffix}@example.com",
            password_hash=password_digest("correct-horse-battery-7"),
            role="store_owner",
            store_name=f"Permission Store {suffix}",
            store_id=store_id,
        )
        db.add(owner)
        db.flush()
        db.add(StoreTenant(
            id=store_id,
            name=f"Permission Store {suffix}",
            slug=f"permission-store-{suffix}",
            owner_account_id=owner.id,
            status="approved",
        ))
        manager = Account(
            name="Permission Manager",
            email=f"permission-manager-{suffix}@example.com",
            password_hash=password_digest("correct-horse-battery-8"),
            role="store_manager",
            store_name=owner.store_name,
            store_id=store_id,
        )
        db.add(manager)
        db.commit()
        manager_token = issue_account_token(manager)
        owner_token = issue_account_token(owner)

    headers = {"Authorization": f"Bearer {owner_token}"}
    manager_headers = {"Authorization": f"Bearer {manager_token}"}
    with TestClient(app) as client:
        created = client.post("/api/v1/admin/products", headers=headers, json={
            "sku": f"ROLE-{suffix}",
            "name": "Role Test Product",
            "category": "Testing",
            "price": 1200,
            "stock_quantity": 5,
        })
        assert created.status_code == 201, created.text
        product_id = created.json()["id"]

        # A manager may perform operational stock adjustments.
        adjusted = client.post("/api/v1/admin/inventory/adjust", headers=manager_headers, json={
            "product_id": product_id,
            "quantity_delta": 2,
            "reason": "cycle count",
            "reference": "role-test",
        })
        assert adjusted.status_code == 200, adjusted.text
        assert adjusted.json()["stock_quantity"] == 7

        # A manager cannot create products, manage staff, or publish a layout.
        denied_product = client.post("/api/v1/admin/products", headers=manager_headers, json={
            "sku": f"DENIED-{suffix}",
            "name": "Must Not Be Created",
            "category": "Testing",
            "price": 1200,
            "stock_quantity": 1,
        })
        assert denied_product.status_code == 403

        denied_staff = client.get("/api/v1/admin/staff", headers=manager_headers)
        assert denied_staff.status_code == 403

        denied_publish = client.post("/api/v1/admin/layout-versions/not-a-version/publish", headers=manager_headers)
        assert denied_publish.status_code == 403
