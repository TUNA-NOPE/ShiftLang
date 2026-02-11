#!/usr/bin/env python3
"""Test script for OpenRouter translator"""

import os
import json
from openrouter_translator import OpenRouterTranslator

def load_config():
    """Load API key from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def test_translator():
    """Test the OpenRouter translator with a simple example."""
    print("Testing OpenRouter Translator...")
    print()

    # Load API key from config
    config = load_config()
    api_key = config.get("openrouter_api_key", "")
    model = config.get("openrouter_model", "openrouter/free")

    # Some models are free and don't require an API key
    free_models = [
        "openrouter/free",
        "google/gemini-2.0-flash-exp:free",
        "meta-llama/llama-3.1-8b-instruct:free",
        "nvidia/nemotron-3-nano-30b-a3b:free",
        "arcee-ai/trinity-mini:free"
    ]
    if not api_key and model not in free_models:
        print("✗ No OpenRouter API key found in config.json")
        print()
        print("To use OpenRouter:")
        print("  1. Get an API key from https://openrouter.ai/")
        print("  2. Run: python install.py --reconfigure")
        print("  3. Choose OpenRouter and enter your API key")
        return

    # Create translator instance (English to Hebrew)
    translator = OpenRouterTranslator(
        source=config.get("source_language", "english"),
        target=config.get("target_language", "hebrew"),
        api_key=api_key,
        model=model
    )

    print(f"Using model: {model}")
    print()

    # Test text
    test_text = "Hello, how are you?"
    print(f"Original text: {test_text}")
    print()

    print("Translating...")
    try:
        translated = translator.translate(test_text)
        print(f"Translated text: {translated}")
        print()

        # Check if translation actually worked
        if translated == test_text:
            print("⚠ Translation returned original text (may indicate an error)")
            print("  Check the messages above for error details")
        else:
            print("✓ Translation successful!")
    except Exception as e:
        print(f"✗ Translation failed: {e}")
        print()
        print("Note: Check your internet connection and API key")

if __name__ == "__main__":
    test_translator()
