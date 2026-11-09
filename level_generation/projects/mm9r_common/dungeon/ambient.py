"""MM9's AmbientSound objects as the scene's `ambient_sounds` (devdocs/AMBIENT_SOUNDS.md).

Each keeps MM9's file (a world sound name under worlds/mm9/audio; a file not there by its path is looked up by its name
anywhere in that folder, else left out and listed), its inner and outer radius (x 2.56), its volume (see
`ambient_volume`), its loop (not with a LoopCount: once per switch-on) and the random wait between plays
(LoopWaitMin/Max seconds), DayOnly/NightOnly (both: night only, as MM9) and StartOn. The fire family's own sounds
(Fire, Brazier, WallTorch, Torch: SoundFile within SoundRadius) are `fire_sounds`.
"""

from __future__ import annotations

import struct

from . import source as _source  # noqa: F401 (puts the MM9 import tools on sys.path)
from .source import ROOT, SCALE
from transcode_mm9_dat_to_odm import normalize_mm9_sound_name  # noqa: E402

AUDIO = ROOT / "assets_dev/worlds/mm9/audio"

# MM9's engine plays an ambient sound at Volume/127 of full scale, not Volume/100: its per-frame update hands the 0-100
# volume to Miles' 0-127 scale unscaled (devdocs/mm9_rework/MM9_AMBIENT_VOLUME_RE.md).
MM9_AMBIENT_FULL_SCALE = 127.0
# MM9 put ambient sounds level with its music (shipped Master 75 on the sounds, Music 75 on the CD line); OpenYAMM's
# default sliders (sound 3/9, music 2/9) put sounds 1.5x above music. This restores MM9's balance under those defaults.
MM9_AMBIENT_MUSIC_BALANCE = 2.0 / 3.0


def ambient_volume(mm9_volume: float) -> float:
    """MM9's Volume (0-100) as the scene's 0-1 volume, as loud against the music as in MM9."""
    level = mm9_volume / MM9_AMBIENT_FULL_SCALE * MM9_AMBIENT_MUSIC_BALANCE
    return round(min(max(level, 0.0), 1.0), 3)


def _float(value, default: float) -> float:
    """MM9 stores some floats as their bit pattern in an int (Volume 1120403456 = 100.0)."""
    if value is None:
        return default
    if isinstance(value, int) and abs(value) > 100000:
        return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]
    return float(value)


def _catalog() -> tuple[dict, dict]:
    paths = [p.relative_to(AUDIO).as_posix() for p in AUDIO.rglob("*") if p.is_file()]
    by_path = {path.lower(): path for path in paths}
    by_name = {}
    for path in sorted(paths):
        by_name.setdefault(path.rsplit("/", 1)[-1].lower(), path)
    return by_path, by_name


def ambient_sounds(source, project, stats) -> list[dict]:
    by_path, by_name = _catalog()
    out, missing = [], []
    for o in source.objects:
        if o["class"] != "AmbientSound":
            continue
        p = o["properties"]
        wanted = normalize_mm9_sound_name(p.get("Filename"))
        sound = by_path.get(wanted.lower()) or by_name.get(wanted.rsplit("/", 1)[-1].lower())
        if not sound:
            missing.append(wanted)
            continue
        inner = _float(p.get("InnerRadius"), 0.0) * SCALE
        outer = max(_float(p.get("OuterRadius"), 0.0) * SCALE, inner + 1.0)
        record = {
            "key": o["index"],
            "sound": sound,
            "position": [round(float(v)) for v in project.native(p["Pos"])],
            "inner_radius": round(inner),
            "outer_radius": round(outer),
            "volume": ambient_volume(min(_float(p.get("Volume"), 100.0), 100.0)),
            # LoopCount (a float, 0: for ever) 1 on the 13 switched sounds (1000 Terrors' Rumble0, the Training
            # Hall's crash sounds, the Dungeon of Secrets' rats): MM9 plays them once each time they are switched on
            "loop": bool(p.get("Loop", 1)) and _float(p.get("LoopCount"), 0.0) < 1.0,
        }
        wait = (_float(p.get("LoopWaitMin"), 0.0), _float(p.get("LoopWaitMax"), 0.0))
        if wait[1] > 0:
            record["wait"] = [round(wait[0], 2), round(max(wait), 2)]
        # MM9's ReadProp clears DayOnly when NightOnly is set too (object.lto 0x100775ed): both is night only
        if p.get("NightOnly"):
            record["night_only"] = True
        elif p.get("DayOnly"):
            record["day_only"] = True
        if not p.get("StartOn", 1):
            record["start_on"] = False
        out.append(record)
    stats["ambient_sounds"] = len(out)
    stats["ambient_sounds_missing_files"] = sorted(set(missing))
    return out


# MM9's fire effect classes, which all carry a SoundFile and SoundRadius (object.lto Fire ReadProp 0x1006b920)
FIRE_CLASSES = ("Fire", "Brazier", "WallTorch", "Torch")


def fire_sounds(build, stats) -> list[dict]:
    """The fire family's looped SoundFile within its SoundRadius (MM9_AMBIENT_AUDIO_RE.md section 1; inner radius a
    quarter of it, as MM9's AmbientSounds' 250 / 1000; full volume; key: the object's DAT index). Every one is
    carried, burning or not, scripted or not: one the map's hooks placed as a decoration with a cog (`primary`:
    Anskram's gate fires, the Bathhouse furnace, Verhoffin's pentagram) follows that decoration's evt.SetSprite
    (`sprite`); the others are on as MM9's `On` says, and a map script can switch them by AmbientSound<key>."""
    from .objects import FIRE_SOUND_INNER, _number
    by_path, by_name = _catalog()
    cogs = {entry["anchor"].lower(): entry["cog"] for entry in build.content.report["decorations"] if entry.get("cog")}
    out, missing = [], []
    for o in build.source.objects:
        p = o["properties"]
        radius = _number(p.get("SoundRadius")) * SCALE
        if o["class"] not in FIRE_CLASSES or not p.get("SoundFile") or radius <= 0 or "Pos" not in p:
            continue
        wanted = normalize_mm9_sound_name(p["SoundFile"])
        sound = by_path.get(wanted.lower()) or by_name.get(wanted.rsplit("/", 1)[-1].lower())
        if not sound:
            missing.append(wanted)
            continue
        record = {"key": o["index"], "sound": sound,
                  "position": [round(float(v)) for v in build.project.native(p["Pos"])],
                  "inner_radius": round(radius * FIRE_SOUND_INNER), "outer_radius": round(radius),
                  "volume": ambient_volume(100.0), "loop": True}
        if not _number(p.get("On"), 1.0):
            record["start_on"] = False
        cog = cogs.get(o["name"].lower())
        if cog:
            record["sprite"] = cog
        out.append(record)
    stats["fire_sounds"] = len(out)
    stats["fire_sounds_by_sprite"] = sum(1 for record in out if "sprite" in record)
    stats["fire_sounds_off_at_start"] = sum(1 for record in out if record.get("start_on") is False)
    if missing:
        stats["fire_sounds_missing_files"] = sorted(set(missing))
    return out
