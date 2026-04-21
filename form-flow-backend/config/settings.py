"""
Application Configuration Module

Centralizes all application settings using Pydantic Settings.
Environment variables are loaded from .env file automatically.

Usage:
    from config.settings import settings
    
    print(settings.DATABASE_URL)
    print(settings.DEBUG)
"""

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict, field_validator
from typing import List, Optional
from functools import lru_cache
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables or .env file.
    Variable names are case-insensitive.
    """
    
    model_config = ConfigDict(extra="ignore")
    
    # ==========================================================================
    # Database Configuration
    # ==========================================================================
    DATABASE_URL: str = Field(
        default="postgresql://localhost/formflow",
        description="PostgreSQL connection string"
    )
    
    # ==========================================================================
    # Authentication & Security
    # ==========================================================================
    SECRET_KEY: Optional[str] = Field(
        default=None,
        description="JWT signing secret key (REQUIRED - set via SECRET_KEY env var)"
    )
    
    @field_validator('SECRET_KEY', mode='before')
    @classmethod
    def validate_secret_key(cls, v):
        if v is None or v == "":
            raise ValueError(
                "SECRET_KEY is required for production. "
                "Set SECRET_KEY environment variable."
            )
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters for security."
            )
        return v
    
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT token expiration time in minutes"
    )
    
    # ==========================================================================
    # External API Keys
    # ==========================================================================
    GOOGLE_API_KEY: Optional[str] = Field(
        default=None,
        description="Google Gemini API key for AI features"
    )
    GEMMA_API_KEY: Optional[str] = Field(
        default=None,
        description="Gemma API key (prioritized over Google API key)"
    )
    OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        description="OpenAI API key (optional, for fallback)"
    )
    ELEVENLABS_API_KEY: Optional[str] = Field(
        default=None,
        description="ElevenLabs API key for text-to-speech"
    )
    OPENROUTER_API_KEY: Optional[str] = Field(
        default=None,
        description="OpenRouter API key for fallback inference (Gemma 3)"
    )
    
    # ==========================================================================
    # CAPTCHA Solving Configuration
    # ==========================================================================
    TWOCAPTCHA_API_KEY: Optional[str] = Field(
        default=None,
        description="2Captcha API key for automated CAPTCHA solving"
    )
    ANTICAPTCHA_API_KEY: Optional[str] = Field(
        default=None,
        description="AntiCaptcha API key for automated CAPTCHA solving"
    )
    CAPTCHA_SOLVE_TIMEOUT: int = Field(
        default=120,
        description="Maximum seconds to wait for CAPTCHA solution"
    )
    
    # ==========================================================================
    # Redis Configuration (for caching and rate limiting)
    # ==========================================================================
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection URL for caching and rate limiting"
    )
    
    # ==========================================================================
    # CORS Configuration
    # ==========================================================================
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Allowed CORS origins (comma-separated)"
    )
    
    @property
    def cors_origins_list(self) -> list:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    CORS_CHROME_EXTENSIONS: str = Field(
        default="",
        description="Allowed Chrome extension IDs (comma-separated, e.g., 'ext1,ext2')"
    )
    
    @property
    def cors_chrome_extension_regex(self) -> str:
        """Get regex pattern for allowed Chrome extensions."""
        if not self.CORS_CHROME_EXTENSIONS:
            return ""  # No Chrome extensions allowed
        # Build regex: chrome-extension://(ext1|ext2|...)
        ext_ids = [e.strip() for e in self.CORS_CHROME_EXTENSIONS.split(",") if e.strip()]
        if not ext_ids:
            return ""
        return f"chrome-extension://({'|'.join(ext_ids)})"
    
    # ==========================================================================
    # Webhook Configuration
    # ==========================================================================
    WEBHOOK_MAX_PER_USER: int = Field(
        default=5,
        description="Maximum webhooks per user"
    )
    WEBHOOK_TIMEOUT_SECONDS: int = Field(
        default=10,
        description="Timeout for webhook HTTP requests"
    )
    WEBHOOK_RETRY_ATTEMPTS: int = Field(
        default=3,
        description="Number of retry attempts for failed webhook deliveries"
    )
    WEBHOOK_MAX_PAYLOAD_SIZE: int = Field(
        default=102400,
        description="Maximum webhook payload size in bytes (100KB default)"
    )
    
    # ==========================================================================
    # Application Settings
    # ==========================================================================
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode with verbose logging"
    )
    APP_NAME: str = Field(
        default="Form Flow AI",
        description="Application name for OpenAPI docs"
    )
    APP_VERSION: str = Field(
        default="1.0.0",
        description="Application version"
    )
    
    # ==========================================================================
    # Local LLM Configuration
    # ==========================================================================
    USE_LOCAL_LLM: bool = Field(
        default=True,
        description="Use local Phi-2 model as primary LLM (faster, free)"
    )
    LOCAL_MODEL_PATH: Optional[str] = Field(
        default=None,
        description="Custom path to local model (defaults to models/phi-2)"
    )
    
    # ==========================================================================
    # Smart Question Engine Configuration
    # ==========================================================================
    SMART_GROUPING_ENABLED: bool = Field(
        default=True,
        description="Enable Smart Question Grouping (reduces 159 fields to ~30 groups)"
    )
    SMART_GROUPING_MIN_FILL_RATIO: float = Field(
        default=0.7,
        description="Minimum field fill ratio to consider a group complete"
    )
    
    # ==========================================================================
    # Voice/Speech Configuration
    # ==========================================================================
    ELEVENLABS_VOICE_ID: str = Field(
        default="21m00Tcm4TlvDq8ikWAM",
        description="Default ElevenLabs voice ID (Rachel)"
    )
    ELEVENLABS_MODEL: str = Field(
        default="eleven_turbo_v2_5",
        description="ElevenLabs model for TTS"
    )
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses LRU cache to ensure settings are only loaded once.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Singleton instance for easy import
settings = get_settings()
