# Aya - Personal Desktop Assistant

A Jarvis-style voice assistant that runs locally on your PC.

## What she does
- Wakes on "Aya" (local, offline keyword spotting)
- Understands natural phrasing, not rigid commands
  ("Aya open Chrome" / "hey Aya can you pull up Chrome" both work)
- Always-on screen/active-window awareness, with an editable exclude
  list so certain apps (banking, password managers) are never seen
- Access control for what she can act on (open/close apps, run checks/scripts),
  configurable per-app or per-category, full or restricted
- **Never executes an action without asking you first** - this is not
  configurable to "off" in the UI on purpose; it's the safety backbone
- Local speech-to-text (Whisper) and local text-to-speech (Piper) -
  no cloud round-trip for voice, so it's fast and free
- Claude API as the reasoning brain - actual understanding, not
  keyword matching
- Starts automatically at Windows logon (optional, one script to enable)

## Project layout
```
aya/
  config/settings.yaml      <- all your settings: exclude lists, access control, personality
  core/
    wake_word.py            <- listens for "Aya"
    stt.py                  <- speech -> text (Whisper)
    tts.py                  <- text -> speech (Piper)
    brain.py                <- Claude API, decides what to say/do
    access_control.py       <- the ONE place that enforces what she can see/touch
    screen_monitor.py       <- tracks active window, respects exclude list
    action_executor.py      <- the ONE place that actually touches your OS
  main.py                   <- ties it all together, run this to start her
  setup/
    SETUP.md                <- full install walkthrough, start here
    VOICE_SETUP.md          <- picking/installing a Piper voice
    register_autostart.ps1  <- run once to make her start at boot
  requirements.txt
```

## Quick start
Read `setup/SETUP.md` top to bottom - it covers Python setup, getting your
Claude API key, installing the local voice, and testing.

## Design choices worth knowing about
- **Confirm-before-acting is structural, not a toggle in the config file** -
  it lives in the code path itself, so there's no accidental way to turn it
  off from settings.yaml. If you genuinely want autonomy for specific safe
  actions down the line, that's a deliberate code change in `main.py`, not
  a settings flip - keeps it intentional.
- **Excluded apps are never captured, not just not-shown** - the exclude
  check in `screen_monitor.py` happens before any screenshot/window data is
  even read into memory.
- She's built with a warm, natural personality dial, but no romantic/intimate
  mode - that's fixed, not a config option.

## What's stubbed vs what's ready to run
- Wake word, STT, TTS, brain, access control, action execution: fully implemented.
- Foreground **process name** detection (used for app-based exclude rules)
  needs a small Windows-API addition once you're testing on your real
  machine - flagged clearly in `screen_monitor.py` and `setup/SETUP.md`.
  Window *title* detection works as-is.
- `run_check` covers disk/CPU/RAM; network check is a placeholder you can
  wire up to whatever tool you prefer.

Bring it up whenever you hit either of those and I'll fill them in with you.
