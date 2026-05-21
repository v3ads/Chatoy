from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment / .env (prefix CHATOY_)."""

    model_config = SettingsConfigDict(
        env_prefix="CHATOY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str | None = None

    # SQLAlchemy URL, e.g. postgresql+psycopg://user:pass@host:5432/chatoy
    # Leave unset to use the in-memory stores (tests / offline dev).
    database_url: str | None = None

    # Per-role models. The strategist and the copywriter can run on different
    # models; voice analysis is a cheap structured-extraction job.
    cro_model: str = "claude-sonnet-4-6"
    shepherd_model: str = "claude-sonnet-4-6"
    voice_model: str = "claude-haiku-4-5-20251001"

    temperature: float = 0.7
    max_tokens: int = 2048

    # Force the deterministic offline LLM even when a key is present.
    use_fake_llm: bool = False

    cors_origins: str = "http://localhost:3000"

    @property
    def offline(self) -> bool:
        """True when no real model can be reached, so we use the FakeLLM."""
        return self.use_fake_llm or not self.anthropic_api_key

    @property
    def use_database(self) -> bool:
        """True when a database is configured; otherwise in-memory stores."""
        return bool(self.database_url)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def model_for(self, role: str) -> str:
        return {
            "cro": self.cro_model,
            "shepherd": self.shepherd_model,
            "voice": self.voice_model,
        }.get(role, self.cro_model)


@lru_cache
def get_settings() -> Settings:
    return Settings()
