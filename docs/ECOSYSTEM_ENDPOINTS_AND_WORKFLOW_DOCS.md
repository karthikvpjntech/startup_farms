# Agri-Smart Ecosystem
### Comprehensive Technical Architecture, Endpoint Workflows & System Documentation

---

## 1. Purpose

This document provides an exhaustive, endpoint-oriented workflow and architectural reference for the **Agri-Smart Ecosystem**. It establishes how the **Next.js 15 (React 19, TypeScript, Tailwind CSS)** frontend interfaces with the **FastAPI (Python 3.12, SQLAlchemy 2.0)** backend REST API, database persistence (**PostgreSQL 16 / SQLite**), media file storage, and automated notification services across all primary user journeys (**Farmer, Super Admin, Trader, Driver, Worker**).

---

## 2. High-Level Endpoint Architecture

```text
       FARMER / SUPER ADMIN / TRADER / DRIVER / WORKER
                              │
                              ▼
            NEXT.JS 15 + REACT 19 FRONTEND (SPA/SSR)
       (Tailwind CSS • Framer Motion • Lucide • TanStack Query)
                              │
                              │ HTTPS / REST JSON (Bearer JWT + HttpOnly Cookie)
                              ▼
                   FASTAPI 0.115+ REST API SERVER
 ┌─────────────────────────────────────────────────────────────┐
 │  API Gateway & Middleware Layer                             │
 │  ├─ CORS Middleware (Whitelisted Origins)                  │
 │  ├─ Static Media Server (/uploads/stages)                   │
 │  └─ Global Exception Handlers & Standard APIResponse Envelope│
 ├─────────────────────────────────────────────────────────────┤
 │  Core Service Modules                                       │
 │  ├─ Authentication & Token Lifecycle (Argon2id + RS256)     │
 │  ├─ RBAC Authorization & Multi-Persona Profiles             │
 │  ├─ Super Admin Governance & Master Catalogs                │
 │  ├─ Farm & Land Parcel Management                           │
 │  ├─ Crop Master & Sequential Cultivation Process Templates  │
 │  ├─ Farm Crop Planning & Requisitions                       │
 │  ├─ Cultivation Lifecycle, Dynamic Stages & Daily Logs      │
 │  ├─ Agricultural Inputs Catalog & Verified Suppliers        │
 │  ├─ Worker Master, Attendance & Wage Settlements            │
 │  ├─ Machinery Master & Fuel/Rental Usage Tracking           │
 │  ├─ Consolidated Billing & Multi-Channel Payments (UPI/Cash)│
 │  ├─ Harvest Logistics & Fleet Dispatch Tracking             │
 │  ├─ SMS Alert & Transactional Notification Engine           │
 │  ├─ Conventional vs. Organic Matrix & Financial Analytics   │
 │  └─ Soft Delete & Trash Bin Recovery System                 │
 └─────────────────────────────────────────────────────────────┘
          │                 │                │               │
          ▼                 ▼                ▼               ▼
 ┌──────────────────┐ ┌───────────┐ ┌────────────────┐ ┌───────────┐
 │ SQLAlchemy 2.0   │ │ Local     │ │ SMS Gateway    │ │ External  │
 │ PostgreSQL 16    │ │ Media     │ │ Notification   │ │ Services  │
 │ / SQLite Storage │ │ Storage   │ │ Engine / Mock  │ │ & APIs    │
 └──────────────────┘ └───────────┘ └────────────────┘ └───────────┘
```

---

## 3. User & Role Endpoint Workflows

### 3.1 Authentication, Session & Token Lifecycle
| Workflow Step | Method & Endpoint | Backend Responsibility | Frontend Integration |
| :--- | :--- | :--- | :--- |
| **Login** | `POST /api/v1/auth/login` | Validates mobile/email & Argon2id password; generates 15-min RS256 access token; issues HttpOnly refresh cookie. | `/login` form submission, stores JWT in AuthContext. |
| **Token Refresh** | `POST /api/v1/auth/refresh` | Validates HttpOnly cookie, rotates refresh token, returns new 15-min RS256 token. | Axios/Fetch request interceptor on 401 error. |
| **Current User** | `GET /api/v1/auth/me` | Decodes Bearer token and returns user profile, verified phone, and active role array. | App root hydration to enforce RBAC routing. |
| **Logout** | `POST /api/v1/auth/logout` | Revokes active DB session refresh token; clears browser HttpOnly cookie. | Header / Sidebar logout button. |

---

### 3.2 Role Profiles & Multi-Persona Identity
| Workflow Step | Method & Endpoint | Backend Responsibility | Frontend Integration |
| :--- | :--- | :--- | :--- |
| **Farmer Profile** | `GET/POST/PUT /api/v1/profiles/farmer` | Manages Farmer KYC, farm location, preferred farming methods (Conventional/Organic). | `/farmer/profile` settings page. |
| **Trader Profile** | `GET/POST/PUT /api/v1/profiles/trader` | Manages APMC license, business registration, GSTIN, and trading commodities. | `/trader/profile` settings page. |
| **Driver Profile** | `GET/POST/PUT /api/v1/profiles/driver` | Manages driver license number, vehicle type, payload capacity, and service districts. | `/driver/profile` settings page. |
| **Worker Profile** | `GET/POST/PUT /api/v1/profiles/worker` | Manages primary labor skills, daily wage expectation, and availability status. | `/worker/profile` settings page. |

