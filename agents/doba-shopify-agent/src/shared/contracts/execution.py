from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentTaskRequest(BaseModel):
    request_id: str = ""
    task: str
    capability: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentTaskResult(BaseModel):
    summary: str = ""
    data: dict[str, Any] = Field(default_factory=dict)

