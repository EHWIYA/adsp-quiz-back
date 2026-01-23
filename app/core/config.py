from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = ""
    db_user: str = ""
    db_password: str = ""

    # AI Provider (Gemini)
    gemini_api_key: str = ""
    
    # Gemini API 토큰 절약 설정
    auto_validate_quiz: bool = False  # 자동 검증 활성화 여부 (기본값: 비활성화)
    auto_validate_sample_rate: float = 0.1  # 자동 검증 샘플링 비율 (0.0-1.0, 기본값: 10%)

    # Security
    secret_key: str = ""
    algorithm: str = "HS256"

    # CORS
    allowed_origins: str = "http://localhost:3000"

    # Environment
    environment: str = "development"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]


settings = Settings()
