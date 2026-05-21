from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.state import Message


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Conversation id; threads state across turns.")
    message: str = Field(..., min_length=1)
    user_id: str | None = Field(
        None, description="Used to load the saved voice profile and Stacking Wins history."
    )
    business_profile: dict | None = Field(
        None, description="Set once at session start; persisted on the session state."
    )


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    new_messages: list[Message]
    next_step: str
    current_strategy: dict | None = None
    retrieved_frameworks: list[str] = Field(default_factory=list)


class VoiceAnalyzeRequest(BaseModel):
    user_id: str
    samples: list[str] = Field(..., min_length=1)


class VoiceProfileResponse(BaseModel):
    user_id: str
    profile: dict
    rendered: str


class AssetCreateRequest(BaseModel):
    user_id: str
    asset_type: str
    marketing_angle: str = ""
    content: str = ""
    metrics: dict = Field(default_factory=dict)


class AssetResponse(BaseModel):
    user_id: str
    asset_type: str
    marketing_angle: str
    content: str
    metrics: dict
    created_at: str


class AssetListResponse(BaseModel):
    user_id: str
    assets: list[AssetResponse]
    summary: str
