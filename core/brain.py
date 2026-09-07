"""
The brain: sends what you said (+ light screen context) to Claude,
and gets back either a spoken reply, an action request (which always
needs your confirmation before executing), or a clarifying question.

Uses Claude's tool-calling so "Aya open Chrome" / "Aya can you open
Chrome" / "hey Aya pull up Chrome" all resolve to the same action
intent - no rigid command syntax required.
"""
from __future__ import annotations
import os
from anthropic import Anthropic

MODEL = "claude-sonnet-4-6"

TOOLS = [
    {
        "name": "open_app",
        "description": "Open/launch an application by name.",
        "input_schema": {
            "type": "object",
            "properties": {"app_name": {"type": "string"}},
            "required": ["app_name"],
        },
    },
    {
        "name": "run_check",
        "description": "Run a diagnostic check (disk space, CPU usage, network status, RAM, running processes).",
        "input_schema": {
            "type": "object",
            "properties": {"check_type": {"type": "string"}},
            "required": ["check_type"],
        },
    },
    {
        "name": "run_script",
        "description": "Run a specific script or command the user has pre-approved.",
        "input_schema": {
            "type": "object",
            "properties": {"script_path": {"type": "string"}, "args": {"type": "string"}},
            "required": ["script_path"],
        },
    },
    {
        "name": "close_app",
        "description": "Close/quit an application.",
        "input_schema": {
            "type": "object",
            "properties": {"app_name": {"type": "string"}},
            "required": ["app_name"],
        },
    },
    {
        "name": "ask_clarification",
        "description": "Use this when the user's request is ambiguous and you need more detail before acting (e.g. 'run a check' without saying what kind).",
        "input_schema": {
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"],
        },
    },
]


def build_system_prompt(personality_cfg: dict, screen_ctx: str) -> str:
    warmth = personality_cfg.get("warmth_dial", 0.5)
    tone = "warm, casual, a little playful" if warmth > 0.6 else \
           "friendly but efficient and professional" if warmth > 0.3 else \
           "strictly professional and concise"

    return f"""You are Aya, a personal desktop voice assistant. Tone: {tone}.
You have real conversational warmth - react genuinely to what the user tells you,
remember recent context, use natural phrasing. You are not a romantic or intimate
companion; keep things warm but platonic, like a sharp, likeable human assistant.

Current screen context (may be empty if excluded from view): {screen_ctx}

Rules:
- If the user asks you to DO something (open/close an app, run a check, run a script),
  call the matching tool. You never execute anything yourself - the app layer will
  always ask the user to confirm before it actually happens, so it's safe to propose freely.
- If the request is ambiguous (e.g. "run a check" with no target), call ask_clarification
  instead of guessing.
- Otherwise just respond conversationally as spoken text (this gets read aloud, so keep
  it natural and not overly long).
"""


class Brain:
    def __init__(self, personality_cfg: dict, api_key: str | None = None):
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.personality_cfg = personality_cfg
        self.history: list[dict] = []

    def think(self, user_text: str, screen_ctx: str = "") -> dict:
        """Returns one of:
        {"type": "speak", "text": ...}
        {"type": "action", "tool": ..., "input": ..., "confirm_prompt": ...}
        {"type": "clarify", "question": ...}
        """
        system = build_system_prompt(self.personality_cfg, screen_ctx)
        self.history.append({"role": "user", "content": user_text})

        resp = self.client.messages.create(
            model=MODEL,
            max_tokens=1000,
            system=system,
            tools=TOOLS,
            messages=self.history,
        )

        self.history.append({"role": "assistant", "content": resp.content})

        for block in resp.content:
            if block.type == "tool_use":
                if block.name == "ask_clarification":
                    return {"type": "clarify", "question": block.input["question"]}
                return {
                    "type": "action",
                    "tool": block.name,
                    "input": block.input,
                    "tool_use_id": block.id,
                    "confirm_prompt": self._confirm_phrase(block.name, block.input),
                }

        text = "".join(b.text for b in resp.content if b.type == "text")
        return {"type": "speak", "text": text}

    def _confirm_phrase(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "open_app":
            return f"Want me to open {tool_input.get('app_name')}?"
        if tool_name == "close_app":
            return f"Want me to close {tool_input.get('app_name')}?"
        if tool_name == "run_check":
            return f"Want me to run a {tool_input.get('check_type')} check?"
        if tool_name == "run_script":
            return f"Want me to run {tool_input.get('script_path')}?"
        return "Want me to go ahead with that?"

    def report_result(self, tool_use_id: str, tool_name: str, result_text: str):
        """Feed the outcome of an executed/declined action back into the
        conversation so follow-ups have context."""
        self.history.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result_text,
            }],
        })
