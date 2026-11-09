"""
MM9's Town Portal altars (TownPortal.scr, one per city: the DAT object TownPortal0, script parameter the city).

MM9: OnUse gives the city's key (5011 Thjorgard ... 5016 Thronheim; the key opens that city in the Town Portal screen),
swaps the model's skin for the clean one (SetModelFilenames Portal-Whole.ABC PortalClean.dtx) and plays quest.wav;
:Init runs FixCheck, which shows the clean skin once the key is set.

Here (the route of Frosgard's ChangeModel.scr maypole): content.props places the altar's decoration (mm9_portalwhole,
the dirty skin) with the SetSprite key COG_DIRTY and a twin `<name>Clean` (mm9_portalclean, the clean skin; the
props project's same mesh and UVs) at the same spot with COG_CLEAN and the same click event. The map script's
`townPortalAltar()` shows one of the two by the key: the click calls it after giving the key, the map load (FixCheck)
on every load.
"""

from __future__ import annotations

KEYS = {"thjorgard": 5011, "sturmford": 5012, "drangheim": 5013, "guberland": 5014, "frosgard": 5015,
        "thronheim": 5016}
CLEAN = "mm9_portalclean"
COG_DIRTY, COG_CLEAN = 490, 491        # SetSprite keys (the cities' own props use 400-4xx, destructibles 20000+)


def is_altar(entry: dict) -> bool:
    return str(entry.get("script") or "").lower().replace("scripts\\", "") == "townportal.scr"


def clean_name(name: str) -> str:
    return f"{name}Clean"


def key(entry: dict) -> int:
    city = str(entry.get("script_params") or "").strip().lower()
    if city not in KEYS:
        raise SystemExit(f"{entry['source_name']}: TownPortal.scr parameter {entry.get('script_params')!r} is no city")
    return KEYS[city]


def handler(name: str, entry: dict, event: int) -> list[str]:
    """The altar's Lua: townPortalAltar() (shows the dirty or the clean altar by the key) and the click handler.
    The map script calls on_load() in its load handler; `has` and `quest` are the city scripts' helpers."""
    k = key(entry)
    city = str(entry["script_params"]).strip()
    return [f"-- {name}: TownPortal.scr \"{city}\": cleansing the altar gives key {k} and MM9 swaps its dirty skin for",
            f"-- the clean one: {name} (SetSprite {COG_DIRTY}) hides and {clean_name(name)} ({COG_CLEAN}, the clean",
            "-- altar at its place) shows; the map load does the same once the key is set (:Init FixCheck).",
            "local function townPortalAltar()",
            f"    local clean = has({k})",
            f"    evt.SetSprite({COG_DIRTY}, clean and 0 or 1, \"0\"); evt.SetSprite({COG_CLEAN}, clean and 1 or 0, \"0\")",
            "end",
            f"handlers[{event}] = function()",
            f"    if has({k}) then return end",
            f"    MM9.giveKey({k}); quest()",
            "    townPortalAltar()",
            "    evt.StatusText(\"The altar is cleansed.\")",
            "end"]


def on_load() -> str:
    return "    townPortalAltar()   -- TownPortal.scr :Init (FixCheck): the clean altar once its key is set"


def click_steps(name: str, event: int, k: int) -> list[dict]:
    """Scenario steps (the map's scripted scenario, after its load): the dirty altar stands, its click gives the key,
    hides it and shows the clean one."""
    qbit = 90000 + k
    return [{"note": {"text": f"TownPortal.scr: {name} stands dirty ({COG_DIRTY} shown, its clean twin {COG_CLEAN} "
                              f"hidden); the click cleanses it: key {k}, the dirty altar hides, the clean one shows."}},
            {"assert": {"qbit_clear": [qbit], "sprite_shown": [COG_DIRTY], "sprite_hidden": [COG_CLEAN]}},
            {"execute_event": {"id": event}},
            {"advance_runtime": {"seconds": 0.5}},
            {"assert": {"qbit_set": [qbit], "sprite_hidden": [COG_DIRTY], "sprite_shown": [COG_CLEAN]}}]


def reload_steps(map_name: str, k: int) -> list[dict]:
    """Scenario steps after click_steps (at the end: they reload the map): the load shows the clean altar."""
    return [{"note": {"text": f"TownPortal.scr :Init (FixCheck): the map loaded again with key {k} shows the clean "
                              "altar."}},
            {"load_map": {"map": map_name}},
            {"advance_runtime": {"seconds": 1.0}},
            {"assert": {"qbit_set": [90000 + k], "sprite_hidden": [COG_DIRTY], "sprite_shown": [COG_CLEAN]}}]


def scenario_steps(props_path, events: dict, map_name: str) -> list[dict]:
    """The altar's scenario steps for the end of a city's scripted scenario: click_steps, then reload_steps."""
    import json
    from pathlib import Path
    name, entry = next((e["source_name"], e) for e in json.loads(Path(props_path).read_text()) if is_altar(e))
    return click_steps(name, events[name], key(entry)) + reload_steps(map_name, key(entry))