---

### 3.3 Farm Master & Land Parcel Management
| Workflow Step | Method & Endpoint | Backend Responsibility | Frontend Integration |
| :--- | :--- | :--- | :--- |
| **Create Farm** | `POST /api/v1/farms` | Creates farm linked to farmer; generates unique sequential code (`FARM-000001`). | `/farmer/farms` Add Farm modal. |
| **List Farms** | `GET /api/v1/farms` | Returns paginated, searchable list of farmer-owned farms with total acreage and coordinates. | `/farmer/farms` grid view. |
| **Get Farm Detail** | `GET /api/v1/farms/{farm_id}` | Returns specific farm land details, soil type, irrigation type, and active crops. | `/farmer/farms/[id]` view. |
| **Update Farm** | `PATCH /api/v1/farms/{farm_id}` | Updates farm name, ownership type (`OWNED`/`LEASED`), coordinates, and land units. | `/farmer/farms` Edit Farm drawer. |
| **Toggle Status** | `PATCH /api/v1/farms/{farm_id}/status` | Toggles farm active/inactive status without altering records. | Quick toggle switch on Farm card. |
| **Soft Delete** | `DELETE /api/v1/farms/{farm_id}` | Soft-deletes farm (`is_deleted=true`) with audit metadata. | Delete Farm confirmation modal. |
| **Restore Farm** | `POST /api/v1/farms/{farm_id}/restore` | Restores soft-deleted farm back to active visibility. | Trash Bin restore action. |

---

### 3.4 Crop Master, Seasons & Cultivation Process Templates
| Workflow Step | Method & Endpoint | Backend Responsibility | Frontend Integration |
| :--- | :--- | :--- | :--- |
| **List Public Crops** | `GET /api/v1/crops` | Returns active agricultural crops filtered by category (`VEGETABLE`, `PULSE`, `SPICE`) & season. | `/farmer/crops` Catalog Explorer. |
| **Crop Detail** | `GET /api/v1/crops/{crop_id}` | Retrieves crop agronomy, duration days, water requirements, and expected yield range. | `/farmer/crops/[id]` detail view. |
| **Template Stages** | `GET /api/v1/crops/{crop_id}/stages` | Returns default sequential cultivation stages (e.g. Land Prep, Sowing, Weeding, Harvesting). | Crop timeline preview component. |

---

### 3.5 Farm Crop Planning & Season Requisitions
| Workflow Step | Method & Endpoint | Backend Responsibility | Frontend Integration |
| :--- | :--- | :--- | :--- |
| **Create Crop Plan** | `POST /api/v1/farm-crop-plans` | Formulates planned crop season for a farm parcel; allocates acreage and planned sowing date. | `/farmer/crop-plans` Planning wizard. |
| **List Plans** | `GET /api/v1/farm-crop-plans` | Lists planned crop cycles with projected cost and target yield estimates. | `/farmer/crop-plans` summary table. |
| **Get Plan Detail** | `GET /api/v1/farm-crop-plans/{plan_id}`| Returns allocated farm details, crop guidelines, and stage duration projections. | Crop plan detail inspection drawer. |
| **Update Plan** | `PATCH /api/v1/farm-crop-plans/{plan_id}`| Modifies planned acreage, sowing window, or farming method (`ORGANIC`/`CONVENTIONAL`). | Edit Crop Plan form. |

---

### 3.6 Cultivation Execution, Dynamic Stages & Stage Transitions
| Workflow Step | Method & Endpoint | Backend Responsibility | Frontend Integration |
| :--- | :--- | :--- | :--- |
| **Start Cultivation** | `POST /api/v1/crops/cultivations` | Instantiates live cultivation run from a verified plan; auto-seeds sequential stages. | `/farmer/cultivations` Start Run modal. |
| **List Cultivations** | `GET /api/v1/crops/cultivations` | Retrieves active/archived cultivation runs with live progress percentage and total cost. | `/farmer/cultivations` dashboard grid. |
| **Cultivation Detail**| `GET /api/v1/crops/cultivations/{id}`| Returns stage progression array, total labor/machine/material costs, and timeline status. | `/farmer/cultivations/[id]` live tracking. |
| **Append Custom Stage**| `POST /api/v1/crops/cultivations/{id}/stages` | Appends custom dynamic stage (e.g., 'நில உழவு', 'பில்லு புடுங்குறது', 'மருந்து அடித்தல்'). | Custom stage creation button. |
| **Update Stage** | `PATCH /api/v1/crops/stages/{stage_id}` | Updates stage dates, status (`PENDING`, `IN_PROGRESS`, `COMPLETED`), or observation notes. | Stage edit drawer. |
| **Complete & Next** | `POST /api/v1/crops/stages/{stage_id}/complete-and-next` | Marks stage `COMPLETED` and automatically promotes next sequential stage to `IN_PROGRESS`. | "Complete & Advance Stage" button. |
| **Record Harvest** | `PATCH /api/v1/crops/cultivations/{id}/harvest-yield` | Records harvest yield quantity, unit selling price, and calculates total sales revenue. | Final stage yield recording dialog. |

