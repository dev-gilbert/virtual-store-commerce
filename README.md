# Virtual Store Commerce

**One store, two shopping experiences, one source of truth.** An original, web-first supermarket with a conventional catalogue and an interactive 3D store backed by the same products, prices, stock, guest basket, orders, and local payment sandbox.

## Current implementation

- Next.js + React + TypeScript storefront and original procedural Three.js / React Three Fiber supermarket.
- FastAPI API with SQLAlchemy data models for products, fixtures, product placements, guest carts, orders, order items, and audit events.
- Reproducible seed catalogue and 3D shelf layout.
- Searchable/filterable conventional catalogue and guest basket shared with 3D shopping.
- Server-side price calculation, stock checks, idempotency-key checkout, stock reservation/release on cancellation, and simulated payment confirmation.
- Development retailer dashboard for product creation, stock changes, summary metrics, and audit events.
- Retailers can create drawers, shelves, tables, and display stands, choose their 3D positions, place catalogue products into levels/slots, and remove placements without changing stock.
- A conventional 2D catalogue remains available alongside the immersive 3D shop; both use the same guest basket and backend inventory.
- Pytest API coverage and Alembic schema migration.
- SQLite by default for a simple first run. PostgreSQL can be selected using `DATABASE_URL`.

**Important:** payment is a local sandbox simulation only. The development admin key is not production authentication. Do not expose this prototype to public customers or process real payments until authentication, tenant isolation, payment-provider verification, concurrency testing, and security review are complete.

## 1. Run the API (Windows PowerShell)

From the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r apps/api/requirements.txt
$env:PYTHONPATH = "apps/api"
$env:ADMIN_API_KEY = "local-dev-admin-change-me"
uvicorn app.main:app --app-dir apps/api --reload --port 8000
```

The first start creates the local SQLite database and seeds the sample catalogue. Keep this terminal running. API docs: [http://localhost:8000/docs](http://localhost:8000/docs).

In a second PowerShell terminal, from the repository root, run the tests:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "apps/api"
pytest apps/api/tests -q
```

To apply the initial schema migration before starting the API, use a fresh database and run:

```powershell
$env:PYTHONPATH = "apps/api"
alembic -c apps/api/alembic.ini upgrade head
```

The API also creates missing tables on startup for local convenience. Alembic should be used to manage schema changes going forward.

## 2. Run the frontend

Open a third PowerShell terminal:

```powershell
cd apps/web
npm ci
npm run dev
```

Open these routes:

- [http://localhost:3000](http://localhost:3000): product landing page.
- [http://localhost:3000/shop](http://localhost:3000/shop): conventional catalogue, shared guest basket, checkout and simulated payment.
- [http://localhost:3000/virtual-store](http://localhost:3000/virtual-store): interactive 3D supermarket. Drag to orbit, scroll to zoom, click a product to inspect and add it.
- [http://localhost:3000/admin](http://localhost:3000/admin): development retailer dashboard. Enter the configured `ADMIN_API_KEY` (default above).

Frontend API URL defaults to `http://localhost:8000`. To change it, set `NEXT_PUBLIC_API_BASE_URL` before starting Next.js.

## 3. Quick end-to-end smoke test

1. Start the API and frontend.
2. Open `/shop`, add a product to the basket, and note the subtotal.
3. Open `/virtual-store` in the same browser. Select a visible shelf product and add it. The basket is stored by the API under the same browser guest session.
4. Return to `/shop`, check the updated basket, then click **Checkout in sandbox**.
5. Click **Simulate successful payment**. The API confirms the order and records audit events.
6. Open `/admin`, enter the development key, and verify the summary, stock changes, product creation, and audit trail. New products are placed into the 3D store layout.

## API overview

- `GET /health`
- `GET /api/v1/products?q=&category=`
- `GET /api/v1/categories`
- `GET /api/v1/store-layout`
- `GET /api/v1/cart?session_id=...`
- `POST /api/v1/cart/items?session_id=...`
- `DELETE /api/v1/cart/items/{product_id}?session_id=...`
- `POST /api/v1/checkout` with an `Idempotency-Key` header
- `GET /api/v1/orders?session_id=...`
- `POST /api/v1/payments/{order_id}/simulate-success`
- `POST /api/v1/orders/{order_id}/cancel`
- Development-only admin endpoints under `/api/v1/admin`
- `POST /api/v1/admin/fixtures`
- `POST /api/v1/admin/fixtures/{fixture_id}/items`
- `DELETE /api/v1/admin/fixtures/{fixture_id}/items/{placement_id}`

## Product principles

1. The backend is authoritative for price, inventory, orders, and payment state.
2. Both shopping experiences use the same product IDs and guest session.
3. 3D rendering is a discovery layer, never the authority for stock or totals.
4. Product identity is separate from fixture placement.
5. Use original or properly licensed assets.
6. Never store real card data in this application; integrate a payment provider through a server-side adapter when ready.

## Next before a production pilot

Implement real retailer identity and tenant-scoped access; database-level concurrency guarantees and automated race tests; expiring stock reservations; verified payment webhooks and reconciliation; delivery/tax rules; accessible keyboard-first 3D fallback; monitoring, backups, deployment and threat modelling. The current admin key and sandbox payment action are explicitly development-only.
