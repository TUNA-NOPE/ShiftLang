"""Translator factory for ShiftLang."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deep_translator import GoogleTranslator, MyMemoryTranslator
import translators as ts
from .openrouter import OpenRouterTranslator


# Provider information for display and selection
PROVIDER_INFO = {
    # Deep Translator providers
    "google": {"name": "Google Translate", "library": "deep-translator", "requires_key": False},
    "mymemory": {"name": "MyMemory", "library": "deep-translator", "requires_key": False, "note": "5000 chars/day free"},
    
    # Translators library providers (no API key required)
    "bing": {"name": "Bing Microsoft Translator", "library": "translators", "requires_key": False},
    "alibaba": {"name": "Alibaba Translate", "library": "translators", "requires_key": False},
    "baidu": {"name": "Baidu Translate", "library": "translators", "requires_key": False},
    "yandex": {"name": "Yandex Translate", "library": "translators", "requires_key": False},
    "reverso": {"name": "Reverso Translate", "library": "translators", "requires_key": False},
    "sogou": {"name": "Sogou Translate", "library": "translators", "requires_key": False},
    "youdao": {"name": "Youdao Translate", "library": "translators", "requires_key": False},
    "tencent": {"name": "Tencent (QQ) Translate", "library": "translators", "requires_key": False},
    "itranslate": {"name": "Itranslate", "library": "translators", "requires_key": False},
    "argos": {"name": "Argos (LibreTranslate)", "library": "translators", "requires_key": False},
    
    # OpenRouter (requires API key for paid models)
    "openrouter": {"name": "OpenRouter AI", "library": "openrouter", "requires_key": True},
}


class TranslatorsWrapper:
    """Wrapper for translators library to provide a consistent interface."""
    
    def __init__(self, provider, source, target):
        self.provider = provider
        self.source = source
        self.target = target
        
        # Map provider names to translators library engine names
        self.engine_map = {
            "bing": "bing",
            "alibaba": "alibaba",
            "baidu": "baidu",
            "yandex": "yandex",
            "reverso": "reverso",
            "sogou": "sogou",
            "youdao": "youdao",
            "tencent": "qq_trans",
            "itranslate": "itranslate",
            "argos": "argos",
        }
    
    def translate(self, text):
        """Translate text using the specified provider."""
        if not text or not text.strip():
            return text
        
        engine = self.engine_map.get(self.provider, self.provider)
        
        try:
            result = ts.translate_text(
                text,
                translator=engine,
                from_language=self.source,
                to_language=self.target,
            )
            return result
        except Exception as e:
            print(f"Translation error with {self.provider}: {e}")
            raise


class MyMemoryWrapper:
    """Wrapper for MyMemory translator with fallback support."""
    
    def __init__(self, source, target, api_key=None):
        self.source = source
        self.target = target
        self.api_key = api_key
        
        # MyMemory uses 2-letter codes
        self.translator = MyMemoryTranslator(
            source=self.source,
            target=self.target,
        )
    
    def translate(self, text):
        """Translate text using MyMemory."""
        if not text or not text.strip():
            return text
        
        return self.translator.translate(text)


def create_translator(provider, source, target, api_key=None, model=None):
    """Create a single translator instance.
    
    Args:
        provider: Provider name (google, bing, mymemory, etc.)
        source: Source language code
        target: Target language code
        api_key: Optional API key for providers that require it
        model: Optional model for OpenRouter
        
    Returns:
        Translator instance with a translate() method
    """
    provider = provider.lower()
    
    if provider == "openrouter":
        return OpenRouterTranslator(
            source=source,
            target=target,
            api_key=api_key or "",
            model=model or "openrouter/free"
        )
    elif provider == "google":
        return GoogleTranslator(source=source, target=target)
    elif provider == "mymemory":
        return MyMemoryWrapper(source=source, target=target, api_key=api_key)
    elif provider in ["bing", "alibaba", "baidu", "yandex", "reverso", 
                      "sogou", "youdao", "tencent", "itranslate", "argos"]:
        return TranslatorsWrapper(provider, source, target)
    else:
        # Default to Google
        print(f"Unknown provider '{provider}', falling back to Google Translate")
        return GoogleTranslator(source=source, target=target)


def create_translators(config):
    """Create translator instances based on configured provider.
    
    Args:
        config: Configuration dictionary with keys:
            - translation_provider: Provider name
            - source_language: Source language name
            - target_language: Target language name
            - openrouter_api_key: Optional API key for OpenRouter
            - openrouter_model: Model to use for OpenRouter
    
    Returns:
        Tuple of (forward_translator, reverse_translator, provider_name)
    """
    provider = config.get("translation_provider", "google").lower()
    source = config["source_language"]
    target = config["target_language"]
    api_key = config.get("openrouter_api_key", "")
    model = config.get("openrouter_model", "openrouter/free")
    
    # Create forward and reverse translators
    forward = create_translator(provider, source, target, api_key, model)
    reverse = create_translator(provider, target, source, api_key, model)
    
    # Get display name
    info = PROVIDER_INFO.get(provider, {})
    display_name = info.get("name", provider.capitalize())
    print(f"Using {display_name}")
    
    return forward, reverse, provider


def get_free_providers():
    """Get list of providers that don't require an API key.
    
    Returns:
        List of (provider_id, display_name) tuples
    """
    providers = []
    for provider_id, info in PROVIDER_INFO.items():
        if not info.get("requires_key", False):
            display = info.get("name", provider_id.capitalize())
            if info.get("note"):
                display += f" ({info['note']})"
            providers.append((provider_id, display))
    return providers


def get_provider_display_name(provider_id):
    """Get the display name for a provider.
    
    Args:
        provider_id: Provider identifier
        
    Returns:
        Display name string
    """
    info = PROVIDER_INFO.get(provider_id.lower(), {})
    return info.get("name", provider_id.capitalize())
