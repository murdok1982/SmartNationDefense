# -*- coding: utf-8 -*-
import json
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}

    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    DEMO_MODE: bool = Field(default=False)
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR)$")

    SECRET_KEY: str = Field(default="CHANGE_ME_IMMEDIATELY", min_length=32)
    ADMIN_INITIAL_PASSWORD: str = Field(default="")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=1, le=60)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)
    JWT_AUDIENCE: str = Field(default="sesis-c2")
    JWT_ISSUER: str = Field(default="sesis-auth-server")
    MFA_ENABLED: bool = Field(default=True)
    MFA_ISSUER: str = Field(default="SESIS")
    MFA_RECOVERY_CODES_COUNT: int = Field(default=10, ge=4, le=100)
    MFA_ENCRYPTION_KEY: str = Field(default="")
    MFA_CHALLENGE_SECRET: str = Field(default="")
    MFA_CHALLENGE_TTL_SECONDS: int = Field(default=300, ge=60, le=900)
    FERNET_KEY_PATH: str = Field(default="fernet.key")

    DATABASE_URL: str = Field(default="postgresql+asyncpg://sesis:sesis@postgres:5432/sesis")
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    NATS_URL: str = Field(default="nats://nats:4222")

    NEO4J_URI: str = Field(default="bolt://neo4j:7687")
    NEO4J_USER: str = Field(default="neo4j")
    NEO4J_PASSWORD: str = Field(default="")

    OLLAMA_BASE_URL: str = Field(default="http://ollama:11434")
    OLLAMA_URL: str = Field(default="http://ollama:11434")
    OLLAMA_MODEL: str = Field(default="fsociety")
    OLLAMA_TIMEOUT: int = Field(default=120, ge=10, le=300)
    VLLM_BASE_URL: str = Field(default="")
    VLLM_MODEL: str = Field(default="")
    VLLM_TIMEOUT: int = Field(default=120, ge=10, le=300)
    OPENROUTER_API_KEY: str = Field(default="")
    OPENROUTER_DEFAULT_MODEL: str = Field(default="")
    ENABLE_OPENROUTER_FALLBACK: bool = Field(default=False)

    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:8501")

    # Multi-tenancy: desactivado por defecto (single-tenant). El esquema de
    # aislamiento por tenant se activa explícitamente en despliegues dedicados.
    MULTI_TENANT: bool = Field(default=False)
    DEFAULT_TENANT_ID: str = Field(default="default")

    RATE_LIMIT_DEFAULT: int = Field(default=60, ge=1)

    GRAFANA_ADMIN_USER: str = Field(default="admin")
    GRAFANA_ADMIN_PASSWORD: str = Field(default="")

    AES_KEY: str = Field(default="")
    JWS_PUBLIC_KEY: Optional[str] = Field(default=None)
    STATE_GRADE_MODE: bool = Field(default=False)
    API_V1_STR: str = Field(default="/api/v1")
    SIGNING_PUBLIC_KEY_PATH: Optional[str] = Field(default=None)
    OPERATOR_API_KEYS: str = Field(default="{}")

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def get_operator_api_keys(self) -> Dict[str, Any]:
        try:
            return json.loads(self.OPERATOR_API_KEYS)
        except (json.JSONDecodeError, TypeError):
            return {}

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        if v in ("change-this-to-a-random-64-char-string", "CHANGE_ME_IMMEDIATELY", "cambia-esto-por-una-cadena-aleatoria-de-64-caracteres-hex"):
            return v
        return v

    @model_validator(mode="after")
    def validate_production_hardening(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            errors = []
            if self.DEMO_MODE:
                errors.append("DEMO_MODE cannot be enabled in production.")
            if not self.SECRET_KEY or self.SECRET_KEY in (
                "change-this-to-a-random-64-char-string",
                "CHANGE_ME_IMMEDIATELY",
                "cambia-esto-en-produccion",
                "cambia-esto-por-una-cadena-aleatoria-de-64-caracteres-hex",
                "admin123",
                "Demo2024!",
            ) or "change" in self.SECRET_KEY.lower():
                errors.append("Insecure or default SECRET_KEY.")
            if "sesis:sesis@" in self.DATABASE_URL or "change" in self.DATABASE_URL.lower():
                errors.append("DATABASE_URL contains default or insecure credentials.")
            if not self.NEO4J_PASSWORD or "change" in self.NEO4J_PASSWORD.lower():
                errors.append("NEO4J_PASSWORD is required in production and cannot be default.")
            if not self.GRAFANA_ADMIN_PASSWORD or "change" in self.GRAFANA_ADMIN_PASSWORD.lower():
                errors.append("GRAFANA_ADMIN_PASSWORD is required in production and cannot be default.")
            if not self.MFA_ENCRYPTION_KEY or len(self.MFA_ENCRYPTION_KEY) != 64:
                errors.append("MFA_ENCRYPTION_KEY (64 hex characters) is required in production.")
            if self.ADMIN_INITIAL_PASSWORD in ("admin123", "Demo2024!", "change-me-in-production"):
                errors.append("Insecure ADMIN_INITIAL_PASSWORD.")
            if errors:
                raise ValueError(
                    "Production configuration incomplete. Refusing to start:\n- "
                    + "\n- ".join(errors)
                )
        return self

    EVIDENCE_STORAGE_PATH: str = Field(default="/tmp/sesis-evidence")
    REPORTS_STORAGE_PATH: str = Field(default="/tmp/sesis-reports")
    max_file_size_bytes: int = Field(default=50 * 1024 * 1024, ge=1024)

    TERRAIN_ELEVATION_API_URL: str = Field(default="https://api.open-elevation.com/api/v1/lookup")
    TERRAIN_ELEVATION_TIMEOUT: float = Field(default=15.0, ge=1.0, le=120.0)
    TERRAIN_ELEVATION_CACHE_TTL: int = Field(default=3600, ge=60)

    CELESTRAK_TLE_URL: str = Field(default="https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle")
    CELESTRAK_TIMEOUT: float = Field(default=20.0, ge=1.0, le=120.0)
    CELESTRAK_CACHE_TTL: int = Field(default=1800, ge=60)

    AISSTREAM_API_KEY: str = Field(default="")
    AISSTREAM_URL: str = Field(default="wss://stream.aisstream.io/v0/stream")
    AISSTREAM_BOUNDING_BOXES: str = Field(default="")
    AISSTREAM_COLLECT_SECONDS: float = Field(default=5.0, ge=1.0, le=60.0)

    MEDIA_STORAGE_PATH: str = Field(default="/tmp/sesis-media")
    MEDIA_UPLOAD_URL_TTL: int = Field(default=3600, ge=60)

    OSINT_DOCS_ALLOWED_DIR: str = Field(default="")
    OSINT_MAX_PER_SOURCE: int = Field(default=25, ge=1, le=100)
    OSINT_HTTP_TIMEOUT: float = Field(default=20.0, ge=5.0, le=120.0)
    NEWSAPI_API_KEY: str = Field(default="")


settings = Settings()


def get_settings() -> Settings:
    return settings
