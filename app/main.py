from __future__ import annotations

import json
import logging
from typing import AsyncIterator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from sse_starlette.sse import EventSourceResponse

from app.agents.state import AgentState
from app.auth import JWTAuth, Principal, bearer_scheme, build_auth
from app.config import Settings, get_settings
from app.llm.factory import build_llm
from app.models import (
    AssetCreateRequest,
    AssetListResponse,
    AssetResponse,
    ChatRequest,
    ChatResponse,
    VoiceAnalyzeRequest,
    VoiceProfileResponse,
)
from app.db.factory import build_stores
from app.orchestrator import Orchestrator
from app.services.memory import AssetLog, MarketingAsset
from app.services.rag import FrameworkRetriever, InMemoryFrameworkRetriever
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
    rag: FrameworkRetriever | None = None,
    auth: JWTAuth | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    auth = auth or build_auth(settings)

    if voice_store is None or asset_log is None or session_store is None:
        default_voice, default_assets, default_sessions = build_stores(settings)
        voice_store = voice_store or default_voice
        asset_log = asset_log or default_assets
        session_store = session_store or default_sessions

    rag = rag or InMemoryFrameworkRetriever()
    voice_llm = voice_llm or build_llm(settings, role="voice")
    orchestrator = orchestrator or Orchestrator(
        build_llm(settings, role="cro"),
        build_llm(settings, role="shepherd"),
        memory=asset_log,
        rag=rag,
    )

    app = FastAPI(title="Chatoy", version="0.1.0")
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
    app.state.auth = auth

    def current_user(
        creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> Principal:
        return auth.authenticate(creds)

    def _session_key(user_id: str, session_id: str) -> str:
        # Namespacing by tenant makes sessions inherently per-user, so one
        # tenant can never read or resume another's conversation.
        return f"{user_id}:{session_id}"

    def _prepare_state(req: ChatRequest, user_id: str) -> tuple[AgentState, int, str]:
        skey = _session_key(user_id, req.session_id)
        state: AgentState = dict(session_store.get(skey))
        messages = list(state.get("messages", []))
        state["user_id"] = user_id
        if req.business_profile is not None:
            state["business_profile"] = req.business_profile
        if not state.get("voice_profile"):
            profile = voice_store.get(user_id)
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
        state, prefix_len, skey = _prepare_state(req, user.user_id)
        final = orchestrator.run(state)
        return _finish(req, final, prefix_len, skey)

    @app.post("/chat/stream")
    async def chat_stream(
        req: ChatRequest, user: Principal = Depends(current_user)
    ) -> EventSourceResponse:
        state, prefix_len, skey = _prepare_state(req, user.user_id)

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

    return app


app = create_app()
