from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Genevidence Similarity Check"
    API_V1_PREFIX: str = ""

    DATABASE_URL: str = "sqlite:///./genevidence.db"
    REDIS_URL: str = "redis://redis:6379/0"

    JWT_SECRET: str = "change-this-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    MAX_UPLOAD_MB: int = 25
    STORAGE_DIR: str = "storage"
    BACKEND_CORS_ORIGINS: str | List[str] = "https://similaritycheck.genevidence.com"
    AUTO_CREATE_TABLES: bool = True

    CHUNK_SIZE_WORDS: int = 150
    CHUNK_OVERLAP_WORDS: int = 30
    EXACT_NGRAM_SIZE: int = 5
    WINNOW_K_GRAM_SIZE: int = 5
    WINNOW_WINDOW_SIZE: int = 4
    JACCARD_THRESHOLD: float = 0.18
    FUZZY_THRESHOLD: int = 82

    SEMANTIC_ENABLED: bool = False
    SEMANTIC_MODEL_NAME: str = "intfloat/multilingual-e5-base"
    SEMANTIC_EMBEDDING_DIMENSIONS: int = 768
    SEMANTIC_COSINE_THRESHOLD: float = 0.86
    SEMANTIC_MIN_WORDS: int = 60
    SEMANTIC_MAX_CANDIDATES: int = 20

    EXTERNAL_ACADEMIC_SEARCH_ENABLED: bool = True
    EXTERNAL_ACADEMIC_PROVIDERS: str | List[str] = "europepmc,crossref,openalex"
    EXTERNAL_ACADEMIC_MAX_QUERIES: int = 6
    EXTERNAL_ACADEMIC_RESULTS_PER_QUERY: int = 4
    EXTERNAL_ACADEMIC_MAX_SOURCES: int = 14
    EXTERNAL_ACADEMIC_MAX_MATCHES: int = 30
    EXTERNAL_ACADEMIC_MIN_SCORE: float = 78.0
    EXTERNAL_ACADEMIC_MIN_QUERY_WORDS: int = 35
    EXTERNAL_ACADEMIC_TIMEOUT_SECONDS: float = 8.0
    EXTERNAL_ACADEMIC_USER_AGENT: str = "GenevidenceSimilarityCheck/0.1"
    OPENALEX_API_KEY: str | None = None

    FREE_PLAN_CREDITS: int = 3

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return f"postgresql+psycopg://{value.removeprefix('postgres://')}"
        if value.startswith("postgresql://"):
            return f"postgresql+psycopg://{value.removeprefix('postgresql://')}"
        return value

    @field_validator("BACKEND_CORS_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, value: str | List[str]) -> List[str]:
        if isinstance(value, list):
            return value
        return [item.strip() for item in value.split(",") if item.strip()]

    @field_validator("EXTERNAL_ACADEMIC_PROVIDERS")
    @classmethod
    def parse_external_providers(cls, value: str | List[str]) -> List[str]:
        if isinstance(value, list):
            return [item.strip().lower() for item in value if item.strip()]
        return [item.strip().lower() for item in value.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
