# Agri-Smart Backend API

FastAPI backend providing REST endpoints and data layer abstractions for the Agri-Smart Ecosystem.

---

## 🛠 Tech Stack
- **FastAPI**
- **SQLAlchemy 2.0**
- **Alembic**
- **Pydantic v2 & Pydantic Settings**
- **Uvicorn**
- **PostgreSQL (via psycopg)**

---

## 🚀 Running Locally

### 1. Create and Activate Virtual Environment
```bash
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
```

### 4. Run Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📡 API Endpoints
- **Root:** `GET http://localhost:8000/`
- **Health Check:** `GET http://localhost:8000/api/v1/health`
- **Interactive Swagger Docs:** `GET http://localhost:8000/docs`
- **ReDoc Documentation:** `GET http://localhost:8000/redoc`

---

## 🗄 Database Migrations & Seeding

### 1. Run Alembic Migrations
```bash
# Check current migration revision
alembic current

# Upgrade database to latest migration
alembic upgrade head
```

### 2. Seed Default Roles and Super Admin
Ensure `SUPER_ADMIN_PASSWORD` is set in `.env`, then execute:
```bash
python -m app.seeds.run_seed
```
This process is idempotent and safely creates:
1. Default system roles: `SUPER_ADMIN`, `FARMER`, `TRADER`, `DRIVER`, `WORKER`
2. Initial `SUPER_ADMIN` user with Argon2id password hashing