---

### 3.7 Stage Expenses, Worker Wages & Attendance (Bilingual Support)
| Workflow Step | Method & Endpoint | Backend Responsibility | Frontend Integration |
| :--- | :--- | :--- | :--- |
| **Add Single Wage** | `POST /api/v1/crops/stages/{id}/workers` | Records days worked, daily rate, computes total wage, sets status (`PAID`/`PENDING`). | Add Wage Entry dialog. |
| **Bulk Add Wages** | `POST /api/v1/crops/stages/{id}/workers/bulk` | Bulk logs multiple laborers' wages in one transactional operation. | Bulk Wage Entry grid. |
| **List Stage Wages**| `GET /api/v1/crops/stages/{id}/workers` | Retrieves all wage entries, days worked, and pending balances for a stage. | Worker Wage tab in Stage tracker. |
| **Toggle Wage Status**| `PATCH /api/v1/crops/workers/{id}/payment-status` | Toggles worker wage payment status between `PAID` and `PENDING`. | Instant status toggle badge. |
| **Add Expense** | `POST /api/v1/crops/stages/{id}/expenses` | Itemizes cost under `LABOR`, `INPUT_MATERIAL`, `MACHINERY` with invoice attachment. | Add Expense modal. |
| **List Expenses** | `GET /api/v1/crops/stages/{id}/expenses` | Returns itemized expenses, receipts, and payment modes (`CASH`/`UPI`). | Stage Financials summary tab. |
| **Undo Delete** | `POST /api/v1/crops/expenses/{id}/restore`| Restores soft-deleted expense (supports 6-second undo toast in UI). | 6-second Undo Toast button. |

---

### 3.8 Machine Master & Farm Machinery Usage
| Workflow Step | Method & Endpoint | Backend Responsibility | Frontend Integration |
| :--- | :--- | :--- | :--- |
| **Create Machine** | `POST /api/v1/farmer/crm/machines` | Registers tractor, harvester, tiller, or pump into farmer's machine master. | `/farmer/machines` Register modal. |
| **List Machines** | `GET /api/v1/farmer/crm/machines` | Lists machines with ownership classification (`OWNED`/`RENTAL`), hourly rate, and status. | `/farmer/machines` inventory list. |
| **Log Machine Usage**| `POST /api/v1/farmer/crm/stages/{id}/machines` | Logs hours used, fuel cost, rental charges, and computes total machinery cost for stage. | Log Machine Hours form. |
| **List Usages** | `GET /api/v1/farmer/crm/stages/{id}/machines` | Returns historical machine usage entries for a cultivation stage. | Machine usage log table. |

---

### 3.9 Agricultural Inputs Catalog, Verified Suppliers & Procurement
| Workflow Step | Method & Endpoint | Backend Responsibility | Frontend Integration |
| :--- | :--- | :--- | :--- |
| **Input Catalog** | `GET /api/v1/inputs` | Returns input master catalog (seeds, fertilizers, bio-inputs) with NPK composition. | `/farmer/inputs` catalog table. |
| **Supplier Directory**| `GET /api/v1/suppliers` | Lists verified agricultural suppliers filtered by district, state, and type. | `/farmer/suppliers` directory. |
| **Create Requisition**| `POST /api/v1/procurement/requests` | Creates procurement requisition (`REQ-000001`) linked to cultivation and input master. | `/farmer/procurement` Request dialog. |
| **List Requisitions** | `GET /api/v1/procurement/requests` | Returns status of requisitions (`PENDING`, `APPROVED`, `FULFILLED`, `CANCELLED`). | `/farmer/procurement` tracking table. |
| **Record Purchase** | `POST /api/v1/farmer/crm/purchases` | Records material purchase invoice, supplier linkage, quantity, and batch number. | `/farmer/purchases` Record form. |

---

