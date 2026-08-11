"""
FastAPI application entry point.

Task 0 scope: the app must start, expose /docs, and expose a health check.
Feature routers (clients, compliance-schedules, tasks, checklists,
dashboard) are registered here as empty placeholders so that future tasks
plug straight into api/routes/ without touching this file's structure.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Internal MIS for HSDG & Associates, Chartered Accountants.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Basic liveness check. Does not touch the database."""
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}


# --- Feature routers ---
# Registered as they are implemented by future tasks. Each router module
# lives in app/api/routes/ and is prefixed per API_SPEC.md.
# Example (added by a future task):
#   from app.api.routes import clients
#   app.include_router(clients.router, prefix=f"{settings.api_v1_prefix}/clients", tags=["clients"])
