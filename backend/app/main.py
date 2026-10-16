from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.schema_sync import sync_database_schema
from app.api.v1.router import api_router

# Initialize and synchronize database schema tables & columns
sync_database_schema()

# Ensure static upload directory exists
uploads_dir = Path("uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)
(uploads_dir / "stages").mkdir(parents=True, exist_ok=True)
(uploads_dir / "profiles").mkdir(parents=True, exist_ok=True)
(uploads_dir / "crops").mkdir(parents=True, exist_ok=True)
(uploads_dir / "general").mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    description="Agri-Smart Ecosystem Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Mount static files for media & stage uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|0\.0\.0\.0)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)


@app.get("/", summary="Root Status Endpoint")
def root():
    """
    Root status endpoint confirming API availability.
    """
    return {
        "name": "Agri-Smart Ecosystem API",
        "status": "running"
    }


# Include versioned API routers
app.include_router(api_router, prefix="/api/v1")
