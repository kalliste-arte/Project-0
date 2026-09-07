"""
Executes actions Claude proposes - but ONLY after the user confirms
out loud, and ONLY if access_control allows it for the current context.

This is the one place that actually touches the OS. Keep it that way -
don't let other modules call subprocess/pyautogui directly.
"""
from __future__ import annotations
import subprocess
import platform

from core.access_control import AccessControl, ActiveContext


class ActionExecutor:
    def __init__(self, access: AccessControl):
        self.access = access

    def execute(self, tool_name: str, tool_input: dict, current_ctx: ActiveContext) -> str:
        if not self.access.can_act(current_ctx):
            return "That app is off-limits in your access settings, so I didn't touch it."

        try:
            if tool_name == "open_app":
                return self._open_app(tool_input["app_name"])
            if tool_name == "close_app":
                return self._close_app(tool_input["app_name"])
            if tool_name == "run_check":
                return self._run_check(tool_input["check_type"])
            if tool_name == "run_script":
                return self._run_script(tool_input["script_path"], tool_input.get("args", ""))
            return f"I don't know how to do '{tool_name}' yet."
        except Exception as e:
            return f"That didn't work - {e}"

    def _open_app(self, app_name: str) -> str:
        if platform.system() == "Windows":
            subprocess.Popen(["start", "", app_name], shell=True)
        else:
            subprocess.Popen([app_name])
        return f"Opened {app_name}."

    def _close_app(self, app_name: str) -> str:
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/IM", app_name, "/F"], check=False)
        else:
            subprocess.run(["pkill", "-f", app_name], check=False)
        return f"Closed {app_name}."

    def _run_check(self, check_type: str) -> str:
        check_type = check_type.lower()
        import psutil
        if "disk" in check_type:
            usage = psutil.disk_usage("/")
            return f"Disk: {usage.percent}% used, {usage.free // (1024**3)} GB free."
        if "cpu" in check_type:
            return f"CPU usage: {psutil.cpu_percent(interval=1)}%."
        if "ram" in check_type or "memory" in check_type:
            mem = psutil.virtual_memory()
            return f"RAM: {mem.percent}% used."
        if "network" in check_type:
            return "Network check placeholder - wire up a ping/speed test here if you want it."
        return f"Not sure how to check '{check_type}' yet - easy to add in action_executor.py."

    def _run_script(self, script_path: str, args: str) -> str:
        cmd = [script_path] + (args.split() if args else [])
        subprocess.Popen(cmd, shell=True)
        return f"Ran {script_path}."
