"""Centralized configuration management for the application."""

import os


class Settings:
    """Application settings with environment-aware configuration loading."""
    
    def __init__(self):
        """Initialize settings with conditional .env loading."""
        self._load_environment_config()
        self._validate_required_settings()
        
    def _load_environment_config(self):
        """Load environment configuration based on APP_ENV."""
        app_env = os.getenv("APP_ENV", "development").lower()
        
        # Only load .env file in development/local environments
        if app_env in ("development", "dev", "local"):
            try:
                from dotenv import load_dotenv
                load_dotenv()
                print(f"🔧 Loaded .env file for {app_env} environment")
            except ImportError:
                print("⚠️  python-dotenv not installed, skipping .env file loading")
        else:
            print(f"🚀 Production mode ({app_env}): Using environment variables only")
    
    def _validate_required_settings(self):
        """Validate that all required environment variables are set."""
        missing_vars = []
        
        if not os.getenv("OPENROUTER_API_KEY"):
            missing_vars.append("OPENROUTER_API_KEY")
        
        if not os.getenv("MySQL_DATABASE_URL"):
            missing_vars.append("MySQL_DATABASE_URL")
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}. "
                f"Please set these variables or ensure your .env file contains them "
                f"(current environment: {self.app_env})"
            )
        
        print(f"✅ All required environment variables are set for {self.app_env} environment")
    
    @property
    def database_url(self) -> str:
        """Get database URL from environment."""
        url = os.getenv("MySQL_DATABASE_URL")
        if not url:
            raise ValueError("MySQL_DATABASE_URL environment variable is required")
        return url
    
    @property
    def openrouter_api_key(self) -> str:
        """Get OpenRouter API key from environment."""
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        return key
    
    @property
    def openrouter_model(self) -> str:
        """Get OpenRouter model from environment."""
        return os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    
    @property
    def openrouter_base_url(self) -> str:
        """Get OpenRouter base URL from environment."""
        return os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    @property
    def app_env(self) -> str:
        """Get application environment."""
        return os.getenv("APP_ENV", "development").lower()
    
    @property
    def log_level(self) -> str:
        """Get log level from environment."""
        return os.getenv("LOG_LEVEL", "INFO").upper()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env in ("production", "prod")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env in ("development", "dev", "local")
    
    @property
    def database_echo_enabled(self) -> bool:
        """Check if database SQL echo should be enabled (only in development)."""
        return self.is_development


# Global settings instance
settings = Settings() 