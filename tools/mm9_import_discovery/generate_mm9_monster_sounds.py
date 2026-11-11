#!/usr/bin/env python3
"""Bind every MM9 monster and NPC row to MM9's own sounds (devdocs/mm9_rework/MM9_MONSTER_SOUNDS.md).

MM9 keys a creature's sounds to its model's animations: a keyframe string of the ABC model names a command, and the
client (cshell.dll) builds the file from the row's MONSTERS.txt BaseName (or FootSound) and the animation's name:

    PlayAnimSound, SpeakAnimSound   sounds\\animSounds\\<BaseName>\\<animation>.wav (speak: the creature's voice)
    PlaySoundFX, PlayAnimFX         sounds\\animSounds\\<BaseName>\\FX_<animation>.wav
    PlayDeathSound                  sounds\\DeathSounds\\<BaseName>\\<animation>.wav
    Flap                            sounds\\animSounds\\<BaseName>\\Flap.wav
    Footstep                        sounds\\animsounds\\footsteps\\<FootSound><n>.wav, n cycling 1..count

Two families add script-played idle sounds on model keys (GuardSounds.inc OnStand/OnSleep, MonkSounds.inc
OnPray/OnSweep/OnWash). This tool finds which of our 3D model clips each ABC animation became (by pose signature), and
writes:

- data_tables/sounds.txt: the world sound table, one id per imported animsounds/deathsounds file (ids 50000-59999);
- models/actor_sounds.yml: per descriptor, the timed sound events of its model's clips (WorldFxSystem plays them);
- mm9_monster_sound_slots.tsv: per row, the four descriptor sound ids (attack, death, wince, fidget) for
  generate_mm9_monster_tables.py, played when the actor is not drawn as a model;
- the coverage table in devdocs/mm9_rework/MM9_MONSTER_SOUNDS.md.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

import convert_abc_model
import generate_mm9_monster_tables as tables
from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE


SOUND_ID_BEGIN = 50000
SOUND_ID_END = 54999   # 55000-59999: the player-character voices (generate_mm9_pc_voices.py)
# weapons/: the launch sounds of MM9's projectiles (PROJECTILE.txt Launch Sound); its ids follow the others' (sorted
# names), so adding it kept every animsounds/deathsounds id.
SOUND_FOLDERS = ("animsounds", "deathsounds", "weapons")
# A ranged attack's clip role per MM9 projectile column (attack3 takes attack2's place when present, as the tables do).
RANGED_ROLES = (("attack1_projectile", ("attack_ranged",)),
                ("attack2_projectile", ("attack_ranged2", "attack_ranged")),
                ("attack3_projectile", ("attack_ranged3", "attack_ranged2", "attack_ranged")))
# MONSTERS.txt columns read here (positional, as generate_mm9_monster_tables.SOURCE_COLUMN).
COLUMN_MODEL = 2
COLUMN_FOOT_SOUND = 53
COLUMN_FOOT_RADIUS = 54
COLUMN_BASE_NAME = 65
COLUMN_VOICE_RADIUS = 78
COLUMN_SCRIPT = tables.SOURCE_COLUMN["script"]

# Model key command -> event kind (cshell.dll 0x1005b040 dispatch; object.lto 0x10002580 precache).
KEY_KINDS = {
    "playanimsound": "play", "speakanimsound": "speak", "playsoundfx": "fx", "playanimfx": "fx",
    "playdeathsound": "death", "footstep": "footstep", "flap": "flap",
}
# Camera shake keys (cshell.dll 0x1005b16d dispatch -> 0x100ab070): radius, amplitude at the radius and at the model,
# seconds at full strength and decay per second (MM9 units). MM9's amplitude is edge + (near - edge)(1 - d / radius),
# none beyond the radius. As the converters' EarthQuakes (devdocs/mm9_rework/MM9_CUTSCENES.md): our intensity is the
# amplitude / 12 (the client's clamp), our seconds the full seconds + amplitude / decay.
EQ_KEYS = {
    "bigeq": (6000.0, 1.0, 6.0, 1.3, 10.0),
    "smalleq": (1200.0, 1.0, 4.0, 0.4, 20.0),
    "smallereq": (900.0, 0.5, 2.0, 0.25, 30.0),
}


def eq_shake(command: str) -> dict:
    radius, edge, near, full, decay = EQ_KEYS[command]
    return {"near": round(near / 12.0, 3), "edge": round(edge / 12.0, 3), "seconds": round(full + near / decay, 3),
            "radius": round(radius * MM9_TO_OPENYAMM_COORDINATE_SCALE, 1)}


# The footstep files precached per FootSound (object.lto 0x10008221: indices 0-4; the files start at 1).
MAX_FOOTSTEPS = 4

# Script idle sounds on model keys: the row scripts that include GuardSounds.inc / MonkSounds.inc, and per key the
# files, the chance of a play, the gate after a play and after a miss (Is_Playing waits), volume and radii (MM9 units).
GUARD_SCRIPTS = {"guardbase.scr", "guardhelp.scr", "guardrude.scr", "jeff.scr", "guardsounds.scr"}
MONK_SCRIPTS = {"monkbase.scr", "monkguardbasic.scr", "thjoradmonk.scr", "thjoradmonkmod.scr", "workingmonk.scr",
                "workingmonkmod.scr"}


@dataclass(frozen=True)
class ScriptSound:
    sounds: tuple[str, ...]
    chance: float = 1.0
    gate: float = 0.0
    miss_gate: float = 0.0
    volume: float = 1.0
    radius: float = 1000.0
    inner: float = 100.0


SCRIPT_SOUNDS = {
    # GetRandomInt 1, 20: 1-7 play Stand<n> and wait 1.2 s, 8-20 wait 50 s.
    ("guard", "stand"): [ScriptSound(tuple(f"animsounds/guard/stand{n}" for n in range(1, 8)), 7 / 20, 1.2, 50.0)],
    # One of four, then a 5 s wait (7 s after the fourth: kept at 5).
    ("guard", "sleep"): [ScriptSound(tuple(f"animsounds/guard/sleep{n}" for n in range(1, 5)), 1.0, 5.0)],
    # The Pray animation's key is PrayMumble (MS_Init: AddModelKey PrayMumble OnPray). GetRandomInt 1, 10: 1-4 play
    # Pray<n> and wait 2.2 s, 5-10 wait 20 s; volume 80, radii 80/300.
    ("monk", "praymumble"): [ScriptSound(tuple(f"animsounds/monk/pray{n}" for n in range(1, 5)), 4 / 10, 2.2, 20.0, 0.8,
                                   300.0, 80.0)],
    ("monk", "sweep"): [ScriptSound(("animsounds/monk/sweep",), 1.0, 1.0, 0.0, 0.8, 300.0, 80.0)],
    # Wash at volume 10 every key, and one time in ten WashFidget, then a 5 s wait.
    ("monk", "wash"): [ScriptSound(("animsounds/monk/wash",), 1.0, 0.0, 0.0, 0.1, 300.0, 80.0),
                       ScriptSound(("animsounds/monk/washfidget",), 0.1, 5.0, 0.0, 0.8, 300.0, 80.0)],
}

# Slot columns of the descriptor (AttackSoundId, DeathSoundId, WinceSoundId, AwareSoundId: OpenYAMM plays the fourth
# on a fidget) and the binding clip role whose first sound fills each.
SLOT_ROLES = (("attack", "attack_melee"), ("death", "dying"), ("wince", "hit"), ("fidget", "fidget"))


# --- the MM9 models' animations ---------------------------------------------------------------------------------------

def key_commands(event: str) -> list[str]:
    """The lowercased command words of one keyframe string ("Velocity 2 0 -2; playanimsound" -> velocity, ...)."""
    words = []
    for command in event.split(";"):
        parts = command.strip().split()
        if parts:
            words.append(parts[0].lower())
    return words


@dataclass
class SourceAnimation:
    name: str
    seconds: float
    keys: list[tuple[float, str]]   # (seconds, lowercased command)
    signatures: dict[str, np.ndarray]


def child_models(path: Path) -> list[str]:
    """The models whose animations a model plays as its own (its ChildModels section: `sheep.ABC` for the Ram,
    `PeasantMale.abc` and `Peasantwork.abc` for a townsman), lowercased file names."""
    data = path.read_bytes()
    sections = convert_abc_model.read_sections(convert_abc_model.BinaryReader(data))
    if "ChildModels" not in sections:
        return []
    following = [offset for offset in sections.values() if offset > sections["ChildModels"]]
    chunk = data[sections["ChildModels"]:min(following) if following else len(data)]
    names = re.findall(rb"([A-Za-z0-9_]+\.abc)", chunk, re.IGNORECASE)
    return list(dict.fromkeys(name.decode("ascii").lower() for name in names))


def read_source_animations(path: Path) -> list[SourceAnimation]:
    model = convert_abc_model.read_abc(path)
    animations = []
    for animation in model.animations:
        times = np.array([key.time_ms / 1000.0 for key in animation.keyframes], dtype=float)
        keys = [(key.time_ms / 1000.0, command) for key in animation.keyframes if key.event
                for command in key_commands(key.event)]
        tracks = {
            model.nodes[node].name: (times, np.array([t.rotation for t in transforms], dtype=float))
            for node, transforms in enumerate(animation.node_transforms)
        }
        seconds = float(times[-1]) if len(times) else 0.0
        animations.append(SourceAnimation(animation.name, seconds, keys, bone_signatures(seconds, tracks)))
    return animations


# --- our models' clips ------------------------------------------------------------------------------------------------

def read_glb_clips(path: Path) -> dict[str, tuple[float, dict[str, np.ndarray], dict]]:
    """Clip name -> (seconds, bone -> rotation signature, bone name -> (times, rotations)) from a GLB's float
    animation accessors."""
    data = path.read_bytes()
    json_length = struct.unpack_from("<I", data, 12)[0]
    document = json.loads(data[20:20 + json_length])
    binary_offset = 20 + json_length
    binary_length = struct.unpack_from("<I", data, binary_offset)[0]
    binary = data[binary_offset + 8:binary_offset + 8 + binary_length]
    widths = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}

    def accessor(index: int) -> np.ndarray:
        entry = document["accessors"][index]
        if entry["componentType"] != 5126:
            raise ValueError(f"{path}: animation accessor {index} is not float")
        view = document["bufferViews"][entry["bufferView"]]
        width = widths[entry["type"]]
        stride = view.get("byteStride", 0) or 4 * width
        start = view.get("byteOffset", 0) + entry.get("byteOffset", 0)
        rows = [np.frombuffer(binary, np.float32, width, start + row * stride) for row in range(entry["count"])]
        return np.array(rows, dtype=float).reshape(entry["count"], width)

    names = [node.get("name", "") for node in document.get("nodes", [])]
    clips = {}
    for animation in document.get("animations", []):
        tracks = {}
        seconds = 0.0
        for channel in animation["channels"]:
            if channel["target"].get("path") != "rotation" or "node" not in channel["target"]:
                continue
            sampler = animation["samplers"][channel["sampler"]]
            times = accessor(sampler["input"])[:, 0]
            tracks[names[channel["target"]["node"]]] = (times, accessor(sampler["output"]))
            seconds = max(seconds, float(times[-1]))
        clips[animation.get("name", "")] = (seconds, bone_signatures(seconds, tracks), tracks)
    return clips


# --- matching a clip to the MM9 animation it was made from -------------------------------------------------------------

SIGNATURE_FRACTIONS = np.linspace(0.0, 1.0, 9)
# Mean angle difference (radians) under which a clip is the animation's; a clip of a static pose matches by name only.
MATCH_TOLERANCE = 0.03
STATIC_POSE = 0.02
# Our clip names for MM9's animation names (the creature projects' role tables): a tie-break among equal signatures.
CLIP_ALIASES = {
    "stand": "standing", "walk": "walking", "run": "running", "fidget1": "fidget", "fidget": "fidget",
    "hattack1": "attackmelee", "hattack2": "attackmelee2", "hattack3": "attackmelee3", "rattack1": "attackranged",
    "rattack2": "attackranged2", "wince1": "hit", "wince2": "hit2", "wince3": "hit3", "die1": "death",
    "die2": "death2",
}


def sample_rotations(times: np.ndarray, rotations: np.ndarray, at: np.ndarray) -> np.ndarray:
    """Linear (normalized) quaternion samples, keeping each key in the previous key's hemisphere."""
    continuous = rotations.copy()
    for index in range(1, len(continuous)):
        if np.dot(continuous[index - 1], continuous[index]) < 0.0:
            continuous[index] = -continuous[index]
    if len(times) == 1:
        samples = np.repeat(continuous[:1], len(at), axis=0)
    else:
        samples = np.stack([np.interp(at, times, continuous[:, c]) for c in range(4)], axis=1)
    lengths = np.linalg.norm(samples, axis=1, keepdims=True)
    return samples / np.where(lengths > 1.0e-9, lengths, 1.0)


