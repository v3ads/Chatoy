from __future__ import annotations

import asyncio
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
    AssetMetricsUpdate,
    AssetResponse,
    AvailableModel,
    AvailableModelsResponse,
    BillingUrlResponse,
    CheckoutRequest,
    ChatRequest,
    ChatResponse,
    ModelConfigResponse,
    ModelConfigUpdate,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
    VoiceAnalyzeRequest,
    VoiceProfileResponse,
    CreditResponse,
    AutoRechargeRequest,
)
from app.db.factory import build_stores, CreditStore
from app.db.model_config_store import build_model_config_store
from app.db.knowledge_store import build_knowledge_retriever
from app.db.project_store import build_project_store
from app.db.project_memory import build_project_recall
from app.llm.resolver import ModelResolver, ResolvingLLM
from app.services.model_config import ModelConfigStore
from app.services.knowledge_seed import SEED_CHUNKS
from app.orchestrator import Orchestrator
from app.services.firecrawl import FirecrawlClient, build_scraper, extract_first_url
from app.services.memory import AssetLog, MarketingAsset
from app.services.profile_extract import evolve_business_profile
from app.services.projects import Project, ProjectStore, merge_profile
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
    project_store: ProjectStore | None = None,
    rag: FrameworkRetriever | None = None,
    scraper: FirecrawlClient | None = None,
    stripe_service: StripeService | None = None,
    email_service: EmailService | None = None,
    auth: JWTAuth | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    auth = auth or build_auth(settings)
    scraper = scraper or build_scraper(settings)

    if voice_store is None or asset_log is None or session_store is None or credit_store is None:
        default_voice, default_assets, default_sessions, default_credits = build_stores(settings)
        voice_store = voice_store or default_voice
        asset_log = asset_log or default_assets
        session_store = session_store or default_sessions
        credit_store = credit_store or default_credits

    model_config_store = model_config_store or build_model_config_store(settings)
    resolver = ModelResolver(settings, model_config_store)

    project_store = project_store or build_project_store(settings)
    rag = rag or build_knowledge_retriever(settings)
    recall = build_project_recall(settings)
    stripe_service = stripe_service or StripeService(settings, credit_store)
    email_service = email_service or EmailService(settings)
    voice_llm = voice_llm or ResolvingLLM("voice", resolver)
    orchestrator = orchestrator or Orchestrator(
        ResolvingLLM("architect", resolver),
        ResolvingLLM("writer", resolver),
        memory=asset_log,
        rag=rag,
        recall=recall,
        credits=credit_store,
    )

    app = FastAPI(title="MythoStack", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=settings.cors_origin_regex or None,
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
    app.state.project_store = project_store
    app.state.project_recall = recall
    app.state.scraper = scraper

    def current_user(
        creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> Principal:
        return auth.authenticate(creds)

    def require_admin(user: Principal = Depends(current_user)) -> Principal:
        if (user.email or "").lower() != settings.admin_email.lower():
            raise HTTPException(status_code=403, detail="Admin access required")
        return user

    def _session_key(project_id: str, session_id: str) -> str:
        # Sessions are namespaced by project (which is owned by one user), so a
        # conversation's state is inherently scoped to its project.
        return f"{project_id}:{session_id}"

    def _resolve_project(user: Principal, project_id: str | None) -> Project:
        if project_id:
            project = project_store.get(project_id)
            if project is None or project.user_id != user.user_id:
                raise HTTPException(status_code=404, detail="Project not found")
            return project
        return project_store.ensure_default(user.user_id)

    def _prepare_state(
        req: ChatRequest, user: Principal
    ) -> tuple[AgentState, int, str, Project]:
        project = _resolve_project(user, req.project_id)
        skey = _session_key(project.id, req.session_id)
        state: AgentState = dict(session_store.get(skey))
        messages = list(state.get("messages", []))
        state["user_id"] = user.user_id
        state["user_email"] = user.email
        state["project_id"] = project.id
        # Always start from the project's accumulated profile; merge any
        # per-request overrides on top so the agent has the full picture.
        profile = dict(project.business_profile or {})
        if req.business_profile:
            profile = merge_profile(profile, req.business_profile)
        # If the user pasted a website, scrape it once (per URL) so the Architect
        # can read the business straight from their site.
        if scraper is not None:
            url = extract_first_url(req.message)
            if url:
                if profile.get("website") != url:
                    profile = merge_profile(profile, {"website": url})
                    project.business_profile = profile
                    project_store.update(project.id, business_profile=profile)
                if state.get("website_url") != url or not state.get("website_content"):
                    content = scraper.gather(url)
                    if content:
                        state["website_url"] = url
                        state["website_content"] = content
        state["business_profile"] = profile
        if not state.get("voice_profile") and project.voice_profile:
            state["voice_profile"] = render_voice_profile(project.voice_profile)
        messages.append({"role": "user", "content": req.message})
        state["messages"] = messages
        return state, len(messages), skey, project

    def _post_turn(final: AgentState, project: Project) -> None:
        """The learning loop: log the asset just produced, remember it for
        semantic recall, and evolve the project's business profile."""
        messages = final.get("messages", [])
        strategy = final.get("current_strategy") or {}

        # (#1)+(#4) The writer produced an asset this turn — log and remember it.
        if final.get("next_step") == "refine" and strategy:
            content = next(
                (m["content"] for m in reversed(messages) if m.get("role") == "assistant"),
                "",
            )
            if content.strip():
                asset_type = str(strategy.get("asset_type") or "general")
                asset_log.add(
                    MarketingAsset(
                        user_id=final.get("user_id", ""),
                        project_id=project.id,
                        asset_type=asset_type,
                        marketing_angle=str(strategy.get("marketing_angle") or ""),
                        content=content,
                    )
                )
                if recall is not None:
                    recall.remember(project.id, asset_type, content)
                # Meter usage: each generated asset costs credits (admin is exempt).
                is_admin = (final.get("user_email") or "").lower() == settings.admin_email.lower()
                if not is_admin and final.get("user_id"):
                    try:
                        credit_store.deduct(final["user_id"], settings.credit_cost_per_asset)
                    except Exception:  # noqa: BLE001 — metering must not break the turn
                        pass

        # (#3) Fold newly stated facts (and any locked strategy) into the profile.
        if settings.profile_evolution:
            last_user = next(
                (m["content"] for m in reversed(messages) if m.get("role") == "user"), ""
            )
            try:
                merged = evolve_business_profile(voice_llm, project.business_profile, last_user)
                if strategy:
                    merged = merge_profile(
                        merged,
                        {
                            k: strategy.get(k)
                            for k in ("audience", "primary_goal", "marketing_angle")
                        },
                    )
                if merged != (project.business_profile or {}):
                    project_store.update(project.id, business_profile=merged)
            except Exception:  # noqa: BLE001 — learning is best-effort, never fatal
                pass

    def _finish(
        req: ChatRequest, final: AgentState, prefix_len: int, skey: str, project: Project
    ) -> ChatResponse:
        session_store.set(skey, final)
        new_messages = final.get("messages", [])[prefix_len:]
        reply = "\n\n".join(
            m["content"] for m in new_messages if m.get("role") == "assistant"
        )
        resp = ChatResponse(
            session_id=req.session_id,
            reply=reply,
            new_messages=new_messages,
            next_step=final.get("next_step", "diagnose"),
            current_strategy=final.get("current_strategy"),
            retrieved_frameworks=final.get("retrieved_frameworks", []),
        )
        _post_turn(final, project)
        return resp

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "offline": settings.offline}

    @app.get("/me")
    def me(user: Principal = Depends(current_user)) -> dict:
        return {
            "user_id": user.user_id,
            "email": user.email,
            "is_admin": (user.email or "").lower() == settings.admin_email.lower(),
        }

    @app.post("/chat", response_model=ChatResponse)
    def chat(
        req: ChatRequest, user: Principal = Depends(current_user)
    ) -> ChatResponse:
        state, prefix_len, skey, project = _prepare_state(req, user)
        final = orchestrator.run(state)
        return _finish(req, final, prefix_len, skey, project)

    @app.post("/chat/stream")
    async def chat_stream(
        req: ChatRequest, user: Principal = Depends(current_user)
    ) -> EventSourceResponse:
        # _prepare_state may scrape a website (blocking I/O) — keep it off the loop.
        state, prefix_len, skey, project = await asyncio.to_thread(_prepare_state, req, user)

        async def event_gen() -> AsyncIterator[dict]:
            async for kind, payload in orchestrator.stream(state):
                if kind == "token":
                    yield {"event": "token", "data": payload}
                elif kind == "error":
                    yield {"event": "error", "data": str(payload)}
                elif kind == "final":
                    # _finish persists state and runs the learning loop (incl. a
                    # model call) — keep that off the event loop.
                    resp = await asyncio.to_thread(
                        _finish, req, payload, prefix_len, skey, project  # type: ignore[arg-type]
                    )
                    yield {"event": "final", "data": resp.model_dump_json()}
            yield {"event": "done", "data": "[DONE]"}

        return EventSourceResponse(event_gen())

    @app.delete("/sessions/{session_id}")
    def reset_session(
        session_id: str,
        user: Principal = Depends(current_user),
        project_id: str | None = None,
    ) -> dict:
        project = _resolve_project(user, project_id)
        session_store.reset(_session_key(project.id, session_id))
        return {"status": "reset", "session_id": session_id}

    # --- Projects (per-user workspaces that hold per-project intelligence) ---

    def _project_response(p: Project) -> ProjectResponse:
        return ProjectResponse(
            id=p.id,
            name=p.name,
            business_profile=p.business_profile or {},
            voice_profile=p.voice_profile or {},
            created_at=p.created_at,
            updated_at=p.updated_at,
        )

    @app.get("/projects", response_model=list[ProjectResponse])
    def list_projects(user: Principal = Depends(current_user)) -> list[ProjectResponse]:
        projects = project_store.list_for(user.user_id)
        if not projects:
            projects = [project_store.ensure_default(user.user_id)]
        return [_project_response(p) for p in projects]

    @app.post("/projects", response_model=ProjectResponse)
    def create_project(
        req: ProjectCreateRequest, user: Principal = Depends(current_user)
    ) -> ProjectResponse:
        return _project_response(project_store.create(user.user_id, req.name))

    @app.get("/projects/{project_id}", response_model=ProjectResponse)
    def get_project(
        project_id: str, user: Principal = Depends(current_user)
    ) -> ProjectResponse:
        return _project_response(_resolve_project(user, project_id))

    @app.put("/projects/{project_id}", response_model=ProjectResponse)
    def update_project(
        project_id: str,
        req: ProjectUpdateRequest,
        user: Principal = Depends(current_user),
    ) -> ProjectResponse:
        project = _resolve_project(user, project_id)
        business_profile = (
            merge_profile(project.business_profile, req.business_profile)
            if req.business_profile is not None
            else None
        )
        updated = project_store.update(
            project_id, name=req.name, business_profile=business_profile
        )
        return _project_response(updated or project)

    @app.delete("/projects/{project_id}")
    def delete_project(
        project_id: str, user: Principal = Depends(current_user)
    ) -> dict:
        _resolve_project(user, project_id)  # 404s unless the caller owns it
        project_store.delete(project_id)
        return {"status": "deleted", "id": project_id}

    @app.post("/voice/analyze", response_model=VoiceProfileResponse)
    def voice_analyze(
        req: VoiceAnalyzeRequest, user: Principal = Depends(current_user)
    ) -> VoiceProfileResponse:
        project = _resolve_project(user, req.project_id)
        profile = analyze_voice(voice_llm, req.samples)
        project_store.update(project.id, voice_profile=profile)
        return VoiceProfileResponse(
            user_id=user.user_id,
            profile=profile,
            rendered=render_voice_profile(profile),
        )

    @app.get("/voice/me", response_model=VoiceProfileResponse)
    def voice_get(
        user: Principal = Depends(current_user), project_id: str | None = None
    ) -> VoiceProfileResponse:
        project = _resolve_project(user, project_id)
        profile = project.voice_profile
        if not profile:
            raise HTTPException(status_code=404, detail="No voice profile for this project")
        return VoiceProfileResponse(
            user_id=user.user_id,
            profile=profile,
            rendered=render_voice_profile(profile),
        )

    @app.post("/assets", response_model=AssetResponse)
    def create_asset(
        req: AssetCreateRequest, user: Principal = Depends(current_user)
    ) -> AssetResponse:
        project = _resolve_project(user, req.project_id)
        asset = asset_log.add(
            MarketingAsset(
                user_id=user.user_id,
                project_id=project.id,
                asset_type=req.asset_type,
                marketing_angle=req.marketing_angle,
                content=req.content,
                metrics=req.metrics,
            )
        )
        if recall is not None and req.content.strip():
            recall.remember(project.id, req.asset_type, req.content)
        return AssetResponse(**asset.__dict__)

    @app.get("/assets", response_model=AssetListResponse)
    def list_assets(
        user: Principal = Depends(current_user), project_id: str | None = None
    ) -> AssetListResponse:
        project = _resolve_project(user, project_id)
        assets = asset_log.list_for(project.id)
        return AssetListResponse(
            user_id=user.user_id,
            project_id=project.id,
            assets=[AssetResponse(**a.__dict__) for a in assets],
            summary=asset_log.summarize(project.id),
        )

    @app.patch("/assets/{asset_id}", response_model=AssetResponse)
    def report_asset_metrics(
        asset_id: int,
        req: AssetMetricsUpdate,
        user: Principal = Depends(current_user),
    ) -> AssetResponse:
        project = _resolve_project(user, req.project_id)
        updated = asset_log.update_metrics(asset_id, req.metrics, project_id=project.id)
        if updated is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        return AssetResponse(**updated.__dict__)

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

    @app.post("/billing/checkout", response_model=BillingUrlResponse)
    def billing_checkout(
        req: CheckoutRequest, user: Principal = Depends(current_user)
    ) -> BillingUrlResponse:
        base = settings.frontend_url.rstrip("/")
        url = stripe_service.create_checkout_session(
            user_id=user.user_id,
            email=user.email,
            kind=req.kind,
            success_url=f"{base}/account?billing=success",
            cancel_url=f"{base}/account?billing=cancel",
        )
        if not url:
            raise HTTPException(status_code=400, detail="Billing isn't configured yet.")
        return BillingUrlResponse(url=url)

    @app.post("/billing/portal", response_model=BillingUrlResponse)
    def billing_portal(user: Principal = Depends(current_user)) -> BillingUrlResponse:
        url = stripe_service.create_portal_session(
            user.email, return_url=f"{settings.frontend_url.rstrip('/')}/account"
        )
        if not url:
            raise HTTPException(
                status_code=400,
                detail="No subscription to manage yet, or billing isn't configured.",
            )
        return BillingUrlResponse(url=url)

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

    @app.get("/admin/models/available", response_model=AvailableModelsResponse)
    def available_models(
        user: Principal = Depends(require_admin),
    ) -> AvailableModelsResponse:
        # Best-effort: an empty list just means the dropdowns offer "Default
        # (Claude)". We never error the page — instead we report WHY it's empty so
        # the admin UI can show it directly.
        if not settings.openrouter_api_key:
            return AvailableModelsResponse(
                reason="No OpenRouter API key is set on the server (MYTHOSTACK_OPENROUTER_API_KEY)."
            )
        try:
            resp = httpx.get(
                f"{settings.openrouter_base_url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
                timeout=8.0,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            if code == 401:
                reason = "OpenRouter rejected the API key (401 Unauthorized) — it may be invalid or rotated."
            elif code == 429:
                reason = "OpenRouter rate-limited the request (429) — try again shortly."
            else:
                reason = f"OpenRouter returned HTTP {code}."
            logging.warning("OpenRouter model list unavailable: %s", exc)
            return AvailableModelsResponse(reason=reason)
        except Exception as exc:  # noqa: BLE001 — timeout / connection / parse
            logging.warning("OpenRouter model list unavailable: %s", exc)
            return AvailableModelsResponse(
                reason=f"Couldn't reach OpenRouter ({type(exc).__name__})."
            )
        models = [
            AvailableModel(id=m["id"], name=m.get("name") or m["id"])
            for m in data
            if m.get("id")
        ]
        models.sort(key=lambda m: m.name.lower())
        return AvailableModelsResponse(models=models)

    # --- Admin: knowledge base (semantic RAG) ---

    @app.get("/admin/knowledge")
    def knowledge_status(user: Principal = Depends(require_admin)) -> dict:
        count = getattr(rag, "count", lambda: 0)()
        backend = getattr(rag, "backend", None)
        return {
            "count": count,
            "semantic": hasattr(rag, "seed"),
            "backend": backend,
            "persistent": backend == "PgVectorKnowledgeStore",
        }

    @app.post("/admin/knowledge/seed")
    def seed_knowledge(user: Principal = Depends(require_admin)) -> dict:
        if not hasattr(rag, "seed"):
            return {
                "ok": False,
                "count": 0,
                "chunks": len(SEED_CHUNKS),
                "reason": "Semantic search isn't configured (set MYTHOSTACK_OPENAI_API_KEY). "
                "Agents are using the built-in keyword framework library.",
            }
        try:
            count = rag.seed(SEED_CHUNKS)  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001 — degrade to keyword library, never 500 the admin
            return {
                "ok": False,
                "count": getattr(rag, "count", lambda: 0)(),
                "chunks": len(SEED_CHUNKS),
                "reason": f"Couldn't reach the embeddings provider ({type(exc).__name__}): {exc}. "
                "Agents will keep using the built-in keyword library until this is fixed.",
            }
        return {"ok": True, "count": count, "chunks": len(SEED_CHUNKS)}

    return app


app = create_app()
