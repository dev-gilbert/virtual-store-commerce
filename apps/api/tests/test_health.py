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
    r=client.post("/api/v1/checkout",headers={"Idempotency-Key":key},json={"session_id":session,"customer_phone":"+250788123456","customer_name":"Test Customer","delivery_address":"Kigali"})
    assert r.status_code==200
    order=r.json()
    assert order["status"]=="pending_payment" and len(order["items"])==1
    again=client.post("/api/v1/checkout",headers={"Idempotency-Key":key},json={"session_id":session,"customer_phone":"+250788123456","customer_name":"Test Customer","delivery_address":"Kigali"})
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

def test_cancelling_unpaid_order_releases_reserved_stock(client):
    session=f"cancel-session-{uuid4()}"
    product=client.get("/api/v1/products").json()["items"][0]
    original_stock=product["stock_quantity"]
    assert client.post(f"/api/v1/cart/items?session_id={session}",json={"product_id":product["id"],"quantity":1}).status_code==200
    order=client.post("/api/v1/checkout",headers={"Idempotency-Key":f"cancel-key-{uuid4()}"},
                      json={"session_id":session,"customer_phone":"+250788123456","customer_name":"Test Customer","delivery_address":"Kigali"}).json()
    after_reservation=client.get(f"/api/v1/products/{product['id']}").json()["stock_quantity"]
    assert after_reservation==original_stock-1
    cancelled=client.post(f"/api/v1/orders/{order['id']}/cancel")
    assert cancelled.status_code==200 and cancelled.json()["status"]=="cancelled"
    restored=client.get(f"/api/v1/products/{product['id']}").json()["stock_quantity"]
    assert restored==original_stock

def test_admin_can_create_drawer_and_manage_product_placements(client):
    headers={"X-Admin-Key":"local-dev-admin-change-me"}
    product=client.get("/api/v1/products").json()["items"][0]
    created=client.post("/api/v1/admin/fixtures",headers=headers,json={
      "code":f"DRAWER-{uuid4().hex[:8]}","name":"Test drawer","kind":"drawer","x":2,"y":0,"z":3})
    assert created.status_code==201
    fixture=created.json()
    placed=client.post(f"/api/v1/admin/fixtures/{fixture['id']}/items",headers=headers,json={
      "product_id":product["id"],"shelf_level":0,"slot":0})
    assert placed.status_code==201
    layout=client.get("/api/v1/store-layout").json()
    found=next(f for f in layout["items"] if f["id"]==fixture["id"])
    assert found["kind"]=="drawer" and found["products"][0]["product_id"]==product["id"]
    removed=client.delete(f"/api/v1/admin/fixtures/{fixture['id']}/items/{placed.json()['id']}",headers=headers)
    assert removed.status_code==200 and removed.json()["removed"] is True

def test_product_search_matches_sku_and_typo_tolerant_terms(client):
    exact=client.get("/api/v1/products",params={"q":"PAN-MIL-001"})
    typo=client.get("/api/v1/products",params={"q":"milkk"})
    assert exact.status_code==200
    assert any(p["sku"]=="PAN-MIL-001" for p in exact.json()["items"])
    assert typo.status_code==200
    assert any("milk" in p["name"].casefold() for p in typo.json()["items"])

def test_product_search_filters_price_stock_and_sorts(client):
    r=client.get("/api/v1/products",params={"min_price":"1000","max_price":"2000","in_stock":"true","sort":"price_asc","limit":100})
    assert r.status_code==200
    items=r.json()["items"]
    assert items
    assert all(1000 <= float(p["price"]) <= 2000 and p["stock_quantity"]>0 for p in items)
    assert [float(p["price"]) for p in items] == sorted(float(p["price"]) for p in items)

def test_product_search_rejects_invalid_price_range(client):
    r=client.get("/api/v1/products",params={"min_price":"3000","max_price":"1000"})
    assert r.status_code==422

def test_checkout_requires_phone_and_anonymous_checkout_can_skip_name_address(client):
    session=f"contact-session-{uuid4()}"
    product=client.get("/api/v1/products").json()["items"][0]
    client.post(f"/api/v1/cart/items?session_id={session}",json={"product_id":product["id"],"quantity":1})
    missing_phone=client.post("/api/v1/checkout",headers={"Idempotency-Key":f"missing-phone-{uuid4()}"},
      json={"session_id":session,"customer_name":"Guest","delivery_address":"Kigali"})
    assert missing_phone.status_code==422
    missing_address=client.post("/api/v1/checkout",headers={"Idempotency-Key":f"missing-address-{uuid4()}"},
      json={"session_id":session,"customer_phone":"+250788123456"})
    assert missing_address.status_code==422
    anonymous=client.post("/api/v1/checkout",headers={"Idempotency-Key":f"anonymous-{uuid4()}"},
      json={"session_id":session,"customer_phone":"+250788123456","is_anonymous":True})
    assert anonymous.status_code==200
    assert anonymous.json()["is_anonymous"] is True
    assert anonymous.json()["customer_phone"]=="+250788123456"
    assert anonymous.json()["customer_name"] is None

def test_orders_are_scoped_to_their_shopping_session(client):
    session=f"private-session-{uuid4()}"
    other=f"other-session-{uuid4()}"
    product=client.get("/api/v1/products").json()["items"][0]
    client.post(f"/api/v1/cart/items?session_id={session}",json={"product_id":product["id"],"quantity":1})
    order=client.post("/api/v1/checkout",headers={"Idempotency-Key":f"private-{uuid4()}"},
      json={"session_id":session,"customer_phone":"+250788123456","is_anonymous":True}).json()
    assert client.get(f"/api/v1/orders/{order['id']}",params={"session_id":session}).status_code==200
    assert client.get(f"/api/v1/orders/{order['id']}",params={"session_id":other}).status_code==404
