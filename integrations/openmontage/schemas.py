from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class VideoRequirements(BaseModel):
    duration_seconds: int = Field(default=20, ge=1)
    aspect_ratio: str = "9:16"
    resolution: str = "1080x1920"
    language: str = "English"
    captions: bool = True
    voiceover: bool = True
    style: str = "Fast-paced direct-response product ad"


class ProductVideoJob(BaseModel):
    sku: str
    product_name: str
    warehouse: Optional[str] = None
    quantity: Optional[int] = None
    target_platforms: List[str] = Field(default_factory=list)
    destination_url: str = ""
    product_facts: List[str] = Field(default_factory=list)
    compliance_rules: List[str] = Field(default_factory=list)
    creative_angle: str = ""
    video_requirements: VideoRequirements = Field(default_factory=VideoRequirements)
    output_requirements: List[str] = Field(default_factory=list)
