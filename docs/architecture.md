# Agri-Smart Ecosystem — Architecture & Technical Design

## 1. High-Level System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        Next.js Frontend (App Router)                   │
│         React 19, TypeScript, Tailwind CSS, Lucide Icons, Three.js      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTPS / JSON REST API (/api/v1)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Application Server                     │
│         Python 3.12+, Uvicorn, Pydantic v2, RS256 JWT, Argon2id        │
├───────────────────────────────────┬────────────────────────────────────┤
│ Routers:                          │ Services:                          │
│  - /auth                          │  - AuthService                     │
│  - /admin/users, /admin/crops     │  - AdminUserService, CropService   │
│  - /farms, /farm-crop-plans       │  - FarmService, CropPlanService    │
│  - /cultivations                  │  - CultivationService              │
│  - /admin/trash-bin               │  - TrashBinService                 │
├───────────────────────────────────┴────────────────────────────────────┤
│ Repositories Layer (SQLAlchemy 2.0 ORM Abstraction)                   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ SQL Connection Pooling (Pre-ping)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        PostgreSQL 16 Database                          │
│               Alembic Schema Migrations & Enforced FKs                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Architectural Layers & Separation of Concerns

### 2.1 Backend Layered Pattern (`backend/app/`)
* **`api/v1/` (Routers):**
  - Defines HTTP methods, route paths, dependency injection (`get_db`, `get_current_user`, `require_roles`), request serialization, and response status codes.
  - Zero raw database queries or direct business mutations inside route definitions.
* **`services/` (Orchestration & Business Logic):**
  - Enforces domain business rules, cross-entity orchestration, authorization validations (e.g. farmer ownership checks), and aggregated summary calculations.
* **`repositories/` (Data Access Layer):**
  - Encapsulates all SQLAlchemy queries, pagination filters, soft-delete clauses (`is_deleted == False`), relationship joins, and transaction commits/rollbacks.
* **`models/` (SQLAlchemy 2.0 Declarative ORM):**
  - Table definitions, column constraints, default values, UUID primary keys, and typed relationships.
* **`schemas/` (Pydantic v2):**
  - Strong input validation, email formatting, password length rules, numeric range validation, and outgoing serialization models.
* **`core/`:**
  - `config.py`: Environment settings with validation via `pydantic-settings`.
  - `database.py`: SQLAlchemy Engine and sessionmaker factory.
  - `jwt.py`: Asymmetric RS256 token creation and decoding with fallback development transient key generation.
  - `security.py`: Argon2id password hashing and verification.

### 2.2 Frontend Modular Architecture (`frontend/src/`)
* **`app/` (Next.js App Router):**
  - Route handlers, layout wrappers, and role-guarded views (`/admin`, `/farmer`, `/dashboard`, `/login`).
* **`components/`:**
  - Reusable UI component library (`ui/Button`, `ui/Card`, `ui/Badge`, `ui/Modal`, `ui/Input`).
  - Domain components (`cultivations/`, `crops/`, `farms/`, `procurement/`, `3d/`).
* **`context/`:**
  - `AuthContext.tsx`: Client-side JWT session state, role verification helpers (`hasRole`, `hasAnyRole`), and automatic 401 redirect handling.
* **`services/`:**
  - Axios/fetch API client abstractions communicating with backend REST endpoints under `/api/v1`.
* **`types/`:**
  - TypeScript interfaces mirroring backend Pydantic models for type safety.

---

## 3. Communication & Data Flow

```text
[Farmer Browser Action]
         │
         ▼
[Frontend Service (e.g., cultivationService.ts)]
         │
         ▼ (Headers: Authorization: Bearer <JWT>)
[FastAPI Route (e.g., POST /api/v1/cultivations/{id}/stages/{stage_id}/expenses)]
         │
         ▼ (Dependency: get_current_user -> verify RS256 signature)
[CultivationService.add_stage_expense]
         │
         ├── Verify Cultivation ownership (farmer_profile_id == current_user.farmer_profile.id)
         ├── Validate ExpenseCategory, PaymentMode, and positive amounts
         │
         ▼
[CultivationRepository.create_expense]
         │
         ├── Insert into stage_expenses
         ├── Commit Session
         │
         ▼
[Compute Aggregated Financial Summaries & Return JSON]
```
