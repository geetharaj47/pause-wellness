from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.auth import router as auth_router

app = FastAPI(
    title="MindTrace API",
    description="Personalized AI for Longitudinal Mental Wellness Monitoring and Self-Reflection",
    version="1.0.0"
)

# Configure CORS Middleware for frontend access
origins = [
    "http://localhost:5173",  # Vite default
    "http://127.0.0.1:5173",
    "http://localhost:3000",  # Create React App default
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event handler to verify database connection and run schema migrations
@app.on_event("startup")
async def on_startup():
    await init_db()

# Mount authentication routers
app.include_router(auth_router)

# Health check route
@app.get("/api/health", status_code=status.HTTP_200_OK, tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected",
        "api_version": "1.0.0"
    }

# Root redirect route
@app.get("/", tags=["System"])
async def root():
    return {
        "message": "Welcome to MindTrace API. Refer to /docs for Swagger documentation."
    }
