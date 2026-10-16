# Agri-Smart Ecosystem — REST API Reference (`/api/v1`)

## 1. Authentication Endpoints (`/api/v1/auth`)

| Endpoint | Method | Description | Auth Required | Roles Permitted |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/auth/login` | `POST` | Authenticate with mobile/email & password. Sets HttpOnly refresh cookie & returns access token. | No | Public |
| `/api/v1/auth/refresh` | `POST` | Rotate refresh token from cookie and issue fresh RS256 access token. | No (Cookie) | Public |
| `/api/v1/auth/logout` | `POST` | Revoke active refresh token and clear cookie. | No (Cookie) | Public |
| `/api/v1/auth/me` | `GET` | Retrieve current authenticated user profile and assigned roles. | Yes | All Roles |

---

## 2. Super Admin User & Role Management (`/api/v1/admin/users`)

| Endpoint | Method | Description | Auth Required | Roles Permitted |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/admin/users` | `GET` | List users with pagination, role filtering, and search. | Yes | `SUPER_ADMIN` |
| `/api/v1/admin/users` | `POST` | Provision a new user account with initial role assignments. | Yes | `SUPER_ADMIN` |
| `/api/v1/admin/users/{id}` | `GET` | Get detailed user information. | Yes | `SUPER_ADMIN` |
| `/api/v1/admin/users/{id}` | `PATCH` | Update user details (name, email, active status). | Yes | `SUPER_ADMIN` |
| `/api/v1/admin/users/{id}/roles` | `PUT` | Synchronize and update user role assignments. | Yes | `SUPER_ADMIN` |
| `/api/v1/admin/users/{id}` | `DELETE` | Soft-delete a user account (with Last Super Admin guard). | Yes | `SUPER_ADMIN` |

---

## 3. Platform Trash Bin Vault (`/api/v1/admin/trash-bin`)

| Endpoint | Method | Description | Auth Required | Roles Permitted |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/admin/trash-bin` | `GET` | List soft-deleted entities across all 6 core business tables with audit metadata. | Yes | `SUPER_ADMIN` |
| `/api/v1/admin/trash-bin/restore` | `POST` | Restore a soft-deleted entity by type and ID. | Yes | `SUPER_ADMIN` |
| `/api/v1/admin/trash-bin/purge` | `POST` | Permanently hard-delete a soft-deleted entity. | Yes | `SUPER_ADMIN` |

---

## 4. Role Profiles (`/api/v1/...`)

| Endpoint | Method | Description | Auth Required | Roles Permitted |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/farmer-profiles/me` | `GET`/`PUT` | Get or update authenticated farmer profile details. | Yes | `FARMER` |
| `/api/v1/trader-profiles/me` | `GET`/`PUT` | Get or update authenticated trader profile details. | Yes | `TRADER` |
| `/api/v1/driver-profiles/me` | `GET`/`PUT` | Get or update authenticated driver profile details. | Yes | `DRIVER` |
| `/api/v1/worker-profiles/me` | `GET`/`PUT` | Get or update authenticated worker profile details. | Yes | `WORKER` |

---

## 5. Farm Parcel Management (`/api/v1/farms`)

| Endpoint | Method | Description | Auth Required | Roles Permitted |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/farms` | `GET` | List farms belonging to the authenticated farmer. | Yes | `FARMER`, `SUPER_ADMIN` |
| `/api/v1/farms` | `POST` | Register a new farm parcel with sequential code `FARM-XXXXXX`. | Yes | `FARMER` |
| `/api/v1/farms/{id}` | `GET` | Retrieve farm parcel details. | Yes | `FARMER`, `SUPER_ADMIN` |
| `/api/v1/farms/{id}` | `PATCH` | Update farm parcel parameters. | Yes | `FARMER` |
| `/api/v1/farms/{id}` | `DELETE` | Soft-delete a farm parcel. | Yes | `FARMER` |

---

## 6. Central Crop Master & Process Stages (`/api/v1/crops` & `/api/v1/admin/crops`)

| Endpoint | Method | Description | Auth Required | Roles Permitted |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/crops` | `GET` | List active crops for farmer planning dropdowns. | Yes | All Roles |
| `/api/v1/crops/{crop_id}/stages` | `GET` | Retrieve active process stage templates for a crop. | Yes | All Roles |
| `/api/v1/admin/crops` | `GET`/`POST` | List and create central crop master records. | Yes | `SUPER_ADMIN` |
| `/api/v1/admin/crops/{id}` | `GET`/`PATCH`/`DELETE` | Manage crop master record. | Yes | `SUPER_ADMIN` |
| `/api/v1/admin/crops/{crop_id}/stages` | `GET`/`POST` | List and create crop stage templates with JSON activities. | Yes | `SUPER_ADMIN` |
| `/api/v1/admin/crops/{crop_id}/stages/{id}` | `GET`/`PATCH`/`DELETE` | Manage crop stage template. | Yes | `SUPER_ADMIN` |

---

## 7. Farm Crop Plans (`/api/v1/farm-crop-plans`)

| Endpoint | Method | Description | Auth Required | Roles Permitted |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/farm-crop-plans` | `GET` | List crop plans for authenticated farmer's farms. | Yes | `FARMER`, `SUPER_ADMIN` |
| `/api/v1/farm-crop-plans` | `POST` | Create seasonal crop plan for a farm parcel. | Yes | `FARMER` |
| `/api/v1/farm-crop-plans/{id}` | `GET`/`PATCH`/`DELETE` | Retrieve, update, or soft-delete crop plan. | Yes | `FARMER` |

---

## 8. Cultivations, Stages, Worker Attendance & Expenses (`/api/v1/cultivations`)

| Endpoint | Method | Description | Auth Required | Roles Permitted |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/cultivations` | `GET` | List active cultivation runs with stage & financial summaries. | Yes | `FARMER`, `SUPER_ADMIN` |
| `/api/v1/cultivations/start` | `POST` | Instantiate a new cultivation run from a crop plan with cloned stages. | Yes | `FARMER` |
| `/api/v1/cultivations/{id}` | `GET` | Get comprehensive cultivation run details, all stages, worker logs & expenses. | Yes | `FARMER`, `SUPER_ADMIN` |
| `/api/v1/cultivations/{id}/stages/{stage_id}/status` | `PATCH` | Advance or update cultivation stage status. | Yes | `FARMER` |
| `/api/v1/cultivations/{id}/stages/{stage_id}/expenses` | `POST` | Log an itemized stage expense. | Yes | `FARMER` |
| `/api/v1/cultivations/{id}/expenses/{expense_id}` | `DELETE` | Soft-delete a stage expense. | Yes | `FARMER` |
| `/api/v1/cultivations/{id}/stages/{stage_id}/workers` | `POST` | Log worker daily attendance and wage. | Yes | `FARMER` |
| `/api/v1/cultivations/{id}/workers/{worker_log_id}` | `DELETE` | Soft-delete worker attendance entry. | Yes | `FARMER` |
| `/api/v1/cultivations/{id}/multi-season-metrics` | `PATCH` | Record harvest yield, selling price, and gross revenue. | Yes | `FARMER` |
| `/api/v1/cultivations/{id}` | `DELETE` | Soft-delete an active cultivation run. | Yes | `FARMER` |

---

## 9. Media Uploads (`/api/v1/media`)

| Endpoint | Method | Description | Auth Required | Roles Permitted |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/media/upload` | `POST` | Upload images for stage bills, farm photos, or crop stage visual assets. | Yes | All Roles |
