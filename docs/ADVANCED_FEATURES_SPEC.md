# Virtual Store Commerce: Product Requirements and AI Implementation Specification

**Repository:** `dev-gilbert/virtual-store-commerce`  
**Status:** Living specification  
**Audience:** Developers, coding agents, reviewers, and future maintainers  
**Purpose:** This document is the source of truth for feature intent, architectural constraints, acceptance criteria, and implementation order. Read it and inspect the repository before changing code.

## 1. Instructions for any AI coding agent

Before implementing a task:

1. Read this document and the repository's `README.md`, relevant application code, database models, migrations, API routes, tests, and package scripts.
2. Report what already exists, what is incomplete, and which files will change. Do not assume a feature is absent or complete from this document alone.
3. Follow the existing architecture unless a documented migration is necessary. Avoid replacing working systems with a new stack.
4. Treat the backend and database as authoritative for products, prices, stock, baskets, orders, promotions, payment state, permissions, and published store layouts. Never trust browser-calculated totals or client-supplied ownership.
5. Reuse the canonical product and inventory records in the 2D shop and 3D supermarket. Do not create separate shadow catalogues for each experience.
6. Make database changes through versioned migrations. Preserve existing data and provide safe defaults/backfills where needed.
7. Add or update automated tests for every behaviour changed. Test invalid input, permissions, empty states, failure paths, and concurrency-sensitive behaviour where applicable.
8. Run the relevant backend tests, frontend lint/type checks, and production builds. Fix failures caused by the change before declaring it complete.
9. Never claim that a feature is implemented, tested, secure, or production-ready unless repository evidence and test results support that claim. Clearly identify external services that remain mocked or unconfigured.
10. Keep credentials and secrets out of source control. Use environment variables and update `.env.example` with placeholders only.
11. Make changes incrementally, with focused commits and descriptive messages. Do not silently delete existing functionality or perform destructive data operations.
12. Update this document when a feature's scope, status, API contract, data model, or acceptance criteria materially changes.

### Required task completion report

For each implementation task, report:
- Feature(s) implemented and user-visible behaviour.
- Important files, API routes, and migrations changed.
- Tests and commands run, with actual pass/fail results.
- Configuration or manual setup still required.
- Known limitations and follow-up work.
- Commit SHA and CI result when pushed.

## 2. Product vision

Build a reliable commerce platform where customers can shop through a conventional 2D storefront or an interactive 3D supermarket. Both experiences must use the same catalogue, price rules, availability, basket, checkout, orders, and payment state. Store staff should be able to operate the business without editing source code. The platform may later support multiple supermarket businesses as a SaaS product.

The 3D environment must be useful, accessible, and optional. Customers must always have a functional 2D fallback. Backend correctness, privacy, security, performance, and operational reliability take priority over visual effects or AI features.

## 3. Architectural invariants

- **Canonical data:** One product identity and authoritative price/stock record per sellable item.
- **Server authority:** The server recalculates totals and validates stock, discounts, delivery fees, and order eligibility at checkout.
- **Transactional integrity:** Order placement and stock reservation must use database transactions and safe concurrency controls. Define reservation expiry and release behaviour.
- **Payment integrity:** A browser redirect or client request never proves payment. Verify provider-signed webhooks, use idempotency, persist provider references, and reconcile payment state.
- **Tenant isolation:** If multi-tenancy is introduced, every tenant-owned read and write must be scoped and authorization-tested. Never rely on a client-supplied tenant ID alone.
- **Authorization:** Enforce role and resource permissions on the backend, not only by hiding UI controls.
- **Auditability:** Record material changes to stock, prices, orders, refunds, permissions, and published layouts with actor, time, reason, and relevant before/after details while minimizing sensitive data.
- **Resilience:** External calls need timeouts, bounded retries, idempotency where applicable, and useful error states.
- **Accessibility:** Keyboard navigation, readable contrast, accessible labels, reduced-motion consideration, and a usable 2D alternative.
- **Performance:** Lazy-load the 3D experience, optimize textures/models, and provide a low-bandwidth/low-end-device mode.
- **Privacy:** Collect only necessary customer data, obtain consent for marketing reminders, and define retention and access policies.
- **Truthful status:** Distinguish planned, implemented, tested, sandboxed, and production-configured functionality.

## 4. Feature roadmap and functional requirements

Feature IDs are stable references for tickets, branches, commits, and AI prompts. “Planned” does not mean implemented. Current implementation status must be verified against code and tests before work begins.

