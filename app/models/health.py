from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    environment: str
    checks: dict[str, Any]