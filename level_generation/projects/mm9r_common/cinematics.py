#!/usr/bin/env python3
"""
MM9 cutscenes to OpenYAMM cinematics (devdocs/mm9_rework/MM9_CUTSCENES.md): the shared part of the converters.

A map's cinematics go to worlds/mm9/maps/<stem>.cinematics.yml (format_version 1, kind openyamm_cinematics), which the
engine loads with the map (game/gameplay/CinematicRuntime.cpp parses and checks it). A converter builds each MM9
cutscene from its DAT Camera/CameraMarker objects and its director script's timeline:

    cinema = Cinematic("book_sinking", source="IsleAshesBook.scr :OnUse")
    cinema.fixed(2.2, eye, direction=forward, fov=MM9_CAMERA_FOV)              # Trigger CameraN On ... Off
    cinema.moving(3.5, [(0, eye, {"direction": d0}), (3.5, eye2, {"direction": d1})], easing="linear")
    cinema.fade(0, "in", 1).event(1.0, 31010).sound(3.2, "sounds\\\\spells\\\\ebolt01.wav")
    write(path, [cinema], source="...")

The camera helpers reproduce MM9's script motions: move_to_pos (MoveToPos x y z speed: a straight line at speed LT
units per second) and face_toward (FaceObject target rate: a turn at rate degrees per second, 0 a snap). Positions
and directions are in the map's own frame (the converter's LT -> map transform); speeds are converted with its scale.

The map's gameplay steps (keys, doors, monsters, the exit) stay in its Lua as map events the cinematic's event cues
run; they also run when the player skips, so a cinematic cue never carries progress the Lua does not.
"""

from __future__ import annotations

import math
from pathlib import Path

# MM9's cutscene view keeps the client's field of view, 90 degrees across (the Camera's FOV property, 90 everywhere, is
# never read: object.lto Camera ReadProp 0x1005a4c0, cshell 0x10090e00): at the game's 4:3 that is 73.7 degrees
# vertically (our gameplay view is 60 vertical). A cinematic key's fov is vertical.
MM9_ASPECT = 4.0 / 3.0


def vertical_fov(horizontal_degrees: float, aspect: float = MM9_ASPECT) -> float:
    return math.degrees(2.0 * math.atan(math.tan(math.radians(horizontal_degrees) / 2.0) / aspect))


MM9_CAMERA_FOV = round(vertical_fov(90.0), 1)


def lt_direction(rotation) -> tuple[float, float, float]:
    """A LithTech rotation [pitch, yaw, roll] as a forward vector in a map frame of (x, z, y) axes (pitch about x, down
    positive; yaw about the up axis from +z): the same formula as the converters' object directions."""
    pitch, yaw = float(rotation[0]), float(rotation[1])
    return (math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), -math.sin(pitch))


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _norm(v):
    length = math.sqrt(sum(x * x for x in v))
    return tuple(x / length for x in v) if length > 1e-9 else None


def move_to_pos(start, target, speed: float, seconds: float):
    """Where MoveToPos has the object after seconds: along the straight line to target at speed (units per second,
    in the same frame as start and target), stopping there. Returns (position, arrival seconds)."""
    delta = _sub(target, start)
    distance = math.sqrt(sum(x * x for x in delta))
    arrival = distance / speed if speed > 0 else 0.0
    if distance < 1e-9 or seconds >= arrival:
        return tuple(target), arrival
    t = seconds / arrival
    return tuple(s + d * t for s, d in zip(start, delta)), arrival


def face_toward(direction, eye, target, rate_degrees: float, seconds: float):
    """Where FaceObject has turned a camera after seconds: its yaw toward target at rate degrees per second (0: at
    once), its pitch kept. Returns (direction, seconds the whole turn takes)."""
    to_target = _sub(target, eye)
    target_yaw = math.atan2(to_target[1], to_target[0])
    yaw = math.atan2(direction[1], direction[0])
    pitch = math.asin(max(-1.0, min(1.0, direction[2])))
    turn = math.remainder(target_yaw - yaw, 2.0 * math.pi)
    whole = abs(math.degrees(turn)) / rate_degrees if rate_degrees > 0 else 0.0
    share = 1.0 if whole <= seconds or whole == 0 else seconds / whole
    yaw += turn * share
    return (math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), math.sin(pitch)), whole


