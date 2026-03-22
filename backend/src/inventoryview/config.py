"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """InventoryView configuration.

    All settings are read from environment variables with the IV_ prefix.
    Example: IV_DATABASE_URL, IV_VAULT_PASSPHRASE, etc.
    """

    model_config = SettingsConfigDict(env_prefix="IV_")

    database_url: str = (
        "postgresql://inventoryview:inventoryview@localhost:5432/inventoryview"
    )
    vault_passphrase: str  # Required, no default - app refuses to start without it
    jwt_secret: str = ""  # Auto-generated on first run if empty
    token_expiry_hours: int = 24
    host: str = "0.0.0.0"
    port: int = 8080
    graph_name: str = "inventory_graph"
    max_traversal_depth: int = 5
    debug: bool = False


def get_settings() -> Settings:
    """Create and return application settings."""
    return Settings()
