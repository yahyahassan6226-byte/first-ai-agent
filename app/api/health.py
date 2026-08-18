import logging

from fastapi import APIRouter

from app.models.health import (
    HealthResponse,
)
from app.services.health_service import (
    get_health_status,
)


logger = logging.getLogger(
    __name__
)


router = APIRouter(
    tags=["Health"],
)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application health check",
    description=(
        "Check API, Agent, SQLite memory, "
        "and RAG vector database status."
    ),
)
def health_check() -> HealthResponse:

    logger.info(
        "Health check requested."
    )

    result = get_health_status()

    return HealthResponse(
        status=result["status"],
        environment=result["environment"],
        checks=result["checks"],
    )