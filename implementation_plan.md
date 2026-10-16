# Agri-Smart — Product Transport, Barcode Generation, Shipment Tracking & Delivery System
## Implementation Plan & Architecture Specification

**Project**: Agri-Smart Farmer Marketplace  
**Document**: `implementation_plan.md`  
**Status**: Pending Review & User Approval  

---

## 1. Executive Summary & Architecture Findings

The Agri-Smart platform enables direct farmer-to-consumer and farmer-to-trader agricultural commerce. To provide end-to-end transparency and logistics visibility, we are designing and implementing a **Courier & Transport Tracking System** (modeled after modern e-commerce standards like Flipkart and Amazon, but purpose-built for agricultural crops, fresh farm produce, and livestock).

### 1.1 Existing Architecture Inspection
- **Frontend**: Next.js 15 (App Router, Turbopack), React 19, TypeScript 5.7, Vanilla CSS with TailwindCSS 3.4.
- **Backend**: FastAPI (Python 3.12), SQLAlchemy 2.0 ORM, Pydantic v2 schemas, Alembic database migrations.
- **Authentication & RBAC**: JWT Bearer auth, Argon2id password hashing, role-based dependency injection supporting `FARMER`, `CUSTOMER`, `DRIVER`, `SUPER_ADMIN`, `TRADER`, and `WORKER`.
- **Existing Ordering & Logistics Systems**:
  - `MarketplaceOrder` & `MarketplaceOrderItem`: Stores customer orders for `FarmSellingProduct` (produce: Mangoes, Sapota, Paddy, Coconut, Lemon, Drumsticks, etc.) and `Livestock`.
  - `MarketplaceDelivery`: Basic placeholder table linking `driver_id` and delivery addresses.
  - `DriverProfile`: Driver vehicle & commercial license directory.
  - `NotificationService`: SMS & notification engine with gateway dispatch (Twilio, Fast2SMS) and persistent `sms_logs` audit records.
  - `LanguageContext` & `i18n`: 5 core Indian regional languages (English, Tamil, Hindi, Kannada, Telugu) + extended locales.

---

## 2. Order to Delivery Lifecycle & Workflow

```text
Customer Places Order (Marketplace produce / livestock)
        ↓
Payment Confirmed / COD Selected
        ↓
Order Status: CONFIRMED (Order #ORD-YYYYMMDD-XXXXX)
        ↓
Farmer Prepares & Packs Produce (Perishable / Fragile / General)
        ↓
Farmer Creates Shipment & Packages
        ↓
System Generates:
  - Shipment Number (e.g. SHP-20261002-00045)
  - Tracking Number (e.g. AGRI2026100200045)
  - Code 128 Barcode & QR Code
        ↓
Farmer Requests Transport Pickup (Address, Time Window, Weight, Special Handling)
        ↓
Transport Provider / Driver Assigned (Status: PICKUP_ASSIGNED)
        ↓
Driver Scans Barcode at Farm → Confirms Pickup (Status: PICKED_UP)
        ↓
Shipment Arrives at Origin Hub (Status: AT_ORIGIN_HUB)
        ↓
In-Transit Between Hubs (Status: IN_TRANSIT)
        ↓
Shipment Arrives at Local Destination Hub (Status: AT_DESTINATION_HUB)
        ↓
Assigned for Local Courier Delivery (Status: OUT_FOR_DELIVERY)
        ↓
Driver Reaches Customer & Scans Barcode / Enters Recipient Confirmation (Status: DELIVERED)
        ↓
[Exception Flows]: DELIVERY_FAILED (with retry or return reason) → RETURN_INITIATED → RETURNED
```

---

## 3. Database Schema Changes & Alembic Migration

We will create migration `0014_create_shipments_and_transport_tracking_tables.py` introducing 6 structured tables:

### 3.1 `transport_providers`
Manages logistics fleet partners and internal transport carriers.
- `id` (UUID, PK)
- `provider_name` (VARCHAR(150), indexed)
- `provider_code` (VARCHAR(50), UNIQUE, indexed)
- `contact_person` (VARCHAR(150))
- `phone_number` (VARCHAR(20))
- `email` (VARCHAR(255))
- `vehicle_type` (VARCHAR(50) — Pickup Van, Mini Truck, Reefer Truck, 3-Wheeler)
- `vehicle_number` (VARCHAR(50))
- `service_areas` (JSONB / TEXT)
- `is_active` (BOOLEAN, default True)
- `created_at`, `updated_at`

### 3.2 `shipments`
The central shipment tracking aggregate.
- `id` (UUID, PK)
- `shipment_number` (VARCHAR(50), UNIQUE, indexed, e.g. `SHP-20261002-00045`)
- `tracking_number` (VARCHAR(50), UNIQUE, indexed, e.g. `AGRI2026100200045`)
- `order_id` (UUID, FK -> `marketplace_orders.id`, indexed)
- `farmer_profile_id` (UUID, FK -> `farmer_profiles.id`, indexed)
- `customer_id` (UUID, FK -> `users.id`, indexed)
- `transport_provider_id` (UUID, FK -> `transport_providers.id`, nullable, indexed)
- `driver_id` (UUID, FK -> `users.id`, nullable, indexed)
- `current_status` (VARCHAR(40), default `CREATED`, indexed)
- `current_location` (VARCHAR(255))
- `origin_address` (TEXT)
- `origin_city` (VARCHAR(100))
- `origin_pincode` (VARCHAR(10))
- `destination_address` (TEXT)
- `destination_city` (VARCHAR(100))
- `destination_pincode` (VARCHAR(10))
- `total_packages` (INTEGER, default 1)
- `total_weight_kg` (NUMERIC(10, 2))
- `is_perishable` (BOOLEAN, default False)
- `special_handling` (VARCHAR(100) — KEEP_COOL, KEEP_DRY, FRAGILE, LIVE_PLANT, DIRECT_FARM)
- `barcode_data` (VARCHAR(100))
- `qr_code_data` (TEXT)
- `estimated_delivery_date` (DATE, nullable)
- `actual_delivery_date` (DATETIME, nullable)
- `created_at`, `updated_at`

### 3.3 `shipment_packages`
Supports multi-package orders (e.g. 2 bags of Paddy + 1 crate of Mangoes).
- `id` (UUID, PK)
- `shipment_id` (UUID, FK -> `shipments.id`, ondelete CASCADE, indexed)
- `package_number` (VARCHAR(50), UNIQUE, indexed, e.g. `PKG-20261002-00045-1`)
- `package_barcode` (VARCHAR(50), UNIQUE, indexed)
- `item_description` (VARCHAR(255))
- `weight_kg` (NUMERIC(8, 2))
- `package_type` (VARCHAR(50) — Jute Bag, Plastic Crate, Wooden Box, Corrugated Carton)
- `created_at`

### 3.4 `shipment_tracking_events` (Append-Only Event Ledger)
Permanent, immutable audit trail for every status and location transition.
- `id` (UUID, PK)
- `shipment_id` (UUID, FK -> `shipments.id`, ondelete CASCADE, indexed)
- `status` (VARCHAR(40), indexed)
- `location_hub` (VARCHAR(255))
- `city` (VARCHAR(100))
- `remarks` (TEXT)
- `updated_by_user_id` (UUID, FK -> `users.id`, nullable)
- `updated_by_role` (VARCHAR(50))
- `event_timestamp` (DATETIME, default now(timezone.utc), indexed)
- `created_at`

