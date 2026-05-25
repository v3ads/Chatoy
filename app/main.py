from __future__ import annotations

import json
import logging
from typing import AsyncIterator

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from sse_starlette.sse import EventSourceResponse

from app.agents.state import AgentState
from app.auth import JWTAuth, Principal, bearer_scheme, build_auth
from app.config import Settings, get_settings
from app.models import (
    AssetCreateRequest,
    AssetListResponse,
    AssetResponse,
    AvailableModel,
    ChatRequest,
    ChatResponse,
    ModelConfigResponse,
    ModelConfigUpdate,
    VoiceAnalyzeRequest,
    VoiceProfileResponse,
    CreditResponse,
    AutoRechargeRequest,
)
from app.db.factory import build_stores, CreditStore
from app.db.model_config_store import build_model_config_store
from app.db.knowledge_store import build_knowledge_retriever
from app.llm.resolver import ModelResolver, ResolvingLLM
from app.services.model_config import ModelConfigStore
from app.services.knowledge_seed import SEED_CHUNKS
from app.orchestrator import Orchestrator
from app.services.memory import AssetLog, MarketingAsset
from app.services.rag import FrameworkRetriever, InMemoryFrameworkRetriever
from app.services.stripe import StripeService
from app.services.email import EmailService
from app.services.voice_profile import (
    VoiceProfileStore,
    analyze_voice,
    render_voice_profile,
)
from app.session import SessionStore

logging.basicConfig(level=logging.INFO)


