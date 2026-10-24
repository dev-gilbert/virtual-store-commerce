from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_service_status():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "virtual-store-commerce-api",
    }


def test_products_endpoint_starts_with_empty_collection():
    response = client.get("/api/v1/products")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}