def bone_key(name: str) -> str:
    """A bone's name without its skeleton prefix (MM9's `vampiresB Spine` became our `Bip01 Spine`)."""
    return name.split(" ", 1)[-1].lower()


def bone_signatures(seconds: float, tracks: dict) -> dict[str, np.ndarray]:
    """Per bone, the angle from its first pose at evenly spaced fractions of the clip: unchanged by a bone's basis (and
    by the mirror the creature projects apply)."""
    signatures = {}
    for name, (times, rotations) in tracks.items():
        bone = bone_key(name)
        samples = sample_rotations(times, rotations, SIGNATURE_FRACTIONS * seconds)
        signatures[bone] = 2.0 * np.arccos(np.clip(np.abs(samples @ samples[0]), 0.0, 1.0))
    return signatures


def normalized_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def clip_sources(clips: dict, animations: list[SourceAnimation]) -> dict[str, SourceAnimation]:
    """Our clip name -> the MM9 animation it plays (stitched or invented clips have none).

    The median over bones of the signature difference decides (the creature projects re-pose a few bones: arms, robes);
    among equal signatures (MM9 models carry duplicate animations: Taunt and Aware) the clip's own name, then its
    length, wins. A clip or animation of a static pose matches by name only. A clip whose motion the project reworked
    beyond the tolerance still takes the animation of its own name and length."""
    sources = {}
    for clip_name, (clip_seconds, clip_signatures, _) in clips.items():
        best = None
        fallback = None
        for animation in animations:
            bones = [bone for bone in clip_signatures if bone in animation.signatures]
            if len(bones) < 3 or animation.seconds <= 0.0 or clip_seconds <= 0.0:
                continue
            named = normalized_name(clip_name) in {normalized_name(animation.name),
                                                   CLIP_ALIASES.get(normalized_name(animation.name), "")}
            same_length = abs(clip_seconds - animation.seconds) <= 0.02 * max(clip_seconds, animation.seconds)
            if named and same_length:
                fallback = animation
            ours = np.array([clip_signatures[bone] for bone in bones])
            theirs = np.array([animation.signatures[bone] for bone in bones])
            difference = np.abs(ours - theirs)
            median = float(np.median(difference))
            if median >= MATCH_TOLERANCE:
                continue
            static = float(np.max(theirs)) < STATIC_POSE or float(np.max(ours)) < STATIC_POSE
            if static and not named:
                continue
            score = (median + 0.1 * float(np.mean(difference)) + (0.0 if same_length else 0.05)
                     - (0.02 if named else 0.0))
            if best is None or score < best[0]:
                best = (score, animation)
        if best is not None:
            sources[clip_name] = best[1]
        elif fallback is not None:
            sources[clip_name] = fallback
    return sources


