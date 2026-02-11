# OpenRouter AI Translation Guide

ShiftLang now supports AI-powered translation using OpenRouter's free LLM models for more accurate translations.

## Quick Start

### 1. Edit your config.json

Open `config.json` and change the `translation_provider` field:

```json
{
  "hotkey": "ctrl+shift+q",
  "auto_start": true,
  "source_language": "english",
  "target_language": "hebrew",
  "translation_provider": "openrouter",
  "openrouter_api_key": ""
}
```

### 2. Restart ShiftLang

Restart the application for changes to take effect.

## How It Works

- **Model**: Uses `openrouter/free` - a free LLM model from OpenRouter
- **AI-powered**: The LLM understands context and nuance better than traditional translation
- **No API key required**: The free tier works without authentication
- **Optional API key**: You can add an API key for higher rate limits

## Getting an API Key (Optional)

1. Visit [OpenRouter](https://openrouter.ai/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Add it to `config.json`:

```json
{
  "translation_provider": "openrouter",
  "openrouter_api_key": "sk-or-v1-..."
}
```

## Benefits of AI Translation

- **Context awareness**: Better understanding of idioms and phrases
- **Accuracy**: More accurate translations, especially for complex sentences
- **Natural output**: Produces more natural-sounding translations
- **Better handling**: Handles technical terms and names better

## Limitations

- **Requires internet**: Must have an active internet connection
- **Slower**: AI translation takes longer than Google Translate
- **Rate limits**: Free tier has rate limits (can be increased with API key)

## Switching Back to Google Translate

Simply change `translation_provider` back to `"google"` in your `config.json`:

```json
{
  "translation_provider": "google"
}
```

## Testing

You can test the OpenRouter translator with:

```bash
python3 test_openrouter.py
```

This will translate a simple phrase and verify the connection works.

## Troubleshooting

### Translation fails or returns original text
- Check your internet connection
- Verify the API endpoint is accessible
- Consider adding an API key if you're hitting rate limits

### Slow translations
- AI translation is inherently slower than traditional translation
- Consider using Google Translate for quick, simple translations
- Use OpenRouter for important or complex translations

### API errors
- Check if OpenRouter's API is operational
- Verify your API key is correct (if using one)
- Check for rate limit errors

## Environment Variable

You can also set the API key via environment variable:

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

This way you don't need to store it in `config.json`.
