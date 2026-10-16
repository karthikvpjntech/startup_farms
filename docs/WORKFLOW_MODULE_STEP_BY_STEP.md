# Agri-Smart Ecosystem — Module-Based Workflow & Step-by-Step Endpoints Guide

> **Production Architectural Document**  
> **Backend Framework:** FastAPI 0.115+ (Python 3.12, SQLAlchemy 2.0, PostgreSQL 16)  
> **Frontend Stack:** Next.js 15 (React 19, TypeScript, Tailwind CSS, TanStack Query)  
> **Security Standards:** Argon2id Password Hashing, RS256 Dual-Token JWT, HttpOnly Cookies, Cryptographic HMAC-SHA256 Signatures

---

## 📑 Table of Contents

- [PART I: Module-Based Step-by-Step Business Workflows](#part-i-module-based-step-by-step-business-workflows)
  - [Module 1: Authentication, 2FA & Session Lifecycle](#module-1-authentication-2fa--session-lifecycle)
  - [Module 2: User Governance, Multi-Persona Roles & Profiles](#module-2-user-governance-multi-persona-roles--profiles)
  - [Module 3: Farm Parcel & Physical Land Management](#module-3-farm-parcel--physical-land-management)
  - [Module 4: Central Crop Agronomy Master & Sequential Stage Templates](#module-4-central-crop-agronomy-master--sequential-stage-templates)
  - [Module 5: Farm Crop Seasonal Planning & Parcel Allocation](#module-5-farm-crop-seasonal-planning--parcel-allocation)
  - [Module 6: Pre-Activity Planning & Agricultural Budget Estimations](#module-6-pre-activity-planning--agricultural-budget-estimations)
  - [Module 7: Precision Crop Cultivation Lifecycle & Dynamic 8-Stage Execution](#module-7-precision-crop-cultivation-lifecycle--dynamic-8-stage-execution)
  - [Module 8: Workforce Management, Worker Master, Daily Attendance & Wages](#module-8-workforce-management-worker-master-daily-attendance--wages)
  - [Module 9: Agricultural Machinery Master, Fuel & Hourly Usage Tracking](#module-9-agricultural-machinery-master-fuel--hourly-usage-tracking)
  - [Module 10: Input Master Catalog, Verified Suppliers & Procurement Requisitions](#module-10-input-master-catalog-verified-suppliers--procurement-requisitions)
  - [Module 11: Consolidated Operations Billing, Invoicing & Multi-Channel Payments](#module-11-consolidated-operations-billing-invoicing--multi-channel-payments)
  - [Module 12: Smart Tool Demand Geofencing Radar & Google Places Proximity Alerts](#module-12-smart-tool-demand-geofencing-radar--google-places-proximity-alerts)
  - [Module 13: Central Livestock Master Data (Categories & Breeds)](#module-13-central-livestock-master-data-categories--breeds)
  - [Module 14: Farmer Livestock Listing & Herd Management](#module-14-farmer-livestock-listing--herd-management)
  - [Module 15: Farmer Harvest Produce & Farm Products Listing Management](#module-15-farmer-harvest-produce--farm-products-listing-management)
  - [Module 16: Public Marketplace Discovery, Geospatial Filters & Buyer Catalog](#module-16-public-marketplace-discovery-geospatial-filters--buyer-catalog)
  - [Module 17: Customer Shopping Cart & Instant Buy-Now Processing](#module-17-customer-shopping-cart--instant-buy-now-processing)
  - [Module 18: Order Management, Concurrency-Safe Stock Deduction & State Machine](#module-18-order-management-concurrency-safe-stock-deduction--state-machine)
  - [Module 19: Razorpay Payment Gateway Integration, Escrow & Webhook Event Reconciliation](#module-19-razorpay-payment-gateway-integration-escrow--webhook-event-reconciliation)
  - [Module 20: Farmer Order Fulfillment, Packaging & Farm Gate Dispatch](#module-20-farmer-order-fulfillment-packaging--farm-gate-dispatch)
  - [Module 21: Logistics Fleet, Driver Pickup, QR/Barcode Scanning & Milestone Tracking](#module-21-logistics-fleet-driver-pickup-qrbarcode-scanning--milestone-tracking)
  - [Module 22: Mandi Bulk Produce Procurement, Harvest Alerts & Subscriptions](#module-22-mandi-bulk-produce-procurement-harvest-alerts--subscriptions)
  - [Module 23: Data Gate Subscriptions, Platform Monetization & Historical Passes](#module-23-data-gate-subscriptions-platform-monetization--historical-passes)
  - [Module 24: Platform Audit, Soft-Delete Recovery Vault (Trash Bin) & Super Admin Control Panel](#module-24-platform-audit-soft-delete-recovery-vault-trash-bin--super-admin-control-panel)
  - [Module 25: Media Storage, File Uploads & Public Asset Delivery](#module-25-media-storage-file-uploads--public-asset-delivery)
- [PART II: Step-by-Step REST Endpoints Specification](#part-ii-step-by-step-rest-endpoints-specification)
  - [Section 1: Authentication & 2FA Security Endpoints](#section-1-authentication--2fa-security-endpoints)
  - [Section 2: RBAC & Multi-Persona Profile Endpoints](#section-2-rbac--multi-persona-profile-endpoints)
  - [Section 3: Farm Parcel Management Endpoints](#section-3-farm-parcel-management-endpoints)
  - [Section 4: Crop Master & Stage Template Endpoints](#section-4-crop-master--stage-template-endpoints)
  - [Section 5: Farm Crop Planning Endpoints](#section-5-farm-crop-planning-endpoints)
  - [Section 6: Pre-Activity Planning & Requirements Endpoints](#section-6-pre-activity-planning--requirements-endpoints)
  - [Section 7: Cultivation Lifecycle, Dynamic Stages & Daily Logs Endpoints](#section-7-cultivation-lifecycle-dynamic-stages--daily-logs-endpoints)
  - [Section 8: Farmer CRM — Labor, Machinery & Operations Endpoints](#section-8-farmer-crm--labor-machinery--operations-endpoints)
  - [Section 9: Input Catalog, Suppliers & Procurement Requisition Endpoints](#section-9-input-catalog-suppliers--procurement-requisition-endpoints)
  - [Section 10: Billing, Invoicing & Payment Settlement Endpoints](#section-10-billing-invoicing--payment-settlement-endpoints)
  - [Section 11: Tool Demand Geofencing Radar & Proximity Discovery Endpoints](#section-11-tool-demand-geofencing-radar--proximity-discovery-endpoints)
  - [Section 12: Livestock Master & Farmer Livestock Endpoints](#section-12-livestock-master--farmer-livestock-endpoints)
  - [Section 13: Farm Produce & Selling Products Endpoints](#section-13-farm-produce--selling-products-endpoints)
  - [Section 14: Customer Cart, Checkout & Marketplace Order Endpoints](#section-14-customer-cart-checkout--marketplace-order-endpoints)
  - [Section 15: Razorpay Payment & Webhook Processing Endpoints](#section-15-razorpay-payment--webhook-processing-endpoints)
  - [Section 16: Logistics, Driver Scanning, Pickup & Tracking Endpoints](#section-16-logistics-driver-scanning-pickup--tracking-endpoints)
  - [Section 17: Produce Procurement & Harvest Broadcast Alert Endpoints](#section-17-produce-procurement--harvest-broadcast-alert-endpoints)
  - [Section 18: Data Gate Subscriptions & Admin Pass Endpoints](#section-18-data-gate-subscriptions--admin-pass-endpoints)
  - [Section 19: Super Admin Governance, Metrics & Trash Bin Vault Endpoints](#section-19-super-admin-governance-metrics--trash-bin-vault-endpoints)
  - [Section 20: Media & File Upload Endpoints](#section-20-media--file-upload-endpoints)

---

# PART I: Module-Based Step-by-Step Business Workflows

---

### Module 1: Authentication, 2FA & Session Lifecycle

#### 1. Overview & Actors
- **Actors:** Unauthenticated Guest, Registered Customer, Farmer, Trader, Driver, Worker, Super Admin.
- **Goal:** Provide military-grade authentication with dual-token architecture (15-min RS256 JWT access token + 7-day HttpOnly refresh cookie), optional TOTP/SMS Two-Factor Authentication, and passwordless OTP login.

#### 2. Preconditions & Triggers
- Guest visits the platform via Web (`/login`, `/register`) or Mobile interface.
- Guest submits mobile number, email, or credentials.

#### 3. Step-by-Step Workflow
1. **User Registration:**
   - User submits `full_name`, unique `mobile_number`, optional `email`, `password`, and requested role (`CUSTOMER`, `FARMER`, `TRADER`, `DRIVER`, `WORKER`).
   - Backend hashes password with Argon2id ($m=65536, t=3, p=4$).
   - A row is inserted into `users` and `user_roles`. If role is specific, corresponding profile shell (`farmer_profiles`, `trader_profiles`, etc.) is auto-provisioned.
   - Access token is returned; refresh token is set into secure HttpOnly cookie.
2. **Standard Credential Login:**
   - User submits mobile or email with password.
   - Argon2id hash is verified against database.
   - If user has 2FA enabled, backend generates a temporary 5-minute session token, sends a 6-digit OTP via SMS/email, and returns `requires_2fa: true`.
   - User inputs the 6-digit OTP. On verification, full credentials (RS256 JWT + refresh cookie) are issued.
3. **Passwordless OTP Login:**
   - User enters mobile number or email requesting sign-in code.
   - Backend generates a cryptographic 6-digit code with 10-minute expiry and dispatches it via SMS/email.
   - User submits OTP code. Backend verifies code, issues active session tokens, and marks phone/email as verified.
4. **Token Refresh Rotation:**
   - On expiration of the 15-minute access token, client's Axios/Fetch interceptor intercepts HTTP 401 and calls token refresh.
   - Backend reads HttpOnly cookie, verifies token hash in `refresh_tokens`, revokes the old token, and issues a freshly signed access token along with a rotated refresh cookie.
5. **Secure Logout:**
   - User initiates logout. Backend invalidates the refresh token record in the database and instructs the browser to delete the cookie with an expired `max_age=0`.

---

### Module 2: User Governance, Multi-Persona Roles & Profiles

#### 1. Overview & Actors
- **Actors:** Super Admin, All Registered Personas.
- **Goal:** Enforce strict Role-Based Access Control (RBAC) across 6 roles (`SUPER_ADMIN`, `FARMER`, `TRADER`, `DRIVER`, `WORKER`, `CUSTOMER`) and manage multi-persona profile data (KYC, APMC license, vehicle license, labor skills).

#### 2. Step-by-Step Workflow
1. **Role Identification & Onboarding:**
   - Upon initial sign-in, user's roles are hydrated via `/api/v1/auth/me`.
   - The frontend routes the user to their persona dashboard (`/farmer`, `/admin`, `/driver`, `/trader`, `/worker`, `/marketplace`).
2. **Profile Completion:**
   - **Farmer Profile:** Farmer fills land survey records, state, district, taluk, village, and preferred farming paradigm (Conventional vs Organic).
   - **Trader Profile:** Trader uploads GSTIN, business trade name, APMC license code, and mandi commodities.
   - **Driver Profile:** Driver provides driving license number, vehicle type (Mini Truck, Tractor, Pickup Van, Three-Wheeler), and payload capacity in metric tonnes.
   - **Worker Profile:** Laborer sets primary agrarian skills (Transplanting, De-weeding, Tractor Driving, Spraying), daily wage expectations, and availability flag.
3. **Admin User Governance:**
   - Super Admin can list all users, filter by active roles, suspend/activate user accounts, reset passwords, or assign secondary roles.

---

### Module 3: Farm Parcel & Physical Land Management

#### 1. Overview & Actors
- **Actors:** Farmer, Super Admin.
- **Goal:** Create and manage physical land parcels (farms) with exact acreages, soil classification, irrigation infrastructure, GPS coordinates, and sequential farm codes (`FARM-000001`).

#### 2. Step-by-Step Workflow
1. **Farm Parcel Registration:**
   - Farmer initiates "Add Farm Parcel" in `/farmer/farms`.
   - Farmer enters `farm_name`, `total_area`, `area_unit` (`ACRE` / `CENT` / `HECTARE`), `survey_number`, `soil_type` (`RED_LOAM`, `CLAY`, `BLACK_COTTON`, `ALLUVIAL`), `irrigation_source` (`BOREWELL`, `CANAL`, `DRIP`, `RAIN_FED`), and location details.
   - Backend generates an immutable sequential code: `FARM-000001`.
2. **Land Parcel Maintenance:**
   - Farmer updates farm parameters (boundary polygons, soil health reports, ownership type: `OWNED` vs `LEASED`).
   - Inactive farms can be toggled without data deletion.
3. **Soft Deletion & Recovery:**
   - If a farm parcel is deleted, it is marked `is_deleted = true` and moved to the Super Admin Trash Vault. All historical cultivation runs linked to this farm remain preserved.

---

### Module 4: Central Crop Agronomy Master & Sequential Stage Templates

#### 1. Overview & Actors
- **Actors:** Super Admin (Catalog Creator), Farmers (Catalog Consumers).
- **Goal:** Maintain central agricultural crop agronomy data (Tamil & English vernacular names, scientific classifications, seasonality, optimal soil pH) and predefined sequential crop stage templates.

#### 2. Step-by-Step Workflow
1. **Master Crop Provisioning:**
   - Super Admin registers agricultural crops (e.g., Tomato / தக்காளி, Paddy / நெல், Banana / வாழை, Coconut / தென்னை, Turmeric / மஞ்சள்).
   - Classifies crop category (`VEGETABLE`, `CEREAL_GRAIN`, `PULSE`, `COMMERCIAL`, `SPICE`, `FRUIT`).
2. **Cultivation Process Stage Sequencing:**
   - Super Admin configures default sequential cultivation stages for the crop (e.g. Stage 1: Seed Selection $\rightarrow$ Stage 2: Nursery $\rightarrow$ Stage 3: Transplanting $\rightarrow$ Stage 4: Vegetative $\rightarrow$ Stage 5: Flowering $\rightarrow$ Stage 6: Maturity $\rightarrow$ Stage 7: Harvest $\rightarrow$ Stage 8: Grading & Storage).
   - Each stage template defines `order_index`, standard duration days, recommended agricultural tips, and activities in JSON format.
3. **Public Catalog Access:**
   - Farmers access this master catalog with zero modification permissions to view best agronomic practices and duration estimates.

---

### Module 5: Farm Crop Seasonal Planning & Parcel Allocation

#### 1. Overview & Actors
- **Actors:** Farmer.
- **Goal:** Formulate pre-season crop plans allocating specific acreage on a farm parcel, choosing farming methodology (`ORGANIC` vs `CONVENTIONAL`), and estimating planned sowing/harvest schedules and target yields.

#### 2. Step-by-Step Workflow
1. **Plan Formulation:**
   - Farmer navigates to `/farmer/crop-plans` and selects target Farm Parcel and Master Crop.
   - Specifies `planned_area` (must not exceed farm parcel available acreage), `season` (`KHARIF`, `RABI`, `ZAID`), `sowing_window_start`, `sowing_window_end`, and `farming_type` (`ORGANIC` / `CONVENTIONAL`).
2. **Cost & Yield Projections:**
   - Farmer enters expected production costs and target harvest yields.
   - Plan is saved in status `PLANNED`.
3. **Conversion to Live Cultivation:**
   - When field work begins, the farmer converts the crop plan into a live **Cultivation Run**. The plan status advances to `ACTIVE`.

---

### Module 6: Pre-Activity Planning & Agricultural Budget Estimations

#### 1. Overview & Actors
- **Actors:** Farmer.
- **Goal:** Plan, budget, and estimate material, machine, and labor requirements *before* physically starting heavy stage operations (e.g. soil testing, land leveling, solar fencing, borewell drilling).

#### 2. Step-by-Step Workflow
1. **Requirement Formulation:**
   - Farmer opens stage planning view and adds a Pre-Activity Plan linked to the cultivation stage.
   - Enters activity purpose (e.g. "Deep chisel ploughing & farmyard manure incorporation"), planned target date, and estimated budget.
2. **Itemized Resource Allocation:**
   - Adds planned machinery (e.g. Tractor 45HP with 2-bottom MB Plough - 6 hours @ ₹900/hr = ₹5,400).
   - Adds planned materials (e.g. 5 tons well-decomposed FYM @ ₹1,500/ton = ₹7,500).
   - Adds planned labor (e.g. 4 laborers @ ₹450/day = ₹1,800).
3. **One-Tap Conversion to Actuals:**
   - Once field execution finishes, farmer clicks "Convert to Actuals".
   - The system automatically creates actual `WorkerAttendance`, `MachineUsage`, and `MaterialPurchase` records, marking the pre-activity plan status as `CONVERTED`.

---

### Module 7: Precision Crop Cultivation Lifecycle & Dynamic 8-Stage Execution

#### 1. Overview & Actors
- **Actors:** Farmer.
- **Goal:** Guide the farmer through the real cultivation cycle, auto-generating sequential process stages, tracking daily field activities, photo verification, and recording final harvest yields.

#### 2. Step-by-Step Workflow
1. **Initiate Cultivation Run:**
   - Farmer starts cultivation run linked to a crop plan.
   - Backend creates `cultivation_runs` record and automatically clones the Master Crop's sequential stage templates into live `cultivation_stages` records.
   - Stage 1 is marked `IN_PROGRESS`; subsequent stages are initialized as `PENDING`.
2. **Dynamic Stage Execution:**
   - In each active stage, farmer logs daily worker wages, machine rental hours, and input material purchases.
   - Farmer uploads geotagged stage photos via `/api/v1/media/upload`.
   - Farmer can add custom local stages (e.g. 'நில உழவு', 'பில்லு புடுங்குறது', 'மருந்து அடித்தல்') with custom order indexing.
3. **Complete & Advance Stage:**
   - Farmer clicks "Complete & Next Stage".
   - Backend marks current stage `COMPLETED`, records completion timestamp, and automatically promotes the next sequential stage to `IN_PROGRESS`.
4. **Harvest & Yield Recording:**
   - Upon completing the final stage, farmer records actual harvested yield (e.g. 450 Quintals / 12,000 KGs), grade quality, unit selling price, and total revenue earned.
   - Cultivation run transitions to `COMPLETED`.
5. **ROI & Comparative Analytics:**
   - System calculates total costs (Labor + Machine + Inputs + Logistics) vs Gross Revenue.
   - Farmer can view side-by-side comparative analytics comparing Organic vs Conventional ROI and profitability.

---

### Module 8: Workforce Management, Worker Master, Daily Attendance & Wages

#### 1. Overview & Actors
- **Actors:** Farmer, Farm Workers.
- **Goal:** Maintain farmer's roster of agricultural laborers, log daily hours and piece-rate work, calculate wage liabilities, and trigger instant SMS wage receipts upon payment.

#### 2. Step-by-Step Workflow
1. **Worker Registration:**
   - Farmer registers laborers in `/farmer/crm/workers` with name, mobile number, gender, skill specialization, and default daily wage rate (e.g. ₹450/day).
2. **Daily Attendance Logging:**
   - During stage operations, farmer logs attendance (individually or in bulk) specifying stage, date, hours worked (full day / half day), and task description (e.g. "Weeding in Tomato Plot B").
   - System computes: $\text{Total Wage} = \text{Days Worked} \times \text{Daily Wage Rate}$.
   - Wage record is created in status `PENDING`.
3. **Wage Settlement:**
   - Farmer pays worker via Cash or UPI.
   - Farmer marks wage status as `PAID`.
   - Backend triggers automated transactional SMS to the worker's mobile acknowledging receipt of wages.

---

### Module 9: Agricultural Machinery Master, Fuel & Hourly Usage Tracking

#### 1. Overview & Actors
- **Actors:** Farmer.
- **Goal:** Catalog farmer-owned and hired machinery (tractors, power tillers, rotavators, sprayers, harvesters), tracking operational hours, operator charges, and diesel fuel costs.

#### 2. Step-by-Step Workflow
1. **Machine Registration:**
   - Farmer catalogs equipment with machine name, registration number, ownership status (`OWNED` vs `RENTAL`), and default hourly rental rate.
2. **Logging Machine Hours:**
   - When equipment is used in a cultivation stage, farmer logs start/end hours, total hours operated, diesel liters consumed, fuel expense, and operator charges.
   - Total machinery cost is added to the stage's real-time financial ledger.
3. **Equipment Maintenance:**
   - Tracks total running hours across all crops for scheduled machinery servicing.

---

### Module 10: Input Master Catalog, Verified Suppliers & Procurement Requisitions

#### 1. Overview & Actors
- **Actors:** Farmer, Verified Input Suppliers, Super Admin.
- **Goal:** Provide verified agricultural inputs (certified seeds, fertilizers, bio-pesticides, organic compost), verified dealer directory, and formal farm procurement requisitions.

#### 2. Step-by-Step Workflow
1. **Catalog Exploration:**
   - Farmer browses central catalog of certified agro-inputs with technical NPK values, application dosages, and brand names.
2. **Supplier Directory:**
   - Farmer searches verified dealers in their district/taluk with physical addresses, contact numbers, and dealer ratings.
3. **Procurement Requisition:**
   - Farmer submits formal procurement requisition (`REQ-000001`) specifying required inputs, quantity, delivery deadline, and target farm parcel.
   - Status begins at `PENDING` $\rightarrow$ `APPROVED` $\rightarrow$ `FULFILLED`.
4. **Purchase Recording:**
   - Upon receiving inputs, farmer logs purchase invoice, batch number, expiry date, unit price, and linked supplier.

---

### Module 11: Consolidated Operations Billing, Invoicing & Multi-Channel Payments

#### 1. Overview & Actors
- **Actors:** Farmer, Suppliers, Workers.
- **Goal:** Automatically compile unbilled stage expenses (wages, machinery, materials) into consolidated invoices (`BIL-2026-0001`), supporting partial settlements, UPI QR codes, cash, and automated SMS alerts.

#### 2. Step-by-Step Workflow
1. **Consolidated Bill Generation:**
   - Farmer clicks "Generate Stage Bill" for a completed or ongoing stage.
   - Backend queries all unbilled worker wages, machine usage, and material purchases for that stage, compiling them into a unified invoice with an immutable bill number (`BIL-2026-0001`).
   - Bill status is set to `PENDING`.
2. **Manual Custom Bills:**
   - Farmer can create custom operational invoices for external contractors, fencing, irrigation parts, or transport with itemized lines.
3. **Payment Settlement:**
   - Farmer records payment transaction specifying amount, payment method (`UPI`, `CASH`, `NET_BANKING`, `CHEQUE`), and transaction reference.
   - System recalculates balance due:
     - If $\text{Balance} = 0$, bill transitions to `PAID`.
     - If $\text{Balance} > 0$, bill transitions to `PARTIALLY_PAID`.
   - Associated worker wage records are updated to `PAID`.
   - SMS notification is dispatched to payee.

---

### Module 12: Smart Tool Demand Geofencing Radar & Google Places Proximity Alerts

#### 1. Overview & Actors
- **Actors:** Farmer, Local Equipment Vendors, Mobile Background GPS.
- **Goal:** Enable farmers to register urgent machinery needs (e.g. "Tractor rental in Mysuru"), auto-discover nearby verified businesses via Google Places API, and trigger real-time in-app alerts when the farmer moves within 500 meters of a vendor.

#### 2. Step-by-Step Workflow
1. **Register Tool Demand:**
   - Farmer enters required tool/service (e.g., "Combine Harvester Rental"), location name (e.g., "Mandya"), radius (e.g., 25 km), and priority.
   - Status starts as `ACTIVE`.
2. **Automatic Google Places Discovery:**
   - Backend queries Google Places Text Search / Nearby Search API for matching agricultural machinery dealers, rental centers, and tractor dealerships.
   - System parses place name, address, phone number, rating, opening status, and GPS coordinates (latitude/longitude), storing them in `tool_discovered_locations`.
3. **Geofenced Radar & Proximity Checking:**
   - As the farmer travels with the app open, the client periodically sends current GPS coordinates to `/api/v1/farmer/tool-interests/check-proximity`.
   - Backend computes Haversine distance between current coordinates and all discovered vendors.
   - If distance $\le 500\text{ meters}$ (or configured threshold), backend returns matched vendor details and triggers a **🔔 Live In-App Notification**.
4. **Actionable Interaction:**
   - Farmer taps notification to view vendor phone number with one-tap dialing and one-tap Google Maps turn-by-turn navigation.

---

### Module 13: Central Livestock Master Data (Categories & Breeds)

#### 1. Overview & Actors
- **Actors:** Super Admin (Catalog Creator), Farmers & Buyers (Consumers).
- **Goal:** Standardize animal species, classifications, indigenous and exotic breeds (e.g., Kangayam Cattle, Tellicherry Goat, Kadaknath Chicken, Murrah Buffalo) with average weight and milk/egg yield statistics.

#### 2. Step-by-Step Workflow
1. **Category Provisioning:**
   - Super Admin creates animal categories (e.g., `COW`, `BUFFALO`, `GOAT`, `SHEEP`, `POULTRY_CHICKEN`, `HORSE`).
2. **Breed Cataloging:**
   - Admin attaches recognized breeds to categories with vernacular name, native geographic region, physical traits, and ideal rearing conditions.
3. **Master Catalog Consumption:**
   - Farmers select standardized categories and breeds when listing livestock on the marketplace, preventing misspelled or unindexed listings.

---

### Module 14: Farmer Livestock Listing & Herd Management

#### 1. Overview & Actors
- **Actors:** Farmer, Marketplace Buyers.
- **Goal:** Allow farmers to register live animals for sale, supporting individual pricing (e.g. Dairy Cow with pedigree) or batch/flock pricing (e.g. 50 Country Chickens @ ₹350/each), health records, vaccination proof, and photos.

#### 2. Step-by-Step Workflow
1. **Animal Listing Creation:**
   - Farmer submits livestock listing selecting category, breed, age in months, weight in KG, gender, lactation status, vaccination certificates, asking price, and photo gallery.
   - Selling model is specified: `INDIVIDUAL` (single tag number) or `QUANTITY` (batch size).
   - Status initialized to `ACTIVE`.
2. **Marketplace Discovery:**
   - Animals appear immediately on the public marketplace with proximity-based distances calculated from the buyer's location.
3. **Inventory State Tracking:**
   - If animal is purchased, status transitions to `RESERVED` $\rightarrow$ `SOLD`. If farmer removes listing, status becomes `INACTIVE`.

---

### Module 15: Farmer Harvest Produce & Farm Products Listing Management

#### 1. Overview & Actors
- **Actors:** Farmer, Retail Consumers, Wholesale Traders.
- **Goal:** Allow farmers to sell freshly harvested vegetables, fruits, coconuts, grains, pulses, and organic processed foods directly to buyers with inventory stock control.

#### 2. Step-by-Step Workflow
1. **Product Listing Creation:**
   - Farmer navigates to `/farmer/products` and clicks "List Fresh Produce".
   - Selects Category (`VEGETABLES`, `FRUITS`, `COCONUT`, `GRAINS_PADDY`, `OTHER`), enters product title, variety (e.g. "Alphonso Mango", "Aman Ponni Rice"), harvest date, available stock quantity, unit of measurement (`KG`, `PIECE`, `QUINTAL`), price per unit, and minimum order quantity.
   - Configures supported delivery methods (`DELIVERY`, `PICKUP`, or both).
   - Uploads high-resolution crate and produce photos.
2. **Live Stock Synchronisation:**
   - Farmer can perform quick stock adjustments via a lightweight slider/patch endpoint following consecutive pickings.
   - If stock reaches 0, system automatically flips listing status to `OUT_OF_STOCK`.

---

### Module 16: Public Marketplace Discovery, Geospatial Filters & Buyer Catalog

#### 1. Overview & Actors
- **Actors:** Public Guest, Registered Buyer, Local Mandi Trader.
- **Goal:** Provide high-speed, SEO-optimized public discovery of fresh produce and livestock with instant search, category filters, price ranges, and proximity radius filtering.

#### 2. Step-by-Step Workflow
1. **Catalog Browsing:**
   - Buyer visits `/marketplace` and searches for items (e.g. "Country Chicken", "Fresh Organic Tomato").
2. **Geospatial Distance Calculation:**
   - Buyer enables browser GPS location or enters district.
   - Backend calculates real-time distance in kilometers using the Haversine formula and sorts listings by proximity (`distance_asc`).
3. **Product Inspection:**
   - Buyer opens listing detail view displaying farmer profile, farm origin, verified harvest date, vaccination records, photo gallery, and verified customer reviews.

---

### Module 17: Customer Shopping Cart & Instant Buy-Now Processing

#### 1. Overview & Actors
- **Actors:** Registered Buyer.
- **Goal:** Provide persistent multi-item shopping cart and instant "Buy Now" single-click checkout with atomic stock verification.

#### 2. Step-by-Step Workflow
1. **Cart Accumulation:**
   - Buyer adds items to cart with desired quantities.
   - Backend enforces minimum order quantities and validates current stock availability.
2. **Cart Review & Modification:**
   - Buyer reviews cart items, updates quantities, or deletes items. Cart subtotal, delivery charges, and taxes are recalculated dynamically.
3. **Instant Buy-Now Option:**
   - For urgent purchases (e.g. live animals or single produce crate), buyer clicks "Buy Now" bypassing the cart for instant checkout.

---

### Module 18: Order Management, Concurrency-Safe Stock Deduction & State Machine

#### 1. Overview & Actors
- **Actors:** Buyer, Farmer, Database Transaction Manager.
- **Goal:** Create orders with atomic inventory locks (`SELECT FOR UPDATE`), preventing overselling, and manage the full order fulfillment state machine.

#### 2. Step-by-Step Workflow
1. **Atomic Checkout Execution:**
   - Buyer clicks "Proceed to Checkout" providing delivery address and payment choice (`ONLINE_PAYMENT`, `CASH_ON_DELIVERY`, or `FARM_PICKUP`).
   - Backend executes a database transaction acquiring an atomic lock (`with_for_update()`) on the inventory row.
   - Verifies `available_quantity >= requested_quantity`.
   - Decrements `available_quantity = available_quantity - ordered_quantity`. If remaining stock is 0, status is set to `OUT_OF_STOCK` or `SOLD`.
2. **Order Entity Instantiation:**
   - System creates `marketplace_orders` record with unique order number (`ORD-20261013-XXXX`).
   - Copies current unit price into immutable `marketplace_order_items` records (protecting against future seller price updates).
   - Generates initial `marketplace_deliveries` and `marketplace_payments` records in status `PENDING`.
3. **Order Lifecycle State Machine:**
   ```text
   PENDING (Checkout)
      │
      ├─→ CONFIRMED (Payment Verified / COD Selected)
      │      │
      │      ├─→ FARMER_ACCEPTED (Farmer confirms availability)
      │      │      │
      │      │      ├─→ PROCESSING (Harvesting, cleaning, weighing)
      │      │      │      │
      │      │      │      ├─→ READY_FOR_PICKUP (Packed at farm gate)
      │      │      │      │      │
      │      │      │      │      ├─→ OUT_FOR_DELIVERY (Driver en route)
      │      │      │      │      │      │
      │      │      │      │      │      └─→ DELIVERED (Delivery confirmed)
      │      │      │      │
      │      │      └─→ CANCELLED / REFUNDED (Stock restored)
      │      │
      │      └─→ FARMER_REJECTED (Stock restored & auto-refunded)
      │
      └─→ CANCELLED (Customer cancelled before confirmation)
   ```

---

### Module 19: Razorpay Payment Gateway Integration, Escrow & Webhook Event Reconciliation

#### 1. Overview & Actors
- **Actors:** Buyer, Razorpay Gateway, Agri-Smart Backend, Payment Webhook Worker.
- **Goal:** Secure digital payments (UPI, Cards, NetBanking) with escrow holding until delivery, and resilient webhook reconciliation.

#### 2. Step-by-Step Workflow
1. **Razorpay Order Creation:**
   - Client calls `/api/v1/marketplace/orders/{order_id}/create-razorpay-order`.
   - Backend contacts Razorpay API to create an order in paise ($\text{amount} \times 100$) with receipt identifier.
   - Returns `razorpay_order_id`, key ID, and payable amount to client.
2. **Client Checkout Modal:**
   - Next.js frontend launches standard Razorpay Checkout JS modal. Buyer completes payment via UPI (GPay/PhonePe/Paytm) or Card.
3. **Direct Signature Verification:**
   - On payment success, client sends `razorpay_payment_id`, `razorpay_order_id`, and `razorpay_signature` to `/verify-razorpay-payment`.
   - Backend calculates HMAC-SHA256 signature using `RAZORPAY_KEY_SECRET`. If valid, marks order payment status as `PAID` and order status as `CONFIRMED`.
4. **Asynchronous Webhook Reconciliation:**
   - If user closes browser before client verification completes, Razorpay sends server-to-server webhook to `/api/v1/payments/webhooks`.
   - Backend verifies `X-Razorpay-Signature` HMAC header, validates event idempotency via `webhook_logs`, and handles:
     - `payment.captured`: Sets payment and order to `PAID`.
     - `payment.failed`: Records error reason and notifies buyer.
     - `refund.processed`: Records refund reference.

---

### Module 20: Farmer Order Fulfillment, Packaging & Farm Gate Dispatch

#### 1. Overview & Actors
- **Actors:** Farmer.
- **Goal:** Enable farmers to view incoming customer orders, accept/reject, prepare produce crates, generate batch shipping labels with Barcode/QR codes, and request logistics transport pickups.

#### 2. Step-by-Step Workflow
1. **Incoming Order Notification:**
   - Farmer receives alert and navigates to `/farmer/products/orders/received` or `/farmer/livestock/orders/received`.
   - Reviews buyer delivery address, quantities ordered, and fulfillment deadline.
2. **Order Acceptance:**
   - Farmer clicks "Accept Order". Order transitions to `FARMER_ACCEPTED`.
3. **Produce Packaging & Weighing:**
   - Farmer harvests, grades, and packages produce into ventilated plastic crates or bags.
   - Farmer updates status to `PROCESSING` and then creates a **Shipment Package** specifying gross weight, crate dimensions, packaging type, and perishable flags.
4. **Barcode/QR Label Generation:**
   - System auto-generates tracking number (`TRK-XXXXXXXXXXXX`), package barcode (`PKG-XXXXXXXX`), and scannable QR code.
   - Farmer prints or displays QR label on the crate.
5. **Transport Pickup Scheduling:**
   - Farmer clicks "Request Transport Pickup", providing preferred farm gate pickup time window and gate access instructions.
   - Order transitions to `READY_FOR_PICKUP`.

---

### Module 21: Logistics Fleet, Driver Pickup, QR/Barcode Scanning & Milestone Tracking

#### 1. Overview & Actors
- **Actors:** Assigned Driver, Customer, Public Recipient.
- **Goal:** Seamless logistics delivery pipeline with universal barcode scanning, real-time status transitions, doorstep delivery confirmation, and public milestone tracking.

#### 2. Step-by-Step Workflow
1. **Driver Assignment & Pickup List:**
   - Super Admin or Logistics Dispatcher assigns pickup task to registered driver.
   - Driver opens driver app (`/driver/pickups`) to view assigned farm pickups.
2. **Universal QR/Barcode Scanning at Farm Gate:**
   - Driver arrives at the farm, opens camera scanner, and scans package barcode or QR code (`/api/v1/driver/shipments/scan/{code}`).
   - System instantly resolves the shipment and order details.
   - Driver taps "Confirm Pickup". Shipment status transitions to `PICKED_UP`; order status moves to `PROCESSING`.
3. **Transit Progression:**
   - Driver transports produce to hub or destination. Updates status to `IN_TRANSIT` $\rightarrow$ `OUT_FOR_DELIVERY`.
   - Real-time in-app alerts and SMS updates are sent to the customer.
4. **Public Tracking Milestone View:**
   - Anyone holding the tracking number can view the public tracking page (`/tracking/{tracking_number}`) displaying progress bar, pickup time, hub milestones, masked customer address, and expected delivery without requiring login.
5. **Doorstep Delivery Completion:**
   - Driver delivers produce crates to customer.
   - Driver records recipient name, notes, and taps "Confirm Delivery" (`/confirm-delivery`).
   - Shipment status transitions to `DELIVERED`; order status becomes `DELIVERED`.
   - If Cash on Delivery was selected, payment status updates to `PAID`.
   - SMS alert is sent to customer inviting verified review submission.

---

### Module 22: Mandi Bulk Produce Procurement, Harvest Alerts & Subscriptions

#### 1. Overview & Actors
- **Actors:** Mandi Trader, Bulk Institutional Buyer, Farmer.
- **Goal:** Facilitate wholesale B2B farm procurement requisitions (e.g. 100 Quintals of Paddy / நெல்), broadcast live harvest yield alerts, and allow buyers to subscribe for SMS/Email notifications.

#### 2. Step-by-Step Workflow
1. **Discover Available Farm Yields:**
   - Traders browse `/produce-procurement/available` to view upcoming and newly harvested crops by district, acreage, and estimated availability date.
2. **Harvest Alert Subscriptions:**
   - Buyers subscribe to automated notifications for specific crops (e.g. "Notify me via SMS and WhatsApp whenever Turmeric or Tomato yields are harvested in Erode district").
3. **Wholesale Procurement Requisition:**
   - Trader submits requisition specifying crop, required quantity, target delivery date, offered price per quintal, and destination mandi.
   - Target farmer receives notification to confirm or negotiate requisition.
4. **Fulfillment & Dispatch:**
   - Farmer accepts requisition, arranges bulk logistics dispatch, and updates delivery status.

---

### Module 23: Data Gate Subscriptions, Platform Monetization & Historical Passes

#### 1. Overview & Actors
- **Actors:** Trader, Commercial Farmer, Researcher, Super Admin.
- **Goal:** Monetize platform by gating historical price trends, multi-season yield analytics, and mandi market rate forecasts behind premium data passes (`MONTHLY`, `ANNUAL`).

#### 2. Step-by-Step Workflow
1. **Feature Gate Evaluation:**
   - When user attempts to inspect multi-season price forecasts or historical mandi comparison charts, frontend verifies access via `/api/v1/subscriptions/my-status`.
   - If user does not have active subscription, a premium feature paywall modal appears.
2. **Order Creation & Payment:**
   - User selects plan (`MONTHLY_PASS` or `ANNUAL_PASS`) and clicks "Subscribe Now".
   - Backend creates Razorpay order and returns payment parameters.
   - User completes payment; backend verifies HMAC signature, grants active subscription (`starts_at = NOW()`, `expires_at = NOW() + 30 days`), and unlocks historical data.
3. **Super Admin Controls:**
   - Super Admin can configure plan pricing, enable/disable data gating, or manually grant/revoke subscriber passes.

---

### Module 24: Platform Audit, Soft-Delete Recovery Vault (Trash Bin) & Super Admin Control Panel

#### 1. Overview & Actors
- **Actors:** Super Admin.
- **Goal:** Full administrative visibility across users, revenue metrics, orders, transport providers, and single-click recovery of soft-deleted records across all core tables.

#### 2. Step-by-Step Workflow
1. **Executive Dashboard Metrics:**
   - Super Admin views unified KPIs: total registered users, active farms, running crop cultivations, marketplace revenue, open dispatches, and system health status (`UP`).
2. **Audit Trash Bin Inspection:**
   - Admin navigates to `/admin/trash-bin`.
   - Vault lists all soft-deleted records across `USERS`, `FARMS`, `CROPS`, `CULTIVATION_RUNS`, `CULTIVATION_STAGES`, `WORKERS`, `MACHINES`, `BILLS`, `SUPPLIERS`.
3. **Single-Click Entity Restoration:**
   - Admin clicks "Restore" on any accidentally deleted entity.
   - Backend flips `is_deleted = false` and clears deleted audit metadata. Entity immediately reappears in all user queries.
4. **Guarded Permanent Purge:**
   - If entity must be permanently removed, admin executes hard deletion. Guard checks prevent deleting the last Super Admin or entities with active transactional order dependencies.

---

### Module 25: Media Storage, File Uploads & Public Asset Delivery

#### 1. Overview & Actors
- **Actors:** All Authenticated Users.
- **Goal:** Secure upload and static hosting of observation photos, receipt scans, crop diseases, and product gallery pictures.

#### 2. Step-by-Step Workflow
1. **Upload Request:**
   - Client sends multipart file upload (`image/jpeg`, `image/png`, `image/webp`) with maximum file size validation (10 MB).
2. **Disk Storage & Organization:**
   - File is given a secure UUID filename and stored under `uploads/stages/`, `uploads/crops/`, `uploads/profiles/`, or `uploads/general/`.
3. **URL Generation:**
   - Server returns accessible public URL path (e.g. `/uploads/stages/uuid-filename.jpg`) for immediate display and persistence in database models.

---

# PART II: Step-by-Step REST Endpoints Specification

---

## Section 1: Authentication & 2FA Security Endpoints

### 1.1 Register New User
- **Method & Path:** `POST /api/v1/auth/register`
- **Auth & Access:** Public (No Bearer token required)
- **Request Headers:** `Content-Type: application/json`
- **Request Body:**
```json
{
  "full_name": "Murugan Palanisamy",
  "mobile_number": "9876543210",
  "email": "murugan.farm@example.com",
  "password": "StrongPassword@123",
  "role": "FARMER"
}
```
- **Response Status:** `201 Created`
- **Response Body:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "requires_2fa": false,
  "user": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "full_name": "Murugan Palanisamy",
    "mobile_number": "9876543210",
    "email": "murugan.farm@example.com",
    "is_active": true,
    "roles": ["FARMER"]
  }
}
```
- **Side Effects & State Changes:**
  - Creates row in `users` table with Argon2id password hash.
  - Creates row in `user_roles` linking user to `FARMER`.
  - Auto-provisions empty `farmer_profiles` shell.
  - Sets secure `refresh_token` cookie (`HttpOnly; Secure; SameSite=Lax; Max-Age=604800; Path=/api/v1/auth`).

---

### 1.2 User Login
- **Method & Path:** `POST /api/v1/auth/login`
- **Auth & Access:** Public
- **Request Body:**
```json
{
  "username": "9876543210",
  "password": "StrongPassword@123"
}
```
- **Response Status:** `200 OK`
- **Response Body (Standard):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "requires_2fa": false,
  "user": {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "full_name": "Murugan Palanisamy",
    "mobile_number": "9876543210",
    "email": "murugan.farm@example.com",
    "is_active": true,
    "roles": ["FARMER"]
  }
}
```
- **Response Body (When 2FA Enabled):**
```json
{
  "access_token": "",
  "token_type": "bearer",
  "expires_in": 0,
  "requires_2fa": true,
  "two_factor_token": "2fa_session_token_xyz"
}
```
- **Side Effects:** Validates password, generates 15-minute access token, sets HttpOnly refresh cookie.

---

### 1.3 Verify 2FA OTP
- **Method & Path:** `POST /api/v1/auth/login/2fa-verify`
- **Auth & Access:** Public
- **Request Body:**
```json
{
  "two_factor_token": "2fa_session_token_xyz",
  "otp_code": "481920"
}
```
- **Response Status:** `200 OK` (Returns access token and sets refresh cookie).

---

### 1.4 Request Passwordless OTP Login
- **Method & Path:** `POST /api/v1/auth/login/otp-request`
- **Auth & Access:** Public
- **Request Body:**
```json
{
  "identifier": "9876543210",
  "channel": "SMS"
}
```
- **Response Status:** `200 OK`
- **Response Body:**
```json
{
  "session_token": "otp_sess_9a8b7c6d",
  "message": "6-digit OTP code dispatched to mobile number ending in 3210",
  "expires_in_seconds": 600
}
```

---

### 1.5 Verify Passwordless OTP Login
- **Method & Path:** `POST /api/v1/auth/login/otp-verify`
- **Auth & Access:** Public
- **Request Body:**
```json
{
  "session_token": "otp_sess_9a8b7c6d",
  "otp_code": "847291"
}
```
- **Response Status:** `200 OK` (Returns access token and sets refresh cookie).

---

### 1.6 Refresh Access Token
- **Method & Path:** `POST /api/v1/auth/refresh`
- **Auth & Access:** Public (Reads `refresh_token` from HttpOnly Cookie)
- **Response Status:** `200 OK`
- **Response Body:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```
- **Side Effects:** Rotates refresh token in database, invalidates old token, sets new cookie.

---

### 1.7 Current User Profile & Roles Hydration
- **Method & Path:** `GET /api/v1/auth/me`
- **Auth & Access:** Bearer JWT (All Roles)
- **Response Status:** `200 OK`
- **Response Body:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "full_name": "Murugan Palanisamy",
  "mobile_number": "9876543210",
  "email": "murugan.farm@example.com",
  "is_active": true,
  "roles": ["FARMER"]
}
```

---

### 1.8 Logout
- **Method & Path:** `POST /api/v1/auth/logout`
- **Auth & Access:** Public (Reads HttpOnly Cookie)
- **Response Status:** `200 OK`
- **Response Body:** `{"message": "Logged out successfully"}`
- **Side Effects:** Deletes token from `refresh_tokens`, sets cookie `max_age=0`.

---

## Section 2: RBAC & Multi-Persona Profile Endpoints

### 2.1 Get / Update Farmer Profile
- **Method & Path:** `GET /api/v1/profiles/farmer` and `PUT /api/v1/profiles/farmer`
- **Auth & Access:** Bearer JWT (`FARMER`)
- **PUT Request Body:**
```json
{
  "farm_name": "Palanisamy Bio Farms",
  "state": "Tamil Nadu",
  "district": "Coimbatore",
  "taluk": "Pollachi",
  "village": "Anaimalai",
  "pincode": "642104",
  "primary_farming_type": "ORGANIC",
  "total_experience_years": 14
}
```
- **Response Status:** `200 OK`

---

### 2.2 Get / Update Trader Profile
- **Method & Path:** `GET /api/v1/profiles/trader` and `PUT /api/v1/profiles/trader`
- **Auth & Access:** Bearer JWT (`TRADER`)
- **PUT Request Body:**
```json
{
  "business_name": "Kongu Agro Mandi Traders",
  "gst_number": "33AAAAA0000A1Z5",
  "apmc_license_number": "APMC-TN-2024-8891",
  "trading_categories": ["VEGETABLES", "GRAINS_PADDY"]
}
```
- **Response Status:** `200 OK`

---

### 2.3 Get / Update Driver Profile
- **Method & Path:** `GET /api/v1/profiles/driver` and `PUT /api/v1/profiles/driver`
- **Auth & Access:** Bearer JWT (`DRIVER`)
- **PUT Request Body:**
```json
{
  "driving_license_no": "TN-38-2018-0099412",
  "vehicle_type": "MINI_TRUCK",
  "vehicle_registration_number": "TN-38-BZ-4412",
  "payload_capacity_kg": 2500,
  "service_districts": ["Coimbatore", "Tiruppur", "Erode"]
}
```
- **Response Status:** `200 OK`

---

### 2.4 Get / Update Worker Profile
- **Method & Path:** `GET /api/v1/profiles/worker` and `PUT /api/v1/profiles/worker`
- **Auth & Access:** Bearer JWT (`WORKER`)
- **PUT Request Body:**
```json
{
  "skill_primary": "Paddy Transplanting & De-weeding",
  "daily_wage_rate": 450.00,
  "is_available": true
}
```
- **Response Status:** `200 OK`

---

## Section 3: Farm Parcel Management Endpoints

### 3.1 Register New Farm Parcel
- **Method & Path:** `POST /api/v1/farms`
- **Auth & Access:** Bearer JWT (`FARMER`)
- **Request Body:**
```json
{
  "farm_name": "Pollachi Coconut & Veggie Grove",
  "total_area": 5.5,
  "area_unit": "ACRE",
  "survey_number": "342/1B",
  "ownership_type": "OWNED",
  "soil_type": "RED_LOAM",
  "irrigation_source": "DRIP",
  "state": "Tamil Nadu",
  "district": "Coimbatore",
  "taluk": "Pollachi",
  "village": "Zamin Uthukuli",
  "pincode": "642004",
  "latitude": 10.6609,
  "longitude": 77.0048
}
```
- **Response Status:** `201 Created`
- **Response Body:**
```json
{
  "id": "9f8e7d6c-5b4a-3f2e-1d0c-9b8a7f6e5d4c",
  "farm_code": "FARM-000001",
  "farm_name": "Pollachi Coconut & Veggie Grove",
  "total_area": 5.5,
  "area_unit": "ACRE",
  "is_active": true,
  "created_at": "2026-10-13T10:00:00Z"
}
```

---

### 3.2 List Farmer Farms
- **Method & Path:** `GET /api/v1/farms`
- **Query Parameters:** `page=1&page_size=20&search=Pollachi&is_active=true`
- **Auth & Access:** Bearer JWT (`FARMER`, `SUPER_ADMIN`)
- **Response Status:** `200 OK`

---

### 3.3 Get Farm Detail / Update / Soft Delete
- `GET /api/v1/farms/{farm_id}` $\rightarrow$ Returns complete farm parcel data.
- `PATCH /api/v1/farms/{farm_id}` $\rightarrow$ Updates farm name, acreage, or coordinates.
- `PATCH /api/v1/farms/{farm_id}/status` $\rightarrow$ Toggles active/inactive state.
- `DELETE /api/v1/farms/{farm_id}` $\rightarrow$ Soft-deletes farm (`is_deleted=true`).
- `POST /api/v1/farms/{farm_id}/restore` $\rightarrow$ Restores farm back to active status.

---

## Section 4: Crop Master & Stage Template Endpoints

### 4.1 List Public Agricultural Crops
- **Method & Path:** `GET /api/v1/crops`
- **Query Parameters:** `category=VEGETABLE&season=KHARIF&search=Tomato`
- **Auth & Access:** Bearer JWT (All Roles)
- **Response Status:** `200 OK`
- **Response Body:**
```json
[
  {
    "id": "e4b1a2c3-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
    "name": "Tomato",
    "vernacular_name": "தக்காளி",
    "scientific_name": "Solanum lycopersicum",
    "category": "VEGETABLE",
    "duration_days": 115,
    "stages_count": 8
  }
]
```

---

### 4.2 Get Master Crop Process Stages
- **Method & Path:** `GET /api/v1/crops/{crop_id}/stages`
- **Auth & Access:** Bearer JWT (All Roles)
- **Response Status:** `200 OK`
- **Response Body:**
```json
[
  {
    "id": "11111111-2222-3333-4444-555555555555",
    "stage_name": "Seed Selection & Priming",
    "order_index": 1,
    "duration_days": 6,
    "archetype": "SEED",
    "tips": "Use high-germination hybrid seeds treated with Trichoderma bio-coating."
  },
  {
    "id": "22222222-3333-4444-5555-666666666666",
    "stage_name": "Nursery Bed Raising",
    "order_index": 2,
    "duration_days": 25,
    "archetype": "NURSERY",
    "tips": "Prepare raised beds under shade net with micro-sprinklers."
  }
]
```

---

### 4.3 Super Admin Crop & Stage Master CRUD
- `POST /api/v1/admin/crops` $\rightarrow$ Creates master crop.
- `PATCH /api/v1/admin/crops/{crop_id}` $\rightarrow$ Modifies crop agronomy.
- `DELETE /api/v1/admin/crops/{crop_id}` $\rightarrow$ Soft-deletes crop.
- `POST /api/v1/admin/crops/{crop_id}/stages` $\rightarrow$ Creates sequential stage template.
- `PATCH /api/v1/admin/stages/{stage_id}` $\rightarrow$ Updates duration and tips.
- `DELETE /api/v1/admin/stages/{stage_id}` $\rightarrow$ Deletes stage template.

---

## Section 5: Farm Crop Planning Endpoints

### 5.1 Create Farm Crop Plan
- **Method & Path:** `POST /api/v1/farm-crop-plans`
- **Auth & Access:** Bearer JWT (`FARMER`)
- **Request Body:**
```json
{
  "farm_id": "9f8e7d6c-5b4a-3f2e-1d0c-9b8a7f6e5d4c",
  "crop_id": "e4b1a2c3-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "plan_name": "Kharif 2026 Tomato Plan",
  "allocated_area": 2.0,
  "area_unit": "ACRE",
  "season": "KHARIF",
  "farming_type": "CONVENTIONAL",
  "planned_sowing_date": "2026-10-20",
  "estimated_cost": 45000.00,
  "target_yield_kg": 12000.00
}
```
- **Response Status:** `201 Created`

---

### 5.2 List & Manage Crop Plans
- `GET /api/v1/farm-crop-plans` $\rightarrow$ Lists seasonal plans with projected costs.
- `GET /api/v1/farm-crop-plans/{plan_id}` $\rightarrow$ Retrieves single plan details.
- `PATCH /api/v1/farm-crop-plans/{plan_id}` $\rightarrow$ Adjusts allocated acreage or sowing dates.
- `DELETE /api/v1/farm-crop-plans/{plan_id}` $\rightarrow$ Soft-deletes plan.

---

## Section 6: Pre-Activity Planning & Requirements Endpoints

### 6.1 Create Pre-Activity Plan
- **Method & Path:** `POST /api/v1/stages/{stage_id}/pre-activities`
- **Auth & Access:** Bearer JWT (`FARMER`)
- **Request Body:**
```json
{
  "purpose": "Primary chisel ploughing & FYM incorporation",
  "planned_date": "2026-10-22",
  "estimated_budget": 14700.00,
  "notes": "Ensure deep ploughing before pre-monsoon showers",
  "machinery_requirements": [
    {
      "machine_name": "Tractor 45HP with MB Plough",
      "planned_hours": 6.0,
      "estimated_rate_per_hour": 900.00,
      "estimated_total_cost": 5400.00
    }
  ],
  "material_requirements": [
    {
      "material_name": "Farmyard Manure (FYM)",
      "planned_quantity": 5.0,
      "unit": "TON",
      "estimated_unit_cost": 1500.00,
      "estimated_total_cost": 7500.00
    }
  ],
  "labor_requirements": [
    {
      "task_description": "Spreading manure & bed leveling",
      "number_of_workers": 4,
      "estimated_days": 1.0,
      "daily_wage_rate": 450.00,
      "estimated_total_wage": 1800.00
    }
  ]
}
```
- **Response Status:** `201 Created`

---

### 6.2 Convert Pre-Activity Plan to Actuals
- **Method & Path:** `POST /api/v1/pre-activities/{plan_id}/convert`
- **Auth & Access:** Bearer JWT (`FARMER`)
- **Request Body:**
```json
{
  "convert_labor": true,
  "convert_machinery": true,
  "convert_materials": true
}
```
- **Response Status:** `200 OK`
- **Side Effects:** Automatically generates actual `WorkerAttendance`, `MachineUsage`, and `MaterialPurchase` records, updating status to `CONVERTED`.

---

## Section 7: Cultivation Lifecycle, Dynamic Stages & Daily Logs Endpoints

### 7.1 Start Live Cultivation Run
- **Method & Path:** `POST /api/v1/crops/cultivations`
- **Auth & Access:** Bearer JWT (`FARMER`)
- **Request Body:**
```json
{
  "farm_crop_plan_id": "b3c2d1e0-9a8b-7c6d-5e4f-3a2b1c0d9e8f",
  "farm_id": "9f8e7d6c-5b4a-3f2e-1d0c-9b8a7f6e5d4c",
  "crop_id": "e4b1a2c3-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "cultivation_name": "Field A Tomato Run",
  "sowing_date": "2026-10-25",
  "actual_area": 2.0,
  "area_unit": "ACRE"
}
```
- **Response Status:** `201 Created`
- **Side Effects:** Auto-seeds 8 sequential stages into `cultivation_stages`. Stage 1 is marked `IN_PROGRESS`.

---

### 7.2 Cultivation Run Management & Comparison
- `GET /api/v1/crops/cultivations` $\rightarrow$ Lists runs with live progress percentage and accrued costs.
- `GET /api/v1/crops/cultivations/{cultivation_id}` $\rightarrow$ Complete breakdown of all 8 stages, workers, machines, and expenses.
- `GET /api/v1/crops/cultivations/comparison` $\rightarrow$ Returns ROI comparison matrix for Organic vs Conventional runs.
- `DELETE /api/v1/crops/cultivations/{cultivation_id}` $\rightarrow$ Soft-deletes cultivation run.

---

### 7.3 Stage Progression & Actions
- `POST /api/v1/crops/cultivations/{cultivation_id}/stages` $\rightarrow$ Appends custom local stage.
- `PATCH /api/v1/crops/stages/{stage_id}` $\rightarrow$ Updates stage dates, status, or notes.
- `POST /api/v1/crops/stages/{stage_id}/complete-and-next` $\rightarrow$ Marks current stage `COMPLETED` and advances next sequential stage to `IN_PROGRESS`.
- `PATCH /api/v1/crops/cultivations/{cultivation_id}/harvest-yield` $\rightarrow$ Records final harvested quantity (KG/Quintal), unit price, and total revenue.

---

### 7.4 Stage Daily Labor Wage Logging
- **Method & Path:** `POST /api/v1/crops/stages/{stage_id}/workers`
- **Auth & Access:** Bearer JWT (`FARMER`)
- **Request Body:**
```json
{
  "worker_name": "Chinnasamy K",
  "worker_mobile": "9842100112",
  "date": "2026-10-26",
  "days_worked": 1.0,
  "daily_wage": 450.00,
  "total_wage": 450.00,
  "work_type": "Transplanting",
  "payment_status": "PENDING"
}
```
- **Response Status:** `201 Created`

---

### 7.5 Bulk Wage Logging
- **Method & Path:** `POST /api/v1/crops/stages/{stage_id}/workers/bulk`
- **Auth & Access:** Bearer JWT (`FARMER`)
- **Request Body:**
```json
{
  "logs": [
    {
      "worker_name": "Rani M",
      "date": "2026-10-26",
      "days_worked": 1.0,
      "daily_wage": 400.00,
      "total_wage": 400.00,
      "work_type": "Weeding"
    },
    {
      "worker_name": "Lakshmi S",
      "date": "2026-10-26",
      "days_worked": 1.0,
      "daily_wage": 400.00,
      "total_wage": 400.00,
      "work_type": "Weeding"
    }
  ]
}
```
- **Response Status:** `201 Created`

---

### 7.6 Stage Expense Logging
- **Method & Path:** `POST /api/v1/crops/stages/{stage_id}/expenses`
- **Request Body:**
```json
{
  "category": "INPUT_MATERIAL",
  "item_name": "Bio Neem Oil 10000 PPM",
  "amount": 1250.00,
  "payment_method": "UPI",
  "expense_date": "2026-10-27",
  "receipt_image_url": "/uploads/stages/receipt_neem.jpg"
}
```
- **Response Status:** `201 Created`
- `DELETE /api/v1/crops/expenses/{expense_id}` $\rightarrow$ Soft-deletes expense.
- `POST /api/v1/crops/expenses/{expense_id}/restore` $\rightarrow$ Instant undo restoration.

---

## Section 8: Farmer CRM — Labor, Machinery & Operations Endpoints

### 8.1 Register Farm Worker in Master Roster
- **Method & Path:** `POST /api/v1/farmer/crm/workers`
- **Auth & Access:** Bearer JWT (`FARMER`)
- **Request Body:**
```json
{
  "name": "Velusamy M",
  "mobile_number": "9842199881",
  "gender": "MALE",
  "skill_primary": "Tractor Operator & Ploughing",
  "default_daily_wage": 550.00
}
```
- **Response Status:** `201 Created`

---

### 8.2 Machinery Master & Usage Logging
- `POST /api/v1/farmer/crm/machines` $\rightarrow$ Registers equipment into machine inventory.
- `GET /api/v1/farmer/crm/machines` $\rightarrow$ Lists owned/rented machinery.
- `POST /api/v1/farmer/crm/stages/{stage_id}/machines` $\rightarrow$ Logs usage:
```json
{
  "machine_id": "5a4b3c2d-1e0f-9a8b-7c6d-5e4f3a2b1c0d",
  "hours_used": 4.5,
  "hourly_rate": 850.00,
  "fuel_liters": 12.0,
  "fuel_cost": 1200.00,
  "operator_cost": 500.00,
  "usage_date": "2026-10-28"
}
```
- **Response Status:** `201 Created`

---

## Section 9: Input Catalog, Suppliers & Procurement Requisition Endpoints

### 9.1 Browse Input Catalog
- `GET /api/v1/inputs` $\rightarrow$ Returns certified seeds, fertilizers, bio-inputs.
- `GET /api/v1/inputs/{input_id}` $\rightarrow$ Detailed NPK composition and guidelines.

### 9.2 Verified Suppliers Directory
- `GET /api/v1/suppliers` $\rightarrow$ Returns verified agricultural dealers in district.
- `GET /api/v1/suppliers/{supplier_id}` $\rightarrow$ Contact details and products sold.

### 9.3 Create Procurement Requisition
- **Method & Path:** `POST /api/v1/procurement-requests`
- **Auth & Access:** Bearer JWT (`FARMER`)
- **Request Body:**
```json
{
  "farm_id": "9f8e7d6c-5b4a-3f2e-1d0c-9b8a7f6e5d4c",
  "input_id": "7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d",
  "quantity": 10.0,
  "unit": "BAG",
  "required_by_date": "2026-11-01",
  "notes": "Urgent requirement for Tomato fertigation"
}
```
- **Response Status:** `201 Created`

---

## Section 10: Billing, Invoicing & Payment Settlement Endpoints

### 10.1 Generate Consolidated Stage Bill
- **Method & Path:** `POST /api/v1/farmer/crm/bills/generate-stage-bill`
- **Auth & Access:** Bearer JWT (`FARMER`)
- **Request Body:**
```json
{
  "cultivation_stage_id": "22222222-3333-4444-5555-666666666666",
  "bill_type": "CONSOLIDATED_STAGE",
  "notes": "Stage 2 Nursery Bed Raising Full Settlement"
}
```
- **Response Status:** `201 Created`
- **Response Body:**
```json
{
  "id": "bill-uuid-123",
  "bill_number": "BIL-2026-0001",
  "subtotal": 12500.00,
  "tax_amount": 0.00,
  "discount_amount": 0.00,
  "total_amount": 12500.00,
  "paid_amount": 0.00,
  "balance_due": 12500.00,
  "status": "PENDING",
  "items_count": 6
}
```

---

### 10.2 Settle Bill Payment
- **Method & Path:** `POST /api/v1/farmer/crm/payments`
- **Auth & Access:** Bearer JWT (`FARMER`)
- **Request Body:**
```json
{
  "bill_id": "bill-uuid-123",
  "amount_paid": 12500.00,
  "payment_method": "UPI",
  "transaction_reference": "UPI/20261028/890123",
  "paid_at": "2026-10-28T14:30:00Z"
}
```
- **Response Status:** `201 Created`
- **Side Effects:** Updates `balance_due = 0.00`, sets bill status to `PAID`, marks linked worker wage records as `PAID`, triggers SMS notification.

---

## Section 11: Tool Demand Geofencing Radar & Proximity Discovery Endpoints

### 11.1 Register Machinery Requirement
- **Method & Path:** `POST /api/v1/farmer/tool-interests`
- **Auth & Access:** Bearer JWT (`FARMER`, `SUPER_ADMIN`)
- **Request Body:**
```json
{
  "tool_category": "TRACTOR_RENTAL",
  "tool_name": "Tractor 45HP with Disc Plough",
  "required_location": "Mysuru",
  "search_radius_km": 25.0,
  "latitude": 12.2958,
  "longitude": 76.6394,
  "urgency": "HIGH"
}
```
- **Response Status:** `201 Created`
- **Side Effects:** Automatically invokes Google Places API search in the background, persists matching equipment dealers into `tool_discovered_locations`, returns discovered count.

---

### 11.2 Check Geofence Proximity
- **Method & Path:** `POST /api/v1/farmer/tool-interests/check-proximity`
- **Auth & Access:** Bearer JWT (`FARMER`, `SUPER_ADMIN`)
- **Request Body:**
```json
{
  "current_latitude": 12.2962,
  "current_longitude": 76.6389,
  "accuracy_meters": 10.0
}
```
- **Response Status:** `200 OK`
- **Response Body:**
```json
{
  "nearby_count": 2,
  "matches": [
    {
      "business_name": "Sri Chamundeshwari Tractor Rental & Custom Hiring",
      "distance_meters": 340.5,
      "address": "Bannur Road, Mysuru",
      "phone_number": "+91 94480 12345",
      "is_within_alert_threshold": true
    }
  ]
}
```

---

## Section 12: Livestock Master & Farmer Livestock Endpoints

### 12.1 Public Read Livestock Categories & Breeds
- `GET /api/v1/livestock/categories` $\rightarrow$ Lists active animal categories (`COW`, `GOAT`, `CHICKEN`, etc.).
- `GET /api/v1/livestock/breeds?category_id={uuid}` $\rightarrow$ Lists specific breeds (e.g. Kangayam, Kadaknath).

### 12.2 Farmer Register Livestock Listing
- **Method & Path:** `POST /api/v1/farmer/livestock`
- **Auth & Access:** Bearer JWT (`FARMER`)
- **Request Body:**
```json
{
  "category_id": "c1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
  "breed_id": "b1a2b3c4-d5e6-7f8a-9b0c-1d2e3f4a5b6c",
  "title": "Healthy Pure Kangayam Heifer (காங்கேயம் கிடாரி)",
  "selling_model": "INDIVIDUAL",
  "price": 38000.00,
  "age_months": 22.0,
  "weight_kg": 280.0,
  "gender": "FEMALE",
  "farm_id": "9f8e7d6c-5b4a-3f2e-1d0c-9b8a7f6e5d4c",
  "images": ["/uploads/general/kangayam_cow.jpg"]
}
```
- **Response Status:** `201 Created`

---

## Section 13: Farm Produce & Selling Products Endpoints

### 13.1 Create Fresh Farm Product Listing
- **Method & Path:** `POST /api/v1/farmer/products`
- **Auth & Access:** Bearer JWT (`FARMER`)
- **Request Body:**
```json
{
  "product_name": "Fresh Farm Grade-A Tomatoes (நாட்டு தக்காளி)",
  "category": "VEGETABLES",
  "variety": "Local Country Desi",
  "description": "Naturally grown, freshly picked morning harvest in plastic crates.",
  "unit": "KG",
  "price_per_unit": 35.00,
  "available_quantity": 500.0,
  "minimum_order_quantity": 5.0,
  "delivery_type": "DELIVERY",
  "primary_image_url": "/uploads/crops/tomato_grade_a.jpg",
  "farm_id": "9f8e7d6c-5b4a-3f2e-1d0c-9b8a7f6e5d4c"
}
```
- **Response Status:** `201 Created`

---

### 13.2 Quick Stock Adjustment
- **Method & Path:** `PATCH /api/v1/farmer/products/{product_id}/stock`
- **Auth & Access:** Bearer JWT (`FARMER`)
- **Request Body:**
```json
{
  "available_quantity": 250.0
}
```
- **Response Status:** `200 OK`

---

## Section 14: Customer Cart, Checkout & Marketplace Order Endpoints

### 14.1 Add Item to Cart
- **Method & Path:** `POST /api/v1/cart/items`
- **Auth & Access:** Bearer JWT (Customer / All Roles)
- **Request Body:**
```json
{
  "product_id": "prod-uuid-123",
  "quantity": 20.0
}
```
- **Response Status:** `200 OK`

---

### 14.2 Direct Instant Buy-Now
- **Method & Path:** `POST /api/v1/marketplace/orders/buy-now`
- **Auth & Access:** Bearer JWT (Customer / All Roles)
- **Request Body:**
```json
{
  "livestock_id": "livestock-uuid-123",
  "quantity": 1.0,
  "payment_method": "ONLINE_PAYMENT",
  "shipping_address": {
    "full_name": "Karthik Subramanian",
    "mobile_number": "9876500000",
    "address_line1": "Flat 4B, Green Acres, Race Course",
    "city": "Coimbatore",
    "state": "Tamil Nadu",
    "pincode": "641018"
  }
}
```
- **Response Status:** `201 Created`
- **Response Body:**
```json
{
  "id": "order-uuid-999",
  "order_number": "ORD-20261013-4B91",
  "total_amount": 38000.00,
  "status": "PENDING",
  "payment_status": "PENDING",
  "created_at": "2026-10-13T16:00:00Z"
}
```

---

## Section 15: Razorpay Payment & Webhook Processing Endpoints

### 15.1 Create Razorpay Gateway Order
- **Method & Path:** `POST /api/v1/marketplace/orders/{order_id}/create-razorpay-order`
- **Auth & Access:** Bearer JWT
- **Response Status:** `200 OK`
- **Response Body:**
```json
{
  "order_id": "order-uuid-999",
  "razorpay_order_id": "order_OA194819B1",
  "amount_in_paise": 3800000,
  "currency": "INR",
  "key_id": "rzp_test_AgriSmartLiveKey"
}
```

---

### 15.2 Client Cryptographic Signature Verification
- **Method & Path:** `POST /api/v1/marketplace/orders/{order_id}/verify-razorpay-payment`
- **Auth & Access:** Bearer JWT
- **Request Body:**
```json
{
  "razorpay_order_id": "order_OA194819B1",
  "razorpay_payment_id": "pay_OA199201C2",
  "razorpay_signature": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```
- **Response Status:** `200 OK`
- **Side Effects:** Validates HMAC-SHA256, marks `payment_status = PAID`, marks `status = CONFIRMED`.

---

### 15.3 Server-to-Server Razorpay Webhook Handler
- **Method & Path:** `POST /api/v1/payments/webhooks` or `POST /api/v1/payments/webhooks/razorpay`
- **Auth & Access:** Public (Validated via `X-Razorpay-Signature` HMAC header)
- **Request Headers:**
  - `X-Razorpay-Signature: <cryptographic_hmac_sha256>`
- **Request Body (Standard Razorpay Event Payload):**
```json
{
  "entity": "event",
  "event": "payment.captured",
  "contains": ["payment"],
  "payload": {
    "payment": {
      "entity": {
        "id": "pay_OA199201C2",
        "order_id": "order_OA194819B1",
        "amount": 3800000,
        "status": "captured"
      }
    }
  }
}
```
- **Response Status:** `200 OK`
- **Side Effects:** Idempotent reconciliation in `webhook_logs`, updates order payment status to `PAID`.

---

## Section 16: Logistics, Driver Scanning, Pickup & Tracking Endpoints

### 16.1 Public Milestone Tracking (Zero Auth Required)
- **Method & Path:** `GET /api/v1/tracking/{tracking_number}`
- **Auth & Access:** Public
- **Response Status:** `200 OK`
- **Response Body:**
```json
{
  "tracking_number": "TRK-20261013-8821",
  "status": "IN_TRANSIT",
  "origin_hub": "Farm Gate, Pollachi",
  "destination_hub": "Coimbatore City Hub",
  "milestones": [
    {
      "status": "PICKED_UP",
      "timestamp": "2026-10-13T14:00:00Z",
      "location": "Pollachi Farm Gate",
      "description": "Package received from farmer"
    },
    {
      "status": "IN_TRANSIT",
      "timestamp": "2026-10-13T15:30:00Z",
      "location": "Pollachi Highway Hub",
      "description": "In transit to destination hub"
    }
  ]
}
```

---

### 16.2 Farmer Create Shipment & Packaging
- **Method & Path:** `POST /api/v1/farmer/shipments`
- **Auth & Access:** Bearer JWT (`FARMER`, `SUPER_ADMIN`)
- **Request Body:**
```json
{
  "order_id": "order-uuid-999",
  "packages": [
    {
      "package_type": "CRATE",
      "weight_kg": 25.0,
      "length_cm": 50.0,
      "width_cm": 35.0,
      "height_cm": 30.0,
      "is_perishable": true,
      "handling_instructions": "Ventilated plastic crate. Keep dry and cool."
    }
  ]
}
```
- **Response Status:** `201 Created`
- **Side Effects:** Generates tracking number, barcode, and QR code representation.

---

### 16.3 Driver Universal Barcode/QR Scanner Resolution
- **Method & Path:** `GET /api/v1/driver/shipments/scan/{code}`
- **Auth & Access:** Bearer JWT (`DRIVER`, `SUPER_ADMIN`)
- **Path Parameter:** `code` (Package Barcode, Tracking #, or Pickup Code)
- **Response Status:** `200 OK`
- **Response Body:**
```json
{
  "match_type": "PACKAGE_BARCODE",
  "shipment": {
    "id": "shipment-uuid-777",
    "tracking_number": "TRK-20261013-8821",
    "status": "READY_FOR_PICKUP",
    "farmer_name": "Murugan Palanisamy",
    "delivery_address": "Coimbatore, Tamil Nadu"
  }
}
```

---

### 16.4 Driver Confirm Pickup at Farm Gate
- **Method & Path:** `POST /api/v1/driver/shipments/{shipment_id}/confirm-pickup`
- **Auth & Access:** Bearer JWT (`DRIVER`, `SUPER_ADMIN`)
- **Query Parameters:** `location_hub=Pollachi%20Farm%20Gate`
- **Response Status:** `200 OK`
- **Side Effects:** Updates shipment status to `PICKED_UP`; order status moves to `PROCESSING`.

---

### 16.5 Driver Confirm Doorstep Delivery
- **Method & Path:** `POST /api/v1/driver/shipments/{shipment_id}/confirm-delivery`
- **Auth & Access:** Bearer JWT (`DRIVER`, `SUPER_ADMIN`)
- **Request Body:**
```json
{
  "recipient_name": "Karthik Subramanian",
  "notes": "Delivered in person at door. Crates inspected.",
  "signature_image_url": "/uploads/general/sig_karthik.png"
}
```
- **Response Status:** `200 OK`
- **Side Effects:** Sets shipment and order status to `DELIVERED`, records delivered timestamp, dispatches SMS review invitation.

---

## Section 17: Produce Procurement & Harvest Broadcast Alert Endpoints

### 17.1 List Available Crop Harvests
- `GET /api/v1/produce-procurement/available` $\rightarrow$ Lists ready and upcoming farm yields by crop and district.

### 17.2 Real-time Broadcast Harvest Yield Alerts
- `GET /api/v1/produce-procurement/harvest-alerts?limit=10` $\rightarrow$ Returns live stream of newly recorded farm yields.

### 17.3 Subscribe for Instant Harvest Alerts
- **Method & Path:** `POST /api/v1/produce-procurement/subscribe-alerts`
- **Request Body:**
```json
{
  "buyer_name": "Coimbatore Wholesale Vegetable Mandi",
  "mobile_number": "9842100000",
  "email": "mandi.cbe@example.com",
  "crop_ids": ["e4b1a2c3-4d5e-6f7a-8b9c-0d1e2f3a4b5c"],
  "districts": ["Coimbatore", "Tiruppur"]
}
```
- **Response Status:** `200 OK`

---

## Section 18: Data Gate Subscriptions & Admin Pass Endpoints

### 18.1 Check User Historical Access Status
- **Method & Path:** `GET /api/v1/subscriptions/my-status`
- **Auth & Access:** Optional Bearer JWT
- **Response Status:** `200 OK`
- **Response Body:**
```json
{
  "has_active_subscription": true,
  "is_admin_bypass": false,
  "plan_type": "MONTHLY_PASS",
  "expires_at": "2026-11-13T10:00:00Z",
  "days_remaining": 30
}
```

---

### 18.2 Create Subscription Order
- **Method & Path:** `POST /api/v1/subscriptions/create-order`
- **Auth & Access:** Bearer JWT
- **Request Body:**
```json
{
  "plan_type": "MONTHLY_PASS"
}
```
- **Response Status:** `200 OK`

---

## Section 19: Super Admin Governance, Metrics & Trash Bin Vault Endpoints

### 19.1 System Executive Metrics Dashboard
- **Method & Path:** `GET /api/v1/admin/dashboard`
- **Auth & Access:** Bearer JWT (`SUPER_ADMIN`)
- **Response Status:** `200 OK`

---

### 19.2 List Trash Bin Soft-Deleted Entities
- **Method & Path:** `GET /api/v1/admin/trash-bin`
- **Auth & Access:** Bearer JWT (`SUPER_ADMIN`)
- **Query Parameters:** `entity_type=FARMS&search=Pollachi&page=1&page_size=20`
- **Response Status:** `200 OK`
- **Response Body:**
```json
{
  "items": [
    {
      "entity_type": "FARMS",
      "entity_id": "9f8e7d6c-5b4a-3f2e-1d0c-9b8a7f6e5d4c",
      "name": "Pollachi Coconut & Veggie Grove",
      "deleted_at": "2026-10-13T09:30:00Z",
      "deleted_by": "Super Admin"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 19.3 Single-Click Restore Soft-Deleted Entity
- **Method & Path:** `POST /api/v1/admin/trash-bin/{entity_type}/{entity_id}/restore`
- **Auth & Access:** Bearer JWT (`SUPER_ADMIN`)
- **Path Parameters:**
  - `entity_type`: `USERS`, `FARMS`, `CROPS`, `CULTIVATION_RUNS`, `CULTIVATION_STAGES`, `WORKERS`, `MACHINES`, `BILLS`, `SUPPLIERS`
  - `entity_id`: UUID
- **Response Status:** `200 OK`
- **Side Effects:** Sets `is_deleted = false` and returns entity to active catalog.

---

### 19.4 Guarded Hard-Deletion (Permanent Purge)
- **Method & Path:** `DELETE /api/v1/admin/trash-bin/{entity_type}/{entity_id}/hard-delete`
- **Auth & Access:** Bearer JWT (`SUPER_ADMIN`)
- **Response Status:** `200 OK`
- **Safety Checks:** Prevents deletion of the last Super Admin and records bound to active orders.

---

## Section 20: Media & File Upload Endpoints

### 20.1 Multipart Image Upload
- **Method & Path:** `POST /api/v1/media/upload`
- **Auth & Access:** Bearer JWT (All Roles)
- **Request Headers:** `Content-Type: multipart/form-data`
- **Form Body:**
  - `file`: Binary image (`image/jpeg`, `image/png`, `image/webp`)
  - `folder`: `stages` / `crops` / `profiles` / `general`
- **Response Status:** `200 OK`
- **Response Body:**
```json
{
  "filename": "e9a8b7c6-d5e4-3f2a-1b0c-9d8e7f6a5b4c.jpg",
  "url": "/uploads/stages/e9a8b7c6-d5e4-3f2a-1b0c-9d8e7f6a5b4c.jpg",
  "size_bytes": 1420840,
  "mime_type": "image/jpeg"
}
```