# The creature projects stitch some roles from several MM9 animations (a flyer's Death: DieAir1, then its fall), each
# played whole and joined by a short blend: such a clip is matched piece by piece from its start.
STITCH_STEP = 1.0 / 30.0
STITCH_BLEND = 0.5
STITCH_MINIMUM = 0.2


def segment_signatures(tracks: dict, start: float, seconds: float) -> dict[str, np.ndarray]:
    signatures = {}
    for name, (times, rotations) in tracks.items():
        samples = sample_rotations(times, rotations, start + SIGNATURE_FRACTIONS * seconds)
        signatures[bone_key(name)] = 2.0 * np.arccos(np.clip(np.abs(samples @ samples[0]), 0.0, 1.0))
    return signatures


def stitched_sources(clip_seconds: float, tracks: dict, animations: list[SourceAnimation]) \
        -> list[tuple[float, SourceAnimation]]:
    """(start seconds, animation) of each MM9 animation a stitched clip plays whole; empty when its start matches none."""
    pieces: list[tuple[float, SourceAnimation]] = []
    start = 0.0
    while clip_seconds - start >= STITCH_MINIMUM and len(pieces) < 4:
        best = None
        offsets = [start] if not pieces else [start + step * STITCH_STEP
                                              for step in range(int(STITCH_BLEND / STITCH_STEP) + 1)]
        for offset in offsets:
            for animation in animations:
                if animation.seconds < STITCH_MINIMUM or offset + animation.seconds > clip_seconds + 0.05:
                    continue
                ours_all = segment_signatures(tracks, offset, animation.seconds)
                bones = [bone for bone in ours_all if bone in animation.signatures]
                if len(bones) < 3:
                    continue
                ours = np.array([ours_all[bone] for bone in bones])
                theirs = np.array([animation.signatures[bone] for bone in bones])
                if float(np.max(theirs)) < STATIC_POSE or float(np.max(ours)) < STATIC_POSE:
                    continue
                difference = np.abs(ours - theirs)
                median = float(np.median(difference))
                if median >= MATCH_TOLERANCE:
                    continue
                score = median + 0.1 * float(np.mean(difference))
                if best is None or score < best[0]:
                    best = (score, offset, animation)
        if best is None:
            break
        pieces.append((best[1], best[2]))
        start = best[1] + best[2].seconds
    return pieces


