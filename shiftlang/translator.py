"""Translator factory for ShiftLang."""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deep_translator import GoogleTranslator
from .openrouter import OpenRouterTranslator


def create_translators(config):
    """Create translator instances based on configured provider.
    
    Args:
        config: Configuration dictionary with keys:
            - translation_provider: "google" or "openrouter"
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

    if provider == "openrouter":
        api_key = config.get("openrouter_api_key", "")
        model = config.get("openrouter_model", "openrouter/free")
        forward = OpenRouterTranslator(
            source=source,
            target=target,
            api_key=api_key,
            model=model
        )
        reverse = OpenRouterTranslator(
            source=target,
            target=source,
            api_key=api_key,
            model=model
        )
        print(f"Using OpenRouter AI translator (model: {model})")
    else:  # default to google
        forward = GoogleTranslator(
            source=source,
            target=target,
        )
        reverse = GoogleTranslator(
            source=target,
            target=source,
        )
        print(f"Using Google Translator")

    return forward, reverse, provider
