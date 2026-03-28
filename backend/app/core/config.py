from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "PastoralProtect API"
    port: int = 8000
    database_url: str = "sqlite:///./pastoral_protect.db"

    base_rpc_url: str = ""
    private_key: str = ""
    admin_private_key: str = ""
    contract_address: str = ""
    contract_artifact_path: str = "../contracts/artifacts/contracts/PastoralProtectPool.sol/PastoralProtectPool.json"

    oracle_secret: str = "dev-oracle-secret"
    admin_api_key: str = "dev-admin-key"

    jwt_secret: str = "change-me-in-production-pastoralprotect"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # Filecoin / IPFS — Storacha (recommended): local Node bridge using @storacha/client (email login, no API keys)
    storacha_uploader_url: str = ""
    storacha_uploader_secret: str = ""
    # If true, 503 from the Storacha bridge (e.g. no space / login) uses in-memory mock CIDs instead of failing the oracle
    storacha_fallback_mock_on_error: bool = True

    # Legacy: web3.storage-compatible HTTP upload (Bearer token) — deprecated by Storacha; prefer storacha_uploader_*
    web3_storage_token: str = ""
    filecoin_upload_url: str = "https://api.web3.storage/upload"
    ipfs_gateway_base: str = "https://w3s.link/ipfs"

    # Comma-separated browser origins for CORS; empty uses localhost/127.0.0.1 :3000–3001
    cors_allowed_origins: str = ""

    # Allow POST /api/demo/run without JWT (hackathon kiosk); prefer False in production
    demo_public_access: bool = True

    mock_payment_delay_ms: int = 2000
    payout_per_head: int = 1000
    chain_enroll_value_wei: int = 1_000_000_000_000_000  # 0.001 ETH


settings = Settings()