# --- the rows -----------------------------------------------------------------------------------------------------------

@dataclass
class SoundRow:
    source_number: int
    name: str
    descriptor: str
    model: str
    base_name: str
    foot_sound: str
    foot_radius: float
    voice_radius: float
    script: str


def sound_rows(sources: dict[int, list[str]], pictures: dict[int, str]) -> dict[str, SoundRow]:
    rows = {}
    for number, row in sorted(sources.items()):
        def cell(column: int) -> str:
            return row[column].strip()
        foot = cell(COLUMN_FOOT_SOUND).lower()
        rows[pictures[number]] = SoundRow(
            number, cell(1), pictures[number], cell(COLUMN_MODEL).lower(), cell(COLUMN_BASE_NAME).lower(),
            "" if foot in {"", "0"} else foot,
            float(cell(COLUMN_FOOT_RADIUS) or 350), float(cell(COLUMN_VOICE_RADIUS) or 1440),
            cell(COLUMN_SCRIPT).lower())
    return rows


def audio_files(audio_root: Path) -> list[str]:
    """Imported monster sound names (relative to the world's audio folder, lowercase, without .wav), sorted."""
    from import_mm9_world_audio import SCRIPT_SOUND_STAND_INS
    # A stand-in under a script's name (not an MM9 file: maps play it by name) takes no id, so the ids stay put.
    stand_ins = {Path(name).with_suffix("").as_posix() for name in SCRIPT_SOUND_STAND_INS}
    names = []
    for folder in SOUND_FOLDERS:
        for path in (audio_root / folder).rglob("*.wav"):
            name = path.relative_to(audio_root).with_suffix("").as_posix().lower()
            if name not in stand_ins:
                names.append(name)
    return sorted(names)


