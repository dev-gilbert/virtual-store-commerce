import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

from uuid import uuid4


def test_checkout_applies_coupon_limit_and_pickup_pricing(client):
    product = client.get("/api/v1/products").json()["items"][0]
    code = "LIMIT" + uuid4().hex[:8].upper()
    admin_headers = {"X-Admin-Key": "local-dev-admin-change-me"}
    promotion = client.post("/api/v1/admin/promotions", headers=admin_headers, json={
        "code": code,
        "discount_percent": 10,
        "min_subtotal": 0,
        "usage_limit": 1,
    })
    assert promotion.status_code == 200, promotion.text

    session = "coupon-session-" + uuid4().hex
    assert client.post(f"/api/v1/cart/items?session_id={session}", json={
        "product_id": product["id"], "quantity": 1,
    }).status_code == 200
    checkout = client.post("/api/v1/checkout", headers={"Idempotency-Key": "coupon-" + uuid4().hex}, json={
        "session_id": session,
        "customer_name": "Coupon Customer",
        "customer_phone": "+250788123456",
        "delivery_address": "Kigali",
        "coupon_code": code,
        "delivery_method": "pickup",
    })
    assert checkout.status_code == 200, checkout.text
    order = checkout.json()
    assert float(order["discount_amount"]) == round(float(order["subtotal"]) * 0.1, 2)
    assert float(order["delivery_fee"]) == 0
    assert float(order["total"]) == float(order["subtotal"]) - float(order["discount_amount"])

    second_session = "coupon-session-" + uuid4().hex
    assert client.post(f"/api/v1/cart/items?session_id={second_session}", json={
        "product_id": product["id"], "quantity": 1,
    }).status_code == 200
    limited = client.post("/api/v1/checkout", headers={"Idempotency-Key": "coupon-" + uuid4().hex}, json={
        "session_id": second_session,
        "customer_name": "Second Coupon Customer",
        "customer_phone": "+250788123457",
        "delivery_address": "Kigali",
        "coupon_code": code,
        "delivery_method": "pickup",
    })
    assert limited.status_code == 422
