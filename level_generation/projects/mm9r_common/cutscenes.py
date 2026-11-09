#!/usr/bin/env python3
"""
MM9 cutscenes in the map converters (devdocs/mm9_rework/MM9_CUTSCENES.md section 6): the parts every map's converter
shares on top of cinematics.py (the format writer).

A converter describes each cutscene as a `Scene`: the cinematic (shots from the DAT cameras, timed cues) plus its
gameplay steps as Lua bodies. `Scene.lua()` turns the steps into map events that the cinematic's event cues run (each
once, guarded by a map variable), a done event that runs any step not yet run (a skip runs them too; a missing file
or an old save loses nothing), and a global start function `MM9Cinematic.<id>()` that the map's own handler calls where
MM9's director started the cutscene. Then:

    scenes = [...]
    text = map_lua + cutscenes.lua_block(scenes)                 # in the converter's map_script hook
    cutscenes.install(stem, scenes)                              # worlds/mm9/maps/<stem>.cinematics.yml (review root)

Without a conversion (the rebuild hold), `pilot(stem, scenes, replacements)` writes the same file and the installed
map Lua with the block appended (and the given text replacements, e.g. a stub handler now calling the start function)
into the scratch root output/mm9_rework/cinematics_pilot_root, for headless scenarios and captures there.

Map frames: `Frame(project_dir)` reads the project's overrides.yml offset (Project.native): positions and directions
of DAT objects in the map's native frame, LT speeds in native units.
"""

from __future__ import annotations

import math
import re
import struct
import subprocess
import sys
import wave
from pathlib import Path

import yaml

COMMON = Path(__file__).resolve().parent
ROOT = COMMON.parents[2]
sys.path.insert(0, str(COMMON))
import cinematics  # noqa: E402
from cinematics import Cinematic, MM9_CAMERA_FOV, face_toward, move_to_pos  # noqa: E402,F401

SCALE = 2.56
RAW_OBJECTS = ROOT / "assets_editor_dev/worlds/mm9/maps"
SCRIPTS = ROOT / "mm9/extracted/SCRIPTS/SCRIPTS"
SOUNDS = ROOT / "mm9/extracted/SOUNDS/SOUNDS"
MODELS = ROOT / "mm9/extracted/MODELS/MODELS"
INSTALLED = ROOT / "assets_dev"
PILOT_ROOT = ROOT / "output/mm9_rework/cinematics_pilot_root"
LUAC = ROOT / "output/mm9_rework/cinematics_pilot_run/luac"   # a plain Lua 5.4 luac (build/_deps/lua-src)


# --- the DAT --------------------------------------------------------------------------------------------------------
def _decode(value_json):
    import json
    try:
        return json.loads(value_json) if value_json is not None else None
    except ValueError:
        return value_json


class Objects:
    """A map's DAT objects by name and index (raw_objects.yml): entry = {index, class, values}."""

    _cache: dict[str, "Objects"] = {}

    def __init__(self, stem: str):
        raw = yaml.load((RAW_OBJECTS / f"{stem}.raw_objects.yml").read_text(), Loader=yaml.CSafeLoader)["objects"]
        self.by_index, self.by_name = {}, {}
        for node in raw:
            values = {p["name"]: _decode(p.get("value_json")) for p in node["properties"]}
            entry = {"index": int(node["object_index"]), "class": str(node["name"]), "values": values}
            self.by_index[entry["index"]] = entry
            if values.get("Name"):
                self.by_name.setdefault(str(values["Name"]), entry)

    @classmethod
    def load(cls, stem: str) -> "Objects":
        if stem not in cls._cache:
            cls._cache[stem] = cls(stem)
        return cls._cache[stem]

    def named(self, name: str) -> dict:
        return self.by_name[name]

    def of_class(self, cls_name: str) -> list[dict]:
        return [e for e in self.by_index.values() if e["class"] == cls_name]


class Frame:
    """LithTech (x, y up, z) to a map's native frame (x, y, z up): position * 2.56 - offset (overrides.yml map.offset,
    as dungeon/source.py Project.native)."""

    def __init__(self, project_dir: Path | str | None = None, offset=None):
        if offset is None:
            overrides = yaml.safe_load((Path(project_dir) / "overrides.yml").read_text())
            offset = overrides["map"].get("offset", (0, 0, 0))
        self.offset = tuple(float(v) for v in offset)

    def point(self, lt) -> tuple[float, float, float]:
        return (lt[0] * SCALE - self.offset[0], lt[2] * SCALE - self.offset[1], lt[1] * SCALE - self.offset[2])

    @staticmethod
    def direction(rotation) -> tuple[float, float, float]:
        return cinematics.lt_direction(rotation or [0, 0, 0])

    @staticmethod
    def speed(lt_per_second: float) -> float:
        return lt_per_second * SCALE

    def camera(self, objects: Objects, name: str):
        """A DAT camera (or marker): its native eye and forward."""
        values = objects.named(name)["values"]
        return self.point(values["Pos"]), self.direction(values.get("Rotation"))