def sound_ids(names: list[str]) -> dict[str, int]:
    if len(names) > SOUND_ID_END - SOUND_ID_BEGIN + 1:
        raise ValueError(f"{len(names)} MM9 monster sounds do not fit the sounds id range")
    return {name: SOUND_ID_BEGIN + index for index, name in enumerate(names)}


@dataclass
class ClipEvent:
    at: float
    kind: str
    sounds: tuple[str, ...] = ()
    script: ScriptSound | None = None
    missing: str = ""      # the file MM9 names, which it does not ship (silent in MM9 too)
    shake: dict | None = None   # a camera shake (EQ_KEYS)


@dataclass
class BindingSounds:
    clips: dict[str, list[ClipEvent]] = field(default_factory=dict)
    footsteps: tuple[str, ...] = ()
    unmatched_clips: list[str] = field(default_factory=list)
    stitched_clips: dict[str, list[str]] = field(default_factory=dict)
    dropped_animations: list[str] = field(default_factory=list)


def script_family(script: str) -> str:
    return "guard" if script in GUARD_SCRIPTS else "monk" if script in MONK_SCRIPTS else ""


def animation_events(animation: SourceAnimation, row: SoundRow, available: set[str], clip_seconds: float,
                     footsteps: tuple[str, ...], start: float | None = None) -> list[ClipEvent]:
    """The animation's sound events on our clip: scaled to the clip's length, or (start given: a piece of a stitched
    clip) at their own times after start."""
    scale = 1.0 if start is not None else clip_seconds / animation.seconds if animation.seconds > 0.0 else 1.0
    offset = start or 0.0
    anim = animation.name.lower()
    events = []
    for seconds, command in animation.keys:
        at = round(min(offset + seconds * scale, clip_seconds), 3)
        kind = KEY_KINDS.get(command)
        if command in EQ_KEYS:
            events.append(ClipEvent(at, "shake", shake=eq_shake(command)))
            continue
        if kind == "footstep":
            if footsteps:
                events.append(ClipEvent(at, kind))
            continue
        if kind is not None:
            name = {"play": f"animsounds/{row.base_name}/{anim}", "speak": f"animsounds/{row.base_name}/{anim}",
                    "fx": f"animsounds/{row.base_name}/fx_{anim}", "death": f"deathsounds/{row.base_name}/{anim}",
                    "flap": f"animsounds/{row.base_name}/flap"}[kind]
            events.append(ClipEvent(at, kind, (name,)) if name in available else ClipEvent(at, kind, missing=name))
            continue
        for script in SCRIPT_SOUNDS.get((script_family(row.script), command), []):
            present = tuple(name for name in script.sounds if name in available)
            if present:
                events.append(ClipEvent(at, "script", present, script))
    return events


def binding_sounds(row: SoundRow, clips: dict, animations: list[SourceAnimation], available: set[str]) -> BindingSounds:
    result = BindingSounds()
    if row.foot_sound:
        steps = []
        for number in range(1, MAX_FOOTSTEPS + 1):
            name = f"animsounds/footsteps/{row.foot_sound}{number}"
            if name not in available:
                break
            steps.append(name)
        result.footsteps = tuple(steps)
    sources = clip_sources(clips, animations)
    used = {animation.name.lower() for animation in sources.values()}
    for clip_name, (clip_seconds, _, tracks) in clips.items():
        animation = sources.get(clip_name)
        if animation is not None:
            events = animation_events(animation, row, available, clip_seconds, result.footsteps)
        else:
            pieces = stitched_sources(clip_seconds, tracks, animations)
            if not pieces:
                result.unmatched_clips.append(clip_name)
                continue
            result.stitched_clips[clip_name] = [piece.name for _, piece in pieces]
            used.update(piece.name.lower() for _, piece in pieces)
            events = [event for start, piece in pieces
                      for event in animation_events(piece, row, available, clip_seconds, result.footsteps, start)]
        if events:
            result.clips[clip_name] = sorted(events, key=lambda event: event.at)
    # MM9 animations whose sounds no clip of ours plays: only those that would play a file of this row.
    for animation in animations:
        if animation.name.lower() in used or animation.name in result.dropped_animations:
            continue
        if any(event.sounds and event.kind != "footstep"
               for event in animation_events(animation, row, available, animation.seconds, result.footsteps)):
            result.dropped_animations.append(animation.name)
    return result


def projectile_launch_sounds(path: Path) -> dict[str, str]:
    """MM9's PROJECTILE.txt: projectile name (lower case) -> its Launch Sound file name (lower case, no .wav)."""
    lines = path.read_text(encoding="latin-1").splitlines()
    header = lines[0].split("\t")
    column = header.index("Launch Sound")
    sounds = {}
    for line in lines[1:]:
        cells = line.split("\t")
        if len(cells) > column and cells[0].strip() and cells[column].strip() not in {"", "0"}:
            sounds[cells[0].strip().lower()] = Path(cells[column].strip()).stem.lower()
    return sounds


