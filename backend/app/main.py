from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.auth import router as auth_router
from app.routes.consents import router as consents_router
from app.routes.checkins import router as checkins_router
from app.routes.journal import router as journal_router
from app.routes.plans import router as plans_router
from app.routes.actions import router as actions_router
from app.routes.reflections import router as reflections_router
from app.routes.support import router as support_router
from app.routes.privacy import router as privacy_router
from app.routes.demo import router as demo_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="Pause AI Student Wellness Companion API",
    description="A consent-first self-reflection companion for university students. Not a therapist, diagnostic tool, or emergency service.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

configured_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
if "*" in configured_origins:
    # Origin regex allows wildcard origins while supporting Authorization headers
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    all_origins = list(set(default_origins + configured_origins))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=all_origins,
        allow_origin_regex=r"https://.*\.onrender\.com",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount all versioned API routes
app.include_router(auth_router)
app.include_router(consents_router)
app.include_router(checkins_router)
app.include_router(journal_router)
app.include_router(plans_router)
app.include_router(actions_router)
app.include_router(reflections_router)
app.include_router(support_router)
app.include_router(privacy_router)
app.include_router(demo_router)

@app.get("/health", status_code=status.HTTP_200_OK, tags=["System"])
@app.get("/api/v1/health", status_code=status.HTTP_200_OK, tags=["System"])
@app.get("/api/health", status_code=status.HTTP_200_OK, tags=["System"])
async def health_check():
    """
    Health check returning operational status without revealing sensitive internal details.
    """
    return {
        "status": "healthy",
        "service": "pause-wellness-api",
        "version": "1.0.0"
    }

@app.get("/", tags=["System"])
async def root():
    return {
        "service": "Pause AI Student Wellness Companion API",
        "docs": "/docs",
        "version": "1.0.0"
    }
