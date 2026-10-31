"""Configuration and environment settings for ClaimLab."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    PUBLIC_ORIGIN: str = "http://127.0.0.1:5173"
    DATABASE_URL: str = "sqlite:///./data/claimlab.db"
    DATA_DIR: str = "./data"
    SESSION_SECRET: str = "dev-secret-change-in-production-min-32-chars-long!"

    # Meta Model API
    MODEL_MODE: str = "fixture"  # "live" or "fixture"
    META_API_KEY: str = ""
    META_BASE_URL: str = "https://api.meta.ai/v1"
    META_MODEL: str = "muse-spark-1.3"

    # Pricing & Budget
    MODEL_INPUT_USD_PER_MILLION: float = 0.30
    MODEL_OUTPUT_USD_PER_MILLION: float = 1.20
    APP_AI_BUDGET_USD: float = 10.00

    # Web research (TinyFish search + fetch). Empty disables the tutor's web tools.
    TINYFISH_API_KEY: str = ""
    TINYFISH_SEARCH_URL: str = "https://api.search.tinyfish.ai"
    TINYFISH_FETCH_URL: str = "https://api.fetch.tinyfish.ai"

    # Runner & Isolation
    RUNNER_IMAGE: str = "claimlab-runner:latest"
    PDF_PARSER_IMAGE: str = "claimlab-parser:latest"
    RUNNER_BACKEND: str = "local"  # "local" or "docker"

    # Agent-written experiment sandbox: a dedicated venv holding only numpy
    SANDBOX_VENV_DIR: str = "./.sandbox-venv"
    SANDBOX_TIMEOUT_SECONDS: float = 10.0
    SANDBOX_MEMORY_MB: int = 768

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def data_path(self) -> Path:
        p = Path(self.DATA_DIR).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
