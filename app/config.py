from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment / .env (prefix MYTHOSTACK_)."""

    model_config = SettingsConfigDict(
        env_prefix="MYTHOSTACK_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str | None = None
    stripe_api_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_pro_price_id: str | None = None
    stripe_credit_pack_price_id: str | None = None
    # Credit economy: how much each generated asset costs, and how many credits a
    # credit-pack purchase / a Pro month grants.
    credit_cost_per_asset: float = 1.0
    credit_pack_credits: int = 50
    pro_monthly_credits: int = 100

    # SQLAlchemy URL, e.g. postgresql+psycopg://user:pass@host:5432/chatoy
    # Leave unset to use the in-memory stores (tests / offline dev).
    database_url: str | None = None

    # Auth. Verifies Supabase bearer JWTs. Two modes:
    #   1. Asymmetric signing keys (current Supabase default): set supabase_url
    #      (or jwks_url) and tokens are verified against the project's public
    #      JWKS using ES256/RS256.
    #   2. Legacy HS256 shared secret: set jwt_secret.
    # Endpoints fail closed if neither is configured, unless auth_disabled.
    supabase_url: str | None = None
    jwks_url: str | None = None
    jwt_secret: str | None = None
    jwt_audience: str = "authenticated"
    jwt_algorithms: str = "HS256"
    auth_disabled: bool = False
    dev_user_id: str = "dev-user"
    admin_email: str = "vipaymanshalaby@gmail.com"
    brevo_api_key: str | None = None
    sender_email: str = "ayman@mythostack.com"
    sender_name: str = "Ayman from MythoStack"
    frontend_url: str = "https://mythostack.com"

    # Per-role models. The strategist and the copywriter can run on different
    # models; voice analysis is a cheap structured-extraction job.
    architect_model: str = "claude-sonnet-4-6"
    writer_model: str = "claude-sonnet-4-6"
    voice_model: str = "claude-haiku-4-5-20251001"

    temperature: float = 0.7
    max_tokens: int = 2048

    # OpenRouter (admin model selector). When set, the admin can route agent
    # roles through OpenRouter models; each falls back to the Anthropic default
    # above if the chosen model errors or times out.
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # OpenAI embeddings power the pgvector knowledge base (semantic RAG). When
    # unset, the app falls back to the built-in keyword framework library.
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    # Firecrawl scrapes a website the user pastes so the Architect can read the
    # business straight from their site. Unset → the feature is simply skipped.
    firecrawl_api_key: str | None = None
    firecrawl_base_url: str = "https://api.firecrawl.dev"
    # How many of the most relevant pages (home, pricing, about, product…) to pull.
    firecrawl_max_pages: int = 6

    # After each turn, run a cheap extraction to fold newly stated business
    # facts into the active project's profile (one small model call per turn).
    profile_evolution: bool = True

    # Force the deterministic offline LLM even when a key is present.
    use_fake_llm: bool = False

    cors_origins: str = "http://localhost:3000,https://mythostack.com"
    # Regex (full-match) for additional allowed browser origins: the apex domain
    # and any subdomain of mythostack.com (e.g. www), plus Vercel preview builds.
    # A too-narrow origin list is what rejects the /chat/stream CORS preflight.
    cors_origin_regex: str = (
        r"https://([a-z0-9-]+\.)*mythostack\.com|https://[a-z0-9-]+\.vercel\.app"
    )

    @property
    def offline(self) -> bool:
        """True when no real model can be reached, so we use the FakeLLM."""
        return self.use_fake_llm or not self.anthropic_api_key

    @property
    def use_database(self) -> bool:
        """True when a database is configured; otherwise in-memory stores."""
        return bool(self.database_url)

    @property
    def resolved_jwks_url(self) -> str | None:
        """JWKS endpoint for asymmetric verification, derived from supabase_url
        if not given explicitly."""
        if self.jwks_url:
            return self.jwks_url
        if self.supabase_url:
            return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        return None

    @property
    def jwt_issuer(self) -> str | None:
        """Expected token issuer when a Supabase URL is configured."""
        if self.supabase_url:
            return f"{self.supabase_url.rstrip('/')}/auth/v1"
        return None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def model_for(self, role: str) -> str:
        return {
            "architect": self.architect_model,
            "writer": self.writer_model,
            "voice": self.voice_model,
        }.get(role, self.architect_model)


@lru_cache
def get_settings() -> Settings:
    return Settings()
