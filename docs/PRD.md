# Product Requirements Document

## Product vision

Virtual Store Commerce combines an interactive 3D supermarket with a conventional e-commerce storefront. Both experiences use the same product catalogue, pricing, inventory, cart, order, and payment services.

## Target users

- Shoppers who want to explore products spatially.
- Shoppers who prefer quick search and conventional checkout.
- Retailers and store managers who manage products, pricing, stock, store layout, and orders.
- Platform operators who onboard retailers and support the service.

## MVP scope

### Customer storefront
- Retailer-branded landing page.
- Searchable product catalogue with category filters and product detail pages.
- 3D supermarket with aisle navigation, selectable products, and interactive fixtures.
- Shared cart between conventional and 3D experiences.
- Checkout that validates prices and stock on the backend.

### 3D store
- Original modular store geometry and original/licensed assets.
- Camera navigation, clear interaction hints, and responsive layout.
- Shelves and fixture identifiers that map to backend records.
- Drawers and cabinets that reveal fixture-specific products.
- Progressive loading and graceful fallback to conventional product pages.

### Retailer operations
- Product and variant management.
- Store-level pricing and stock management.
- Layout editor or placement management.
- Order management and fulfillment states.
- Role-based access and audit history.

### Commerce integrity
- Transactional checkout and inventory reservations.
- Sandbox payment integration before live processing.
- Verified payment webhooks, idempotency, retries, and reconciliation.
- Tenant isolation between retailers.

## Non-functional requirements

- No authoritative prices, stock values, or payment states are trusted from the browser.
- The conventional storefront remains usable if 3D rendering fails.
- Sensitive credentials stay server-side.
- 3D assets are optimized and have clear licensing provenance.
- Automated tests cover API contracts, checkout, inventory concurrency, payment callbacks, and tenant isolation.
- Backup, recovery, logging, and monitoring are documented before a retailer pilot.

## Not in the first release

- Native smart-glasses application.
- Universal VR/AR compatibility.
- AI-generated reconstruction of full stores.
- Microservices or distributed event infrastructure before scale requires it.
- Live payment processing before sandbox flows and reconciliation are verified.

## Acceptance criteria

1. A user can enter the 3D store and interact with at least one fixture.
2. Products in the 3D scene resolve to stable backend product IDs.
3. A product can be added to the same cart from both shopping interfaces.
4. The API validates prices and stock during checkout.
5. Concurrent checkout attempts cannot oversell stock.
6. Duplicate payment callbacks cannot cause duplicate payment confirmation or fulfillment.
7. Retailer data is isolated by tenant and role.
8. A model-loading failure does not block conventional shopping.
9. The API tests, frontend lint, and production build pass in CI.

## Current status

The repository currently contains a landing page, an original procedural 3D scene with an interactive drawer, a virtual-store route, FastAPI health and placeholder product endpoints, API smoke tests, setup documentation, and a CI workflow. Database-backed products, shared cart, retailer management, and payments remain planned work.
