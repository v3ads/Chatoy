from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.state import Message


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Conversation id; threads state across turns.")
    message: str = Field(..., min_length=1)
    project_id: str | None = Field(
        None, description="Active project. Omit to use the user's default project."
    )
    business_profile: dict | None = Field(
        None, description="Optional overrides merged into the project's profile."
    )


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    new_messages: list[Message]
    next_step: str
    current_strategy: dict | None = None
    retrieved_frameworks: list[str] = Field(default_factory=list)


class VoiceAnalyzeRequest(BaseModel):
    samples: list[str] = Field(..., min_length=1)
    project_id: str | None = None


class VoiceProfileResponse(BaseModel):
    user_id: str
    profile: dict
    rendered: str


class AssetCreateRequest(BaseModel):
    asset_type: str
    marketing_angle: str = ""
    content: str = ""
    metrics: dict = Field(default_factory=dict)
    project_id: str | None = None


class AssetMetricsUpdate(BaseModel):
    metrics: dict = Field(..., description="Reported results, e.g. {'open_rate': '42%'}.")
    project_id: str | None = None


class AssetResponse(BaseModel):
    id: int | None = None
    user_id: str
    project_id: str = ""
    asset_type: str
    marketing_angle: str
    content: str
    metrics: dict
    created_at: str


class AssetListResponse(BaseModel):
    user_id: str
    project_id: str = ""
    assets: list[AssetResponse]
    summary: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    business_profile: dict = Field(default_factory=dict)
    voice_profile: dict = Field(default_factory=dict)
    created_at: str
    updated_at: str


class ProjectCreateRequest(BaseModel):
    name: str = Field("My Project", min_length=1, max_length=255)


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(None, max_length=255)
    business_profile: dict | None = None


class CreditResponse(BaseModel):
    user_id: str
    credits_balance: float
    auto_recharge_enabled: bool


class AutoRechargeRequest(BaseModel):
    enabled: bool


class AvailableModel(BaseModel):
    id: str
    name: str


class AvailableModelsResponse(BaseModel):
    models: list[AvailableModel] = Field(default_factory=list)
    # Human-readable explanation when the list is empty (shown in the admin UI).
    reason: str | None = None


class ModelConfigResponse(BaseModel):
    # Per-role OpenRouter model overrides (empty/None = use the Claude default).
    architect: str | None = None
    writer: str | None = None
    voice: str | None = None


class ModelConfigUpdate(BaseModel):
    architect: str | None = None
    writer: str | None = None
    voice: str | None = None
