# Agri-Smart Ecosystem — Database Schema & Migration Specification

## 1. Overview & Engine
* **Engine:** PostgreSQL 16+ (Production / Docker) / SQLite (In-Memory Test Isolation & Local Dev Fallback).
* **Migration Framework:** Alembic (stored in `backend/alembic/versions/`).
* **Primary Key Strategy:** UUID v4 across all tables for secure distributed identifiers and collision resistance.
* **Audit Standard:** All core entities contain `created_at`, `updated_at`, `created_by`, `updated_by`, `is_deleted`, `deleted_at`, and `deleted_by`.

---

## 2. Table Specifications

### 2.1 Identity & Access Control Layer

#### `roles`
* `id` (UUID, PK)
* `name` (VARCHAR(50), Unique, Not Null) — e.g. `SUPER_ADMIN`, `FARMER`, `TRADER`, `DRIVER`, `WORKER`
* `description` (VARCHAR(255), Nullable)
* `is_active` (BOOLEAN, Default: true, Not Null)
* `created_at`, `updated_at` (TIMESTAMP WITH TIME ZONE)

#### `users`
* `id` (UUID, PK)
* `full_name` (VARCHAR(255), Not Null)
* `mobile_number` (VARCHAR(20), Unique, Not Null, Indexed)
* `email` (VARCHAR(255), Unique, Nullable, Indexed)
* `password_hash` (VARCHAR(255), Not Null) — Argon2id
* `is_active` (BOOLEAN, Default: true, Not Null, Indexed)
* `is_deleted` (BOOLEAN, Default: false, Not Null, Indexed)
* `deleted_at`, `deleted_by`, `created_at`, `updated_at`, `created_by`, `updated_by`

#### `user_roles`
* `id` (UUID, PK)
* `user_id` (UUID, FK -> `users.id` ON DELETE CASCADE)
* `role_id` (UUID, FK -> `roles.id` ON DELETE CASCADE)
* `created_at` (TIMESTAMP WITH TIME ZONE)
* *Constraint:* Unique(`user_id`, `role_id`)

#### `refresh_tokens`
* `id` (UUID, PK)
* `user_id` (UUID, FK -> `users.id` ON DELETE CASCADE)
* `token_hash` (VARCHAR(255), Unique, Not Null)
* `expires_at` (TIMESTAMP WITH TIME ZONE, Not Null)
* `is_revoked` (BOOLEAN, Default: false, Not Null)
* `created_at`, `revoked_at` (TIMESTAMP WITH TIME ZONE)
* `replaced_by_token_id` (UUID, FK -> `refresh_tokens.id` ON DELETE SET NULL)

---

### 2.2 Role Profiles Layer

#### `farmer_profiles`
* `id` (UUID, PK)
* `user_id` (UUID, Unique, FK -> `users.id` ON DELETE CASCADE)
* `profile_image_url` (VARCHAR(500), Nullable)
* `address_line1`, `address_line2`, `village`, `district`, `state`, `pincode`
* `created_at`, `updated_at`

#### `trader_profiles`
* `id` (UUID, PK)
* `user_id` (UUID, Unique, FK -> `users.id` ON DELETE CASCADE)
* `business_name`, `business_registration_number`, `address_line1`, `district`, `state`, `pincode`
* `created_at`, `updated_at`

#### `driver_profiles`
* `id` (UUID, PK)
* `user_id` (UUID, Unique, FK -> `users.id` ON DELETE CASCADE)
* `license_number`, `license_expiry_date`, `address_line1`, `district`, `state`, `pincode`
* `created_at`, `updated_at`

#### `worker_profiles`
* `id` (UUID, PK)
* `user_id` (UUID, Unique, FK -> `users.id` ON DELETE CASCADE)
* `address_line1`, `district`, `state`, `pincode`
* `created_at`, `updated_at`

---

### 2.3 Farm & Crop Master Layer

#### `farms`
* `id` (UUID, PK)
* `farmer_profile_id` (UUID, FK -> `farmer_profiles.id` ON DELETE CASCADE)
* `farm_name` (VARCHAR(255), Not Null)
* `farm_code` (VARCHAR(50), Unique, Not Null) — e.g. `FARM-000001`
* `ownership_type` (VARCHAR(50), Not Null) — `OWNED`, `LEASED`, `SHARED`
* `total_land_area` (NUMERIC(12, 4), Not Null)
* `land_area_unit` (VARCHAR(50), Not Null) — `ACRES`, `HECTARES`, `CENTS`, `GUNTHA`, `BIGHA`
* `address_line1`, `village`, `district`, `state`, `pincode`, `latitude`, `longitude`
* `is_active`, `is_deleted`, `deleted_at`, `deleted_by`, `created_at`, `updated_at`, `created_by`, `updated_by`

