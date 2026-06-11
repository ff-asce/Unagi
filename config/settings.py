"""Configuration management for Unagi."""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import yaml


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class Settings:
    """Application settings loaded from .env and config.yaml."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize settings by loading from config files.
        
        Args:
            config_dir: Directory containing config files. Defaults to project root.
        """
        if config_dir is None:
            # Default to the parent directory of this file (project root)
            config_dir = Path(__file__).parent.parent
        
        self.config_dir = Path(config_dir)
        self._load_env()
        self._load_yaml()
        self._validate()
    
    def _load_env(self):
        """Load environment variables from .env file."""
        env_path = self.config_dir / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        
        # LLM Configuration
        self.llm_api_key = os.getenv("LLM_API_KEY", "")
        self.llm_base_url = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
        self.llm_model_name = os.getenv("LLM_MODEL_NAME", "models/gemini-2.5-flash")
        
        # Git Configuration
        self.git_author_name = os.getenv("GIT_AUTHOR_NAME", "Unagi")
        self.git_author_email = os.getenv("GIT_AUTHOR_EMAIL", "unagi@local")
        self.git_remote_url = os.getenv("GIT_REMOTE_URL", "")
        self.git_remote_token = os.getenv("GIT_REMOTE_TOKEN", "")
        
        # Intelligence System API Keys (optional)
        self.usda_api_key = os.getenv("USDA_API_KEY", "")
        self.openfoodfacts_user_agent = os.getenv("OPENFOODFACTS_USER_AGENT", "Unagi/1.0")
    
    def _load_yaml(self):
        """Load configuration from config.yaml."""
        yaml_path = self.config_dir / "config.yaml"
        
        if not yaml_path.exists():
            raise ConfigError(f"config.yaml not found at {yaml_path}")
        
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Vault configuration
        vault_config = config.get("vault", {})
        self.vault_root = vault_config.get("root_path", "")
        self.vault_unagi_folder = vault_config.get("unagi_folder", "Unagi")
        self.vault_logs_subfolder = vault_config.get("logs_subfolder", "Daily Logs")
        self.vault_data_subfolder = vault_config.get("data_subfolder", "Data")
        self.vault_user_profile_filename = vault_config.get("user_profile_filename", "User Profile.md")
        self.vault_dashboard_filename = vault_config.get("dashboard_filename", "Nutrition Dashboard.md")
        
        # Agent configuration
        agent_config = config.get("agent", {})
        self.agent_context_days = agent_config.get("context_days", 7)
        self.agent_confirm_before_write = agent_config.get("confirm_before_write", True)
        
        # Intelligence system configuration
        intelligence_config = config.get("intelligence", {})
        self.intelligence_enabled = intelligence_config.get("enabled", True)
        self.intelligence_memory_enabled = intelligence_config.get("memory_enabled", True)
        self.intelligence_suggestions_enabled = intelligence_config.get("suggestions_enabled", True)
        self.intelligence_data_enrichment_enabled = intelligence_config.get("data_enrichment_enabled", True)
        self.intelligence_semantic_search_results = intelligence_config.get("semantic_search_results", 5)
        self.intelligence_pattern_learning_days = intelligence_config.get("pattern_learning_days", 30)
        self.intelligence_trend_detection_days = intelligence_config.get("trend_detection_days", 30)
        
        # Git configuration
        git_config = config.get("git", {})
        self.git_enabled = git_config.get("enabled", True)
        self.git_branch = git_config.get("branch", "main")
        self.git_auto_push = git_config.get("auto_push", True)
        
        # UI configuration
        ui_config = config.get("ui", {})
        self.ui_show_mascot = ui_config.get("show_mascot", True)
        self.ui_theme = ui_config.get("theme", "dark")
    
    def _validate(self):
        """Validate required configuration values."""
        errors = []
        
        # LLM API key is required
        if not self.llm_api_key:
            errors.append(
                "LLM_API_KEY is missing. Please add it to your .env file.\n"
                "Get your API key from: https://aistudio.google.com/app/apikey (for Gemini)"
            )
        
        # Vault root can be empty (will be set during onboarding)
        # but if set, it should be a valid path
        if self.vault_root and not Path(self.vault_root).exists():
            errors.append(
                f"Vault root path does not exist: {self.vault_root}\n"
                "Please update config.yaml with a valid path or leave it empty for first-run setup."
            )
        
        if errors:
            raise ConfigError("\n\n".join(errors))
    
    def get_vault_path(self) -> Path:
        """Get the full path to the Unagi folder in the vault."""
        if not self.vault_root:
            raise ConfigError("Vault root is not configured. Please run onboarding first.")
        return Path(self.vault_root) / self.vault_unagi_folder
    
    def get_logs_path(self) -> Path:
        """Get the full path to the Daily Logs folder."""
        return self.get_vault_path() / self.vault_logs_subfolder
    
    def get_data_path(self) -> Path:
        """Get the full path to the Data folder."""
        return self.get_vault_path() / self.vault_data_subfolder
    
    def get_user_profile_path(self) -> Path:
        """Get the full path to the User Profile file."""
        return self.get_data_path() / self.vault_user_profile_filename
    
    def update_vault_root(self, new_path: str):
        """Update the vault root path in config.yaml.
        
        Args:
            new_path: New vault root path
        """
        yaml_path = self.config_dir / "config.yaml"
        
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if "vault" not in config:
            config["vault"] = {}
        config["vault"]["root_path"] = new_path
        
        with open(yaml_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        self.vault_root = new_path
    
    def __repr__(self) -> str:
        """String representation of settings (masks sensitive data)."""
        return (
            f"Settings(\n"
            f"  LLM: {self.llm_model_name} @ {self.llm_base_url}\n"
            f"  API Key: {'*' * 8 if self.llm_api_key else 'NOT SET'}\n"
            f"  Vault: {self.vault_root or 'NOT SET'}\n"
            f"  Git: {'enabled' if self.git_enabled else 'disabled'}\n"
            f"  Auto-push: {self.git_auto_push}\n"
            f")"
        )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(reload: bool = False) -> Settings:
    """Get the global settings instance.
    
    Args:
        reload: If True, reload settings from files
        
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None or reload:
        _settings = Settings()
    return _settings

# Made with Bob