# --- timing sources -------------------------------------------------------------------------------------------------
def wav_seconds(relative: str) -> float:
    """A sound's length: an MM9 path as the scripts name it (voices\\cinema\\theargument\\01.wav), case-insensitive."""
    parts = [p for p in re.split(r"[\\/]+", relative) if p]
    if parts and parts[0].lower() == "sounds":
        parts = parts[1:]
    path = SOUNDS
    for part in parts:
        matches = [c for c in path.iterdir() if c.name.lower() == part.lower()] if path.is_dir() else []
        if not matches:
            raise FileNotFoundError(relative)
        path = matches[0]
    try:
        with wave.open(str(path)) as stream:
            return stream.getnframes() / float(stream.getframerate())
    except wave.Error:
        # ADPCM and other non-PCM wavs: data size over the byte rate.
        data = path.read_bytes()
        rate = struct.unpack_from("<I", data, 28)[0]
        index = data.find(b"data")
        size = struct.unpack_from("<I", data, index + 4)[0] if index >= 0 else len(data)
        return size / float(rate)


def abc_animation(model: str, animation: str) -> tuple[float, list[tuple[float, str]]]:
    """An MM9 model animation's length and its key events [(seconds, event)] (MODELS/<model>.abc)."""
    sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
    import convert_abc_model
    abc = convert_abc_model.read_abc(MODELS / f"{model.upper()}.abc")
    for anim in abc.animations:
        if anim.name.lower() == animation.lower():
            events = [(k.time_ms / 1000.0, k.event) for k in anim.keyframes if k.event]
            return anim.keyframes[-1].time_ms / 1000.0, events
    raise KeyError(f"{model}.{animation}")


# --- scenes ---------------------------------------------------------------------------------------------------------
def _lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


class Scene:
    """One cutscene: its cinematic and its gameplay steps. Steps are (name, Lua body) in the order they run; `step()`
    adds one and its event cue at a time. Event ids: event_base + 1.. for the steps, event_base for the done event."""

    def __init__(self, cinematic_id: str, event_base: int, source: str = "", skippable: bool = True,
                 letterbox: bool = True, ambient: bool = False):
        self.cinema = Cinematic(cinematic_id, source=source, skippable=skippable, letterbox=letterbox,
                                ambient=ambient)
        # Cameras the gate may leave failing ("<id> shot <n>": reason; camera_gate.py).
        self.gate_overrides: dict[str, str] = {}
        self.event_base = int(event_base)
        self.steps: list[tuple[str, str, int]] = []

    @property
    def id(self) -> str:
        return self.cinema.id

    @property
    def done_event(self) -> int:
        return self.event_base

    def step(self, at: float, name: str, body: str, note: str = "") -> int:
        """A gameplay step at `at` seconds: Lua body (statements of the map script, which may use its locals)."""
        if any(existing == name for existing, _, _ in self.steps):
            raise ValueError(f"{self.id}: step {name} twice")
        event_id = self.event_base + 1 + len(self.steps)
        self.steps.append((name, body.strip("\n"), event_id))
        self.cinema.event(at, event_id, note=note or name)
        return event_id

    def lua(self) -> str:
        """The map Lua of the scene: its step events, done event and start function."""
        key = f"Cinema.{self.id}"
        lines = [f"-- Cinematic {self.id} ({self.cinema.source or 'MM9 cutscene'}): <stem>.cinematics.yml shows it;",
                 "-- its gameplay steps are map events its cues run (also on a skip), each once; the done event runs",
                 "-- any not yet run (mm9r_common/cutscenes.py).",
                 f"MM9Cinematic.steps[{_lua_string(self.id)}] = {{"]
        for name, body, _ in self.steps:
            lines.append(f"    {{ {_lua_string(name)}, function()")
            lines += ["        " + line if line.strip() else "" for line in body.split("\n")]
            lines.append("    end },")
        lines.append("}")
        for index, (name, _, event_id) in enumerate(self.steps, 1):
            lines.append(f"RegisterEvent({event_id}, {_lua_string('Cinema ' + self.id + ': ' + name)}, "
                         f"function() MM9Cinematic.runStep({_lua_string(self.id)}, {index}) end)")
        lines.append(f"RegisterEvent({self.done_event}, {_lua_string('Cinema ' + self.id + ': done')}, "
                     f"function() MM9Cinematic.finish({_lua_string(self.id)}) end)")
        lines.append(f"MM9Cinematic.play[{_lua_string(self.id)}] = function()")
        lines.append(f"    if evt.GetMapVar({_lua_string(key + '.started')}, 0) == 0 then")
        lines.append(f"        evt.SetMapVar({_lua_string(key + '.started')}, 1)")
        lines.append(f"        evt.PlayCinematic({_lua_string(self.id)}, {self.done_event})")
        lines.append("    end")
        lines.append("end")
        return "\n".join(lines)