### A. Advanced customer shopping experience

#### F01. Intelligent product search and discovery — High priority
**Requirements**
- Search product name, SKU, brand, category, description, and curated synonyms.
- Provide keyboard-accessible autocomplete while typing, with loading and empty states.
- Support typo tolerance without returning misleading results; use a documented matching/ranking strategy.
- Filter by price, availability, brand, category, ratings when real review data exists, and active promotions.
- Sort by relevance, price ascending/descending, popularity based on defined events, and newest arrivals.
- Show useful alternatives when no exact match exists.
- Record aggregate popular searches and zero-result searches while avoiding unnecessary personal data.
- Use the same search API/data and product identifiers in the 2D shop and 3D supermarket.
**Acceptance criteria**
- Search is case-insensitive and handles whitespace consistently.
- SKU/name/category matching is tested, including empty query and no-results cases.
- Filters and sort can be combined predictably and pagination does not duplicate or omit results.
- Selecting a result opens the canonical product detail and, where a published placement exists, can focus that item in 3D.
- Search telemetry is bounded, privacy-aware, and cannot break shopping if analytics storage fails.

#### F02. Rich product pages
**Requirements**
- Support multiple photos, image zoom, and optional video metadata.
- Show brand, size, unit, ingredients, allergens, nutrition information where applicable, and price per unit.
- Show variants, real stock state, estimated delivery where supported, and clear discontinued/out-of-stock states.
- Support verified ratings/reviews only when a review system exists.
- Show related products and frequently bought together only when backed by catalogue rules or measured data.
**Acceptance criteria**
- Both storefronts resolve the same canonical product record and display consistent price and availability.
- Missing optional information is omitted gracefully, not fabricated.
- Product images have accessible alternative text and resilient loading fallbacks.

#### F03. Persistent basket and smart checkout
**Requirements**
- Preserve a guest basket across refreshes; persist signed-in baskets server-side across devices.
- Add, remove, and update quantities; support favourites/saved items where account features exist.
- Revalidate price, promotion eligibility, quantity limits, and stock on every checkout attempt.
- Support configured coupons, loyalty points, delivery fees, minimum-order rules, and guest/account checkout.
- Show a clear order confirmation and downloadable receipt when order creation succeeds.
- Send abandoned-basket reminders only with valid consent and configured notification services.
**Acceptance criteria**
- 2D and 3D share the same basket identity and server-side rules.
- The final order total is recalculated server-side; stale or tampered client totals are ignored.
- Duplicate submission/retry cannot create duplicate orders or double-reserve stock.
- Errors explain which items need attention and preserve the rest of the basket.

#### F04. Delivery, pickup, and order tracking
**Requirements**
- Save multiple customer addresses with appropriate access controls.
- Configure delivery windows, pickup options, delivery zones, fees, and order cut-off rules.
- Support explicit order states: placed, confirmed, picking, packed, dispatched, delivered, cancelled, and failed delivery as appropriate.
- Notify customers of state changes through configured channels.
- Permit cancellation/change requests only within configured state/time limits.
- Record proof of delivery and failed-delivery outcomes where applicable.
**Acceptance criteria**
- Customers see actual persisted order status and only a grounded delivery estimate.
- Staff transitions are authorized and validated against an explicit state machine.
- Notifications are retried safely and do not duplicate state transitions.

#### F05. Customer accounts, favourites, and repeat orders
**Requirements**
- Secure sign-in, sign-out, password recovery, session management, and optional MFA.
- Wishlist and saved shopping lists; reorder from past orders.
- Optional household/shared lists with explicit membership and access controls.
- Preferred substitutions, delivery instructions, order history, invoices, and support requests.
**Acceptance criteria**
- One customer cannot read or change another customer's account, address, list, or order.
- Reorder adds currently valid products and revalidates current prices and stock instead of copying old totals.

### B. Advanced 3D virtual supermarket

#### F06. Realistic, navigable 3D supermarket
- Keyboard, mouse, and touch controls for movement, rotation, pan, and zoom.
- Clear aisles, shelves, refrigerators/freezers, checkout counters, and signage.
- Product models/textures fit fixture slots and dimensions.
- Collision boundaries prevent moving through fixtures.
- Level-of-detail, compressed/optimized assets, lazy loading, and performance budgets.
- Simplified mode for lower-end devices and bandwidth; always provide 2D fallback.
**Acceptance:** Controls are discoverable, work on supported input types, respect collision rules, and do not trap keyboard focus.

