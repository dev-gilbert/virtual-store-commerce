# Virtual Store Commerce

An original, web-first 3D retail experience combining an interactive virtual supermarket with a conventional e-commerce storefront. The long-term product goal is to support retailers with shared product, inventory, cart, order, and payment infrastructure.

## Current status

The repository is in the foundation/prototype stage. The frontend contains a Next.js storefront scaffold and an original procedural 3D scene. The FastAPI service currently exposes a health endpoint and a placeholder products endpoint. Product data is not database-backed yet, and checkout/payment processing is not implemented.

## Stack

- Frontend: Next.js, React, TypeScript
- 3D: Three.js, React Three Fiber, Drei
- Backend: Python, FastAPI
- Planned data layer: PostgreSQL, SQLAlchemy, Alembic
- Tests: Pytest, Playwright (planned for frontend end-to-end coverage)

## Run the API on Windows PowerShell

From the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install "fastapi[standard]" httpx pytest
$env:PYTHONPATH = "apps/api"
uvicorn app.main:app --app-dir apps/api --reload --port 8000
```

In another terminal, run the API smoke tests:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "apps/api"
pytest apps/api/tests -q
```

API documentation is available at `http://localhost:8000/docs`.

## Run the frontend

```powershell
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000` for the storefront and `http://localhost:3000/virtual-store` for the 3D prototype.

## Product principles

1. One store, two shopping experiences, one source of truth.
2. The backend is authoritative for pricing, stock, orders, and payment state.
3. The conventional shopping experience must remain usable when 3D rendering is unavailable.
4. Store layouts and product placements are separate from product identity and inventory.
5. Use original or properly licensed assets; do not copy third-party demo assets.

## Roadmap

1. Establish API tests and interactive 3D prototype.
2. Add PostgreSQL models and migrations for stores, products, fixtures, and placements.
3. Connect the conventional catalogue and 3D product selection to the same API.
4. Implement cart, inventory reservations, orders, and payment sandbox integration.
5. Build retailer administration, tenant isolation, observability, and pilot deployment.
