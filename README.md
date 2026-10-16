# Agri-Smart Ecosystem

Smart Agriculture Management Platform connecting farmers, traders, workers, and transport services.

### 🌟 Key Feature Highlights
* **Precision Crop Cultivation Lifecycle:** 8-stage agronomic workflow with worker attendance, machinery usage, and input logs.
* **Smart Tool Demand & Geofencing Radar:** Farmers add equipment requirements (e.g. Tractor rental in Mysuru). Agri-Smart automatically queries Google Places, stores matching local businesses, and triggers instant **🔔 in-app popup notifications** when traveling within 500m of them!
* **Harvest Fresh Produce & Livestock Marketplace:** Direct farmer-to-consumer commerce with live tracking and Razorpay escrow payments.

---

## 🛠 Technology Stack

### Frontend
- **Framework:** Next.js (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Linting:** ESLint

### Backend
- **Framework:** FastAPI (Python 3.12+)
- **ORM:** SQLAlchemy 2.0
- **Validation & Settings:** Pydantic / Pydantic Settings
- **Migrations:** Alembic
- **ASGI Server:** Uvicorn

### Database
- **Primary Database:** PostgreSQL 16+

---

## 📁 Repository Structure

```text
Agri-Smart/
├── frontend/             # Next.js frontend application
├── backend/              # FastAPI backend API
├── database/             # Database design documents and scripts
├── infrastructure/       # Deployment and infrastructure configurations
├── docs/                 # System architecture and documentation
├── docker-compose.yml    # Development PostgreSQL service
├── .gitignore            # Multi-stack gitignore
└── README.md             # Project documentation
```

---

## 🚀 Local Development Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.12+
- Docker & Docker Compose (for PostgreSQL)

---

### Step 1: Start PostgreSQL

Start the database using Docker Compose:

```bash
docker compose up -d
```

PostgreSQL will be accessible at `localhost:5432` with database name `agri_smart`.

---

### Step 2: Start FastAPI Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

5. Start the backend development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. Verify backend APIs:
   - Root Status: [http://localhost:8000/](http://localhost:8000/)
   - Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
   - Interactive Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Step 3: Start Next.js Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Copy the environment template:
   ```bash
   cp .env.local.example .env.local
   ```

4. Start the frontend development server:
   ```bash
   npm run dev
   ```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 📋 Architecture & Documentation

- **Step-by-Step Module Workflow & Endpoints Guide:** [docs/WORKFLOW_MODULE_STEP_BY_STEP.md](docs/WORKFLOW_MODULE_STEP_BY_STEP.md)
- Comprehensive architecture overview: [docs/architecture.md](docs/architecture.md)
- End-to-End Workflow Process & Flowcharts: [docs/WORKFLOW_PROCESS.md](docs/WORKFLOW_PROCESS.md)
- Supabase, Cloudinary & Razorpay Setup Guide: [docs/SUPABASE_SETUP.md](docs/SUPABASE_SETUP.md)
- Database schema plans & design: [database/README.md](database/README.md)
- Infrastructure plans: [infrastructure/README.md](infrastructure/README.md)