#### F07. Search-to-shelf navigation
- Search from inside 3D; focus the actual placed product's aisle/fixture/slot.
- Animate the camera, highlight the exact item, and show a product card with price, availability, and add-to-basket.
- Show a route/floor marker when useful.
- Offer catalogue alternatives if unavailable.
**Acceptance:** Camera target and highlight come from the published placement record, never a guessed location. Unplaced products receive a clear result with a 2D detail link.

#### F08. Direct 3D product interaction
- Product meshes have distinct, reliable selectable hit areas.
- Labels/overlays must not intercept clicks intended for products or neighbouring objects.
- Selection opens a focused detail panel; support quantity, basket, wishlist, and comparison as those features become available.
- Use restrained feedback animation that does not block nearby items.
**Acceptance:** Clicking a visible item resolves the correct product ID and is covered by interaction/regression tests where practical.

#### F09. Interactive store map and shopping route
- Mini-map with customer position and aisle locations.
- Plan a route through multiple shopping-list items; highlight next stop and collected items.
- Aisle directory, category shortcuts, entrance/home action.
**Acceptance:** Routes use published store geometry and product placements. If route data is incomplete, show a safe fallback instead of fabricating directions.

#### F10. Professional visual store builder
- Drag shelves, fridges, drawers, tables/displays, and checkout counters onto a floor plan.
- Assign products to fixture slots and shelf levels.
- Configure dimensions, rotation, aisle spacing, and capacity.
- Preview the real 3D result before publishing.
- Save drafts, create versions, preview changes, publish, and roll back.
- Validate overlapping fixtures, duplicate/conflicting placements, blocked aisles, out-of-bounds positions, and capacity.
**Acceptance:** Draft layouts are not customer-visible. Only a validated published version is served to shoppers. Publish/rollback operations are permission-protected and audited.

#### F11. Live inventory in the virtual store
- Display in-stock, low-stock, and unavailable states; update labels/prices/promotions from canonical data.
- Prevent unavailable items being newly added to a basket; revalidate existing basket items at checkout.
- Reserve stock at the defined order/payment stage and release expired/failed reservations.
- Refresh availability after admin stock changes.
**Acceptance:** The 3D scene cannot independently set price or availability. Concurrent checkout tests demonstrate no overselling beyond the explicitly documented stock policy.

### C. Store management and business operations

#### F12. Inventory management
- Stock adjustments and movement ledger, supplier receipts, damaged/expired goods, expiry dates, thresholds, reservations, and reconciliation.
- Every material adjustment records actor, timestamp, reason, and reference.
- Define whether stock is tracked per store/branch and per unit.

#### F13. Order management
- Search/filter orders, inspect lines and status history, confirm verified payment, assign pickers, process substitutions, cancellation/refunds, and fulfilment events.
- Enforce allowed state transitions and role permissions.

#### F14. Product import and bulk editing
- CSV/spreadsheet import, schema validation, SKU generation, duplicate detection, dry-run preview, row-level errors, safe commit, and export.
- Large imports run as background jobs with progress and downloadable error reports.

#### F15. Promotions and pricing rules
- Scheduled percentage/fixed discounts, bundles, quantity pricing, coupon codes, customer-specific offers, limits, and usage tracking.
- Define stacking, timezone, rounding, eligibility, and refund behaviour explicitly.

#### F16. Supplier management
- Supplier profiles, purchase orders, expected deliveries, cost prices, lead times, performance, and receiving workflows.

#### F17. Multi-store management
- Branches, branch-specific stock/prices, shared or branch-specific catalogues, fulfilment routing, and consolidated reports.

#### F18. Staff accounts and permissions
- Owner, store manager, cashier, inventory manager, picker, delivery staff, support, and other least-privilege roles.
- Backend-enforced permissions and audit logs for privileged actions.

#### F19. Returns and refunds
- Return requests, reason codes, evidence, approval limits, restocking rules, refund status, and audit trail.
- Refunds must reconcile with the payment provider and original transaction.

#### F20. Receipts and invoicing
- Receipts, tax breakdowns, invoice numbering, customer/business details, downloadable PDFs, and configurable business identity.
- Tax rules must be confirmed for target jurisdictions; do not invent legal treatment.

### D. AI and automation

