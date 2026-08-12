"""
FastAPI application entry point.

Exposes /health and /docs. Feature routers (clients, compliance-schedules,
tasks, checklists, dashboard) are registered below as they're implemented
— each router module lives in app/api/routes/ and is mounted here.
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
from app.api.routes import clients, compliance_schedules  # noqa: E402

app.include_router(clients.router, prefix=f"{settings.api_v1_prefix}/clients", tags=["clients"])
app.include_router(
    compliance_schedules.router,
    prefix=f"{settings.api_v1_prefix}/compliance-schedules",
    tags=["compliance-schedules"],
)

# Example (added by a future task):
#   from app.api.routes import tasks
#   app.include_router(tasks.router, prefix=f"{settings.api_v1_prefix}/tasks", tags=["tasks"])
