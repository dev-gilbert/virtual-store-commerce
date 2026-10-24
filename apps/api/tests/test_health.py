from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    # Entering TestClient runs FastAPI's lifespan, which creates tables and seeds fixtures.
    with TestClient(app) as test_client:
        yield test_client

def test_health(client):
    r=client.get("/health")
    assert r.status_code==200 and r.json()["status"]=="ok"

def test_seeded_catalogue_and_layout_share_product_ids(client):
    ps=client.get("/api/v1/products").json()
    layout=client.get("/api/v1/store-layout").json()
    ids={p["id"] for p in ps["items"]}
    placed={p["product_id"] for f in layout["items"] for p in f["products"]}
    assert ps["total"]>=8 and layout["total"]>=4 and placed.issubset(ids) and placed

def test_cart_checkout_idempotency_and_sandbox_payment(client):
    session=f"test-session-{uuid4()}"
    product=client.get("/api/v1/products").json()["items"][0]
    cart=client.post(f"/api/v1/cart/items?session_id={session}",json={"product_id":product["id"],"quantity":1})
    assert cart.status_code==200 and cart.json()["item_count"]==1
    key=f"test-checkout-{uuid4()}"
    r=client.post("/api/v1/checkout",headers={"Idempotency-Key":key},json={"session_id":session})
    assert r.status_code==200
    order=r.json()
    assert order["status"]=="pending_payment" and len(order["items"])==1
    again=client.post("/api/v1/checkout",headers={"Idempotency-Key":key},json={"session_id":session})
    assert again.json()["id"]==order["id"]
    paid=client.post(f"/api/v1/payments/{order['id']}/simulate-success")
    assert paid.json()["payment_status"]=="paid"
    assert "no duplicate action" in client.post(f"/api/v1/payments/{order['id']}/simulate-success").json()["message"]

def test_admin_key_required_and_product_creation(client):
    assert client.get("/api/v1/admin/summary").status_code==401
    r=client.post("/api/v1/admin/products",headers={"X-Admin-Key":"local-dev-admin-change-me"},json={
      "sku":f"TEST-{uuid4().hex[:10]}","name":"Test product","category":"Tests","price":"999.00","stock_quantity":5,"color":"#799d79"})
    assert r.status_code==201 and r.json()["stock_quantity"]==5
    layout=client.get("/api/v1/store-layout").json()
    assert any(any(p["product_id"]==r.json()["id"] for p in f["products"]) for f in layout["items"])
