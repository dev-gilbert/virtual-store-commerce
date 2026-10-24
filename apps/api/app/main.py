
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Virtual Store Commerce API",
    version="0.1.0",
    description="Commerce API for an interactive 3D retail platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health", tags=["Operations"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "virtual-store-commerce-api",
    }


@app.get("/api/v1/products", tags=["Products"])
def list_products() -> dict:
    # Temporary response. Replace with database-backed catalogue queries.
    return {
        "items": [],
        "total": 0,
    }
