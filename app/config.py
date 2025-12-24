# Support both pydantic v1 and v2. In v2, BaseSettings moved to pydantic-settings.
try:
    # Try v1-style import first (works if pydantic v1 or if v2 kept compatibility)
    from pydantic import BaseSettings
except Exception as first_exc:
    try:
        # Fallback for pydantic v2: pydantic-settings package
        from pydantic_settings import BaseSettings
    except Exception:
        # Re-raise the original error to surface the most relevant message
        raise first_exc


class Settings(BaseSettings):
    POLL_INTERVAL: int = 10
    MAX_SERVERS: int = 100
    POLL_CONCURRENCY: int = 10
    HTTPX_TIMEOUT_SECONDS: int = 5
    RESTART_STOP_TIMEOUT_SECONDS: int = 10
    RESTART_START_TIMEOUT_SECONDS: int = 10
    SERVERS_CONFIG_PATH: str = "servers/servers.json"
    LOG_LEVEL: str = "info"


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