#### `crops`
* `id` (UUID, PK)
* `crop_name` (VARCHAR(100), Not Null)
* `crop_code` (VARCHAR(50), Unique, Not Null) — e.g. `CROP-000001`
* `scientific_name` (VARCHAR(150), Nullable)
* `crop_category` (VARCHAR(50), Not Null) — `CEREALS`, `PULSES`, `VEGETABLES`, `FRUITS`, `OILSEEDS`, `SPICES`, `COMMERCIAL`, `FIBER`
* `description` (TEXT, Nullable)
* `is_active`, `is_deleted`, `deleted_at`, `deleted_by`, `created_at`, `updated_at`, `created_by`, `updated_by`

#### `crop_cultivation_stages` (Master Process Stage Templates)
* `id` (UUID, PK)
* `crop_id` (UUID, FK -> `crops.id` ON DELETE CASCADE)
* `stage_order` (INTEGER, Not Null)
* `stage_name` (VARCHAR(200), Not Null) — e.g. `Land Preparation & Basal Fertilization`
* `stage_name_local` (VARCHAR(200), Nullable) — e.g. `நில உழவு & அடி உரம்`
* `description` (TEXT, Nullable)
* `duration_days` (INTEGER, Default: 15, Not Null)
* `image_url`, `thumbnail_url` (VARCHAR(500), Nullable)
* `visual_asset_type` (VARCHAR(50), Default: 'VEGETATIVE')
* `visual_theme_color` (VARCHAR(20), Default: '#10b981')
* `recommended_activities` (JSON, Not Null)
* `recommended_inputs` (JSON, Not Null)
* `is_active`, `is_deleted`, `deleted_at`, `deleted_by`, `created_at`, `updated_at`, `created_by`, `updated_by`

#### `farm_crop_plans`
* `id` (UUID, PK)
* `farm_id` (UUID, FK -> `farms.id` ON DELETE RESTRICT)
* `crop_id` (UUID, FK -> `crops.id` ON DELETE RESTRICT)
* `season` (VARCHAR(50), Not Null) — `KHARIF`, `RABI`, `ZAID`, `SUMMER`, `YEAR_ROUND`
* `planned_start_date` (DATE, Not Null)
* `planned_end_date` (DATE, Nullable)
* `planned_area` (NUMERIC(10, 2), Not Null, Check > 0)
* `land_area_unit` (VARCHAR(30), Not Null)
* `notes` (TEXT, Nullable)
* `is_active`, `is_deleted`, `deleted_at`, `deleted_by`, `created_at`, `updated_at`, `created_by`, `updated_by`
* *Constraint:* Unique(`farm_id`, `crop_id`, `season`) where `is_deleted = false AND is_active = true`

---

### 2.4 Cultivation Lifecycle & Stage Accounting Layer

#### `cultivation_runs`
* `id` (UUID, PK)
* `farm_crop_plan_id` (UUID, FK -> `farm_crop_plans.id` ON DELETE CASCADE)
* `farmer_profile_id` (UUID, FK -> `farmer_profiles.id` ON DELETE CASCADE)
* `sowing_date` (DATE, Not Null)
* `maturity_days` (INTEGER, Default: 90, Not Null)
* `target_harvest_date` (DATE, Not Null)
* `current_stage_order` (INTEGER, Default: 1, Not Null)
* `farming_method` (VARCHAR(50), Default: 'CONVENTIONAL')
* `season_year` (VARCHAR(50), Nullable)
* `land_area` (NUMERIC(8, 2), Nullable)
* `land_area_unit` (VARCHAR(20), Default: 'ACRE')
* `yield_quantity` (NUMERIC(10, 2), Nullable)
* `yield_unit` (VARCHAR(50), Nullable)
* `selling_price_per_unit` (NUMERIC(10, 2), Nullable)
* `gross_revenue` (NUMERIC(12, 2), Nullable)
* `is_active`, `is_deleted`, `deleted_at`, `deleted_by`, `created_at`, `updated_at`, `created_by`, `updated_by`

#### `cultivation_stages` (Active Instances per Run)
* `id` (UUID, PK)
* `cultivation_id` (UUID, FK -> `cultivation_runs.id` ON DELETE CASCADE)
* `stage_order` (INTEGER, Not Null)
* `stage_name` (VARCHAR(200), Not Null)
* `farming_type` (VARCHAR(50), Default: 'CONVENTIONAL')
* `status` (VARCHAR(50), Default: 'PENDING') — `PENDING`, `IN_PROGRESS`, `COMPLETED`, `SKIPPED`
* `start_date` (DATE, Nullable)
* `completed_date` (DATE, Nullable)
* `is_deleted`, `created_at`, `updated_at`, `created_by`, `updated_by`

