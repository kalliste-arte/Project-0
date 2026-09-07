"""
Aya - main loop.

Flow: wait for wake word -> record command -> transcribe ->
      think (Claude) -> if action: confirm out loud -> execute -> speak result
                      -> if speak: just speak
                      -> if clarify: speak the question, then listen again

Run: python main.py
(Set up venv + models first - see setup/SETUP.md)
"""
import os
import sys
import yaml

from core.wake_word import WakeWordListener
from core.stt import SpeechToText
from core.tts import TextToSpeech
from core.brain import Brain
from core.access_control import AccessControl, ActiveContext
from core.action_executor import ActionExecutor
from core.screen_monitor import ScreenMonitor, get_active_context

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "settings.yaml")


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def main():
    cfg = load_config()
    input_mode = cfg["assistant"].get("input_mode", "voice")

    print(f"[Aya] Starting up. Wake word: '{cfg['assistant']['wake_word']}' | input mode: {input_mode}")

    access = AccessControl(cfg)
    screen = ScreenMonitor(cfg, access)
    screen.start()

    brain = Brain(personality_cfg=cfg["personality"])
    executor = ActionExecutor(access)

    piper_exe = os.environ.get("PIPER_EXE", "piper")  # set in setup/SETUP.md
    voice_model = os.path.join(
        os.path.dirname(__file__), "voices",
        cfg["voice"]["voice_model"] + ".onnx"
    )
    tts = TextToSpeech(piper_exe, voice_model, cfg["voice"]["speaking_rate"])

    if input_mode == "text":
        # No mic needed - Aya still SPEAKS her replies, you just type instead of talk.
        stt = None
        wake = None
        print("[Aya] Ready. Type a command below (e.g. 'open Chrome', 'check my disk space').")
    else:
        stt = SpeechToText()
        wake = WakeWordListener(wake_word=cfg["assistant"]["wake_word"])
        print("[Aya] Ready. Listening for wake word...")

    def get_command() -> str:
        """Gets the next user command, via mic or typed text depending on input_mode."""
        if input_mode == "text":
            return input("You: ").strip()
        wake.listen_for_wake()
        print("[Aya] Wake word heard. Listening...")
        audio = stt.record_command()
        return stt.transcribe(audio)

    def get_confirmation() -> str:
        if input_mode == "text":
            return input("You: ").strip().lower()
        audio = stt.record_command(max_seconds=4)
        return stt.transcribe(audio).lower()

    while True:
        try:
            user_text = get_command()
            if not user_text.strip():
                continue
            print(f"[You] {user_text}")

            screen_state = screen.get_latest()
            screen_ctx = (
                f"active window: {screen_state.window_title}"
                if screen_state.visible else "(current window excluded from view)"
            )

            result = brain.think(user_text, screen_ctx=screen_ctx)

            if result["type"] == "speak":
                print(f"[Aya] {result['text']}")
                tts.speak(result["text"])

            elif result["type"] == "clarify":
                print(f"[Aya] {result['question']}")
                tts.speak(result["question"])
                # Next wake-free follow-up handled by hold_context window (extend as needed)

            elif result["type"] == "action":
                if cfg["behavior"].get("confirm_before_acting", True):
                    print(f"[Aya] {result['confirm_prompt']}")
                    tts.speak(result["confirm_prompt"])
                    confirm_text = get_confirmation()
                    confirmed = any(w in confirm_text for w in ["yes", "yeah", "yep", "go ahead", "sure", "do it"])
                else:
                    confirmed = True

                current_ctx = ActiveContext(
                    process_name=screen_state.process_name,
                    window_title=screen_state.window_title,
                )

                if confirmed:
                    outcome = executor.execute(result["tool"], result["input"], current_ctx)
                else:
                    outcome = "Okay, didn't do that."

                print(f"[Aya] {outcome}")
                tts.speak(outcome)
                brain.report_result(result["tool_use_id"], result["tool"], outcome)

        except KeyboardInterrupt:
            print("\n[Aya] Shutting down.")
            screen.stop()
            sys.exit(0)
        except Exception as e:
            print(f"[Aya] Error: {e}")


if __name__ == "__main__":
    main()
