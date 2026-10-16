# Agri-Smart Ecosystem — Project Context & Master Specification

## 1. Project Overview & Name
* **Project Name:** Agri-Smart Ecosystem (`startup_farms`)
* **Mission:** An enterprise-grade, end-to-end digital agriculture and agronomic lifecycle platform designed to connect farmers, traders, agricultural workers, logistics drivers, and central administrators into a unified digital ecosystem.
* **Core Philosophy:** Eliminate agricultural opacity, empower smallholder and commercial farmers with actionable crop stage guidance, provide granular field expense & daily worker wage tracking, and enable seamless farm planning, procurement, and market linkages.

---

## 2. Stakeholders & Personas
1. **Super Admin (`SUPER_ADMIN`):**
   * Central platform governance, role assignments, security policy oversight.
   * Central Crop Master taxonomy management and dynamic cultivation process stage templates (e.g. Onion, Paddy, Turmeric, Tomato).
   * Soft-delete trash bin vault auditing with restoration and purge capabilities.
   * Supplier and input catalog management.
2. **Farmer (`FARMER`):**
   * Farm parcel registration (GPS coordinates, ownership, area, soil).
   * Crop planning per season (Kharif, Rabi, Zaid, Summer, Year-round).
   * Active Cultivation Run management: tracking daily growth stages, updating progress, logging itemized expenses (seeds, fertilizers, machinery, diesel, labor).
   * Worker attendance & wage logging with cash/UPI settlement tracking.
   * Input procurement requests to verified suppliers.
3. **Trader (`TRADER`):**
   * Business profile, license verification, trade procurement, commodity lot bidding (planned/future scope).
4. **Driver / Logistics (`DRIVER`):**
   * Vehicle registration, driving license compliance, farm-to-mandi transport tracking (planned/future scope).
5. **Agricultural Worker (`WORKER`):**
   * Profile verification, daily labor logs, wage history, farm task allocation.

---

## 3. Business & Functional Requirements

### 3.1 Authentication & Multi-Role RBAC
* Secure mobile number/email authentication with Argon2id password hashing.
* RS256 asymmetric JWT authentication with 15-minute access tokens and 7-day refresh token rotation via HttpOnly secure cookies.
* Granular role-based access control (`SUPER_ADMIN`, `FARMER`, `TRADER`, `DRIVER`, `WORKER`).
* Support for multi-role users (e.g., a user who is both a Farmer and a Trader).

### 3.2 Farm Parcel Management
* Multi-farm support per farmer profile.
* Unique sequential farm identifier (`FARM-XXXXXX`).
* Boundary data: total land area, unit (Acres, Hectares, Cents, Bigha, Guntha), geographical coordinates, soil type, water source.

### 3.3 Crop Master & Cultivation Process Templates
* Standardized crop catalog (`CROP-XXXXXX`) with scientific names, category classifications, and local language translations.
* Sequential dynamic cultivation process stages (e.g., Land Preparation -> Sowing -> Vegetative -> Flowering -> Harvesting).
* Stage assets, theme color coding, duration estimates, recommended agronomic practices, and required input specifications.

### 3.4 Active Cultivation Run Lifecycle
* Instantiation of active cultivation runs linked to approved Farm Crop Plans.
* Real-time stage progression with status updates (`PENDING`, `IN_PROGRESS`, `COMPLETED`, `SKIPPED`).
* Expected harvest date calculation based on crop maturity cycles.
* Multi-season yield and gross revenue tracking for economic benchmarking.

### 3.5 Field Expenses & Labor Wage Accounting
* Real-time itemized stage expense capture across categories (`SEEDS`, `FERTILIZERS`, `PESTICIDES`, `LABOR`, `MACHINERY`, `IRRIGATION`, `TRANSPORT`, `OTHER`).
* Payment mode recording (`CASH`, `UPI`, `BANK_TRANSFER`, `CREDIT`).
* Daily worker attendance logs with day-fraction calculations (e.g., 2.5 days @ ₹350/day = ₹875) and payment settlement status (`PAID`, `PENDING`).
* Automated stage-wise and cultivation-wide expense totals aggregation.

### 3.6 Platform Trash Bin Vault & Data Governance
* Universal soft-delete mechanism across all 6 core business tables (`users`, `crops`, `farms`, `farm_crop_plans`, `cultivation_runs`, `stage_expenses`).
* Deleted records preserved with `deleted_at` timestamps and `deleted_by` user references.
* Centralized Super Admin Trash Vault enabling one-click entity restoration and safe permanent hard purge.

---

## 4. Non-Functional Requirements
* **Security:** OWASP compliance, zero plain-text passwords, cryptographic JWT verification, strict CORS origin whitelisting, database connection pooling with pre-ping validation.
* **Performance:** Millisecond API responses with optimized indexed queries, eager-loading (`joinedload`) to prevent N+1 queries, client-side React Query caching.
* **Reliability:** Atomic database transactions, strict foreign key cascade/restrict integrity rules, reproducible Alembic schema migrations.
* **Maintainability:** Clean layered architecture in FastAPI (Router -> Service -> Repository -> Model) and modular Next.js App Router design.
