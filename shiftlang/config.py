"""Configuration management for ShiftLang."""

import os
import json
import platform

# ──────────────────────── Constants ───────────────────────────
OS_NAME = platform.system()  # 'Windows' | 'Darwin' | 'Linux'

DEFAULT_HOTKEYS = {
    "Windows": "ctrl+shift+q",
    "Darwin": "cmd+shift+g",
    "Linux": "alt+shift+g",
}

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

# Available translation providers
FREE_PROVIDERS = [
    "google",       # Google Translate (default)
    "mymemory",     # MyMemory (5000 chars/day free)
    "bing",         # Bing Microsoft Translator
    "alibaba",      # Alibaba Translate
    "baidu",        # Baidu Translate
    "yandex",       # Yandex Translate
    "reverso",      # Reverso Translate
    "sogou",        # Sogou Translate
    "youdao",       # Youdao Translate
    "tencent",      # Tencent (QQ) Translate
    "itranslate",   # Itranslate
    "argos",        # Argos (LibreTranslate)
]

API_KEY_PROVIDERS = [
    "openrouter",   # OpenRouter AI (free tier available, paid for higher limits)
]

ALL_PROVIDERS = FREE_PROVIDERS + API_KEY_PROVIDERS

# Default configuration values
DEFAULT_CONFIG = {
    "hotkey": DEFAULT_HOTKEYS.get(OS_NAME, "ctrl+shift+q"),
    "auto_start": False,
    "source_language": "hebrew",
    "target_language": "english",
    "translation_provider": "google",  # Any provider from FREE_PROVIDERS or API_KEY_PROVIDERS
    "openrouter_api_key": "",  # Optional API key for OpenRouter
    "openrouter_model": "openrouter/free",
    "clear_clipboard_after_paste": True,  # Clear clipboard after pasting to prevent history spam
}


def load_config():
    """Load user preferences from config.json, with sensible defaults."""
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                cfg = json.load(f)
            config.update(cfg)
        except Exception as e:
            print(f"Config load error: {e}")
    return config


def save_config(
    hotkey,
    auto_start,
    source_lang,
    target_lang,
    provider="google",
    api_key="",
    model="openrouter/free",
):
    """Save configuration to config.json."""
    cfg = {
        "hotkey": hotkey,
        "auto_start": auto_start,
        "source_language": source_lang,
        "target_language": target_lang,
        "translation_provider": provider,
        "openrouter_api_key": api_key,
        "openrouter_model": model,
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
    return True


def is_valid_provider(provider):
    """Check if a provider name is valid.
    
    Args:
        provider: Provider name to check
        
    Returns:
        True if valid, False otherwise
    """
    return provider.lower() in ALL_PROVIDERS


def requires_api_key(provider):
    """Check if a provider requires an API key.
    
    Args:
        provider: Provider name to check
        
    Returns:
        True if API key is required, False otherwise
    """
    return provider.lower() in API_KEY_PROVIDERS


def get_provider_display_name(provider):
    """Get a human-readable name for a provider.
    
    Args:
        provider: Provider identifier
        
    Returns:
        Display name string
    """
    display_names = {
        "google": "Google Translate",
        "mymemory": "MyMemory (5000 chars/day free)",
        "bing": "Bing Microsoft Translator",
        "alibaba": "Alibaba Translate",
        "baidu": "Baidu Translate",
        "yandex": "Yandex Translate",
        "reverso": "Reverso Translate",
        "sogou": "Sogou Translate",
        "youdao": "Youdao Translate",
        "tencent": "Tencent (QQ) Translate",
        "itranslate": "Itranslate",
        "argos": "Argos (LibreTranslate)",
        "openrouter": "OpenRouter AI",
    }
    return display_names.get(provider.lower(), provider.capitalize())