class Cinematic:
    """One cinematic: consecutive camera shots and timed cues (seconds from its start)."""

    def __init__(self, cinematic_id: str, source: str = "", skippable: bool = True, letterbox: bool = True,
                 ambient: bool = False):
        self.id = cinematic_id
        self.source = source
        self.skippable = skippable
        self.letterbox = letterbox and not ambient
        # Overheard talk: no shots, no letterbox, no input lock; cues only (sounds, subtitles, actor faces/clips).
        self.ambient = ambient
        self.letterbox_seconds: float | None = None
        self.shots: list[dict] = []
        self.cues: list[dict] = []

    @property
    def shots_seconds(self) -> float:
        return sum(shot["duration"] for shot in self.shots)

    # --- shots ------------------------------------------------------------------------------------------------------
    @staticmethod
    def _aim(aim: dict) -> dict:
        keys = {"look_at", "look_at_actor", "look_at_party", "direction"}
        if len(keys & set(aim)) != 1:
            raise ValueError(f"a camera key needs exactly one aim of {sorted(keys)}: {aim}")
        out = {}
        for key, value in aim.items():
            if key in ("look_at", "direction"):
                value = _norm(value) if key == "direction" else value
                if value is None:
                    raise ValueError("a zero direction")
                out[key] = [round(float(x), 4 if key == "direction" else 1) for x in value]
            elif key == "fov":
                out[key] = round(float(value), 1)
            else:
                out[key] = value
        return out

    def fixed(self, duration: float, position, note: str = "", **aim) -> "Cinematic":
        """A fixed camera for duration seconds (aim: look_at=, look_at_actor=, look_at_party=True or direction=, and
        fov=)."""
        shot = {"duration": round(float(duration), 3), "position": [round(float(x), 1) for x in position]}
        shot.update(self._aim(aim))
        if note:
            shot["note"] = note
        self.shots.append(shot)
        return self

    def moving(self, duration: float, keys, easing: str = "smooth", note: str = "") -> "Cinematic":
        """A moving camera: keys of (seconds into the shot, position, aim dict), the first at 0."""
        out = []
        for at, position, aim in keys:
            key = {"at": round(float(at), 3), "position": [round(float(x), 1) for x in position]}
            key.update(self._aim(aim))
            out.append(key)
        shot = {"duration": round(float(duration), 3), "easing": easing, "keys": out}
        if note:
            shot["note"] = note
        self.shots.append(shot)
        return self

    def party(self, duration: float, note: str = "") -> "Cinematic":
        shot = {"duration": round(float(duration), 3), "party": True}
        if note:
            shot["note"] = note
        self.shots.append(shot)
        return self

    # --- cues -------------------------------------------------------------------------------------------------------
    def _cue(self, at: float, note: str, **fields) -> "Cinematic":
        cue = {"at": round(float(at), 3)}
        cue.update(fields)
        if note:
            cue["note"] = note
        self.cues.append(cue)
        return self

    def fade(self, at: float, direction: str, seconds: float = 1.0, note: str = "") -> "Cinematic":
        if direction not in ("in", "out"):
            raise ValueError(direction)
        return self._cue(at, note, fade=direction, seconds=round(float(seconds), 3))

    def letterbox_cue(self, at: float, on: bool, seconds: float = 0.5, note: str = "") -> "Cinematic":
        return self._cue(at, note, letterbox=bool(on), seconds=round(float(seconds), 3))

    def sound(self, at: float, name: str, note: str = "") -> "Cinematic":
        return self._cue(at, note, sound=name)

    def subtitle(self, at: float, text: str, seconds: float, note: str = "") -> "Cinematic":
        return self._cue(at, note, subtitle=text, seconds=round(float(seconds), 3))

    def event(self, at: float, event_id: int, note: str = "") -> "Cinematic":
        if not 1 <= int(event_id) <= 65535:
            raise ValueError(event_id)
        return self._cue(at, note, event=int(event_id))

    def actor(self, at: float, actor_index: int, action: str, to=None, seconds: float | None = None,
              note: str = "") -> "Cinematic":
        fields = {"actor": int(actor_index), "action": action}
        if to is not None:
            fields["to"] = [round(float(x), 1) for x in to]
        if seconds is not None:
            fields["seconds"] = round(float(seconds), 3)
        return self._cue(at, note, **fields)

    def shake(self, at: float, intensity: float, seconds: float, note: str = "") -> "Cinematic":
        return self._cue(at, note, shake=round(float(intensity), 3), seconds=round(float(seconds), 3))

    def body(self) -> dict:
        body = {}
        if self.source:
            body["source"] = self.source
        if self.ambient:
            body["ambient"] = True
        if not self.skippable:
            body["skippable"] = False
        if not self.letterbox and not self.ambient:
            body["letterbox"] = False
        if self.letterbox_seconds is not None:
            body["letterbox_seconds"] = self.letterbox_seconds
        if self.shots:
            body["shots"] = self.shots
        if self.cues:
            body["cues"] = sorted(self.cues, key=lambda cue: cue["at"])
        return body


