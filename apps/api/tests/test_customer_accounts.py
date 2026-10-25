from fastapi.testclient import TestClient
from app.main import app


def test_customer_accounts_addresses_and_shared_lists():
    with TestClient(app) as client:
        registered = client.post("/api/v1/customer/register", json={
            "name": "Customer Test",
            "email": "customer-test-flow@example.com",
            "password": "correct-horse-battery-7",
        })
        assert registered.status_code == 200, registered.text
        token = registered.json()["token"]
        assert registered.json()["account"]["role"] == "customer"
        headers = {"Authorization": f"Bearer {token}"}

        saved = client.post("/api/v1/customer/addresses", headers=headers, json={
            "label": "Home",
            "recipient_name": "Customer Test",
            "phone": "+250788123456",
            "address": "Kigali, Rwanda",
            "is_default": True,
        })
        assert saved.status_code == 200, saved.text
        listed = client.get("/api/v1/customer/addresses", headers=headers)
        assert listed.status_code == 200 and listed.json()["total"] == 1

        shopping_list = client.post("/api/v1/customer/shopping-lists", headers=headers, json={"name": "Weekly groceries"})
        assert shopping_list.status_code == 200, shopping_list.text
        shared = client.get(
            "/api/v1/customer/shared-lists/" + shopping_list.json()["share_code"],
            headers=headers,
        )
        assert shared.status_code == 200 and shared.json()["name"] == "Weekly groceries"

        support = client.post("/api/v1/customer/support-requests", headers=headers, json={
            "subject": "Delivery question",
            "message": "Please let me know when delivery is expected.",
        })
        assert support.status_code == 200, support.text
        assert client.get("/api/v1/customer/support-requests", headers=headers).json()["total"] == 1