### 3.5 `pickup_requests`
Farmer pickup scheduling and dispatch orders.
- `id` (UUID, PK)
- `pickup_code` (VARCHAR(50), UNIQUE, indexed, e.g. `PKP-20261002-00012`)
- `shipment_id` (UUID, FK -> `shipments.id`, ondelete CASCADE, indexed)
- `farmer_profile_id` (UUID, FK -> `farmer_profiles.id`, indexed)
- `pickup_address` (TEXT)
- `pickup_contact_name` (VARCHAR(150))
- `pickup_contact_phone` (VARCHAR(20))
- `scheduled_date` (DATE)
- `time_window` (VARCHAR(50) — MORNING_7_11, AFTERNOON_12_4, EVENING_4_8)
- `status` (VARCHAR(30) — PENDING, ASSIGNED, COMPLETED, CANCELLED, indexed)
- `assigned_driver_id` (UUID, FK -> `users.id`, nullable)
- `assigned_vehicle_number` (VARCHAR(50), nullable)
- `created_at`, `updated_at`

### 3.6 `delivery_attempts`
Records delivery tries, customer absence, reschedules, or delivery proof.
- `id` (UUID, PK)
- `shipment_id` (UUID, FK -> `shipments.id`, ondelete CASCADE, indexed)
- `attempt_number` (INTEGER, default 1)
- `attempt_status` (VARCHAR(30) — SUCCESS, FAILED, RESCHEDULED)
- `failure_reason` (VARCHAR(100) — CUSTOMER_UNAVAILABLE, INCORRECT_ADDRESS, DAMAGED, TRANSPORT_ISSUE, OTHER)
- `recipient_name` (VARCHAR(150), nullable)
- `recipient_signature_note` (TEXT, nullable)
- `driver_notes` (TEXT, nullable)
- `attempt_time` (DATETIME, default now(timezone.utc))

---

## 4. Barcode (Code 128) & QR Code Vector Engine

### 4.1 Code 128 Barcode Generation
- Standard Code 128 encoding generates deterministic bar-and-space patterns with start code, character symbols, and modulo-103 checksum.
- Implemented as a clean vector SVG engine in frontend and backend.
- Renders crisp lines at any DPI (print-ready for 4×6 thermal labels, A4 laser printers, or smartphone screen scanning).

### 4.2 QR Code Vector Generation
- Generates high-contrast QR Matrix encoding the absolute or relative tracking URL (`/tracking/{tracking_number}`).
- High error correction level (ECC Level M / Q) ensures camera decodability even if physical labels get slightly soiled on farm pickup.

### 4.3 Printable 4×6 Shipment Label Component
- Printable layout displaying:
  - Header: Agri-Smart Logistics
  - Shipment Number & Tracking Number
  - Origin: Farmer Name, Farm Parcel, Village, District
  - Destination: Customer Name, Masked Phone, Delivery City, Pincode
  - Perishable / Temperature handling icons
  - Scannable Code 128 Barcode + Scannable QR Code
  - One-click print with CSS `@media print` styling.

---

## 5. Status Transition State Machine

```text
[CREATED]
    ↓ (Farmer requests pickup / confirms packing)
[READY_FOR_PICKUP]
    ↓ (Driver/Transport assigned)
[PICKUP_ASSIGNED]
    ↓ (Driver scans barcode at farm and confirms pickup)
[PICKED_UP]
    ↓ (Package checked in at regional origin center)
[AT_ORIGIN_HUB]
    ↓ (Dispatched on long-haul transport vehicle)
[IN_TRANSIT]
    ↓ (Arrives at customer city local distribution hub)
[AT_DESTINATION_HUB]
    ↓ (Loaded onto delivery van / two-wheeler)
[OUT_FOR_DELIVERY]
    ├── (Customer accepts delivery) ──────────────────→ [DELIVERED]
    └── (Customer unavailable / reschedule / damaged) → [DELIVERY_FAILED]
                                                            ├── [Retry next day] ──→ [OUT_FOR_DELIVERY]
                                                            └── [Return to farm] ──→ [RETURN_INITIATED] → [RETURN_IN_TRANSIT] → [RETURNED]
```

---

## 6. Backend API Design

All endpoints follow Agri-Smart REST conventions under `/api/v1`:

### 6.1 Public Tracking
- `GET /api/v1/tracking/{tracking_number}`: Public tracking endpoint.
  - **Privacy Enforcement**: Returns masked customer name (`K***r M`), delivery city & district only (no door number or full phone number), full milestone timeline, current status, latest known hub location, and estimated delivery date.

### 6.2 Farmer Shipment APIs
- `POST /api/v1/farmer/shipments`: Farmer creates shipment from confirmed order.
- `GET /api/v1/farmer/shipments`: List farmer's shipments with pagination, search, status filter.
- `GET /api/v1/farmer/shipments/{shipment_id}`: Get full shipment details with package breakdown.
- `POST /api/v1/farmer/shipments/{shipment_id}/pickup-request`: Create transport pickup request.
- `GET /api/v1/farmer/shipments/{shipment_id}/label`: Generate printable shipment label data.

### 6.3 Driver / Transport Staff Scanning & Updates
- `GET /api/v1/driver/pickups`: List assigned pickup tasks for driver.
- `GET /api/v1/driver/shipments/scan/{code}`: Scan Barcode/QR code to fetch shipment info.
- `POST /api/v1/driver/shipments/{shipment_id}/confirm-pickup`: Confirm physical package pickup at farm.
- `POST /api/v1/driver/shipments/{shipment_id}/update-status`: Update status (`AT_ORIGIN_HUB`, `IN_TRANSIT`, `AT_DESTINATION_HUB`, `OUT_FOR_DELIVERY`).
- `POST /api/v1/driver/shipments/{shipment_id}/confirm-delivery`: Complete delivery with recipient confirmation.
- `POST /api/v1/driver/shipments/{shipment_id}/record-failure`: Record delivery attempt failure with reason.