# --- writing --------------------------------------------------------------------------------------------------------
def _scalar(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        text = f"{value:.4f}".rstrip("0").rstrip(".")
        return text if text not in ("-0", "") else "0"
    text = str(value)
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _flow(value) -> str:
    if isinstance(value, dict):
        return "{" + ", ".join(f"{key}: {_flow(item)}" for key, item in value.items()) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_flow(item) for item in value) + "]"
    return _scalar(value)


def to_yaml(cinematics: list[Cinematic], source: str = "") -> str:
    """The .cinematics.yml text: one shot or cue per line (flow maps), stable for diffs."""
    lines = ["# Generated by the MM9 rework converters (level_generation/projects/mm9r_common/cinematics.py);",
             "# the format is devdocs/mm9_rework/MM9_CUTSCENES.md.", "format_version: 1", "kind: openyamm_cinematics"]
    if source:
        lines.append(f"source: {_scalar(source)}")
    lines.append("cinematics:")
    for cinema in cinematics:
        lines.append(f"  {cinema.id}:")
        for key, value in cinema.body().items():
            if key in ("shots", "cues"):
                lines.append(f"    {key}:")
                for item in value:
                    if "keys" in item:
                        # A moving shot: its fields one per line, then its keys one per line.
                        head = [(k, v) for k, v in item.items() if k != "keys"]
                        for number, (k, v) in enumerate(head):
                            lines.append(("      - " if number == 0 else "        ") + f"{k}: {_flow(v)}")
                        lines.append("        keys:")
                        for k in item["keys"]:
                            lines.append(f"          - {_flow(k)}")
                    else:
                        lines.append(f"      - {_flow(item)}")
            else:
                lines.append(f"    {key}: {_scalar(value)}")
    return "\n".join(lines) + "\n"


def check(cinematics: list[Cinematic]) -> list[str]:
    """The converter-side checks the engine's parser makes too (it is authoritative): ids, ordered keys, cue times."""
    problems = []
    seen = set()
    for cinema in cinematics:
        if cinema.id in seen:
            problems.append(f"{cinema.id}: defined twice")
        seen.add(cinema.id)
        if not cinema.shots and not cinema.cues:
            problems.append(f"{cinema.id}: no shots or cues")
        for number, shot in enumerate(cinema.shots, 1):
            if shot["duration"] <= 0:
                problems.append(f"{cinema.id} shot {number}: duration {shot['duration']}")
            times = [key["at"] for key in shot.get("keys", [])]
            if times and (times[0] != 0 or any(b <= a for a, b in zip(times, times[1:])) or times[-1] > shot["duration"]):
                problems.append(f"{cinema.id} shot {number}: key times {times}")
        for cue in cinema.cues:
            if cue["at"] < 0:
                problems.append(f"{cinema.id}: cue at {cue['at']}")
    return problems


def write(path: Path, cinematics: list[Cinematic], source: str = "") -> str:
    problems = check(cinematics)
    if problems:
        raise ValueError("; ".join(problems))
    text = to_yaml(cinematics, source)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return text