def with_launch_events(row_cells: list[str], entry: dict, sounds: BindingSounds, launches: dict[str, str],
                       available: set[str]) -> BindingSounds:
    """The binding's sounds with each ranged attack's projectile launch sound (MM9 plays it as the projectile leaves:
    PROJECTILE.txt Launch Sound) on that attack's clip at its release (actors.yml events <role>: impact). A spell
    (Projectile "Spell") sounds as its spell; a row that never throws has no ranged clip."""
    roles = binding_clip_roles(entry)
    events_by_role = ((entry.get("animation") or {}).get("events") or {})
    extra: dict[str, list[ClipEvent]] = {}
    for column, role_order in RANGED_ROLES:
        projectile = row_cells[tables.SOURCE_COLUMN[column]].strip().lower()
        launch = launches.get(projectile)
        name = f"weapons/{launch}" if launch else ""
        if not launch or name not in available:
            continue
        role = next((r for r in role_order if r in roles and isinstance(events_by_role.get(r), dict)
                     and "impact" in events_by_role[r]), None)
        if role is None:
            continue
        at = round(float(events_by_role[role]["impact"]), 3)
        clip = roles[role]
        if any(event.kind == "launch" for event in extra.get(clip, [])):
            continue
        extra.setdefault(clip, []).append(ClipEvent(at, "launch", (name,)))
    if not extra:
        return sounds
    clips = {clip: list(events) for clip, events in sounds.clips.items()}
    for clip, events in extra.items():
        clips[clip] = sorted(clips.get(clip, []) + events, key=lambda event: event.at)
    return BindingSounds(clips, sounds.footsteps, sounds.unmatched_clips, sounds.stitched_clips,
                         sounds.dropped_animations)


def binding_clip_roles(entry: dict) -> dict[str, str]:
    """Role -> clip name of an actors.yml binding (clips, script_clips, animation run/cast)."""
    roles = {}
    roles.update({str(k): str(v) for k, v in (entry.get("script_clips") or {}).items()})
    roles.update({str(k): str(v) for k, v in (entry.get("clips") or {}).items()})
    animation = entry.get("animation") or {}
    for role in ("run", "cast", "sprint"):
        if isinstance(animation.get(role), str):
            roles[role] = animation[role]
    return roles


def first_sound(events: list[ClipEvent], kinds: tuple[str, ...]) -> str:
    for event in events:
        if event.kind in kinds and event.sounds:
            return event.sounds[0]
    return ""


def slot_sounds(entry: dict, sounds: BindingSounds) -> dict[str, str]:
    roles = binding_clip_roles(entry)
    slots = {}
    for slot, role in SLOT_ROLES:
        events = sounds.clips.get(roles.get(role, ""), [])
        name = first_sound(events, ("speak", "play"))
        if not name and slot == "death":
            name = first_sound(events, ("death",))
        slots[slot] = name
    return slots


# --- outputs ------------------------------------------------------------------------------------------------------------

def write_sound_table(path: Path, ids: dict[str, int]) -> None:
    lines = [
        "/NAME\tID\tTYPE\t3D\tCOMMENTS",
        "/MM9 monster and NPC sounds (generate_mm9_monster_sounds.py; devdocs/mm9_rework/MM9_MONSTER_SOUNDS.md).",
        "/Names are paths under the world's audio folder; ids are the world.yml sounds range.",
    ]
    lines += [f"{name}\t{sound_id}\tswap\t0" for name, sound_id in sorted(ids.items(), key=lambda item: item[1])]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def event_document(event: ClipEvent) -> dict:
    document: dict = {"at": event.at}
    if event.kind == "footstep":
        document["footstep"] = True
        return document
    if event.kind == "shake":
        document["shake"] = dict(event.shake)
        return document
    if len(event.sounds) == 1:
        document["sound"] = event.sounds[0]
    else:
        document["sounds"] = list(event.sounds)
    if event.kind == "speak":
        document["voice"] = True
    if event.script is not None:
        script = event.script
        if script.chance < 1.0:
            document["chance"] = round(script.chance, 4)
        if script.gate > 0.0:
            document["gate"] = script.gate
        if script.miss_gate > 0.0:
            document["miss_gate"] = script.miss_gate
        if script.volume != 1.0:
            document["volume"] = script.volume
        document["radius"] = round(script.radius * MM9_TO_OPENYAMM_COORDINATE_SCALE, 1)
        document["inner"] = round(script.inner * MM9_TO_OPENYAMM_COORDINATE_SCALE, 1)
    return document


