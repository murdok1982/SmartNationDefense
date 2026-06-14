# -*- coding: utf-8 -*-
import json
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}

    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR)$")

    SECRET_KEY: str = Field(default="CHANGE_ME_IMMEDIATELY", min_length=32)
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=1, le=60)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)
    MFA_ENABLED: bool = Field(default=True)
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

    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:8501")

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
        if v in ("change-this-to-a-random-64-char-string", "CHANGE_ME_IMMEDIATELY"):
            raise ValueError("SECRET_KEY must be set via environment variable")
        return v

    @field_validator("NEO4J_PASSWORD")
    @classmethod
    def validate_neo4j_password(cls, v, info):
        if info.data.get("ENVIRONMENT") == "production" and not v:
            raise ValueError("NEO4J_PASSWORD is required in production")
        return v

    @field_validator("GRAFANA_ADMIN_PASSWORD")
    @classmethod
    def validate_grafana_password(cls, v, info):
        if info.data.get("ENVIRONMENT") == "production" and not v:
            raise ValueError("GRAFANA_ADMIN_PASSWORD is required in production")
        return v

    EVIDENCE_STORAGE_PATH: str = Field(default="/tmp/sesis-evidence")
    REPORTS_STORAGE_PATH: str = Field(default="/tmp/sesis-reports")
    max_file_size_bytes: int = Field(default=50 * 1024 * 1024, ge=1024)


settings = Settings()


def get_settings() -> Settings:
    return settings
