# ShiftLang Installation Flow

## Interactive Installation

When you run `python install.py`, you'll now see these steps:

### 1. Welcome Screen
```
   ╭───────────────────────────────────────────────╮
   │                                               │
   │     ⚡  S H I F T L A N G  ⚡              │
   │                                               │
   │     Instant translation, any language         │
   │                                               │
   ╰───────────────────────────────────────────────╯
```

### 2. Language Selection
```
  Select 2 languages

    Select 2 languages · 0/2

    Search: type to filter...

  › english
    french
    spanish
    hebrew
    ...

    ↑↓ navigate • space select • enter confirm • backspace clear • esc exit
```

### 3. **NEW: Translation Provider Choice**
```
  Choose translation provider

    Google Translate is recommended for most users

  › Google Translate (Fast, free, no setup)
    OpenRouter AI (More accurate, requires internet)

    ↑↓ navigate • enter confirm • esc exit
```

#### If you choose Google Translate:
- No additional setup needed
- Continues to next step

#### If you choose OpenRouter AI:
```
    OpenRouter API key is optional (free tier available)
    Get an API key at https://openrouter.ai/ for higher limits

    OpenRouter API key (press Enter to skip): _
```

### 4. Auto-start Preference
```
  Start automatically on boot?

  › Yes
    No, I'll start manually

    ↑↓ navigate • enter confirm • esc exit
```

### 5. Hotkey Selection
```
  Choose keyboard shortcut

  › Default (Ctrl+Shift+Q)
    Custom shortcut

    ↑↓ navigate • enter confirm • esc exit
```

### 6. Setup Complete
```
  ✓ Setup complete


    Languages    english → hebrew
    Provider     Google Translate  (or "OpenRouter AI")
    Hotkey       ctrl+shift+q
    Auto-start   enabled

    Ready to translate ⚡
```

## Automatic/Silent Installation

For automatic installation (`python install.py --auto`):
- Uses saved config if it exists
- Otherwise uses defaults (Google Translate)
- Can be run on remote servers or in CI/CD

## Reconfiguration

To change settings later:
```bash
python install.py --reconfigure
```

This will run through all setup steps again, including the translation provider choice.

## Provider Comparison

### Google Translate
✓ Very fast (instant)
✓ Free, unlimited
✓ No setup required
✓ Works offline (cached)
✓ 130+ languages
✗ Less accurate for complex text
✗ Poor with idioms/context

### OpenRouter AI
✓ More accurate translations
✓ Better context understanding
✓ Natural-sounding output
✓ Free tier available
✓ Handles idioms well
✗ Slower (2-3 seconds)
✗ Requires internet
✗ Rate limits on free tier