### 3.10 Farmer CRM Billing, Invoicing & Multi-Channel Payments
| Workflow Step | Method & Endpoint | Backend Responsibility | Frontend Integration |
| :--- | :--- | :--- | :--- |
| **Generate Stage Bill**| `POST /api/v1/farmer/crm/bills/generate-stage-bill` | Compiles unbilled labor wages, machinery usage, and input expenses into single bill. | "Generate Stage Invoice" action. |
| **Create Custom Bill** | `POST /api/v1/farmer/crm/bills` | Generates manual vendor, worker, or operational bill with custom line items. | `/farmer/billing` Create Bill dialog. |
| **List Bills** | `GET /api/v1/farmer/crm/bills` | Returns all bills, balance dues, payment statuses (`PENDING`, `PARTIALLY_PAID`, `PAID`). | `/farmer/billing` invoice ledger. |
| **Get Bill Detail** | `GET /api/v1/farmer/crm/bills/{bill_id}` | Retrieves full bill breakdown, associated payments, and outstanding balance. | `/farmer/billing/[id]` invoice view. |
| **Process Payment** | `POST /api/v1/farmer/crm/payments` | Records payment settlement (`UPI`, `CASH`, `NET_BANKING`), updates bill balance, sends SMS alert. | `/farmer/payments` Checkout modal. |
| **List Payments** | `GET /api/v1/farmer/crm/payments` | Returns timestamped transaction receipts and payment verification records. | `/farmer/payments` ledger view. |

---

### 3.11 Harvest Logistics & Dispatch Tracking
| Workflow Step | Method & Endpoint | Backend Responsibility | Frontend Integration |
| :--- | :--- | :--- | :--- |
| **Create Dispatch** | `POST /api/v1/farmer/crm/logistics` | Schedules harvest transport trip; assigns driver, vehicle number, and destination mandi. | `/farmer/logistics` Schedule Trip form. |
| **List Dispatches** | `GET /api/v1/farmer/crm/logistics` | Lists logistics trips with live status (`PLANNED`, `IN_TRANSIT`, `DELIVERED`). | `/farmer/logistics` dispatch board. |
| **Update Dispatch** | `PATCH /api/v1/farmer/crm/logistics/{id}/status` | Updates trip progression, delivery confirmation timestamp, and freight charges. | Trip status update popover. |

---

### 3.12 SMS & Notification Delivery Engine
| Workflow Step | Method & Endpoint | Backend Responsibility | Frontend Integration |
| :--- | :--- | :--- | :--- |
| **Send Manual SMS** | `POST /api/v1/farmer/crm/notifications/send-sms` | Dispatches SMS notification to worker/supplier regarding wage settlement or purchase. | Send SMS notification dialog. |
| **Notification Logs**| `GET /api/v1/farmer/crm/notifications` | Returns audit history of sent SMS messages, timestamps, recipient phone numbers, and statuses. | `/farmer/notifications` audit page. |

---

### 3.13 Comparative Analytics & Financial Reports
| Workflow Step | Method & Endpoint | Backend Responsibility | Frontend Integration |
| :--- | :--- | :--- | :--- |
| **Dashboard KPIs** | `GET /api/v1/farmer/crm/dashboard-summary` | Aggregates active farms, running crops, today's work, active labor, and total dues. | `/farmer` Executive Dashboard. |
| **Comparison Matrix**| `GET /api/v1/crops/cultivations/comparison`| Generates side-by-side ROI matrix for Conventional vs Organic cultivation runs. | `/farmer/cultivations/comparison`. |
| **Crop Cost Report** | `GET /api/v1/farmer/crm/reports/crop-cost` | Itemized labor, machine, material, and logistics cost totals per crop cycle. | `/farmer/reports` Cost analysis tab. |
| **Worker Report** | `GET /api/v1/farmer/crm/reports/worker-payments` | Summarizes individual worker days worked, total wages earned, paid, and pending balances.| `/farmer/reports` Worker wage ledger. |
| **Supplier Report** | `GET /api/v1/farmer/crm/reports/supplier-purchases` | Summarizes total purchases, supplier balances, and settlement history. | `/farmer/reports` Supplier ledger. |
| **Expense Report** | `GET /api/v1/farmer/crm/reports/farm-expenses` | Aggregates all operational farm expenses categorized by type. | `/farmer/reports` Expense pie chart. |

---

### 3.14 Media Uploads
| Workflow Step | Method & Endpoint | Backend Responsibility | Frontend Integration |
| :--- | :--- | :--- | :--- |
| **Upload File** | `POST /api/v1/media/upload` | Validates file type/size, stores in `/uploads/stages/`, returns public URL. | Drag-and-drop media uploaders. |

---

## 4. End-to-End Workflow Lifecycles

### 4.1 End-to-End Cultivation & Farm Operations Flow

