# Agri-Smart Ecosystem — Gemini Historical Context & Architectural Decisions

## 1. Context Summary
The Agri-Smart Ecosystem was previously conceptualized, designed, and developed collaboratively with Google Gemini.
Key architectural milestones achieved during previous design phases include:
1. **Domain Modeling:** Comprehensive multi-stakeholder model (Super Admin, Farmer, Trader, Driver, Worker) with dedicated profile extensions (`farmer_profiles`, `trader_profiles`, `driver_profiles`, `worker_profiles`).
2. **Security & Cryptography:** Zero plain-text passwords (Argon2id), asymmetric RS256 JWT tokens with automatic rotation and HttpOnly cookie security.
3. **Sequential Code Standard:** Enforcing system-generated sequential identifiers for core assets:
   - Farms: `FARM-XXXXXX`
   - Crops: `CROP-XXXXXX`
   - Inputs: `INP-XXXXXX`
   - Suppliers: `SUP-XXXXXX`
   - Procurements: `REQ-XXXXXX`
4. **Soft-Deletion Governance:** Never physically drop business records upon standard user actions; maintain full auditability via `is_deleted`, `deleted_at`, and `deleted_by` with a centralized Super Admin Trash Vault.
5. **Cultivation Process Engine:** Transition from static stages to dynamic, crop-specific process stage templates stored in `crop_cultivation_stages` with rich agronomic JSON metadata (recommended activities, recommended inputs, theme colors, visual assets).

---

## 2. Invariants & Rules — What MUST NOT Be Changed
* **Authentication Architecture:** Do NOT replace RS256 JWT with symmetric HS256 or basic auth. Do NOT remove HttpOnly refresh cookie rotation.
* **Layered Architecture:** Do NOT put raw SQL or business logic inside FastAPI route handlers. Preserve `Router -> Service -> Repository -> Model` separation.
* **Database Migration Integrity:** Do NOT edit existing Alembic migrations `0001` through `0007`. Any future schema updates must be created as new sequential migrations (e.g. `0008`).
* **Soft Delete Principle:** Do NOT introduce hard DELETE queries in standard application flows. Preserve `is_deleted` filtering in repositories.
* **No Mock Data:** Do NOT introduce mock arrays, fake delays, or hardcoded dummy records in place of real database transactions.

---

## 3. Scope of Permitted & Planned Evolutions
* **Supplier & Input API Layer:** Completing the backend REST endpoints and services for `input_masters`, `suppliers`, and `procurement_requests` to match the existing frontend services and database schema (`0006`).
* **PostgreSQL Parity Migration for Cultivations:** Creating Alembic migration `0008` for `cultivation_runs`, `cultivation_stages`, `stage_worker_logs`, and `stage_expenses` to ensure 100% parity across PostgreSQL Docker and in-memory test environments.
* **Multi-Language Expansion:** Enhancing agronomic descriptions with local Tamil / regional language terminology.
* **Marketplace & Logistics (Stage 2):** Trader bidding on harvested lots and Driver GPS transit tracking.