#### F21. Voice and multilingual shopping
- English and Kinyarwanda speech/text input; extract product, variant, and quantity intents against the real catalogue.
- Ask clarification for ambiguous matches and show a reviewable list before basket changes.
- Speech/translation errors must never silently place an order or charge a customer.

#### F22. Shopping assistant
- Meal ingredients, budget-aware lists, and alternatives using only catalogue-backed products/prices.
- Respect stated allergy/dietary constraints; distinguish verified product facts from suggestions.
- Ask permission before editing a basket; do not make unsupported medical/nutrition assurances.

#### F23. Demand forecasting and replenishment
- Use sales history, seasonality, lead times, and stock data to recommend demand/quantities.
- Explain input data and uncertainty; start advisory-only.
- Managers approve purchase orders; evaluate forecasts against outcomes before considering automation.

#### F24. AI-assisted business insights
- Surface sales anomalies, product combinations, search failures, abandonment, and stock anomalies.
- Explain source metrics and time periods. Label estimates and avoid presenting correlation as causation.

### E. Payments, security, and reliability

#### F25. Real payment integrations
- Provider adapter pattern for selected mobile-money/card providers.
- Signed webhook verification, idempotency, durable transaction records, provider references, reconciliation, and pending/success/failed/refunded states.
- Separate sandbox and production credentials; never store raw card details.
**Acceptance:** Only verified provider evidence can confirm payment. Webhook replays and duplicate/out-of-order events do not double-charge or corrupt order state.

#### F26. Account security and fraud prevention
- Secure sessions, password recovery, optional MFA, rate limiting, backend authorization, audit logs, suspicious-login signals, and cross-customer access protection.
- Apply configurable limits and additional checks to high-risk actions.

#### F27. Production monitoring and recovery
- Centralized structured logs, error tracking, health checks, queue monitoring, backups, tested restores, alerts, and deployment rollback.
- Measure checkout failures, webhook delays, stock conflicts, API latency, and 3D performance.

#### F28. Tax, privacy, and auditability
- Configurable tax rules, transparent totals, retention policy, marketing consent, controlled customer-data access, and exportable audit records.
- Validate legal/tax requirements with qualified local expertise.

### F. Platform owner and commercial features

#### F29. Multi-tenant SaaS
- Tenant isolation for customers, catalogues, staff, orders, inventory, settings, and store layouts.
- Tenant-scoped authorization tests, safe onboarding, and explicit data ownership.

#### F30. Subscription and billing
- Plans, trials, usage limits, subscription lifecycle, invoices, and software-service payment collection.

#### F31. Platform-owner console
- Tenant onboarding, subscription status, platform health, support requests, feature flags, and audit events.
- Support access must be controlled, justified, time-bounded where appropriate, and audited; avoid casual tenant-data exposure.

#### F32. Integrations and APIs
- Documented, versioned, authenticated APIs and adapters for accounting, delivery, inventory, messaging, payments, and POS systems.

#### F33. Webhooks and background jobs
- Reliable order events, notifications, imports, and retryable jobs.
- Idempotent consumers, bounded retries, dead-letter/failed-job visibility, and operational controls.

#### F34. Analytics and conversion tracking
- Search success, product views, add-to-basket rate, checkout conversion, average order value, delivery performance, and 2D-vs-3D behaviour.
- Document event definitions and avoid collecting unnecessary personal data.

#### F35. PWA and notifications
- Installable mobile experience, fast repeat visits, optional push notifications, and resilient temporary-offline behaviour.
- Clearly indicate when a cart or order action has not reached the server.

## 5. Recommended implementation order

Build thin, tested end-to-end slices. Do not attempt all 35 features in one change.

### Phase 0: Baseline and contracts
- Inspect current repository and record verified existing behaviour.
- Confirm local development setup, API schemas, database migrations, and CI.
- Add or repair tests before extending fragile areas.
- Document API contracts and authoritative data ownership.

### Phase 1: Customer shopping foundation
1. **F01 Search and discovery:** shared backend search contract, matching, filters/sort, accessible autocomplete, and 2D/3D parity.
2. **F02 Product detail:** canonical detail endpoint/model, multiple image support, key product facts, real availability, and out-of-stock states.
3. **F03 Basket/checkout:** server-authoritative basket and totals, quantity updates, stock/price validation, duplicate-submit protection, and clear order confirmation.
4. **F11 Inventory parity:** make stock and prices consistent across shop, 3D labels, basket, and checkout.
5. **F04 Basic order status:** persisted status history and a usable customer order result before adding complex delivery logistics.
6. **F05 Account persistence:** only after secure account/session behaviour and tenant/customer isolation are tested.

