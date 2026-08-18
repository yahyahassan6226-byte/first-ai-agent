import logging

from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)
from fastapi.middleware.httpsredirect import (
    HTTPSRedirectMiddleware,
)
from fastapi.middleware.trustedhost import (
    TrustedHostMiddleware,
)

from app.api.chat import (
    router as chat_router,
)
from app.api.errors import (
    register_error_handlers,
)
from app.api.health import (
    router as health_router,
)
from app.config import settings
from app.logging_config import (
    setup_logging,
)


setup_logging()

logger = logging.getLogger(
    __name__
)


# =========================================================
# DOCS
# =========================================================

docs_url = (
    "/docs"
    if settings.docs_enabled
    else None
)

redoc_url = (
    "/redoc"
    if settings.docs_enabled
    else None
)

openapi_url = (
    "/openapi.json"
    if settings.docs_enabled
    else None
)


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title=settings.app_name,
    description=(
        "Production-style API for "
        "the LangGraph AI Agent."
    ),
    version=settings.app_version,
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
    debug=settings.debug,
)


# =========================================================
# TRUSTED HOSTS
# =========================================================

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=(
        settings.get_allowed_hosts()
    ),
)


# =========================================================
# HTTPS
# =========================================================

if settings.force_https:

    app.add_middleware(
        HTTPSRedirectMiddleware
    )


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.get_cors_origins()
    ),
    allow_credentials=(
        settings.cors_allow_credentials
    ),
    allow_methods=[
        "GET",
        "POST",
        "OPTIONS",
    ],
    allow_headers=[
        "Content-Type",
        "Authorization",
    ],
)


# =========================================================
# ERROR HANDLERS
# =========================================================

register_error_handlers(
    app
)


# =========================================================
# STARTUP
# =========================================================

@app.on_event("startup")
def startup_event() -> None:

    logger.info(
        "API started. environment=%s",
        settings.app_environment,
    )

    logger.info(
        "Debug mode=%s",
        settings.debug,
    )

    logger.info(
        "HTTPS enforcement=%s",
        settings.force_https,
    )


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root() -> dict:

    return {
        "message": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_environment,
        "status": "running",
    }


# =========================================================
# FRONTEND CONFIG
# =========================================================

@app.get("/frontend-config")
def frontend_config() -> dict:

    return {
        "api_name": settings.app_name,
        "api_version": settings.app_version,
        "environment": settings.app_environment,
        "endpoints": {
            "chat": "/chat",
            "stream": "/chat/stream",
            "health": "/health",
        },
    }


# =========================================================
# ROUTERS
# =========================================================

app.include_router(
    health_router
)

app.include_router(
    chat_router
)