```text
Farmer opens /farmer/crops or /farmer/crop-plans
       │
       ▼
Select Crop Master & Configure Acreage / Season
       │
       ▼
POST /api/v1/farm-crop-plans (Plan Created)
       │
       ▼
POST /api/v1/crops/cultivations (Live Cultivation Run Initialized)
       │
       ├─ Auto-seeds Sequential Stages (e.g. Land Prep, Sowing, Weeding, Harvesting)
       │
       ▼
Stage 1: IN_PROGRESS (e.g., Land Preparation / நில உழவு)
       │
       ├─ POST /api/v1/crops/stages/{id}/workers (Add Labor Wages & Attendance)
       ├─ POST /api/v1/farmer/crm/stages/{id}/machines (Log Tractor Usage)
       ├─ POST /api/v1/crops/stages/{id}/expenses (Log Inputs & Fuel)
       └─ POST /api/v1/media/upload (Attach Stage Photo)
       │
       ▼
POST /api/v1/crops/stages/{id}/complete-and-next
       │
       ├─ Stage 1 marked COMPLETED
       └─ Stage 2 marked IN_PROGRESS
       │
       ▼
(Repeat for Weeding, Fertilization, Pest Management, Irrigation stages)
       │
       ▼
Final Stage: Harvesting & Marketing
       │
       ├─ PATCH /api/v1/crops/cultivations/{id}/harvest-yield (Record 45 Quintals @ ₹2,800/Qtl)
       ├─ POST /api/v1/farmer/crm/logistics (Dispatch to Mandi / Trader)
       └─ POST /api/v1/farmer/crm/bills/generate-stage-bill (Consolidated Stage Invoice)
       │
       ▼
POST /api/v1/farmer/crm/payments (Settle Labor / Machine Dues via UPI or Cash)
       │
       ▼
GET /api/v1/crops/cultivations/comparison & GET /api/v1/farmer/crm/reports/crop-cost
(Full Financial ROI, Net Profit, and Operational Efficiency Visualized)
```

---

### 4.2 Worker Attendance & Wage Settlement Flow

```text
Farmer opens /farmer/workers
       │
       ▼
Register Worker in Master: POST /api/v1/farmer/crm/workers
       │
       ▼
Daily Stage Labor Logging:
POST /api/v1/farmer/crm/stages/{id}/attendance
(Computes days_worked * daily_wage = total_wage; status: PENDING)
       │
       ▼
Consolidate Labor Invoices:
POST /api/v1/farmer/crm/bills/generate-stage-bill (Bill Type: WORKER_PAYMENT)
       │
       ▼
Payment Checkout:
POST /api/v1/farmer/crm/payments (Payment Method: UPI / CASH)
       │
       ├─ Bill status transitions PENDING ──→ PAID
       ├─ Worker log status transitions PENDING ──→ PAID
       └─ SMS Gateway triggers instant wage confirmation SMS to Worker
```

---

## 5. System Lifecycle State Transitions

### 5.1 Cultivation Stage Lifecycle
```text
PENDING ─────────→ IN_PROGRESS ─────────→ COMPLETED
   │                                           ▲
   └─────────────────→ SKIPPED ────────────────┘
```

### 5.2 Bill & Payment Settlement Lifecycle
```text
PENDING ─────────→ PARTIALLY_PAID ─────────→ PAID
   │
   └─────────────→ CANCELLED
```

### 5.3 Harvest Logistics Dispatch Lifecycle
```text
PLANNED ────→ PICKUP_SCHEDULED ────→ IN_TRANSIT ────→ DELIVERED
   │
   └────────→ CANCELLED
```

### 5.4 Procurement Requisition Lifecycle
```text
PENDING ─────────→ APPROVED ─────────→ FULFILLED
   │                    │
   └─→ REJECTED         └─→ CANCELLED
```

---

## 6. Super Admin Governance & Master Management

### 6.1 Admin Endpoint Workflow
| Function | Method & Endpoint | Backend Responsibility | Frontend Integration |
| :--- | :--- | :--- | :--- |
| **Admin Metrics** | `GET /api/v1/admin/dashboard` | Aggregates platform-wide users, farms, cultivations, and system health. | `/admin` Executive Overview. |
| **Create User** | `POST /api/v1/admin/users` | Registers user with pre-assigned roles (`FARMER`, `TRADER`, `DRIVER`, `WORKER`). | `/admin/users` Add User dialog. |
| **List All Users** | `GET /api/v1/admin/users` | Lists platform users with multi-role filters, search, and activity tracking. | `/admin/users` user ledger. |
| **Assign Roles** | `POST /api/v1/admin/users/{id}/roles` | Grants system roles to existing user identity. | Role management modal. |
| **Reset Password** | `POST /api/v1/admin/users/{id}/reset-password` | Resets user password securely with Argon2id hashing. | Reset password popover. |
| **Crop Master** | `POST/GET/PATCH/DELETE /api/v1/admin/crops` | CRUD for agricultural crop catalog, scientific names, and cultivation metadata. | `/admin/crops` master view. |
| **Stage Templates**| `POST/GET/PATCH/DELETE /api/v1/admin/crops/{id}/stages` | Configures default cultivation stage sequences, standard days, and tips for crops. | `/admin/crops/[id]` stages tab. |
| **Supplier Admin** | `POST/GET/PATCH/DELETE /api/v1/admin/suppliers` | Verifies and manages agricultural input suppliers and distributor ratings. | `/admin/suppliers` verification. |
| **Trash Bin View** | `GET /api/v1/admin/trash` | Audits soft-deleted records across Users, Farms, Crops, and Suppliers. | `/admin/trash-bin` console. |
| **Restore Entity** | `POST /api/v1/admin/trash/restore` | Restores soft-deleted entity back to active database queries. | Trash restore action. |
| **Purge Entity** | `DELETE /api/v1/admin/trash/purge` | Permanently hard-deletes entity from the database. | Permanent purge modal. |