### Phase 2: 3D usability and store operations
- F07 search-to-shelf, F08 reliable product selection, F06 navigation/performance, F09 routes, F10 draft/version/publish lifecycle.
- F12 inventory ledger, F13 order operations, F14 imports, F18 permissions, then promotions/suppliers/returns/invoices as dependencies mature.

### Phase 3: Security, payments, and reliability
- F25 provider sandbox integration then production integration after provider selection and credentials.
- F26 security hardening, F27 observability/recovery, F28 validated tax/privacy requirements.

### Phase 4: Business scale and intelligent assistance
- F17 multi-store, F29 multi-tenant design before onboarding multiple businesses, F30/F31 SaaS operations, F32/F33 integrations and jobs, F34 analytics, F35 PWA, then F21-F24 AI features based on real data and clear user consent.

## 6. API and data contract expectations

Exact route names must be discovered from the repository and documented before use. Do not invent routes, models, fields, migrations, or environment variables. For each new endpoint specify:
- Method/path and purpose.
- Request/response schemas with examples.
- Authentication and required permission.
- Validation and error responses.
- Pagination/filter/sort semantics where relevant.
- Transaction, idempotency, and concurrency behaviour.
- Data migration and backward compatibility.
- Tests for success, invalid data, unauthorized access, and failure cases.

Prefer explicit domain concepts such as Product, ProductImage, Category, Brand, InventoryBalance/Movement, Basket/BasketItem, Order/OrderItem, PaymentTransaction, Promotion, Store, Fixture, ProductPlacement, and StoreLayoutVersion. Reuse existing models where they already serve the same purpose; do not duplicate them solely to match these suggested names.

## 7. Definition of done

A feature is not done merely because a screen renders. It is done when:
- The intended customer/staff workflow works end to end.
- Server-side validation and authorization are enforced.
- Data remains consistent across 2D and 3D views.
- Empty, loading, error, unavailable, and retry states are handled.
- Automated tests cover important business rules and regressions.
- Database changes are migrated and safe for existing data.
- Lint, type checks, backend tests, and production build pass, or any pre-existing failure is clearly isolated and reported.
- Documentation and environment examples are updated.
- No secret, fake payment confirmation, invented stock, or unverified production claim is introduced.

## 8. First 10 implementation slices and verified status

The following ten feature IDs are the first delivery set. The status below describes only the working core slice that is present in the repository, not every advanced requirement listed under that feature. Any unimplemented acceptance criteria remain open work. This distinction prevents an AI agent from mistaking a starter implementation for a production-complete feature.

| # | Feature ID | Implemented core slice | Verification / remaining scope |
|---:|---|---|---|
| 1 | F01 Intelligent search and discovery | API supports query matching across name, SKU, category and description; basic synonyms/typo tolerance; category, price and stock filters; sorting and pagination. | API tests cover SKU/typo matching, price/stock filtering, sorting, and invalid price ranges. Brand/ratings/promotions filters, autocomplete, search analytics, and full 2D/3D API parity still need implementation. |
| 2 | F03 Persistent basket and smart checkout | Shared server-side guest basket keyed by session, add/remove items, server-calculated subtotal, stock checks, idempotent checkout, stock reservation, and sandbox payment simulation. | CI tests cover checkout idempotency and sandbox payment. Cross-device signed-in baskets, quantity editing, coupons, delivery/tax totals, downloadable receipts, and consent-based reminders remain open. |
| 3 | F06 Navigable 3D supermarket | Interactive Three.js/React Three Fiber scene with OrbitControls, fixture types, product textures, and 2D fallback route. | This is an orbit/inspect experience, not a complete walk-through simulator. Keyboard/touch movement, collision boundaries, low-end mode, and performance budgets remain open. |
| 4 | F07 Search-to-shelf navigation | 3D search can match catalogue products, highlight a placed product, pulse its mesh, and show product selection details. | Existing 3D placement data supplies the target. Camera auto-navigation, aisle route/map, and alternative-product recommendations remain open. |
| 5 | F08 Direct 3D product interaction | Clickable product meshes open the corresponding product details and allow adding to the shared basket; selected item is highlighted. | Manual interaction exists. Automated browser interaction tests and dense-shelf hit-target/accessibility hardening remain open. |
| 6 | F10 Visual store builder | Admin can create supported fixture types, place/remove products at shelf levels/slots, and adjust basic fixture positions in the builder workflow. | Persistent versioned drafts, validated publish/rollback, true 3D draft preview, fixture dimensions/capacity, and aisle/overlap validation remain open. Do not describe this as a complete production layout publisher. |
| 7 | F11 Live inventory in the virtual store | Canonical product stock and prices are returned in catalogue/layout APIs; out-of-stock items cannot be added; checkout validates stock and reserves it. | Basic reservation/release behaviour has tests for unpaid order cancellation. Reservation expiry, multi-warehouse inventory, and concurrency/load tests remain open. |
| 8 | F12 Inventory management | Admin can increment/decrement product stock through a backend PATCH route and see updated stock in the catalogue. | This is basic stock adjustment only. Stock movement ledger, reason codes, supplier receipts, expiry/damage handling, reconciliation, and reservation reporting remain open. |
| 9 | F13 Order management | API creates and retrieves orders, lists orders by guest session, supports cancellation of unpaid orders, and exposes basic admin order counts/status summaries. | A full staff order workbench, picking assignment, substitution workflow, verified real payment handling, refunds, and full fulfilment state machine remain open. |
| 10 | F27 Production monitoring and recovery | A health endpoint reports API service status and the CI pipeline runs API tests, migration checks, frontend lint, and production build. | This is a baseline only. Centralized logs, alerting, queue/database monitoring, backup/restore drills, error tracking, and rollback automation remain open. |

