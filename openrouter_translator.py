"""OpenRouter LLM-based translator using the free tier."""

import requests
import os


class OpenRouterTranslator:
    """AI-powered translator using OpenRouter's free models."""

    def __init__(self, source, target, api_key=None, model=None):
        """
        Initialize OpenRouter translator.

        Args:
            source: Source language (e.g., 'english', 'hebrew')
            target: Target language
            api_key: OpenRouter API key (optional, can use env var OPENROUTER_API_KEY)
            model: OpenRouter model to use (default: 'openrouter/free')
        """
        self.source = source
        self.target = target
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.model = model or "openrouter/free"
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def translate(self, text):
        """
        Translate text using OpenRouter LLM.

        Args:
            text: Text to translate

        Returns:
            Translated text
        """
        if not text or not text.strip():
            return text

        # Build translation prompt
        prompt = self._build_prompt(text)

        # Make API request
        headers = {
            "Content-Type": "application/json",
        }

        # Only add authorization if API key is provided
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            # Handle 401 Unauthorized specifically
            if response.status_code == 401:
                print("✗ OpenRouter authentication failed")
                print("  API key is missing or invalid")
                print("  Get your API key at: https://openrouter.ai/keys")
                print("  Then run: python install.py --reconfigure")
                return text

            response.raise_for_status()

            result = response.json()
            translated = result["choices"][0]["message"]["content"].strip()

            # Clean up response - remove quotes if LLM added them
            translated = translated.strip('"').strip("'")

            return translated

        except requests.exceptions.RequestException as e:
            print(f"OpenRouter API error: {e}")
            if "401" in str(e):
                print("  Hint: Check your API key in config.json")
            # Fallback to original text if translation fails
            return text
        except (KeyError, IndexError) as e:
            print(f"OpenRouter response parsing error: {e}")
            return text

    def _build_prompt(self, text):
        """Build translation prompt for the LLM."""
        # Normalize language names
        source_lang = self._normalize_language_name(self.source)
        target_lang = self._normalize_language_name(self.target)

        prompt = f"""Translate the following text from {source_lang} to {target_lang}.
Only provide the translation, without any explanations, quotes, or additional text.

Text to translate:
{text}"""

        return prompt

    @staticmethod
    def _normalize_language_name(lang):
        """Convert language code to full name for better LLM understanding."""
        # Handle common language names
        lang_lower = lang.lower().strip()

        # Map of common variations to standard names
        lang_map = {
            "en": "English",
            "english": "English",
            "he": "Hebrew",
            "hebrew": "Hebrew",
            "iw": "Hebrew",
            "es": "Spanish",
            "spanish": "Spanish",
            "fr": "French",
            "french": "French",
            "de": "German",
            "german": "German",
            "it": "Italian",
            "italian": "Italian",
            "pt": "Portuguese",
            "portuguese": "Portuguese",
            "ru": "Russian",
            "russian": "Russian",
            "ja": "Japanese",
            "japanese": "Japanese",
            "ko": "Korean",
            "korean": "Korean",
            "zh": "Chinese",
            "chinese": "Chinese",
            "chinese (simplified)": "Simplified Chinese",
            "chinese (traditional)": "Traditional Chinese",
            "ar": "Arabic",
            "arabic": "Arabic",
            "hi": "Hindi",
            "hindi": "Hindi",
            "bn": "Bengali",
            "bengali": "Bengali",
            "tr": "Turkish",
            "turkish": "Turkish",
            "vi": "Vietnamese",
            "vietnamese": "Vietnamese",
            "th": "Thai",
            "thai": "Thai",
            "pl": "Polish",
            "polish": "Polish",
            "uk": "Ukrainian",
            "ukrainian": "Ukrainian",
        }

        return lang_map.get(lang_lower, lang.capitalize())