LUA_PRELUDE = """
-- MM9 cutscenes as in-engine cinematics (devdocs/mm9_rework/MM9_CUTSCENES.md; mm9r_common/cutscenes.py).
MM9Cinematic = MM9Cinematic or { steps = {}, play = {} }

function MM9Cinematic.runStep(id, index)
    local step = MM9Cinematic.steps[id][index]
    local name = "Cinema." .. id .. ".step." .. step[1]
    if evt.GetMapVar(name, 0) == 0 then
        evt.SetMapVar(name, 1)
        step[2]()
    end
end

function MM9Cinematic.finish(id)
    for index = 1, #MM9Cinematic.steps[id] do
        MM9Cinematic.runStep(id, index)
    end
end

-- Starts a cinematic once per map state (its started map var); a second start while or after it played does nothing.
function MM9Cinematic.start(id)
    local play = MM9Cinematic.play[id]
    if play ~= nil then
        play()
    end
end
"""


def lua_block(scenes: list[Scene]) -> str:
    if not scenes:
        return ""
    ids = [s.event_base for s in scenes] + [e for s in scenes for _, _, e in s.steps]
    if len(ids) != len(set(ids)):
        raise ValueError("cinematic event ids overlap")
    return "\n" + LUA_PRELUDE + "\n" + "\n\n".join(scene.lua() for scene in scenes) + "\n"


def yaml_text(stem: str, scenes: list[Scene]) -> str:
    return cinematics.to_yaml([scene.cinema for scene in scenes], source=f"MM9 {stem}.dat (mm9r converters)")


def check(scenes: list[Scene]) -> list[str]:
    problems = cinematics.check([scene.cinema for scene in scenes])
    for scene in scenes:
        events = [cue["event"] for cue in scene.cinema.cues if "event" in cue]
        for _, _, event_id in scene.steps:
            if event_id not in events:
                problems.append(f"{scene.id}: step event {event_id} has no cue")
    return problems


def install(stem: str, scenes: list[Scene]) -> str | None:
    """Writes worlds/mm9/maps/<stem>.cinematics.yml into the review root (a conversion's install)."""
    if not scenes:
        return None
    problems = check(scenes)
    if problems:
        raise ValueError("; ".join(problems))
    import review_root
    relative = f"worlds/mm9/maps/{stem}.cinematics.yml"
    review_root.install(relative, yaml_text(stem, scenes).encode())
    return relative


# --- the scratch root (no conversion) -------------------------------------------------------------------------------
def syntax_check(lua_text: str) -> None:
    luac = str(LUAC) if LUAC and Path(LUAC).exists() else "luac"
    result = subprocess.run([luac, "-p", "-"], input=lua_text.encode(), capture_output=True)
    if result.returncode != 0:
        raise SyntaxError(result.stderr.decode())


def pilot(stem: str, scenes: list[Scene], replacements: list[tuple[str, str]] = (), extra_lua: str = "",
          luac: str | None = None) -> Path:
    """The scratch root's copy of the map: its cinematics file from the scenes, and the installed map Lua with the
    replacements made (each old text must occur exactly once) and the scenes' block (and extra_lua) appended. The
    root's file is replaced, never written through (it is a hard link of assets_dev's)."""
    problems = check(scenes)
    if problems:
        raise ValueError("; ".join(problems))
    lua_path = Path(f"worlds/mm9/events/maps/{stem}.lua")
    text = (INSTALLED / lua_path).read_text(encoding="latin-1")
    for old, new in replacements:
        count = text.count(old)
        if count != 1:
            raise ValueError(f"{stem}: replacement text occurs {count} times: {old[:80]!r}")
        text = text.replace(old, new)
    text += lua_block(scenes) + extra_lua
    global LUAC
    LUAC = luac or LUAC
    syntax_check(text)
    target = PILOT_ROOT / lua_path
    if target.exists():
        target.unlink()
    target.write_text(text, encoding="latin-1")
    yml = PILOT_ROOT / f"worlds/mm9/maps/{stem}.cinematics.yml"
    if yml.exists():
        yml.unlink()
    yml.write_text(yaml_text(stem, scenes))
    # The camera gate as the conversion runs it (camera_gate.py), here reporting: moves are applied to the file.
    import camera_gate
    maps = PILOT_ROOT / "worlds/mm9/maps"
    for line in camera_gate.gate_installed(stem, yml, maps / f"{stem}.blv", maps / f"{stem}.scene.yml", None,
                                           strict=False):
        print("camera gate: " + line)
    return target
