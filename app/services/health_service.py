import logging
from pathlib import Path

from app.config import settings


logger = logging.getLogger(__name__)


def check_memory_db() -> dict:
    """
    Hubi LangGraph SQLite memory database-ka.
    """

    try:
        db_path = Path(
            settings.rag_agent_memory_db
        )

        return {
            "status": "healthy",
            "path": str(db_path),
            "exists": db_path.exists(),
        }

    except Exception as error:
        logger.exception(
            "Memory DB health check failed."
        )

        return {
            "status": "unhealthy",
            "error": str(error),
        }


def check_rag_database() -> dict:
    """
    Hubi RAG Chroma directory-ga.
    """

    try:
        rag_path = Path(
            settings.rag_chroma_dir
        )

        if not rag_path.exists():
            return {
                "status": "unhealthy",
                "path": str(rag_path),
                "error": (
                    "RAG vector database lama helin."
                ),
            }

        return {
            "status": "healthy",
            "path": str(rag_path),
        }

    except Exception as error:
        logger.exception(
            "RAG health check failed."
        )

        return {
            "status": "unhealthy",
            "error": str(error),
        }


def check_agent() -> dict:
    """
    Hubi in Agent module-ka la import-gareyn karo.

    Halkan LLM request dhab ah ma dirayno,
    si /health uusan qaali ama gaabis u noqon.
    """

    try:
        from app.agents.agent import graph

        if graph is None:
            return {
                "status": "unhealthy",
                "error": "Agent graph lama heli karo.",
            }

        return {
            "status": "healthy",
        }

    except Exception as error:
        logger.exception(
            "Agent health check failed."
        )

        return {
            "status": "unhealthy",
            "error": str(error),
        }


def get_health_status() -> dict:
    """
    Samee application health report.
    """

    checks = {
        "api": {
            "status": "healthy",
        },
        "agent": check_agent(),
        "memory": check_memory_db(),
        "rag": check_rag_database(),
    }

    all_healthy = all(
        item.get("status") == "healthy"
        for item in checks.values()
    )

    overall_status = (
        "healthy"
        if all_healthy
        else "degraded"
    )

    return {
        "status": overall_status,
        "environment": settings.app_environment,
        "checks": checks,
    }