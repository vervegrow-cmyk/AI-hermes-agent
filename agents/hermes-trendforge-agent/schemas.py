from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    agent: str
    version: str = "0.1.0"
    environment: str
    capabilities: list[str] = Field(default_factory=list)


class ExecuteRequest(BaseModel):
    request_id: str = Field(default="", description="External request correlation id.")
    task: str = Field(..., description="The requested agent task.")
    capability: str = Field(default="", description="Requested business capability.")
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecuteResponse(BaseModel):
    ok: bool = True
    agent: str
    capability: str = ""
    request_id: str = ""
    status: str = "success"
    summary: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
