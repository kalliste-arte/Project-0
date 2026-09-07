"""
Access control: the single source of truth for what Aya is allowed
to SEE (screen capture) and ACT ON (click/type/run/close).

Every check funnels through here so there's exactly one place that
enforces the exclude list / category rules - no module bypasses it.
"""
from __future__ import annotations
import fnmatch
from dataclasses import dataclass


@dataclass
class ActiveContext:
    process_name: str        # e.g. "chrome.exe"
    window_title: str        # e.g. "Instagram - Google Chrome"


class AccessControl:
    def __init__(self, config: dict):
        self.cfg = config
        self.categories = config.get("categories", {})

    # ---------- helpers ----------

    def _expand_category(self, name: str) -> list[str]:
        return self.categories.get(name, [])

    def _matches_any(self, ctx: ActiveContext, patterns: list[str]) -> bool:
        proc = (ctx.process_name or "").lower()
        title = (ctx.window_title or "").lower()
        for pat in patterns:
            pat = pat.lower()
            if "|" in pat:
                # "chrome.exe|instagram.com" -> process AND title-substring match
                proc_pat, title_pat = pat.split("|", 1)
                if fnmatch.fnmatch(proc, proc_pat) and title_pat in title:
                    return True
            elif pat.endswith(".exe"):
                if fnmatch.fnmatch(proc, pat):
                    return True
            else:
                if pat in title or pat in proc:
                    return True
        return False

    # ---------- SEE ----------

    def can_see(self, ctx: ActiveContext) -> bool:
        screen_cfg = self.cfg.get("screen_access", {})
        if not screen_cfg.get("enabled", True):
            return False

        excl = screen_cfg.get("exclude", {})
        if self._matches_any(ctx, excl.get("apps", [])):
            return False
        for kw in excl.get("window_title_contains", []):
            if kw.lower() in (ctx.window_title or "").lower():
                return False
        for cat in excl.get("categories", []):
            if self._matches_any(ctx, self._expand_category(cat)):
                return False
        return True

    # ---------- ACT ----------

    def can_act(self, ctx: ActiveContext) -> bool:
        act_cfg = self.cfg.get("action_access", {})
        if act_cfg.get("mode", "full") == "full":
            blocked = act_cfg.get("blocked", {})
        else:
            blocked = act_cfg.get("blocked", {})

        if self._matches_any(ctx, blocked.get("apps", [])):
            return False
        for cat in blocked.get("categories", []):
            if self._matches_any(ctx, self._expand_category(cat)):
                return False
        return True

    def reload(self, new_config: dict):
        """Call after editing settings.yaml at runtime (e.g. via voice: 'block Discord')."""
        self.cfg = new_config
        self.categories = new_config.get("categories", {})