def write_actor_sounds(path: Path, bindings: list[tuple[SoundRow, BindingSounds]]) -> None:
    actors = []
    for row, sounds in bindings:
        if not sounds.clips:
            continue
        entry: dict = {
            "descriptor": row.descriptor,
            "radius": round(row.voice_radius * MM9_TO_OPENYAMM_COORDINATE_SCALE, 1),
        }
        if sounds.footsteps and any(event.kind == "footstep" for events in sounds.clips.values()
                                    for event in events):
            entry["footstep_radius"] = round(row.foot_radius * MM9_TO_OPENYAMM_COORDINATE_SCALE, 1)
            entry["footsteps"] = list(sounds.footsteps)
        entry["clips"] = {
            clip: [event_document(event) for event in events if event.sounds or event.kind in ("footstep", "shake")]
            for clip, events in sounds.clips.items()
            if any(event.sounds or event.kind in ("footstep", "shake") for event in events)
        }
        actors.append(entry)
    header = (
        "# MM9's own monster and NPC sounds, keyed to the clips of their 3D models (WorldFxSystem: an event plays when\n"
        "# its clip passes `at` seconds). Generated by tools/mm9_import_discovery/generate_mm9_monster_sounds.py from\n"
        "# the ABC models' keys; see devdocs/mm9_rework/MM9_MONSTER_SOUNDS.md. Do not edit by hand.\n"
    )
    text = yaml.safe_dump({"actors": actors}, sort_keys=False, default_flow_style=None, width=120)
    path.write_text(header + text, encoding="utf-8")


def write_slots(path: Path, bindings: list[tuple[SoundRow, dict[str, str]]], ids: dict[str, int]) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        writer.writerow(["mm9_source_number"] + [f"{slot}_sound_id" for slot, _ in SLOT_ROLES]
                        + [f"{slot}_sound" for slot, _ in SLOT_ROLES])
        for row, slots in sorted(bindings, key=lambda item: item[0].source_number):
            writer.writerow([row.source_number] + [ids.get(slots[slot], 0) for slot, _ in SLOT_ROLES]
                            + [slots[slot] for slot, _ in SLOT_ROLES])


COVERAGE_BEGIN = "<!-- coverage:begin (generated by generate_mm9_monster_sounds.py) -->"
COVERAGE_END = "<!-- coverage:end -->"
# Coverage columns: heading and the binding roles whose clips it reports.
COVERAGE_COLUMNS = (
    ("Attack", ("attack_melee",)), ("Attack 2", ("attack_ranged", "attack2", "attack_melee2", "attack3")),
    ("Cast", ("cast",)), ("Hit", ("hit", "hit2")), ("Death", ("dying", "death2", "dying2")),
    ("Aware", ("aware", "aware2")), ("Taunt", ("taunt",)), ("Fidget", ("fidget", "fidget2", "stand")),
)


def short(name: str, row: SoundRow) -> str:
    for prefix in (f"animsounds/{row.base_name}/", "animsounds/footsteps/", "deathsounds/"):
        if name.startswith(prefix):
            return ("death:" if prefix == "deathsounds/" else "") + name[len(prefix):].split("/")[-1]
    return name


def coverage_cell(entry: dict, sounds: BindingSounds, roles: tuple[str, ...], row: SoundRow) -> str:
    clip_roles = binding_clip_roles(entry)
    clips = []
    for role in roles:
        clip = clip_roles.get(role)
        if clip and clip not in clips:
            clips.append(clip)
    if not clips:
        return "n"
    parts = []
    for clip in clips:
        events = sounds.clips.get(clip, [])
        names = [short(name, row) for event in events if event.kind not in {"footstep"} for name in event.sounds[:1]]
        missing = [short(event.missing, row) + "?" for event in events if event.missing]
        if clip in sounds.unmatched_clips:
            parts.append("u")
        elif names or missing:
            parts.append(" ".join(dict.fromkeys(names + missing)))
        else:
            parts.append("k")
    return ", ".join(parts)


def write_coverage(doc_path: Path, rows: list[tuple[SoundRow, dict, BindingSounds, dict[str, str]]]) -> None:
    lines = [COVERAGE_BEGIN, "",
             "| Row | Name | Sound folder | " + " | ".join(h for h, _ in COVERAGE_COLUMNS) + " | Steps | Other |",
             "|---|---|---|" + "---|" * (len(COVERAGE_COLUMNS) + 2)]
    for row, entry, sounds, _ in sorted(rows, key=lambda item: item[0].source_number):
        cells = [coverage_cell(entry, sounds, roles, row) for _, roles in COVERAGE_COLUMNS]
        steps = "-"
        if row.foot_sound:
            steps = f"{row.foot_sound} x{len(sounds.footsteps)}" if sounds.footsteps else f"{row.foot_sound}?"
        reported = {clip for _, roles in COVERAGE_COLUMNS for role in roles
                    for clip in [binding_clip_roles(entry).get(role)] if clip}
        other = []
        for clip, events in sounds.clips.items():
            names = [short(name, row) for event in events if event.kind not in {"footstep"} and clip not in reported
                     for name in event.sounds[:1]]
            if names:
                other.append(f"{clip}: {' '.join(dict.fromkeys(names))}")
        if sounds.dropped_animations:
            other.append("dropped: " + " ".join(sounds.dropped_animations))
        lines.append(f"| {row.source_number} | {row.name} | {row.base_name or '-'} | " + " | ".join(cells)
                     + f" | {steps} | {'; '.join(other) or '-'} |")
    lines += ["", COVERAGE_END]
    text = doc_path.read_text(encoding="utf-8")
    begin, end = text.index(COVERAGE_BEGIN), text.index(COVERAGE_END) + len(COVERAGE_END)
    doc_path.write_text(text[:begin] + "\n".join(lines) + text[end:], encoding="utf-8")


