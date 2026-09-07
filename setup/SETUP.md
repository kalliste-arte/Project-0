# Setting up Aya on your PC

## 1. Prerequisites
- Windows 10/11
- Python 3.10 or 3.11 installed (check "Add to PATH" during install)
- A microphone and speakers/headset

## 2. Get the code onto your PC
Copy the whole `aya/` folder to somewhere permanent, e.g. `C:\Aya\`

## 3. Create a virtual environment and install dependencies
Open PowerShell in the `C:\Aya\` folder:
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Get your Claude API key
1. Go to https://console.anthropic.com and create an API key.
2. Set it as an environment variable (PowerShell, permanent):
```
setx ANTHROPIC_API_KEY "your-key-here"
```
Close and reopen PowerShell after this so it takes effect.

## 5. Set up the voice (Piper) - see VOICE_SETUP.md
Quick version:
1. Download Piper from https://github.com/rhasspy/piper/releases (Windows build)
2. Put `piper.exe` somewhere, e.g. `C:\Aya\piper\piper.exe`
3. Download the voice model files (`en_US-amy-medium.onnx` + `.json`) from
   https://github.com/rhasspy/piper/blob/master/VOICES.md
4. Put both files in `C:\Aya\voices\`
5. Set the exe path:
```
setx PIPER_EXE "C:\Aya\piper\piper.exe"
```

## 6. Whisper models
`faster-whisper` downloads models automatically on first run (needs internet
the first time only, then it's cached locally and works fully offline).

## 7. Test it
```
venv\Scripts\activate
python main.py
```
Say "Aya" and wait for the listening prompt, then talk.

## 8. Make her start on boot
See `setup/AUTOSTART.md` and run `setup/register_autostart.ps1`.

## Notes on the screen-seeing / active-window code
`core/screen_monitor.py` has a placeholder for reliable foreground-window
detection - `pygetwindow` gets the window title fine, but full process-name
detection needs a small `win32gui`/`win32process` lookup (a few lines,
included as a TODO comment) since that's genuinely Windows-API-specific and
worth wiring up once you're testing on your actual machine rather than
guessing at behavior blind. I can fill that in with you once you hit it -
it's a quick addition.
