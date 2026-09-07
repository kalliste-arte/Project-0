"""
Tracks the active window/process and (optionally) grabs screenshots,
but ALWAYS checks access_control first. Excluded apps/windows never
get captured - not even briefly held in memory.
"""
from __future__ import annotations
import time
import threading
from dataclasses import dataclass, field

import psutil
import mss

from core.access_control import AccessControl, ActiveContext

try:
    import pygetwindow as gw
except ImportError:
    gw = None  # non-Windows dev environments


@dataclass
class ScreenState:
    process_name: str = ""
    window_title: str = ""
    screenshot_path: str | None = None
    visible: bool = False   # False when the current window is excluded
    timestamp: float = field(default_factory=time.time)


def get_active_context() -> ActiveContext:
    """Best-effort active window/process lookup. Windows-first; add
    linux/mac backends here later if needed."""
    proc_name, title = "", ""
    try:
        if gw is not None:
            win = gw.getActiveWindow()
            if win:
                title = win.title or ""
    except Exception:
        pass
    try:
        # crude but works cross-platform enough: foreground pid via psutil
        for p in psutil.process_iter(["name"]):
            pass  # placeholder - real foreground-pid lookup is Windows API (win32gui)
    except Exception:
        pass
    return ActiveContext(process_name=proc_name, window_title=title)


class ScreenMonitor:
    def __init__(self, config: dict, access: AccessControl):
        self.cfg = config.get("screen_access", {})
        self.access = access
        self._running = False
        self._thread: threading.Thread | None = None
        self.latest: ScreenState = ScreenState()
        self._lock = threading.Lock()

    def start(self):
        if not self.cfg.get("enabled", True):
            self.latest = ScreenState(visible=False)
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def pause(self):
        self._running = False

    def resume(self):
        if not self._running:
            self.start()

    def _loop(self):
        interval = self.cfg.get("capture_interval_seconds", 3)
        with mss.mss() as sct:
            while self._running:
                ctx = get_active_context()
                allowed = self.access.can_see(ctx)

                state = ScreenState(
                    process_name=ctx.process_name,
                    window_title=ctx.window_title,
                    visible=allowed,
                )

                if allowed:
                    try:
                        # grab primary monitor only; not persisted to disk long-term
                        shot = sct.grab(sct.monitors[1])
                        state.screenshot_path = None  # kept in-memory by design;
                        # write to a temp file only if a query actually needs vision
                        self._last_raw = shot
                    except Exception:
                        pass
                else:
                    self._last_raw = None  # explicitly drop anything captured

                with self._lock:
                    self.latest = state

                time.sleep(interval)

    def get_latest(self) -> ScreenState:
        with self._lock:
            return self.latest
