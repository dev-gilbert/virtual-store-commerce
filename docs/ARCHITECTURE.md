# Architecture

## Guiding principle

One store, two shopping experiences, one source of truth. The conventional storefront and the 3D scene are separate clients of the same commerce APIs.

## Current implementation

- `apps/web`: Next.js storefront and client-side 3D scene.
- `apps/api`: FastAPI service with health and placeholder product endpoints.
- `apps/api/tests`: API smoke tests.

## Target architecture

- Web clients: conventional catalogue, 3D supermarket, retailer dashboard.
- API: modular FastAPI application with catalogue, store layout, inventory, cart, orders, and payments domains.
- PostgreSQL: authoritative data store for tenant, product, stock, layout, cart, order, and payment records.
- Redis: optional cache and rate-limit support when justified.
- Object storage: product images, 3D models, and textures.
- Payment adapter: sandbox provider integration first, with server-verified callbacks and reconciliation.

## Domain boundaries

Product identity and inventory are independent of store placement. A product may move between fixtures without changing its SKU or historical order items. A fixture has a stable identifier and a placement links a product variant to a fixture and layout version.

The browser never determines authoritative price, inventory, payment state, or final order total. Those are validated by the API and database.

## Planned delivery order

1. API smoke tests and interactive 3D prototype.
2. PostgreSQL connection, SQLAlchemy models, Alembic migrations, and seeded development data.
3. Product and store-layout APIs; connect both storefront modes to the same product IDs.
4. Cart, transactional checkout, inventory reservations, and payment sandbox.
5. Tenant isolation, retailer dashboard, audit events, and operational monitoring.
6. Performance optimization, accessibility checks, security review, and controlled retailer pilot.

## 3D asset policy

Use original procedural geometry, original Blender models, or assets with verified commercial licenses. Keep editable source assets organized separately from optimized runtime exports. Treat 3D rendering as optional: failures in model loading must not block conventional product discovery or checkout.
