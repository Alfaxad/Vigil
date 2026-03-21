from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Locus
    locus_api_key: str = ""
    locus_owner_private_key: str = ""
    locus_owner_address: str = ""
    locus_wallet_address: str = ""
    locus_base_url: str = "https://beta-api.paywithlocus.com/api"

    # Synthesis hackathon
    synthesis_api_key: str = ""
    synthesis_participant_id: str = ""
    synthesis_team_id: str = ""

    # Vigil config
    monitor_interval_seconds: int = 30
    risk_threshold_review: float = 0.3
    risk_threshold_alert: float = 0.7
    audit_price_usdc: float = 0.01
    claude_model: str = "claude-sonnet-4-20250514"

    # Optional fallback Anthropic key
    anthropic_api_key: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
