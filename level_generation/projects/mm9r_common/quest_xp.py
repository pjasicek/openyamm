"""The MM9 quest XP caps for the rework converters (devdocs/mm9_rework/BALANCE_PLAN.md section 3.1).

Every experience award a rework converter writes goes through `balanced_experience` (or `experience_lua` /
`experience_note` for the Lua text), which looks the original MM9 amount up in
`tools/mm9_import_discovery/mm9_quest_xp_profile.yml`, the profile `mm9_scr_to_lua.py` uses. An award matches by its
quest key and original amount, else by its SCR script, routine and original amount (the four keyless entries, and
awards whose rework key differs from the profile's); awards not in the profile are the small ones under the caps and
keep their amount. `quest_xp_audit.py` lists every site and the profile entries no site matches.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
PROFILE_PATH = ROOT / "tools/mm9_import_discovery/mm9_quest_xp_profile.yml"
PROFILE_NAME = PROFILE_PATH.name


@lru_cache(maxsize=None)
def load_profile(path: Path = PROFILE_PATH) -> tuple[dict, dict]:
    """The balanced amounts by (key, original) and by (script, routine, original), script and routine in lower case."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    by_key: dict[tuple[int, int], int] = {}
    by_script: dict[tuple[str, str, int], int] = {}
    for award in data.get("awards") or []:
        original, xp = int(award["original"]), int(award["xp"])
        if award.get("key") is not None:
            found = by_key.setdefault((int(award["key"]), original), xp)
            if found != xp:
                raise ValueError(f"{path}: key {award['key']} pays {original} as {found} and {xp}")
        by_script[(str(award["script"]).lower(), str(award["routine"]).lower(), original)] = xp
    return by_key, by_script


def balanced_experience(original: int, key: int | None = None, script: str | None = None,
                        routine: str | None = None, path: Path = PROFILE_PATH) -> int:
    """The capped amount of an MM9 award of `original` experience: by (key, original), else by (script, routine,
    original), else the original (not in the profile: under the cap)."""
    by_key, by_script = load_profile(path)
    original = int(original)
    if key is not None and (int(key), original) in by_key:
        return by_key[(int(key), original)]
    if script is not None and routine is not None:
        found = by_script.get((script.lower(), routine.lower(), original))
        if found is not None:
            return found
    return original


def experience_note(original: int, key: int | None = None, script: str | None = None,
                    routine: str | None = None, path: Path = PROFILE_PATH) -> str:
    """The Lua line-end comment of a capped award (` -- MM9 GiveExp <original>, mm9_quest_xp_profile.yml`), else ""."""
    if balanced_experience(original, key, script, routine, path) == int(original):
        return ""
    return f" -- MM9 GiveExp {int(original)}, {PROFILE_NAME}"


def experience_lua(original: int, key: int | None = None, script: str | None = None,
                   routine: str | None = None, path: Path = PROFILE_PATH) -> str:
    """`MM9.giveExperience(<xp>)`, with `-- MM9 GiveExp <original>, mm9_quest_xp_profile.yml` when capped (as
    mm9_scr_to_lua.py writes it); the comment runs to the end of the line, so nothing may follow it there."""
    xp = balanced_experience(original, key, script, routine, path)
    return f"MM9.giveExperience({xp}){experience_note(original, key, script, routine, path)}"