---

### 6.2 Admin Governance Architecture Flow

```text
SUPER ADMIN LOGIN
       │
       ▼
POST /api/v1/auth/login (Role: SUPER_ADMIN)
       │
       ▼
ADMIN CONTROL PANEL (/admin)
 ├── User Administration (/admin/users)
 │    ├── POST /api/v1/admin/users
 │    ├── POST /api/v1/admin/users/{id}/roles
 │    └── POST /api/v1/admin/users/{id}/reset-password
 │
 ├── Crop Agronomy & Stage Master (/admin/crops)
 │    ├── POST/PATCH /api/v1/admin/crops
 │    └── POST/PATCH /api/v1/admin/crops/{id}/stages
 │
 ├── Supplier Directory Verification (/admin/suppliers)
 │    ├── POST /api/v1/admin/suppliers
 │    └── PATCH /api/v1/admin/suppliers/{id}/status
 │
 └── System Audit & Trash Bin (/admin/trash-bin)
      ├── GET /api/v1/admin/trash
      ├── POST /api/v1/admin/trash/restore
      └── DELETE /api/v1/admin/trash/purge
```

---

## 7. Endpoint-to-Service Integration Matrix

| Integration Layer | Connection & Protocols | Primary System Purpose |
| :--- | :--- | :--- |
| **Frontend UI** | Next.js 15, React 19, TypeScript, Tailwind CSS, TanStack Query | Responsive desktop & mobile interfaces for Farmers, Traders, Drivers, Workers, Admins. |
| **REST API Server** | FastAPI 0.115+, ASGI Uvicorn, Python 3.12+ | High-throughput async routing, request validation, business logic, role security. |
| **Database Engine** | SQLAlchemy 2.0 ORM $\leftrightarrow$ PostgreSQL 16+ / SQLite | Relational schema persistence, foreign keys, transactions, and soft-delete filters. |
| **Media Storage** | FastAPI StaticFiles mount at `/uploads/` | Stores observation photos, weed comparison pictures, crop disease photos, and receipts. |
| **Notification Engine**| `SMSLog` Service / SMS Gateway Integration | Dispatches wage receipts, stage transition alerts, and invoice payment confirmations. |
| **Financial Engine** | Python Financial Calculation Utilities | Itemized stage breakdowns, billing generation, and ROI comparison matrices. |

---

## 8. Security, RBAC & Data Architecture

1. **Decoupled Architecture:** The Next.js frontend has zero direct database credentials and connects exclusively via authenticated REST API requests.
2. **Dual-Token Authentication Scheme:**
   - **Access Token:** Short-lived (15 minutes), cryptographically signed RS256 JWT containing user identity and role scopes.
   - **Refresh Token:** Long-lived (7 days), stored securely as an `HttpOnly`, `SameSite=Lax`, `Secure` cookie, rotated on every refresh call.
3. **Password Security:** All passwords are mathematically protected using state-of-the-art **Argon2id** password hashing.
4. **Role-Based Access Control (RBAC):** Every endpoint enforces strict role validation via FastAPI dependencies (`require_roles(RoleEnum.FARMER)`, `require_roles(RoleEnum.SUPER_ADMIN)`).
5. **Soft-Delete Architecture:** Critical entities (`Farm`, `Crop`, `CultivationRun`, `CultivationStage`, `Worker`, `Machine`, `Bill`) enforce soft deletion (`is_deleted=true`), preventing accidental data loss and allowing single-click restorations via the Trash Bin.
6. **SQL Injection Protection:** 100% of database queries utilize SQLAlchemy 2.0 type-safe parameterized expressions.
7. **Cross-Origin Resource Sharing (CORS):** Backend strictly restricts incoming origins to explicit whitelisted frontend domains (`http://localhost:3000`, `http://127.0.0.1:3000`).

---

## 9. Exhaustive Complete Endpoint Map

### AUTH
```http
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
GET    /api/v1/auth/me
```

### RBAC & ROLES
```http
GET    /api/v1/rbac/roles
GET    /api/v1/rbac/me/permissions
```

### PROFILES
```http
GET    /api/v1/profiles/farmer
POST   /api/v1/profiles/farmer
PUT    /api/v1/profiles/farmer
GET    /api/v1/profiles/trader
POST   /api/v1/profiles/trader
PUT    /api/v1/profiles/trader
GET    /api/v1/profiles/driver
POST   /api/v1/profiles/driver
PUT    /api/v1/profiles/driver
GET    /api/v1/profiles/worker
POST   /api/v1/profiles/worker
PUT    /api/v1/profiles/worker
```

### FARMS
```http
POST   /api/v1/farms
GET    /api/v1/farms
GET    /api/v1/farms/{farm_id}
PATCH  /api/v1/farms/{farm_id}
PATCH  /api/v1/farms/{farm_id}/status
DELETE /api/v1/farms/{farm_id}
POST   /api/v1/farms/{farm_id}/restore
```