### Completion rule for this delivery set

These ten items are marked **core slice implemented**, not **feature fully complete**. A feature may be marked fully implemented only when its full requirements and acceptance criteria above are satisfied and verified by tests. Keep remaining scope visible in follow-up tasks.

## 9. Current status tracker


Use this tracker as a planning aid, not proof of implementation. Update each status only after inspecting code and tests.

| ID | Feature | Priority | Status |
|---|---|---:|---|
| F01 | Intelligent search and discovery | P0 | Core slice implemented; autocomplete and advanced filters remain |
| F02 | Rich product pages | P0 | Planned; basic product detail API exists, rich product page not complete |
| F03 | Persistent basket and checkout | P0 | Core slice implemented; account persistence and advanced checkout rules remain |
| F04 | Delivery/pickup/order tracking | P1 | Planned |
| F05 | Accounts/favourites/repeat orders | P1 | Planned |
| F06 | Navigable 3D supermarket | P1 | Core slice implemented; full walk-through and optimization remain |
| F07 | Search-to-shelf | P0 | Core slice implemented; camera navigation and route map remain |
| F08 | Direct 3D interaction | P0 | Core slice implemented; automated interaction coverage remains |
| F09 | Store map and shopping route | P2 | Planned |
| F10 | Visual store builder | P1 | Core slice implemented; versioned publishing and validation remain |
| F11 | Live inventory in 3D | P0 | Core slice implemented; expiry-based reservations and concurrency hardening remain |
| F12 | Inventory management | P1 | Basic stock adjustment implemented; movement ledger and receiving remain |
| F13 | Order management | P1 | Basic order API/admin summary implemented; staff fulfilment workbench remains |
| F14-F20 | Remaining store operations | P1-P2 | Planned or partial; inspect implementation per feature |
| F21-F24 | AI and automation | P3 | Planned |
| F25-F26 | Real payments and account security | P0-P1 | Sandbox payments only; production provider and security work remain |
| F27 | Monitoring and recovery | P1 | Health endpoint and CI baseline implemented; production observability remains |
| F28 | Tax, privacy, and auditability | P1 | Basic audit events exist; full policies and tax configuration remain |
| F29-F35 | SaaS, integrations, analytics, PWA | P2-P3 | Planned or partial; inspect implementation per feature |

## 10. First implementation task template

Use this template when assigning work to an AI coding agent:

> Read `docs/ADVANCED_FEATURES_SPEC.md` and inspect the current repository before editing. Implement only the requested feature IDs: **[IDs]**. First report existing implementation, gaps, relevant files/routes/models, and a small implementation plan. Preserve the current stack and existing functionality. Treat the backend as authoritative and share canonical records across the 2D shop and 3D supermarket. Add migrations if needed, automated tests for success and failure paths, and update documentation. Run relevant tests, lint/type checks, and production builds. Fix regressions introduced by your changes. Do not invent APIs or claim checks passed unless you ran them. Commit with a descriptive message and report changed files, test results, CI status, limitations, and exact setup steps.