# --- the run ------------------------------------------------------------------------------------------------------------

def generate(args: argparse.Namespace) -> dict:
    npc_actors = tables.npc_actor_ids(args.npc_actors)
    sources = tables.source_monsters(args.source_monsters, frozenset(npc_actors))
    pictures = tables.picture_names(sources, tables.load_families(args.families, sources))
    rows = sound_rows(sources, pictures)
    names = audio_files(args.audio_root)
    ids = sound_ids(names)
    available = set(names)
    launches = projectile_launch_sounds(args.projectiles)
    model_files = {path.name.lower(): path for path in args.models_dir.iterdir()}
    bindings = yaml.safe_load(args.actors.read_text(encoding="utf-8"))["actors"]

    # A row without its own ABC (n/a, a missing file) takes the ABC of another row drawn with the same 3D model.
    abc_by_glb: dict[str, str] = {}
    for entry in bindings:
        row = rows.get(entry["descriptor"])
        if row is not None and row.model in model_files:
            abc_by_glb.setdefault(entry["model"], row.model)

    animation_cache: dict[str, list[SourceAnimation]] = {}
    clip_cache: dict[str, dict] = {}
    sound_cache: dict[tuple, BindingSounds] = {}
    results = []
    missing_rows = sorted(set(rows) - {entry["descriptor"] for entry in bindings})
    for entry in bindings:
        row = rows.get(entry["descriptor"])
        if row is None:
            continue
        abc = row.model if row.model in model_files else abc_by_glb.get(entry["model"], "")
        if not abc:
            sounds = BindingSounds()
        else:
            if abc not in animation_cache:
                animation_cache[abc] = read_source_animations(model_files[abc])
                for child in child_models(model_files[abc]):
                    if child in model_files and child != abc:
                        animation_cache[abc] = animation_cache[abc] + read_source_animations(model_files[child])
            animations = animation_cache[abc]
            if entry["model"] not in clip_cache:
                clip_cache[entry["model"]] = read_glb_clips(args.assets_root / entry["model"])
            key = (abc, entry["model"], row.base_name, row.foot_sound, row.script)
            if key not in sound_cache:
                sound_cache[key] = binding_sounds(row, clip_cache[entry["model"]], animations, available)
            sounds = sound_cache[key]
        sounds = with_launch_events(sources[row.source_number], entry, sounds, launches, available)
        results.append((row, entry, sounds, slot_sounds(entry, sounds)))

    args.sound_table.parent.mkdir(parents=True, exist_ok=True)
    write_sound_table(args.sound_table, ids)
    write_actor_sounds(args.actor_sounds, [(row, sounds) for row, _, sounds, _ in results])
    write_slots(args.slots, [(row, slots) for row, _, _, slots in results], ids)
    if args.coverage is not None:
        write_coverage(args.coverage, results)
    return {"rows": len(results), "sounds": len(ids), "unbound_rows": missing_rows,
            "silent_rows": [row.source_number for row, _, sounds, _ in results if not sounds.clips]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    here = Path("tools/mm9_import_discovery")
    parser.add_argument("--source-monsters", type=Path, default=Path("mm9/extracted/DATA/DATA/MONSTERS.txt"))
    parser.add_argument("--families", type=Path, default=here / "mm9_monster_families.yml")
    parser.add_argument("--npc-actors", type=Path, default=here / "mm9_npc_actor_rows.tsv")
    parser.add_argument("--models-dir", type=Path, default=Path("mm9/extracted/MODELS/MODELS"))
    parser.add_argument("--projectiles", type=Path, default=Path("mm9/extracted/DATA/DATA/PROJECTILE.txt"))
    parser.add_argument("--audio-root", type=Path, default=Path("assets_dev/worlds/mm9/audio"))
    parser.add_argument("--assets-root", type=Path, default=Path("assets_dev"))
    parser.add_argument("--actors", type=Path, default=Path("assets_dev/worlds/mm9/models/actors.yml"))
    parser.add_argument("--sound-table", type=Path, default=Path("assets_dev/worlds/mm9/data_tables/sounds.txt"))
    parser.add_argument("--actor-sounds", type=Path, default=Path("assets_dev/worlds/mm9/models/actor_sounds.yml"))
    parser.add_argument("--slots", type=Path, default=here / "mm9_monster_sound_slots.tsv")
    parser.add_argument("--coverage", type=Path, default=Path("devdocs/mm9_rework/MM9_MONSTER_SOUNDS.md"))
    summary = generate(parser.parse_args())
    print(f"MM9 monster sounds: {summary['rows']} rows bound, {summary['sounds']} sounds registered;"
          f" rows without any MM9 clip sound: {summary['silent_rows']}; rows without a 3D binding:"
          f" {summary['unbound_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