#### `stage_worker_logs`
* `id` (UUID, PK)
* `stage_id` (UUID, FK -> `cultivation_stages.id` ON DELETE CASCADE)
* `cultivation_id` (UUID, FK -> `cultivation_runs.id` ON DELETE CASCADE)
* `worker_name` (VARCHAR(150), Not Null)
* `worker_id` (UUID, FK -> `users.id` ON DELETE SET NULL, Nullable)
* `days_worked` (NUMERIC(6, 1), Not Null)
* `daily_wage` (NUMERIC(10, 2), Not Null)
* `total_wage` (NUMERIC(12, 2), Not Null)
* `payment_status` (VARCHAR(30), Default: 'PENDING') — `PAID`, `PENDING`
* `notes` (TEXT, Nullable)
* `is_deleted`, `deleted_at`, `deleted_by`, `created_at`, `updated_at`, `created_by`, `updated_by`

#### `stage_expenses`
* `id` (UUID, PK)
* `stage_id` (UUID, FK -> `cultivation_stages.id` ON DELETE CASCADE)
* `cultivation_id` (UUID, FK -> `cultivation_runs.id` ON DELETE CASCADE)
* `expense_category` (VARCHAR(50), Not Null) — `SEEDS`, `FERTILIZERS`, `PESTICIDES`, `LABOR`, `MACHINERY`, `IRRIGATION`, `TRANSPORT`, `OTHER`
* `title` (VARCHAR(255), Not Null)
* `amount` (NUMERIC(12, 2), Not Null)
* `payment_mode` (VARCHAR(50), Default: 'CASH') — `CASH`, `UPI`, `BANK_TRANSFER`, `CREDIT`
* `worker_count` (INTEGER, Nullable)
* `per_head_wage` (NUMERIC(10, 2), Nullable)
* `quantity_desc` (VARCHAR(200), Nullable)
* `machinery_type` (VARCHAR(50), Nullable)
* `bill_image_url` (VARCHAR(500), Nullable)
* `notes` (TEXT, Nullable)
* `is_deleted`, `deleted_at`, `deleted_by`, `created_at`, `updated_at`, `created_by`, `updated_by`

---

### 2.5 Input Master, Suppliers & Procurement Layer

#### `input_masters`
* `id` (UUID, PK)
* `input_code` (VARCHAR(50), Unique, Not Null)
* `input_name` (VARCHAR(150), Not Null)
* `category` (VARCHAR(50), Not Null) — `SEEDS`, `FERTILIZERS`, `PESTICIDES`, `BIO_INPUTS`, `EQUIPMENT`, `IRRIGATION`
* `unit` (VARCHAR(30), Not Null) — `KG`, `LITRE`, `BAG`, `PACKET`, `TONNE`, `PIECE`
* `technical_name`, `brand_name`, `description`
* `is_active`, `is_deleted`, `deleted_at`, `deleted_by`, `created_at`, `updated_at`, `created_by`, `updated_by`

#### `suppliers`
* `id` (UUID, PK)
* `supplier_code` (VARCHAR(50), Unique, Not Null)
* `supplier_name` (VARCHAR(150), Not Null)
* `contact_person`, `phone_number`, `email`, `address_line1`, `address_line2`, `village_city`, `district`, `state`, `pincode`, `gstin`
* `supplier_type` (VARCHAR(50), Default: 'DISTRIBUTOR')
* `is_active`, `is_deleted`, `deleted_at`, `deleted_by`, `created_at`, `updated_at`, `created_by`, `updated_by`

#### `procurement_requests`
* `id` (UUID, PK)
* `request_code` (VARCHAR(50), Unique, Not Null)
* `farmer_profile_id` (UUID, FK -> `farmer_profiles.id` ON DELETE CASCADE)
* `farm_id` (UUID, FK -> `farms.id` ON DELETE CASCADE)
* `input_id` (UUID, FK -> `input_masters.id` ON DELETE RESTRICT)
* `preferred_supplier_id` (UUID, FK -> `suppliers.id` ON DELETE SET NULL, Nullable)
* `quantity` (NUMERIC(12, 2), Not Null)
* `unit` (VARCHAR(30), Not Null)
* `required_date` (DATE, Not Null)
* `status` (VARCHAR(30), Default: 'PENDING') — `PENDING`, `APPROVED`, `DISPATCHED`, `DELIVERED`, `CANCELLED`
* `is_deleted`, `deleted_at`, `deleted_by`, `created_at`, `updated_at`, `created_by`, `updated_by`

---

## 3. Alembic Migration History
1. `0001_initial_schema`: Roles, Users, UserRoles tables.
2. `0002_refresh_tokens`: RefreshTokens table with revocation & rotation tracking.
3. `0003_role_profiles`: FarmerProfiles, TraderProfiles, DriverProfiles, WorkerProfiles tables.
4. `0004_farms`: Farms table with parcel area and GPS location.
5. `0005_crops_and_plans`: Crops master and FarmCropPlans tables.
6. `0006_inputs_suppliers_procurements`: InputMasters, Suppliers, ProcurementRequests tables.
7. `0007_crop_cultivation_stages`: Master Crop Cultivation Stages table with agronomic JSON metadata.
