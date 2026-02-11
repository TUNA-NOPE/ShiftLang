"""ShiftLang - Core shared modules."""

from .config import load_config, save_config, CONFIG_PATH, DEFAULT_HOTKEYS
from .language import detect_is_source_language, LANGUAGE_UNICODE_RANGES
from .translator import create_translators
from .openrouter import OpenRouterTranslator

__all__ = [
    "load_config",
    "save_config", 
    "CONFIG_PATH",
    "DEFAULT_HOTKEYS",
    "detect_is_source_language",
    "LANGUAGE_UNICODE_RANGES",
    "create_translators",
    "OpenRouterTranslator",
]
