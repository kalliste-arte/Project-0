# Voice setup (Piper - free, local, natural-sounding)

Piper is the recommended default: runs fully offline, no API cost, and has
several natural female voices.

## Recommended voices to try (all free)
- `en_US-amy-medium` - warm, clear American female voice (default in config)
- `en_US-hfc_female-medium` - another solid natural option
- `en_GB-jenny_dioco-medium` - British female voice, very natural cadence

Browse the full list with samples here: https://rhasspy.github.io/piper-samples/

## Steps
1. Download `piper_windows_amd64.zip` from the Piper GitHub releases page.
2. Extract it, note the path to `piper.exe`.
3. Download your chosen voice's `.onnx` and `.onnx.json` files from the
   Piper voices repo and place both in `aya/voices/`.
4. Update `config/settings.yaml` -> `voice.voice_model` if you pick a
   different voice than the default.
5. Set `PIPER_EXE` env var to the full path of `piper.exe` (see SETUP.md).

## If you want an even more natural/expressive voice later
ElevenLabs gives noticeably more emotional range but costs money and needs
internet. If you want to switch, `core/tts.py` is written so swapping the
engine is a self-contained change - just replace the `speak()` method's
internals, nothing else in the app needs to change.
