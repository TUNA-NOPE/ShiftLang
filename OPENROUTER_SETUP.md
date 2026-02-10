# OpenRouter Setup Guide

ShiftLang now supports **OpenRouter AI** for more accurate, AI-powered translations!

## What is OpenRouter?

OpenRouter provides access to various AI models including free models that can translate with better context understanding than traditional translation services.

## Setup Instructions

### 1. Get an API Key

1. Visit https://openrouter.ai/keys
2. Sign up or log in
3. Create a new API key
4. Copy your API key (starts with `sk-or-...`)

**Note:** OpenRouter requires you to add credits to your account ($5 minimum). Free models are available but you still need to fund your account.

### 2. Configure ShiftLang

Run the installer in reconfigure mode:

```bash
python install.py --reconfigure
```

When prompted:
1. Select **OpenRouter AI** as your translation provider
2. Paste your API key when asked
3. Complete the rest of the setup

### 3. Test Your Setup

```bash
python test_openrouter.py
```

If configured correctly, you should see:
```
✓ Translation successful!
```

## Troubleshooting

### "401 Unauthorized" Error

This means your API key is missing or invalid:

1. Check your API key at https://openrouter.ai/keys
2. Make sure you've added credits to your account
3. Run `python install.py --reconfigure` to update your key

### API Key Not Working

- Verify the key starts with `sk-or-`
- Check your OpenRouter account has available credits
- Test at https://openrouter.ai/playground to verify the key works

### Want to Switch Back to Google Translate?

Run `python install.py --reconfigure` and select **Google Translate** instead.

## Manual Configuration

You can also manually edit `config.json`:

```json
{
  "hotkey": "ctrl+shift+q",
  "auto_start": true,
  "source_language": "english",
  "target_language": "hebrew",
  "translation_provider": "openrouter",
  "openrouter_api_key": "sk-or-your-key-here"
}
```

## Comparison: Google vs OpenRouter

| Feature | Google Translate | OpenRouter AI |
|---------|-----------------|---------------|
| **Cost** | Free | Requires credits (~$5 min) |
| **Setup** | None needed | API key required |
| **Speed** | Fast | Moderate |
| **Accuracy** | Good | Better context understanding |
| **Languages** | 100+ | Depends on model |
| **Internet** | Required | Required |

## Support

- OpenRouter Docs: https://openrouter.ai/docs
- ShiftLang Issues: https://github.com/yourusername/ShiftLang/issues

## Cost Estimation

OpenRouter uses a pay-per-use model:
- Free models available (like `openrouter/free`)
- Most translations cost < $0.001 per request
- $5 credit typically lasts for thousands of translations

Check https://openrouter.ai/models for current pricing.