### CROPS & CROP STAGES (PUBLIC & FARMER)
```http
GET    /api/v1/crops
GET    /api/v1/crops/{crop_id}
GET    /api/v1/crops/{crop_id}/stages
```

### FARM CROP PLANS
```http
POST   /api/v1/farm-crop-plans
GET    /api/v1/farm-crop-plans
GET    /api/v1/farm-crop-plans/{plan_id}
PATCH  /api/v1/farm-crop-plans/{plan_id}
PATCH  /api/v1/farm-crop-plans/{plan_id}/status
DELETE /api/v1/farm-crop-plans/{plan_id}
```

### CULTIVATION LIFECYCLE & STAGE EXECUTION
```http
POST   /api/v1/crops/cultivations
GET    /api/v1/crops/cultivations
GET    /api/v1/crops/cultivations/comparison
GET    /api/v1/crops/cultivations/{cultivation_id}
PATCH  /api/v1/crops/cultivations/{cultivation_id}/status
PATCH  /api/v1/crops/cultivations/{cultivation_id}/harvest-yield
DELETE /api/v1/crops/cultivations/{cultivation_id}
GET    /api/v1/crops/cultivations/{cultivation_id}/stages
POST   /api/v1/crops/cultivations/{cultivation_id}/stages
PATCH  /api/v1/crops/stages/{stage_id}
DELETE /api/v1/crops/stages/{stage_id}
POST   /api/v1/crops/stages/{stage_id}/complete-and-next
```

### STAGE WORKERS & EXPENSES
```http
POST   /api/v1/crops/stages/{stage_id}/workers
POST   /api/v1/crops/stages/{stage_id}/workers/bulk
GET    /api/v1/crops/stages/{stage_id}/workers
PATCH  /api/v1/crops/workers/{worker_log_id}/payment-status
DELETE /api/v1/crops/workers/{worker_log_id}
POST   /api/v1/crops/stages/{stage_id}/expenses
GET    /api/v1/crops/stages/{stage_id}/expenses
DELETE /api/v1/crops/expenses/{expense_id}
POST   /api/v1/crops/expenses/{expense_id}/restore
```

### FARMER CRM (WORKERS, MACHINES, PURCHASES, SCHEDULES)
```http
GET    /api/v1/farmer/crm/dashboard-summary
GET    /api/v1/farmer/crm/cultivations/{cultivation_id}/crm-detail
GET    /api/v1/farmer/crm/cultivations/{cultivation_id}/cost-summary
POST   /api/v1/farmer/crm/workers
GET    /api/v1/farmer/crm/workers
GET    /api/v1/farmer/crm/workers/{worker_id}
PUT    /api/v1/farmer/crm/workers/{worker_id}
DELETE /api/v1/farmer/crm/workers/{worker_id}
POST   /api/v1/farmer/crm/stages/{stage_id}/attendance
POST   /api/v1/farmer/crm/stages/{stage_id}/attendance/bulk
GET    /api/v1/farmer/crm/stages/{stage_id}/attendance
DELETE /api/v1/farmer/crm/attendance/{attendance_id}
POST   /api/v1/farmer/crm/machines
GET    /api/v1/farmer/crm/machines
PUT    /api/v1/farmer/crm/machines/{machine_id}
DELETE /api/v1/farmer/crm/machines/{machine_id}
POST   /api/v1/farmer/crm/stages/{stage_id}/machines
GET    /api/v1/farmer/crm/stages/{stage_id}/machines
DELETE /api/v1/farmer/crm/machine-usage/{usage_id}
POST   /api/v1/farmer/crm/purchases
GET    /api/v1/farmer/crm/purchases
POST   /api/v1/farmer/crm/cultivations/{cultivation_id}/schedules
GET    /api/v1/farmer/crm/cultivations/{cultivation_id}/schedules
```

### BILLING, INVOICING & PAYMENTS
```http
POST   /api/v1/farmer/crm/bills/generate-stage-bill
POST   /api/v1/farmer/crm/bills
GET    /api/v1/farmer/crm/bills
GET    /api/v1/farmer/crm/bills/{bill_id}
POST   /api/v1/farmer/crm/payments
GET    /api/v1/farmer/crm/payments
```

### LOGISTICS, NOTIFICATIONS & REPORTS
```http
POST   /api/v1/farmer/crm/logistics
GET    /api/v1/farmer/crm/logistics
PATCH  /api/v1/farmer/crm/logistics/{logistics_id}/status
POST   /api/v1/farmer/crm/notifications/send-sms
GET    /api/v1/farmer/crm/notifications
GET    /api/v1/farmer/crm/reports/crop-cost
GET    /api/v1/farmer/crm/reports/worker-payments
GET    /api/v1/farmer/crm/reports/supplier-purchases
GET    /api/v1/farmer/crm/reports/farm-expenses
```