def create_app(
    settings: Settings | None = None,
    *,
    orchestrator: Orchestrator | None = None,
    voice_llm=None,
    voice_store: VoiceProfileStore | None = None,
    asset_log: AssetLog | None = None,
    session_store: SessionStore | None = None,
    credit_store: CreditStore | None = None,
    model_config_store: ModelConfigStore | None = None,
    rag: FrameworkRetriever | None = None,
    stripe_service: StripeService | None = None,
    email_service: EmailService | None = None,
    auth: JWTAuth | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    auth = auth or build_auth(settings)

    if voice_store is None or asset_log is None or session_store is None or credit_store is None:
        default_voice, default_assets, default_sessions, default_credits = build_stores(settings)
        voice_store = voice_store or default_voice
        asset_log = asset_log or default_assets
        session_store = session_store or default_sessions
        credit_store = credit_store or default_credits

    model_config_store = model_config_store or build_model_config_store(settings)
    resolver = ModelResolver(settings, model_config_store)

    rag = rag or build_knowledge_retriever(settings)
    stripe_service = stripe_service or StripeService(settings, credit_store)
    email_service = email_service or EmailService(settings)
    voice_llm = voice_llm or ResolvingLLM("voice", resolver)
    orchestrator = orchestrator or Orchestrator(
        ResolvingLLM("architect", resolver),
        ResolvingLLM("writer", resolver),
        memory=asset_log,
        rag=rag,
        credits=credit_store,
    )

    app = FastAPI(title="MythoStack", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Stash dependencies for handlers / tests.
    app.state.settings = settings
    app.state.orchestrator = orchestrator
    app.state.voice_llm = voice_llm
    app.state.voice_store = voice_store
    app.state.asset_log = asset_log
    app.state.session_store = session_store
    app.state.credit_store = credit_store
    app.state.stripe_service = stripe_service
    app.state.email_service = email_service
    app.state.auth = auth
    app.state.model_config_store = model_config_store
    app.state.model_resolver = resolver

    def current_user(
        creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> Principal:
        return auth.authenticate(creds)

    def require_admin(user: Principal = Depends(current_user)) -> Principal:
        if (user.email or "").lower() != settings.admin_email.lower():
            raise HTTPException(status_code=403, detail="Admin access required")
        return user

    def _session_key(user_id: str, session_id: str) -> str:
        # Namespacing by tenant makes sessions inherently per-user, so one
        # tenant can never read or resume another's conversation.
        return f"{user_id}:{session_id}"

    def _prepare_state(
        req: ChatRequest, user: Principal
    ) -> tuple[AgentState, int, str]:
        skey = _session_key(user.user_id, req.session_id)
        state: AgentState = dict(session_store.get(skey))
        messages = list(state.get("messages", []))
        state["user_id"] = user.user_id
        state["user_email"] = user.email
        if req.business_profile is not None:
            state["business_profile"] = req.business_profile
        if not state.get("voice_profile"):
            profile = voice_store.get(user.user_id)
            if profile:
                state["voice_profile"] = render_voice_profile(profile)
        messages.append({"role": "user", "content": req.message})
        state["messages"] = messages
        return state, len(messages), skey

    def _finish(
        req: ChatRequest, final: AgentState, prefix_len: int, skey: str
    ) -> ChatResponse:
        session_store.set(skey, final)
        new_messages = final.get("messages", [])[prefix_len:]
        reply = "\n\n".join(
            m["content"] for m in new_messages if m.get("role") == "assistant"
        )
        return ChatResponse(
            session_id=req.session_id,
            reply=reply,
            new_messages=new_messages,
            next_step=final.get("next_step", "diagnose"),
            current_strategy=final.get("current_strategy"),
            retrieved_frameworks=final.get("retrieved_frameworks", []),
        )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "offline": settings.offline}

    @app.post("/chat", response_model=ChatResponse)
    def chat(
        req: ChatRequest, user: Principal = Depends(current_user)
    ) -> ChatResponse:
        state, prefix_len, skey = _prepare_state(req, user)
        final = orchestrator.run(state)
        return _finish(req, final, prefix_len, skey)

    @app.post("/chat/stream")
    async def chat_stream(
        req: ChatRequest, user: Principal = Depends(current_user)
    ) -> EventSourceResponse:
        state, prefix_len, skey = _prepare_state(req, user)

        async def event_gen() -> AsyncIterator[dict]:
            async for kind, payload in orchestrator.stream(state):
                if kind == "token":
                    yield {"event": "token", "data": payload}
                elif kind == "error":
                    yield {"event": "error", "data": str(payload)}
                elif kind == "final":
                    resp = _finish(req, payload, prefix_len, skey)  # type: ignore[arg-type]
                    yield {"event": "final", "data": resp.model_dump_json()}
            yield {"event": "done", "data": "[DONE]"}

        return EventSourceResponse(event_gen())

    @app.delete("/sessions/{session_id}")
    def reset_session(
        session_id: str, user: Principal = Depends(current_user)
    ) -> dict:
        session_store.reset(_session_key(user.user_id, session_id))
        return {"status": "reset", "session_id": session_id}

    @app.post("/voice/analyze", response_model=VoiceProfileResponse)
    def voice_analyze(
        req: VoiceAnalyzeRequest, user: Principal = Depends(current_user)
    ) -> VoiceProfileResponse:
        profile = analyze_voice(voice_llm, req.samples)
        voice_store.save(user.user_id, profile)
        return VoiceProfileResponse(
            user_id=user.user_id,
            profile=profile,
            rendered=render_voice_profile(profile),
        )

    @app.get("/voice/me", response_model=VoiceProfileResponse)
    def voice_get(user: Principal = Depends(current_user)) -> VoiceProfileResponse:
        profile = voice_store.get(user.user_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="No voice profile for user")
        return VoiceProfileResponse(
            user_id=user.user_id,
            profile=profile,
            rendered=render_voice_profile(profile),
        )

    @app.post("/assets", response_model=AssetResponse)
    def create_asset(
        req: AssetCreateRequest, user: Principal = Depends(current_user)
    ) -> AssetResponse:
        asset = asset_log.add(
            MarketingAsset(
                user_id=user.user_id,
                asset_type=req.asset_type,
                marketing_angle=req.marketing_angle,
                content=req.content,
                metrics=req.metrics,
            )
        )
        return AssetResponse(**asset.__dict__)

    @app.get("/assets", response_model=AssetListResponse)
    def list_assets(user: Principal = Depends(current_user)) -> AssetListResponse:
        assets = asset_log.list_for(user.user_id)
        return AssetListResponse(
            user_id=user.user_id,
            assets=[AssetResponse(**a.__dict__) for a in assets],
            summary=asset_log.summarize(user.user_id),
        )

    @app.get("/credits", response_model=CreditResponse)
    def get_credits(user: Principal = Depends(current_user)) -> CreditResponse:
        row = credit_store.get(user.user_id, email=user.email)
        return CreditResponse(
            user_id=user.user_id,
            credits_balance=row.credits_balance,
            auto_recharge_enabled=row.auto_recharge_enabled,
        )

    @app.post("/credits/auto-recharge")
    def set_auto_recharge(
        req: AutoRechargeRequest, user: Principal = Depends(current_user)
    ) -> dict:
        credit_store.set_auto_recharge(user.user_id, req.enabled)
        return {"status": "ok", "auto_recharge_enabled": req.enabled}

    @app.post("/auth/notify-signup")
    async def notify_signup(user: Principal = Depends(current_user)):
        """Triggered by frontend after a new Supabase signup."""
        email_service.send_verification_email(user.email)
        return {"status": "email_sent"}

    @app.post("/webhooks/stripe")
    async def stripe_webhook(request: Request):
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        return stripe_service.handle_webhook(payload.decode("utf-8"), sig_header)

    # --- Admin: per-role model selection (OpenRouter) ---

    def _current_model_config() -> ModelConfigResponse:
        ov = model_config_store.get_overrides()
        return ModelConfigResponse(
            architect=ov.get("architect"),
            writer=ov.get("writer"),
            voice=ov.get("voice"),
        )

    @app.get("/admin/models", response_model=ModelConfigResponse)
    def get_model_config(user: Principal = Depends(require_admin)) -> ModelConfigResponse:
        return _current_model_config()

    @app.put("/admin/models", response_model=ModelConfigResponse)
    def set_model_config(
        req: ModelConfigUpdate, user: Principal = Depends(require_admin)
    ) -> ModelConfigResponse:
        model_config_store.set_overrides(
            {"architect": req.architect, "writer": req.writer, "voice": req.voice}
        )
        return _current_model_config()

    @app.get("/admin/models/available", response_model=list[AvailableModel])
    def available_models(user: Principal = Depends(require_admin)) -> list[AvailableModel]:
        headers = {}
        if settings.openrouter_api_key:
            headers["Authorization"] = f"Bearer {settings.openrouter_api_key}"
        try:
            resp = httpx.get(
                f"{settings.openrouter_base_url.rstrip('/')}/models",
                headers=headers,
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=502, detail=f"Could not fetch OpenRouter models: {exc}"
            )
        models = [
            AvailableModel(id=m["id"], name=m.get("name") or m["id"])
            for m in data
            if m.get("id")
        ]
        models.sort(key=lambda m: m.name.lower())
        return models

    # --- Admin: knowledge base (semantic RAG) ---

    @app.get("/admin/knowledge")
    def knowledge_status(user: Principal = Depends(require_admin)) -> dict:
        count = getattr(rag, "count", lambda: 0)()
        return {"count": count, "semantic": hasattr(rag, "seed")}

    @app.post("/admin/knowledge/seed")
    def seed_knowledge(user: Principal = Depends(require_admin)) -> dict:
        if not hasattr(rag, "seed"):
            raise HTTPException(
                status_code=400,
                detail="Knowledge base not configured (set MYTHOSTACK_OPENAI_API_KEY).",
            )
        count = rag.seed(SEED_CHUNKS)  # type: ignore[attr-defined]
        return {"count": count, "chunks": len(SEED_CHUNKS)}

    return app


app = create_app()
