# Quick Start - OpenRouter Integration

## What's New?

ShiftLang now supports **AI-powered translation** using OpenRouter LLM!

## Installation

Just run the installer as usual:

```bash
python install.py
```

You'll now see a new step asking which translation provider you want:

```
  Choose translation provider

    Google Translate is recommended for most users

  › Google Translate (Fast, free, no setup)
    OpenRouter AI (More accurate, requires internet)
```

### Option 1: Google Translate (Recommended for most users)
- ✓ Instant translations
- ✓ No setup needed
- ✓ Works offline (cached)
- Select and continue

### Option 2: OpenRouter AI (For better accuracy)
- ✓ More accurate translations
- ✓ Better context understanding
- ✓ Free tier available
- Select, then optionally enter API key (or press Enter to skip)

## Already Installed?

### Option A: Reconfigure
```bash
python install.py --reconfigure
```

This will let you choose your provider interactively.

### Option B: Manual Edit
Edit your `config.json`:

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

Then restart ShiftLang.

## Which Provider Should I Choose?

### Choose Google Translate if:
- You want instant translations
- You translate frequently
- Speed is more important than perfect accuracy
- You don't want to deal with API keys

### Choose OpenRouter AI if:
- You need highly accurate translations
- You're translating important documents
- You want better handling of idioms and context
- You don't mind 2-3 second translation time

## Testing

Test OpenRouter connection:
```bash
python3 test_openrouter.py
```

## Getting an API Key (Optional)

1. Visit https://openrouter.ai/
2. Sign up (free)
3. Get your API key
4. Add to config.json or set environment variable:
   ```bash
   export OPENROUTER_API_KEY="sk-or-v1-..."
   ```

## Need Help?

- Full guide: See `OPENROUTER_GUIDE.md`
- Installation details: See `INSTALL_FLOW.md`
- All changes: See `CHANGES.md`

## TL;DR

1. Run `python install.py --reconfigure`
2. Choose your provider when asked
3. Restart ShiftLang
4. Done! 🎉