### 6.4 Super Admin Transport Hub
- `GET /api/v1/admin/transport/dashboard`: Overall transport metrics (Today's pickups, In-transit, Out for delivery, Delivered, Failed, Active providers).
- `GET /api/v1/admin/transport/shipments`: Paginated master shipment directory with multi-filter support.
- `GET /api/v1/admin/transport/providers`: List & manage transport providers.
- `POST /api/v1/admin/transport/providers`: Create/edit transport carrier partner.
- `POST /api/v1/admin/transport/shipments/{shipment_id}/assign-provider`: Assign transport provider & driver.

---

## 7. Frontend Pages & Components

1. **Public Tracking Page**:
   - `frontend/src/app/tracking/page.tsx`: Input tracking number search bar.
   - `frontend/src/app/tracking/[trackingNumber]/page.tsx`: Flipkart-style vertical tracking timeline, latest known location card, product summary, and ETA.
2. **Customer Order Integration**:
   - Update `frontend/src/app/orders/[id]/page.tsx`: Embed live shipment tracking card with quick link to `/tracking/[trackingNumber]`.
3. **Farmer Shipment Management**:
   - `frontend/src/app/farmer/shipments/page.tsx`: Farmer shipment listing, status badges, pickup request actions, and label generation.
   - `frontend/src/components/farmer/CreateShipmentModal.tsx`: Package weight, handling flags, and pickup window selector.
   - `frontend/src/components/farmer/ShipmentLabelModal.tsx`: Scannable Barcode + QR Code printable shipping label.
4. **Transport Driver Mobile Scanner Portal**:
   - `frontend/src/app/driver/page.tsx`: Driver dashboard with assigned pickups, out-for-delivery counter, and quick scanner button.
   - `frontend/src/app/driver/scan/page.tsx`: Real-time mobile camera barcode/QR scanner with manual input fallback, instant shipment identification, and status update actions.
5. **Super Admin Transport Dashboard**:
   - `frontend/src/app/admin/transport/page.tsx`: Logistics operations hub with metric cards, shipment data grid with 7-cell pagination, carrier management modal, and driver assignment dialog.
6. **Core Shared Components**:
   - `frontend/src/components/logistics/BarcodeRenderer.tsx`: Pure vector Code 128 SVG generator.
   - `frontend/src/components/logistics/QRCodeRenderer.tsx`: Crisp vector QR code SVG generator.
   - `frontend/src/components/logistics/ShipmentTimeline.tsx`: Responsive vertical/horizontal milestone stepper.

---

## 8. Multi-Language Translations (5 Languages)

All new UI text, status titles, and timeline milestones will be added to `frontend/src/i18n/locales/`:
- `en.json` (English)
- `ta.json` (Tamil / தமிழ்)
- `hi.json` (Hindi / हिन्दी)
- `kn.json` (Kannada / ಕನ್ನಡ)
- `te.json` (Telugu / తెలుగు)

---

## 9. Testing & Verification Strategy

1. **Backend Pytest Suite (`backend/tests/test_transport_and_shipments.py`)**:
   - Shipment creation from confirmed order.
   - Unique tracking number & barcode data generation.
   - Valid status transitions (`CREATED` -> `PICKED_UP` -> `IN_TRANSIT` -> `DELIVERED`).
   - Invalid status transition rejection (e.g. `CREATED` cannot jump directly to `DELIVERED`).
   - Public tracking endpoint privacy masking (ensuring no sensitive customer details are leaked).
   - Delivery failure and return initiation tests.
   - Role-based authorization checks (Farmer cannot update another farmer's shipment; Customer cannot update shipment status).
2. **Frontend Validation**:
   - `npx tsc --noEmit` validation for zero TypeScript errors.
   - Barcode & QR rendering checks.
   - Mobile responsive inspection for camera scanner and shipment timeline.

---

## 10. File Modification & Creation Manifest

### Backend Files to Create/Modify
- `backend/alembic/versions/0014_create_shipments_and_transport_tracking_tables.py` (New Migration)
- `backend/app/models/shipment.py` (New Model)
- `backend/app/models/transport_provider.py` (New Model)
- `backend/app/models/pickup_request.py` (New Model)
- `backend/app/models/enums.py` (Add `ShipmentStatus`, `SpecialHandlingType`, `PackageType`)
- `backend/app/schemas/shipment.py` (New Schemas)
- `backend/app/repositories/shipment_repository.py` (New Repository)
- `backend/app/services/shipment_service.py` (New Service)
- `backend/app/api/v1/shipments.py` (New Router for public tracking, farmer & driver endpoints)
- `backend/app/api/v1/admin_transport.py` (New Router for admin transport hub)
- `backend/app/main.py` (Register new routers)
- `backend/tests/test_transport_and_shipments.py` (New Test Suite)

### Frontend Files to Create/Modify
- `frontend/src/types/shipment.ts` (New Types)
- `frontend/src/services/shipmentService.ts` (New Service)
- `frontend/src/components/logistics/BarcodeRenderer.tsx` (New Component)
- `frontend/src/components/logistics/QRCodeRenderer.tsx` (New Component)
- `frontend/src/components/logistics/ShipmentTimeline.tsx` (New Component)
- `frontend/src/components/farmer/CreateShipmentModal.tsx` (New Component)
- `frontend/src/components/farmer/ShipmentLabelModal.tsx` (New Component)
- `frontend/src/app/tracking/page.tsx` (New Page)
- `frontend/src/app/tracking/[trackingNumber]/page.tsx` (New Page)
- `frontend/src/app/farmer/shipments/page.tsx` (New Page)
- `frontend/src/app/farmer/orders/page.tsx` (Update to include "Create Shipment" & "Track" actions)
- `frontend/src/app/orders/[id]/page.tsx` (Update to include shipment tracking badge)
- `frontend/src/app/driver/page.tsx` (Update driver portal with pickup queue & scan shortcut)
- `frontend/src/app/driver/scan/page.tsx` (New Camera Scanner & Pickup/Delivery Page)
- `frontend/src/app/admin/transport/page.tsx` (New Admin Transport Hub)
- `frontend/src/i18n/locales/*.json` (Add transport & tracking translations across 5 languages)
