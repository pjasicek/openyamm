"""
MM9's greeting voices (scr_audit npc_quest_minigame.md G6): most NPC scripts' :OnUse play the NPC's voice when the
party uses (clicks) it, beside the dialogue the engine opens (Shopkeeper.scr and Retainer.scr with their first
ScriptParams token, NPCnnn.scr with its own file). `use_voices` reads that from each object's script; objects.py
`voice_lines` gives each placed NPC actor whose map script has no click event of its own (53000 + its DAT index,
game/mm9/Mm9RudeDialogue.h) a handler that plays the voice and opens the actor's RUDE dialogue; a click the map's own
Lua handles without that voice gets the voice first. The placement's GreetingSound (`greeting_voice`) counts too.
"""

from __future__ import annotations

import re

from .source import ROOT

AUDIO = ROOT / "assets_dev/worlds/mm9/audio"
USE_EVENT_BASE = 53000              # an MM9 object's Use (click) event: 53000 + its DAT index


def _block(text: str, label: str) -> str:
    """The lines of a script label (`:OnUse`) up to its `exit` or the next label (lower-case text)."""
    match = re.search(rf"^\s*:{label}\b(.*?)(?=^\s*:\w|\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def _sound_name(value: str) -> str | None:
    """An MM9 sound path as the world's audio name ("\\voices\\NPC\\NPC_103.wav" -> "voices/npc/npc_103.wav"), or
    None when the world has no such file."""
    name = value.strip().strip('"').replace("\\", "/").lstrip("/").lower()
    if name.startswith("sounds/"):
        name = name[len("sounds/"):]
    return name if name.endswith(".wav") and (AUDIO / name).is_file() else None


def use_voice(o: dict) -> str | None:
    """The sound an object's script plays on use (its :OnUse's Playsound): a literal path, else the variable's
    GetParam token of ScriptParams or its `set` value in the script."""
    from .objects import _script_text
    p = o["properties"]
    text = _script_text(str(p.get("ScriptName") or ""))
    played = re.search(r"^\s*playsound\s+([^,\s]+)", _block(text, "onuse"), re.M)
    if not played:
        return None
    value = played.group(1)
    if ".wav" in value:
        return _sound_name(value)
    param = re.search(rf"^\s*getparam\s+(\d+)\s*,?\s*{re.escape(value)}\b", text, re.M)
    tokens = str(p.get("ScriptParams") or "").split()
    if param and int(param.group(1)) < len(tokens):
        return _sound_name(tokens[int(param.group(1))])
    assigned = re.search(rf"^\s*set\s+{re.escape(value)}\s*,?\s*(\S+\.wav)", text, re.M)
    return _sound_name(assigned.group(1)) if assigned else None


def greeting_voice(o: dict) -> str | None:
    """The placement's own GreetingSound: MM9's native NPC use plays it as the NPC's voice before the dialogue opens
    (object.lto NPC +0x1e4 -> +0xbb4, monster_ai/MM9_AMBIENT_ANIMATION.md section 2.4); most shopkeepers, trainers and
    bankers have theirs here, not in a script."""
    value = str(o["properties"].get("GreetingSound") or "").strip()
    return _sound_name(value) if value else None


def use_voices(source) -> dict:
    """DAT index -> the voice a click on the object plays: its GreetingSound, else its script's :OnUse voice."""
    out = {}
    for o in source.objects:
        voice = greeting_voice(o) or (use_voice(o) if o["properties"].get("ScriptName") else None)
        if voice:
            out[o["index"]] = voice
    return out
