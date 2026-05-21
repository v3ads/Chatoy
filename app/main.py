from __future__ import annotations

import json
import logging
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from app.agents.state import AgentState
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
from app.orchestrator import Orchestrator
from app.services.memory import AssetLog, InMemoryAssetLog, MarketingAsset
from app.services.rag import FrameworkRetriever, InMemoryFrameworkRetriever
from app.services.voice_profile import (
    InMemoryVoiceProfileStore,
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
) -> FastAPI:
    settings = settings or get_settings()

    asset_log = asset_log or InMemoryAssetLog()
    rag = rag or InMemoryFrameworkRetriever()
    voice_store = voice_store or InMemoryVoiceProfileStore()
    session_store = session_store or SessionStore()
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

    def _prepare_state(req: ChatRequest) -> tuple[AgentState, int]:
        state: AgentState = dict(session_store.get(req.session_id))
        messages = list(state.get("messages", []))
        if req.user_id:
            state["user_id"] = req.user_id
        if req.business_profile is not None:
            state["business_profile"] = req.business_profile
        if req.user_id and not state.get("voice_profile"):
            profile = voice_store.get(req.user_id)
            if profile:
                state["voice_profile"] = render_voice_profile(profile)
        messages.append({"role": "user", "content": req.message})
        state["messages"] = messages
        return state, len(messages)

    def _finish(req: ChatRequest, final: AgentState, prefix_len: int) -> ChatResponse:
        session_store.set(req.session_id, final)
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
    def chat(req: ChatRequest) -> ChatResponse:
        state, prefix_len = _prepare_state(req)
        final = orchestrator.run(state)
        return _finish(req, final, prefix_len)

    @app.post("/chat/stream")
    async def chat_stream(req: ChatRequest) -> EventSourceResponse:
        state, prefix_len = _prepare_state(req)

        async def event_gen() -> AsyncIterator[dict]:
            async for kind, payload in orchestrator.stream(state):
                if kind == "token":
                    yield {"event": "token", "data": payload}
                elif kind == "error":
                    yield {"event": "error", "data": str(payload)}
                elif kind == "final":
                    resp = _finish(req, payload, prefix_len)  # type: ignore[arg-type]
                    yield {"event": "final", "data": resp.model_dump_json()}
            yield {"event": "done", "data": "[DONE]"}

        return EventSourceResponse(event_gen())

    @app.delete("/sessions/{session_id}")
    def reset_session(session_id: str) -> dict:
        session_store.reset(session_id)
        return {"status": "reset", "session_id": session_id}

    @app.post("/voice/analyze", response_model=VoiceProfileResponse)
    def voice_analyze(req: VoiceAnalyzeRequest) -> VoiceProfileResponse:
        profile = analyze_voice(voice_llm, req.samples)
        voice_store.save(req.user_id, profile)
        return VoiceProfileResponse(
            user_id=req.user_id,
            profile=profile,
            rendered=render_voice_profile(profile),
        )

    @app.get("/voice/{user_id}", response_model=VoiceProfileResponse)
    def voice_get(user_id: str) -> VoiceProfileResponse:
        profile = voice_store.get(user_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="No voice profile for user")
        return VoiceProfileResponse(
            user_id=user_id, profile=profile, rendered=render_voice_profile(profile)
        )

    @app.post("/assets", response_model=AssetResponse)
    def create_asset(req: AssetCreateRequest) -> AssetResponse:
        asset = asset_log.add(
            MarketingAsset(
                user_id=req.user_id,
                asset_type=req.asset_type,
                marketing_angle=req.marketing_angle,
                content=req.content,
                metrics=req.metrics,
            )
        )
        return AssetResponse(**asset.__dict__)

    @app.get("/assets/{user_id}", response_model=AssetListResponse)
    def list_assets(user_id: str) -> AssetListResponse:
        assets = asset_log.list_for(user_id)
        return AssetListResponse(
            user_id=user_id,
            assets=[AssetResponse(**a.__dict__) for a in assets],
            summary=asset_log.summarize(user_id),
        )

    return app


app = create_app()
