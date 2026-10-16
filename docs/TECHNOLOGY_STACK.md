# Agri-Smart Ecosystem — Technology Stack Inventory

## 1. Frontend Technology Stack

| Technology / Library | Version | Purpose | Usage Area | Preservation Decision |
| :--- | :--- | :--- | :--- | :--- |
| **Next.js** | `^15.1.0` | React meta-framework (App Router) | Core web application, SSR/CSR, routing | Keep unchanged |
| **React / React-DOM** | `^19.0.0` | Declarative UI component library | Core UI rendering | Keep unchanged |
| **TypeScript** | `^5.7.2` | Static type safety | Entire frontend codebase | Keep unchanged |
| **Tailwind CSS** | `^3.4.17` | Utility-first CSS framework | Global design system & component styles | Keep unchanged |
| **Lucide React** | `^1.43.0` | Iconography suite | UI icons throughout dashboard and forms | Keep unchanged |
| **Three.js** | `^0.186.0` | 3D WebGL graphics library | 3D plant and crop stage visualizations | Keep unchanged |
| **@react-three/fiber** | `^9.7.0` | React renderer for Three.js | Declarative 3D scene graphs | Keep unchanged |
| **@react-three/drei** | `^10.7.8` | Three.js helpers & abstractions | Camera controls, lighting, and 3D effects | Keep unchanged |
| **Framer Motion** | `^13.2.0` | Production-ready motion & animations | Transitions, card entries, progress bars | Keep unchanged |
| **@tanstack/react-query** | `^5.102.8` | Server state management & caching | API query and mutation hooks | Keep unchanged |
| **Canvas Confetti** | `^1.9.4` | Micro-animation celebration effects | Stage completion & cultivation finish | Keep unchanged |
| **Playwright** | `^1.63.0` | End-to-end browser testing | Automated frontend testing suite | Keep unchanged |

---

## 2. Backend Technology Stack

| Technology / Library | Version | Purpose | Usage Area | Preservation Decision |
| :--- | :--- | :--- | :--- | :--- |
| **Python** | `3.12+` | Core programming runtime | Entire backend | Keep unchanged |
| **FastAPI** | `>=0.115.0` | High-performance async ASGI web framework | REST API endpoints, routing, docs | Keep unchanged |
| **Uvicorn** | `>=0.30.0` | Lightning-fast ASGI web server | Production and local development server | Keep unchanged |
| **SQLAlchemy** | `>=2.0.32` | Object-Relational Mapper (ORM) 2.0 | Declarative models, queries, repositories | Keep unchanged |
| **Alembic** | `>=1.13.2` | Database migration engine | Database schema versions 0001 to 0007 | Keep unchanged |
| **Pydantic / Settings** | `>=2.8.0` / `>=2.4.0` | Schema validation & environment configs | Request/response models, `.env` parsing | Keep unchanged |
| **psycopg (v3)** | `>=3.2.1` | Modern PostgreSQL database adapter | PostgreSQL connection pooling | Keep unchanged |
| **Argon2-cffi** | `>=23.1.0` | Password hashing algorithm | User authentication & password security | Keep unchanged |
| **PyJWT & Cryptography**| `>=2.9.0` / `>=43.0.0` | RS256 asymmetric cryptographic tokens | JWT access/refresh token generation | Keep unchanged |
| **pytest & anyio** | `9.1.1` / `4.15.1` | Testing framework | Backend unit, integration, & API tests | Keep unchanged |

---

## 3. Database & Storage

| Component | Specification | Purpose | Usage Area |
| :--- | :--- | :--- | :--- |
| **PostgreSQL** | `16-alpine` (Docker) | Primary relational database | Production and docker development persistence |
| **SQLite (In-Memory)** | In-memory with `StaticPool` | Fast isolated test environment | Pytest execution suite (`backend/tests`) |
| **Static File Storage** | Local directory (`backend/uploads/`) | Bill receipts, crop stage photos, farm media | Mounted under `/uploads` in FastAPI |

---

## 4. Infrastructure & DevOps

| Tool | Configuration | Purpose |
| :--- | :--- | :--- |
| **Docker Compose** | `docker-compose.yml` (PostgreSQL 16) | Local containerized database management |
| **Git** | Multi-stack `.gitignore` | Version control across frontend and backend |
| **ESLint** | `eslint.config.mjs` | Frontend linting and code quality standards |