### INPUT CATALOG, SUPPLIERS & PROCUREMENT
```http
GET    /api/v1/inputs
GET    /api/v1/inputs/{input_id}
GET    /api/v1/suppliers
GET    /api/v1/suppliers/{supplier_id}
POST   /api/v1/procurement/requests
GET    /api/v1/procurement/requests
GET    /api/v1/procurement/requests/{request_id}
PATCH  /api/v1/procurement/requests/{request_id}/status
```

### MEDIA & FILE UPLOADS
```http
POST   /api/v1/media/upload
```

### SUPER ADMIN & GOVERNANCE
```http
GET    /api/v1/admin/dashboard
POST   /api/v1/admin/users
GET    /api/v1/admin/users
GET    /api/v1/admin/users/{user_id}
PATCH  /api/v1/admin/users/{user_id}
PATCH  /api/v1/admin/users/{user_id}/status
POST   /api/v1/admin/users/{user_id}/reset-password
POST   /api/v1/admin/users/{user_id}/roles
DELETE /api/v1/admin/users/{user_id}/roles/{role_code}
DELETE /api/v1/admin/users/{user_id}
POST   /api/v1/admin/users/{user_id}/restore
POST   /api/v1/admin/crops
GET    /api/v1/admin/crops
GET    /api/v1/admin/crops/{crop_id}
PATCH  /api/v1/admin/crops/{crop_id}
PATCH  /api/v1/admin/crops/{crop_id}/status
DELETE /api/v1/admin/crops/{crop_id}
POST   /api/v1/admin/crops/{crop_id}/restore
POST   /api/v1/admin/crops/{crop_id}/stages
GET    /api/v1/admin/crops/{crop_id}/stages
GET    /api/v1/admin/stages/{stage_id}
PATCH  /api/v1/admin/stages/{stage_id}
DELETE /api/v1/admin/stages/{stage_id}
POST   /api/v1/admin/suppliers
GET    /api/v1/admin/suppliers
GET    /api/v1/admin/suppliers/{supplier_id}
PATCH  /api/v1/admin/suppliers/{supplier_id}
PATCH  /api/v1/admin/suppliers/{supplier_id}/status
DELETE /api/v1/admin/suppliers/{supplier_id}
GET    /api/v1/admin/trash
POST   /api/v1/farmer/tool-interests
GET    /api/v1/farmer/tool-interests
GET    /api/v1/farmer/tool-interests/{tool_interest_id}
PUT    /api/v1/farmer/tool-interests/{tool_interest_id}
DELETE /api/v1/farmer/tool-interests/{tool_interest_id}
POST   /api/v1/farmer/tool-interests/{tool_interest_id}/refresh-discovery
POST   /api/v1/farmer/tool-interests/check-proximity
POST   /api/v1/admin/trash/restore
DELETE /api/v1/admin/trash/purge
```

---

## 10. Presentation Summary & Persona Journeys

The Agri-Smart Ecosystem connects six coordinated business paths:

1. **Farmer Cultivation & Operations Journey:**  
   `Farm Creation` $\rightarrow$ `Crop Planning` $\rightarrow$ `Cultivation Run` $\rightarrow$ `Stage Execution (Wages / Machinery / Inputs)` $\rightarrow$ `Harvest & Yield Recording` $\rightarrow$ `Comparison & Financial Analytics`
2. **Tool Demand, Google Places Discovery & Geofencing Radar Journey:**  
   `Add Tool Information (Tractor/Rental/Mysuru)` $\rightarrow$ `Automatic Google Places Search` $\rightarrow$ `Persist Matching Vendor Locations & GPS Coordinates` $\rightarrow$ `Farmer Travels Across Region` $\rightarrow$ `Proximity Detection (<500m)` $\rightarrow$ `🔔 In-App Popup Notification` $\rightarrow$ `One-Tap Call & Google Maps Navigation`
3. **Worker Attendance & Wage Settlement Journey:**  
   `Worker Registration` $\rightarrow$ `Daily Stage Attendance & Days Log` $\rightarrow$ `Stage Consolidation` $\rightarrow$ `Bill Generation` $\rightarrow$ `Payment Settle (Cash/UPI)` $\rightarrow$ `SMS Notification`
4. **Input Requisition & Supplier Journey:**  
   `Input Catalog Explorer` $\rightarrow$ `Procurement Requisition` $\rightarrow$ `Purchase Recording` $\rightarrow$ `Supplier Billing` $\rightarrow$ `Financial Report`
5. **Harvest Logistics & Mandi Transport Journey:**  
   `Harvest Yield Confirmation` $\rightarrow$ `Logistics Trip Booking` $\rightarrow$ `Driver & Vehicle Assignment` $\rightarrow$ `In-Transit Tracking` $\rightarrow$ `Mandi Delivery Confirmation`
6. **Super Admin Governance Journey:**  
   `Admin Login` $\rightarrow$ `User Management & Role Granting` $\rightarrow$ `Crop & Stage Template Master` $\rightarrow$ `Supplier Verification` $\rightarrow$ `Trash Bin Recovery & Auditing`
