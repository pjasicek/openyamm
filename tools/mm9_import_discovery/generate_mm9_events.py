#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import json
import math
import re
import shutil
import sys
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from mm9_scr_to_lua import CompiledRudeExit, ScrCompileError, compile_rude_exit


YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
YAML_DUMPER = getattr(yaml, "CSafeDumper", yaml.SafeDumper)


KNOWN_NORMALIZED_PROPERTIES = {
    "Name",
    "Pos",
    "Rotation",
    "Scale",
    "Filename",
    "Skin",
    "ScriptName",
    "ScriptParams",
    "Parameters",
    "Visible",
    "Solid",
    "Rayhit",
    "RayHit",
    "Hidden",
    "Dims",
    "MoveToFloor",
    "BoxPhysics",
    "StartOn",
    "StartOpen",
    "PushOpen",
    "TouchToOpen",
    "AutoTrigger",
    "Locked",
    "ReopenOnContact",
    "DoubleDoorName",
    "TriggerDims",
    "LockJiggleSpeed",
    "Speed",
    "ClosingSpeed",
    "MoveDelay",
    "OpenWaitTime",
    "MoveDir",
    "MoveDist",
    "RotationPoint",
    "RotationAngles",
    "OpenAway",
    "Sounds",
    "SoundPos",
    "OpenStartSound",
    "OpenBusySound",
    "OpenStopSound",
    "CloseStartSound",
    "CloseBusySound",
    "CloseStopSound",
    "OpenSoundName",
    "CloseSoundName",
    "JiggleSound",
    "DoRude",
    "NPCNbr",
    "GreetingSound",
    "Damage",
    "DamageType",
    "ShowSurface",
    "RotatingStuff",
    "SpinUpSound",
    "BusySound",
    "SpinDownSound",
    "XRotateForward",
    "YRotateForward",
    "ZRotateForward",
    "DestinationWorld",
    "StartPointName",
    "LoadScreen",
    "LoadTextID",
    "TravelDays",
    "AskPlayer",
    "TeamNbr",
    "PlayerNbr",
    "MovePlayerToFloor",
}

for slot in range(1, 11):
    KNOWN_NORMALIZED_PROPERTIES.add(f"TargetName{slot}")
    KNOWN_NORMALIZED_PROPERTIES.add(f"MessageName{slot}")

for slot in range(4):
    KNOWN_NORMALIZED_PROPERTIES.add(f"OpenTriggerTarget{slot}")
    KNOWN_NORMALIZED_PROPERTIES.add(f"OpenTrigger{slot}")
    KNOWN_NORMALIZED_PROPERTIES.add(f"CloseTriggerTarget{slot}")
    KNOWN_NORMALIZED_PROPERTIES.add(f"CloseTrigger{slot}")


MECHANISM_CLASS_KINDS = {
    "Door": "linear_door",
    "RotatingDoor": "rotating_door",
    "WeightedLift": "weighted_lift",
    "Button": "linear_button",
    "Switch": "rotating_switch",
    "RotatingBrush": "rotating_brush",
    "BlueWater": "water_volume",
    "Ladder": "ladder_volume",
    "Shooter": "shooter",
    "InvisibleBrush": "collision_volume",
    "DestructableBrush": "destructible_brush",
    "DestructableProp": "destructible_prop",
    "AIBarrier": "ai_barrier",
    "PerceptionBrush": "perception_brush",
    "ScriptObject": "script_object",
}

VOLUME_CLASS_KINDS = {
    "Trigger": "trigger_volume",
    "BlueWater": "water_volume",
    "Ladder": "ladder_volume",
    "InvisibleBrush": "collision_volume",
    "AIBarrier": "collision_volume",
    "PerceptionBrush": "collision_volume",
}

SCRIPTED_INTERACTION_CLASSES = {
    "Door",
    "RotatingDoor",
    "WeightedLift",
    "Trigger",
    "ScriptObject",
    "Prop",
    "WorldObject",
    "TreasureChest",
    "DestructableProp",
    "DestructableBrush",
    "BlueWater",
    "Ladder",
}

TRAVEL_TRIGGER_CLASSES = {
    "ExitTrigger",
}

MM9_MECHANISM_EVENT_ID_BASE = 30000
MM9_INTERACTIVE_MECHANISM_KINDS = {
    "linear_door",
    "linear_button",
    "weighted_lift",
    "rotating_door",
    "rotating_switch",
    "rotating_brush",
}

MM9_SOUND_SOURCE_ALIASES = {
    "animsounds/dragonredhop.wav": "animsounds/dragon/hop.wav",
    "dragonredhop.wav": "animsounds/dragon/hop.wav",
    "dragonredhop": "animsounds/dragon/hop",
    "door/elestart.wav": "ambient/machinery lich - start.wav",
    "door/elestart": "ambient/machinery lich - start",
    "door/eleloop.wav": "ambient/machinery lich - loop.wav",
    "door/eleloop": "ambient/machinery lich - loop",
    "door/elestop.wav": "ambient/machinery lich - end.wav",
    "door/elestop": "ambient/machinery lich - end",
    "events/pushterrain.wav": "events/stonestonescrape01.wav",
    "events/pushterrain": "events/stonestonescrape01",
}

MM9_SYNTHETIC_NOTE_PATTERN = re.compile(r"^music/([a-g])(#?)([1-3])\.wav$")

MOVEMENT_COMMANDS = {"movetopos", "movedir", "rotate", "setpos"}
STATE_COMMANDS = {"setflag", "clearflag", "setstat", "getstat", "destroyobject"}
PRESENTATION_COMMANDS = {"playanim", "loopanim", "setmodelfilenames"}


@dataclass
class ScriptCommand:
    line: int
    command: str
    arguments: str
    raw: str


@dataclass
class ScriptIr:
    source_path: Path
    includes: list[dict[str, Any]] = field(default_factory=list)
    labels: list[dict[str, Any]] = field(default_factory=list)
    commands: list[ScriptCommand] = field(default_factory=list)
    registered_triggers: list[dict[str, Any]] = field(default_factory=list)
    trigger_edges: list[dict[str, Any]] = field(default_factory=list)
    movement_commands: list[dict[str, Any]] = field(default_factory=list)
    state_commands: list[dict[str, Any]] = field(default_factory=list)
    presentation_commands: list[dict[str, Any]] = field(default_factory=list)
    unknown_commands: list[dict[str, Any]] = field(default_factory=list)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        loaded = yaml.load(stream, Loader=YAML_LOADER)
    return loaded if isinstance(loaded, dict) else {}


def remove_suffix(value: str, suffix: str) -> str:
    return value[:-len(suffix)] if value.endswith(suffix) else value


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml_text(data), encoding="utf-8")


def yaml_text(data: dict[str, Any]) -> str:
    return yaml.dump(
        data,
        Dumper=YAML_DUMPER,
        sort_keys=False,
        allow_unicode=False,
        width=120,
        default_flow_style=False,
    )


def decode_property_value(property_node: dict[str, Any]) -> Any:
    if not property_node.get("decoded", False):
        return None
    value_json = property_node.get("value_json")
    if value_json is None:
        return None
    try:
        return json.loads(value_json)
    except json.JSONDecodeError:
        return None


def object_properties(object_node: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int]]:
    values: dict[str, Any] = {}
    indices: dict[str, int] = {}
    for index, property_node in enumerate(object_node.get("properties", [])):
        name = property_node.get("name", "")
        if not name or name in values:
            continue
        value = decode_property_value(property_node)
        if value is not None:
            values[name] = value
            indices[name] = index
    return values, indices


def normalized_script_name(script_name: str) -> str:
    normalized = script_name.replace("\\", "/").strip()
    if normalized.lower().startswith("scripts/"):
        normalized = normalized.split("/", 1)[1]
    return Path(normalized).name.lower()


def build_script_index(scripts_root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    if not scripts_root.exists():
        return result
    for path in sorted(scripts_root.iterdir()):
        if path.is_file() and path.suffix.lower() in {".scr", ".inc"}:
            result[path.name.lower()] = path
    return result


def collect_script_include_sources(script_path: Path, script_index: dict[str, Path]) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    visited: set[str] = set()

    def collect(path: Path) -> None:
        source_text = path.read_text(encoding="latin-1")
        for raw_line in source_text.splitlines():
            code = strip_script_comment(raw_line)
            include_match = re.match(r"^#include\s+(.+)$", code, re.IGNORECASE)
            if include_match is None:
                continue
            include_id = normalized_script_name(include_match.group(1))
            if include_id in visited:
                continue
            visited.add(include_id)
            include_path = script_index.get(include_id)
            if include_path is None:
                continue
            result.append((include_path.name, include_path.read_text(encoding="latin-1")))
            collect(include_path)

    collect(script_path)
    return result


def strip_script_comment(line: str) -> str:
    return line.split(";", 1)[0].strip()


def command_name_and_args(code: str) -> tuple[str, str]:
    if not code:
        return "", ""
    if "=" in code and not re.match(r"^[A-Za-z_][A-Za-z0-9_]*[\s,]", code):
        left, right = code.split("=", 1)
        return "assign", f"{left.strip()}, {right.strip()}"
    match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)(?:[\s,]+(.*))?$", code)
    if not match:
        return "unknown", code
    return match.group(1), (match.group(2) or "").strip()


def split_arguments(arguments: str) -> list[str]:
    if not arguments:
        return []
    return [part.strip() for part in re.split(r"\s*,\s*|\s+", arguments) if part.strip()]


def parse_script_ir(path: Path) -> ScriptIr:
    ir = ScriptIr(source_path=path)
    for line_number, raw_line in enumerate(path.read_text(encoding="latin-1").splitlines(), start=1):
        code = strip_script_comment(raw_line)
        if not code:
            continue
        include_match = re.match(r"^#include\s+(.+)$", code, re.IGNORECASE)
        if include_match:
            ir.includes.append({"line": line_number, "path": include_match.group(1).strip()})
            continue
        if code.startswith("#"):
            continue
        if code.startswith(":"):
            label = code[1:].strip()
            if label:
                ir.labels.append({"line": line_number, "name": label})
            continue

        command, arguments = command_name_and_args(code)
        command_ref = ScriptCommand(line=line_number, command=command, arguments=arguments, raw=raw_line.rstrip())
        ir.commands.append(command_ref)
        command_key = command.lower()
        argument_values = split_arguments(arguments)

        if command_key == "addtrigger":
            ir.registered_triggers.append(
                {
                    "line": line_number,
                    "message": argument_values[0] if len(argument_values) >= 1 else "",
                    "callback": argument_values[1] if len(argument_values) >= 2 else "",
                    "arguments_raw": arguments,
                }
            )
        elif command_key == "trigger":
            ir.trigger_edges.append(
                {
                    "line": line_number,
                    "target_expression": argument_values[0] if len(argument_values) >= 1 else "",
                    "message_expression": argument_values[1] if len(argument_values) >= 2 else "",
                    "arguments_raw": arguments,
                }
            )

        if command_key in MOVEMENT_COMMANDS:
            ir.movement_commands.append({"line": line_number, "command": command, "arguments_raw": arguments})
        elif command_key in STATE_COMMANDS:
            ir.state_commands.append({"line": line_number, "command": command, "arguments_raw": arguments})
        elif command_key in PRESENTATION_COMMANDS:
            ir.presentation_commands.append({"line": line_number, "command": command, "arguments_raw": arguments})
        elif command_key not in {
            "addtrigger",
            "trigger",
            "getparam",
            "getobjecthandle",
            "getpos",
            "getdims",
            "exit",
            "if",
            "else",
            "endif",
            "gosub",
            "wait",
            "playsound",
            "getmyhandle",
            "hasitem",
            "takeitem",
            "rollovertext",
            "assign",
        }:
            ir.unknown_commands.append({"line": line_number, "command": command, "arguments_raw": arguments})

    return ir


def script_ir_to_yaml(ir: ScriptIr, scripts_root: Path) -> dict[str, Any]:
    try:
        source = ir.source_path.relative_to(scripts_root).as_posix()
    except ValueError:
        source = ir.source_path.as_posix()
    return {
        "script_id": ir.source_path.name.lower(),
        "source_path": source,
        "parse_status": "parsed",
        "includes": ir.includes,
        "labels": ir.labels,
        "registered_triggers": ir.registered_triggers,
        "trigger_edges": ir.trigger_edges,
        "movement_commands": ir.movement_commands,
        "state_commands": ir.state_commands,
        "presentation_commands": ir.presentation_commands,
        "unknown_commands": ir.unknown_commands,
        "command_count": len(ir.commands),
    }


def lua_string(value: str) -> str:
    return json.dumps(value)


def classic_mechanism_runtime_id(source_object_index: int) -> int:
    return 900000 + source_object_index


def mechanism_event_id(source_object_index: int) -> int:
    return MM9_MECHANISM_EVENT_ID_BASE + source_object_index


def normalize_mm9_sound_name(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    normalized = value.strip().replace("\\", "/")
    while normalized.startswith("/"):
        normalized = normalized[1:]

    lower = normalized.lower()
    for prefix in ("sounds/", "source/sounds/"):
        if lower.startswith(prefix):
            normalized = normalized[len(prefix):]
            lower = normalized.lower()

    return normalized


def lt_position_to_openyamm(position: list[Any], scale: float = 2.56) -> dict[str, int]:
    return {
        "x": int(round(float(position[0]) * scale)),
        "y": int(round(float(position[2]) * scale)),
        "z": int(round(float(position[1]) * scale)),
    }


def lt_rotation_to_openyamm_yaw_degrees(rotation: list[Any]) -> float:
    if len(rotation) < 2:
        return 0.0
    return (-math.degrees(float(rotation[1]))) % 360.0


def lt_rotation_to_openyamm_yaw_units(rotation: list[Any]) -> int:
    return int(round(lt_rotation_to_openyamm_yaw_degrees(rotation) * 2048.0 / 360.0)) % 2048


def bool_property(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def int_property(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return default
    return default


def start_point_entry(
    source_object_index: int,
    source_name: str,
    values: dict[str, Any],
    start_index: int,
) -> dict[str, Any] | None:
    position = values.get("Pos")
    if not isinstance(position, list) or len(position) < 3:
        return None

    rotation = values.get("Rotation")
    if not isinstance(rotation, list) or len(rotation) < 4:
        rotation = [0.0, 0.0, 0.0, 0.0]

    return {
        "start_index": start_index,
        "source_object_index": source_object_index,
        "source_class": "StartPoint",
        "source_name": source_name or f"StartPoint{start_index}",
        "source_position_lt": [float(value) for value in position[:3]],
        "position": lt_position_to_openyamm(position),
        "source_rotation_lt": [float(value) for value in rotation[:4]],
        "direction_yaw_units": lt_rotation_to_openyamm_yaw_units(rotation),
        "direction_degrees": lt_rotation_to_openyamm_yaw_degrees(rotation),
        "team_number": int_property(values.get("TeamNbr"), 0),
        "player_number": int_property(values.get("PlayerNbr"), 0),
        "move_player_to_floor": bool_property(values.get("MovePlayerToFloor"), True),
    }


def append_map_lua_start_points(lines: list[str], event_data: dict[str, Any]) -> None:
    lines.append("map.start_points = {")
    for start in event_data.get("start_points", []) or []:
        if not isinstance(start, dict):
            continue
        position = start.get("position", {})
        if not isinstance(position, dict):
            position = {}
        lines.append("    {")
        lines.append(f"        start_index = {int(start.get('start_index', 0))},")
        lines.append(f"        source_object_index = {int(start.get('source_object_index', 0))},")
        lines.append(f"        source_name = {lua_string(str(start.get('source_name', '')))},")
        lines.append(f"        x = {int(position.get('x', 0))},")
        lines.append(f"        y = {int(position.get('y', 0))},")
        lines.append(f"        z = {int(position.get('z', 0))},")
        lines.append(f"        direction_yaw_units = {int(start.get('direction_yaw_units', 0))},")
        lines.append(f"        move_player_to_floor = {str(bool(start.get('move_player_to_floor', True))).lower()},")
        lines.append("    },")
    lines.append("}")
    lines.append("map.start_point_by_name = {}")
    lines.append("map.start_point_by_source_object_index = {}")
    lines.append("for _, start_point in ipairs(map.start_points) do")
    lines.append("    if start_point.source_name ~= nil and start_point.source_name ~= \"\" then")
    lines.append("        map.start_point_by_name[start_point.source_name] = start_point")
    lines.append("    end")
    lines.append("    map.start_point_by_source_object_index[start_point.source_object_index] = start_point")
    lines.append("end")
    lines.append("")
    lines.append("function map.resolveStartPoint(nameOrIndex)")
    lines.append("    if type(nameOrIndex) == \"number\" then")
    lines.append("        return map.start_points[nameOrIndex + 1] or map.start_point_by_source_object_index[nameOrIndex]")
    lines.append("    end")
    lines.append("    if type(nameOrIndex) == \"string\" then")
    lines.append("        return map.start_point_by_name[nameOrIndex]")
    lines.append("    end")
    lines.append("    return nil")
    lines.append("end")
    lines.append("")
    lines.append("function map.moveToStartPoint(nameOrIndex, targetMapFileName)")
    lines.append("    local start_point = map.resolveStartPoint(nameOrIndex)")
    lines.append("    if start_point == nil or evt == nil or evt.MoveToMap == nil then")
    lines.append("        return false")
    lines.append("    end")
    lines.append("    evt.MoveToMap(")
    lines.append("        start_point.x,")
    lines.append("        start_point.y,")
    lines.append("        start_point.z,")
    lines.append("        start_point.direction_yaw_units,")
    lines.append("        0,")
    lines.append("        0,")
    lines.append("        0,")
    lines.append("        1,")
    lines.append("        targetMapFileName)")
    lines.append("    return true")
    lines.append("end")
    lines.append("")


def append_map_lua_actor_bindings(lines: list[str], event_data: dict[str, Any]) -> None:
    lines.append("map.actor_bindings = {")
    for actor in event_data.get("actor_bindings", []) or []:
        if not isinstance(actor, dict):
            continue
        actor_index = actor.get("actor_index")
        source_object_index = actor.get("source_object_index")
        if not isinstance(actor_index, int) or not isinstance(source_object_index, int):
            continue
        lines.append("    {")
        lines.append(f"        actor_index = {actor_index},")
        lines.append(f"        source_object_index = {source_object_index},")
        lines.append(f"        source_class = {lua_string(str(actor.get('source_class', '')))},")
        lines.append(f"        source_name = {lua_string(str(actor.get('source_name', '')))},")
        lines.append("    },")
    lines.append("}")
    lines.append("map.actor_by_source_name = {}")
    lines.append("for _, actor in ipairs(map.actor_bindings) do")
    lines.append("    if actor.source_name ~= nil and actor.source_name ~= \"\" then")
    lines.append("        map.actor_by_source_name[actor.source_name] = actor")
    lines.append("    end")
    lines.append("end")
    lines.append("")


def map_lua_mechanism_entries(event_data: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for mechanism in event_data.get("mechanisms", []) or []:
        if not isinstance(mechanism, dict):
            continue

        source_object_index = mechanism.get("source_object_index")
        if not isinstance(source_object_index, int):
            continue

        mechanism_motion_data = mechanism.get("mechanism", {})
        mechanism_kind = (
            str(mechanism_motion_data.get("kind", ""))
            if isinstance(mechanism_motion_data, dict)
            else ""
        )
        entry = {
            "mechanism_id": classic_mechanism_runtime_id(source_object_index),
            "event_id": mechanism_event_id(source_object_index),
            "source_object_index": source_object_index,
            "source_class": str(mechanism.get("source_class", "")),
            "source_name": str(mechanism.get("source_name", "")),
            "kind": mechanism_kind,
            "hint": str(mechanism.get("source_name", "")) or str(mechanism.get("source_class", "")),
            "classic_door_id": None,
            "double_door_name": "",
            "sounds": [],
        }
        activation_data = mechanism.get("activation", {})
        if isinstance(activation_data, dict):
            double_door_name = activation_data.get("double_door_name")
            if isinstance(double_door_name, str):
                entry["double_door_name"] = double_door_name
        sounds = mechanism.get("sounds", [])
        if isinstance(sounds, list):
            entry["sounds"] = [
                sound
                for sound in sounds
                if isinstance(sound, dict)
                and isinstance(sound.get("phase"), str)
                and isinstance(sound.get("sound_name"), str)
                and sound.get("sound_name")
            ]
        classic_event_face = mechanism.get("classic_event_face", {})
        if isinstance(classic_event_face, dict):
            event_id = classic_event_face.get("event_id")
            if isinstance(event_id, int):
                entry["event_id"] = event_id
            hint = classic_event_face.get("hint")
            if isinstance(hint, str) and hint:
                entry["hint"] = hint
        classic_runtime = mechanism.get("classic_runtime", {})
        if isinstance(classic_runtime, dict):
            classic_door_id = classic_runtime.get("door_id")
            if isinstance(classic_door_id, int):
                entry["classic_door_id"] = classic_door_id
        entries.append(entry)
    return entries


def append_map_lua_mechanisms(lines: list[str], event_data: dict[str, Any]) -> None:
    mechanisms = map_lua_mechanism_entries(event_data)
    lines.append("map.mechanisms = {")
    for mechanism in mechanisms:
        lines.append("    {")
        lines.append(f"        mechanism_id = {mechanism['mechanism_id']},")
        lines.append(f"        event_id = {mechanism['event_id']},")
        lines.append(f"        source_object_index = {mechanism['source_object_index']},")
        lines.append(f"        source_class = {lua_string(mechanism['source_class'])},")
        lines.append(f"        source_name = {lua_string(mechanism['source_name'])},")
        lines.append(f"        kind = {lua_string(mechanism['kind'])},")
        lines.append(f"        hint = {lua_string(mechanism['hint'])},")
        if mechanism["double_door_name"]:
            lines.append(f"        double_door_name = {lua_string(mechanism['double_door_name'])},")
        if mechanism["classic_door_id"] is not None:
            lines.append(f"        classic_door_id = {mechanism['classic_door_id']},")
        if mechanism["sounds"]:
            lines.append("        sounds = {")
            for sound in mechanism["sounds"]:
                phase = str(sound.get("phase", ""))
                sound_name = str(sound.get("sound_name", ""))
                position = sound.get("position")
                lines.append(f"            [{lua_string(phase)}] = {{")
                lines.append(f"                name = {lua_string(sound_name)},")
                if isinstance(position, dict):
                    x = int(position.get("x", 0) or 0)
                    y = int(position.get("y", 0) or 0)
                    z = int(position.get("z", 0) or 0)
                    lines.append(f"                x = {x},")
                    lines.append(f"                y = {y},")
                    lines.append(f"                z = {z},")
                lines.append("            },")
            lines.append("        },")
        lines.append("    },")
    lines.append("}")
    lines.append("map.mechanism_by_name = {}")
    lines.append("map.mechanism_by_source_object_index = {}")
    lines.append("map.mechanism_by_door_id = {}")
    lines.append("for _, mechanism in ipairs(map.mechanisms) do")
    lines.append("    if mechanism.source_name ~= nil and mechanism.source_name ~= \"\" then")
    lines.append("        map.mechanism_by_name[mechanism.source_name] = mechanism")
    lines.append("    end")
    lines.append("    map.mechanism_by_source_object_index[mechanism.source_object_index] = mechanism")
    lines.append("    map.mechanism_by_door_id[mechanism.mechanism_id] = mechanism")
    lines.append("    if mechanism.classic_door_id ~= nil then")
    lines.append("        map.mechanism_by_door_id[mechanism.classic_door_id] = mechanism")
    lines.append("    end")
    lines.append("end")
    lines.append("")
    lines.append("function map.resolveMechanism(nameOrId)")
    lines.append("    if type(nameOrId) == \"number\" then")
    lines.append("        return map.mechanism_by_door_id[nameOrId] or map.mechanism_by_source_object_index[nameOrId]")
    lines.append("    end")
    lines.append("    if type(nameOrId) == \"string\" then")
    lines.append("        return map.mechanism_by_name[nameOrId]")
    lines.append("    end")
    lines.append("    return nil")
    lines.append("end")
    lines.append("")
    lines.append("function map.triggerResolvedMechanism(mechanism, resolved_action)")
    lines.append("    if mechanism.classic_door_id ~= nil and evt ~= nil and evt.SetDoorState ~= nil then")
    lines.append("        evt.SetDoorState(mechanism.classic_door_id, resolved_action)")
    lines.append("        return true")
    lines.append("    end")
    lines.append("    if evt ~= nil and evt.SetOutdoorModelMechanismState ~= nil then")
    lines.append("        evt.SetOutdoorModelMechanismState(mechanism.mechanism_id, resolved_action)")
    lines.append("        return true")
    lines.append("    end")
    lines.append("    return false")
    lines.append("end")
    lines.append("")
    lines.append("function map.triggerMechanism(nameOrId, action)")
    lines.append("    local mechanism = map.resolveMechanism(nameOrId)")
    lines.append("    if mechanism == nil then")
    lines.append("        return false")
    lines.append("    end")
    lines.append("    local resolved_action = action or 2")
    lines.append("    local triggered = map.triggerResolvedMechanism(mechanism, resolved_action)")
    lines.append("    if mechanism.double_door_name ~= nil and mechanism.double_door_name ~= \"\" then")
    lines.append("        local partner = map.resolveMechanism(mechanism.double_door_name)")
    lines.append("        if partner ~= nil and partner.mechanism_id ~= mechanism.mechanism_id then")
    lines.append("            triggered = map.triggerResolvedMechanism(partner, resolved_action) or triggered")
    lines.append("        end")
    lines.append("    end")
    lines.append("    return triggered")
    lines.append("end")
    lines.append("")


def append_map_lua_classic_event_handlers(lines: list[str], event_data: dict[str, Any]) -> None:
    mechanisms = [
        mechanism
        for mechanism in map_lua_mechanism_entries(event_data)
        if mechanism["kind"] in MM9_INTERACTIVE_MECHANISM_KINDS
        and 0 < int(mechanism["event_id"]) <= 0xffff
    ]
    pickup_callbacks = {
        str(source.get("on_pickup_event", ""))
        for source in event_data.get("world_items", []) or []
        if isinstance(source, dict)
    }
    yanmir_locked_names = {
        "DoorTeleportRight",
        "DoorTeleportLeft",
        "RotatingDoor61",
        "RotatingDoor62",
        "RotatingDoor63",
        "RotatingDoor64",
        "RotatingDoor65",
        "RotatingDoor66",
        "RotatingDoor67",
    }

    def required_qbit(mechanism: dict[str, Any]) -> int | None:
        source_name = str(mechanism.get("source_name", ""))
        if "yanmirs_key" in pickup_callbacks and source_name in yanmir_locked_names:
            return 97001
        if "golden_honk" in pickup_callbacks and source_name in {"DoubleDoorL13", "DoubleDoorR13"}:
            return 90343
        return None

    lines.append("SetMapMetadata({")
    lines.append("    onLoad = {},")
    lines.append("    onLeave = {},")
    lines.append("    contextActions = {")
    for mechanism in mechanisms:
        action_kind = "open_door" if mechanism["kind"] in {"linear_door", "rotating_door"} else "generic_event"
        lines.append(
            f"    [{mechanism['event_id']}] = {{ kind = {lua_string(action_kind)}, "
            f"source = \"mm9_mechanism\", targetName = {lua_string(mechanism['hint'])} }},"
        )
    lines.append("    },")
    lines.append("    textureNames = {},")
    lines.append("    spriteNames = {},")
    lines.append("    castSpellIds = {},")
    lines.append("    timers = {},")
    lines.append("})")
    lines.append("")

    for mechanism in mechanisms:
        hint = mechanism["hint"]
        gate_qbit = required_qbit(mechanism)
        lines.append(
            f"RegisterEvent({mechanism['event_id']}, {lua_string(hint)}, function()"
        )
        if gate_qbit is not None:
            lines.append(f"    if not IsQBitSet({gate_qbit}) then")
            lines.append("        return")
            lines.append("    end")
        lines.append(f"    map.triggerMechanism({mechanism['source_object_index']}, 2)")
        lines.append(f"end, {lua_string(hint)})")
        lines.append("")

def append_map_lua_item_source_handlers(lines: list[str], event_data: dict[str, Any]) -> None:
    for source in event_data.get("world_items", []) or []:
        if not isinstance(source, dict):
            continue
        callback = source.get("on_pickup_event")
        source_object_index = source.get("source_object_index")
        source_id = source.get("source_id")
        if not isinstance(callback, str) or not callback:
            continue
        if not isinstance(source_object_index, int) or not isinstance(source_id, str):
            continue
        event_id = mechanism_event_id(source_object_index)
        if event_id <= 0 or event_id > 0xffff:
            continue
        append_map_lua_world_item_callback(lines, event_id, source, callback, event_data)

    persistent_sources = [
        source
        for source in event_data.get("persistent_item_mechanisms", []) or []
        if isinstance(source, dict)
    ]
    persistent_by_handler = {
        str(source.get("handler", "")): source
        for source in persistent_sources
    }
    tasar_books: dict[tuple[str, int], dict[str, Any]] = {}
    for source in persistent_sources:
        if source.get("handler") != "tasar_textbook":
            continue
        params = str(source.get("script_params", "")).split()
        if len(params) == 2 and params[0].isdigit():
            tasar_books[(params[1].lower(), int(params[0]))] = source

    persistent_init_lines: list[str] = []
    for source in persistent_sources:
        if not isinstance(source, dict):
            continue
        handler = str(source.get("handler", ""))
        source_object_index = source.get("source_object_index")
        source_id = source.get("source_id")
        if not isinstance(source_object_index, int) or not isinstance(source_id, str):
            continue
        event_id = mechanism_event_id(source_object_index)
        if event_id <= 0 or event_id > 0xffff:
            continue
        required_items = source.get("required_items", []) or []
        grant_items = source.get("grant_items", []) or []
        if not all(isinstance(item_id, int) and item_id > 0 for item_id in required_items):
            raise ValueError(f"persistent item mechanism {source_object_index} has invalid required items")
        translated_grants = [
            int(grant.get("item_id", 0))
            for grant in grant_items
            if isinstance(grant, dict)
        ]
        if any(item_id <= 0 for item_id in translated_grants):
            raise ValueError(f"persistent item mechanism {source_object_index} has invalid grant items")
        hint = str(source.get("source_name", "")) or "Use"

        if handler in {"elixir_burner", "elixir_cookpot"}:
            if not translated_grants:
                raise ValueError(f"persistent item mechanism {source_object_index} has no grant item")
            condition = " and ".join(f"HasItemAnywhere({item_id})" for item_id in required_items)
            lines.append(f"RegisterEvent({event_id}, {lua_string(hint)}, function()")
            lines.append(f"    if {condition} then")
            for item_id in required_items:
                lines.append(f"        RemoveItem({item_id})")
            for item_id in translated_grants:
                lines.append(f"        GiveItem({item_id})")
            lines.append("        evt.PlaySoundName(\"sounds/events/quest.wav\")")
            lines.append("    end")
            lines.append(f"end, {lua_string(hint)})")
            lines.append("")
        elif handler == "slag_extractor":
            if len(translated_grants) != 1:
                raise ValueError("slag extractor must grant exactly one broken machine item")
            lines.append(f"RegisterEvent({event_id}, {lua_string(hint)}, function()")
            lines.append("    if not IsQBitSet(99512) then")
            lines.append(f"        GiveItem({translated_grants[0]})")
            lines.append("        SetQBit(99512)")
            lines.append(
                f"        evt.SetPersistentItemMechanismState({lua_string(source_id)}, false, false)")
            lines.append("    end")
            lines.append(f"end, {lua_string(hint)})")
            lines.append("")
            persistent_init_lines.extend([
                "    if IsQBitSet(90037) then",
                f"        evt.SetPersistentItemMechanismState({lua_string(source_id)}, true, true)",
                f"        evt.SetPersistentItemMechanismVariant({lua_string(source_id)}, 1)",
                "    elseif IsQBitSet(99512) then",
                f"        evt.SetPersistentItemMechanismState({lua_string(source_id)}, false, false)",
                "    else",
                f"        evt.SetPersistentItemMechanismState({lua_string(source_id)}, true, true)",
                "    end",
            ])
        elif handler == "slag_extractor_socket":
            slag = persistent_by_handler.get("slag_extractor")
            if slag is None or len(required_items) != 1:
                raise ValueError("slag extractor socket is missing its retained target or repair item")
            target_id = str(slag.get("source_id", ""))
            lines.append(f"RegisterEvent({event_id}, {lua_string(hint)}, function()")
            lines.append(
                f"    if IsQBitSet(99512) and not IsQBitSet(90037) "
                f"and HasItemAnywhere({required_items[0]}) then")
            lines.append("        AddValue(Experience, 5000)")
            lines.append(f"        RemoveItem({required_items[0]})")
            lines.append("        SetQBit(90037)")
            lines.append("        evt.PlaySoundName(\"sounds/events/quest.wav\")")
            lines.append(f"        evt.SetPersistentItemMechanismState({lua_string(target_id)}, true, true)")
            lines.append(f"        evt.SetPersistentItemMechanismVariant({lua_string(target_id)}, 1)")
            lines.append("    end")
            lines.append(f"end, {lua_string(hint)})")
            lines.append("")
        elif handler == "capstone_socket":
            persistent_init_lines.extend([
                "    if IsQBitSet(90099) then",
                f"        evt.SetPersistentItemMechanismState({lua_string(source_id)}, true, true)",
                "    else",
                f"        evt.SetPersistentItemMechanismState({lua_string(source_id)}, false, false)",
                "    end",
            ])
        elif handler == "capstone_pedestal":
            capstone = persistent_by_handler.get("capstone_socket")
            if capstone is None or len(required_items) != 1:
                raise ValueError("capstone pedestal is missing its retained target or capstone item")
            target_id = str(capstone.get("source_id", ""))
            lines.append(f"RegisterEvent({event_id}, {lua_string(hint)}, function()")
            lines.append(
                f"    if IsQBitSet(90098) and not IsQBitSet(90099) "
                f"and HasItemAnywhere({required_items[0]}) then")
            lines.append("        SetQBit(90099)")
            lines.append("        AddValue(Experience, 154000)")
            lines.append("        evt.PlaySoundName(\"sounds/events/quest.wav\")")
            lines.append(f"        RemoveItem({required_items[0]})")
            lines.append(f"        evt.SetPersistentItemMechanismState({lua_string(target_id)}, true, true)")
            lines.append("    end")
            lines.append(f"end, {lua_string(hint)})")
            lines.append("")
        elif handler == "tasar_textbook_table":
            location = str(source.get("script_params", "")).strip().lower()
            stage = {
                "offense": (0, 9501, 9517),
                "strategy": (1, 9502, 9518),
                "defense": (2, 9503, 9519),
                "intelligence": (3, 9504, 9520),
            }.get(location)
            lines.append(f"RegisterEvent({event_id}, {lua_string(hint)}, function()")
            if stage is not None:
                designated_item = required_items[stage[0]]
                lines.append(f"    if HasItemAnywhere({designated_item}) then")
                lines.append(f"        SetQBit({90000 + stage[1]})")
                lines.append(f"        SetQBit({90000 + stage[2]})")
                lines.append("    end")
            for raw_item_id, item_id in zip((435, 436, 437, 438), required_items):
                target = tasar_books.get((location, raw_item_id))
                if target is None:
                    continue
                target_id = str(target.get("source_id", ""))
                lines.append(f"    if HasItemAnywhere({item_id}) then")
                lines.append(f"        RemoveItem({item_id})")
                lines.append(
                    f"        evt.SetPersistentItemMechanismState({lua_string(target_id)}, true, true)")
                lines.append("    end")
            lines.append(
                "    if IsQBitSet(99501) and IsQBitSet(99502) "
                "and IsQBitSet(99503) and IsQBitSet(99504) then")
            lines.append("        SetQBit(99516)")
            lines.append("        local libraryDoor = map.resolveMechanism(\"LibraryDoor\")")
            lines.append("        if libraryDoor ~= nil then")
            lines.append("            map.triggerResolvedMechanism(libraryDoor, \"open\")")
            lines.append("        end")
            lines.append("    end")
            lines.append(f"end, {lua_string(hint)})")
            lines.append("")
        elif handler == "tasar_textbook":
            params = str(source.get("script_params", "")).split()
            if len(params) != 2 or not params[0].isdigit() or len(translated_grants) != 1:
                raise ValueError(f"TaSar textbook {source_object_index} has invalid parameters")
            raw_item_id = int(params[0])
            location = params[1].lower()
            own_key = {435: 9501, 436: 9502, 437: 9503, 438: 9504}.get(raw_item_id)
            prerequisite = {435: None, 436: 9517, 437: 9518, 438: 9519}.get(raw_item_id)
            if own_key is None:
                raise ValueError(f"TaSar textbook {source_object_index} has invalid item {raw_item_id}")
            condition = f"not IsQBitSet({90000 + own_key}) and not IsQBitSet(99516)"
            if prerequisite is not None:
                condition += f" and IsQBitSet({90000 + prerequisite})"
            lines.append(f"RegisterEvent({event_id}, {lua_string(hint)}, function()")
            lines.append(f"    if {condition} then")
            lines.append(f"        ClearQBit({90000 + own_key})")
            lines.append(f"        GiveItem({translated_grants[0]})")
            lines.append(
                f"        evt.SetPersistentItemMechanismState({lua_string(source_id)}, false, false)")
            lines.append("    end")
            lines.append(f"end, {lua_string(hint)})")
            lines.append("")

            location_key = {"offense": 9517, "strategy": 9518, "defense": 9519, "intelligence": 9520}.get(
                location)
            if location == "start":
                if raw_item_id == 435:
                    visible_condition = f"not HasItemAnywhere({translated_grants[0]}) and not IsQBitSet(99501)"
                else:
                    visible_condition = "true"
            elif location_key is not None:
                visible_condition = f"IsQBitSet({90000 + location_key})"
                expected_item = {"offense": 436, "strategy": 437, "defense": 438}.get(location)
                if raw_item_id == expected_item:
                    next_key = {436: 9502, 437: 9503, 438: 9504}[raw_item_id]
                    visible_condition += (
                        f" and not HasItemAnywhere({translated_grants[0]}) "
                        f"and not IsQBitSet({90000 + next_key})")
            else:
                visible_condition = "false"
            persistent_init_lines.extend([
                f"    if {visible_condition} then",
                f"        evt.SetPersistentItemMechanismState({lua_string(source_id)}, true, true)",
                "    else",
                f"        evt.SetPersistentItemMechanismState({lua_string(source_id)}, false, false)",
                "    end",
            ])
        elif handler == "genie_lamp":
            random_item_pool = source.get("random_item_pool", []) or []
            if not random_item_pool or not all(isinstance(item_id, int) and item_id > 0 for item_id in random_item_pool):
                raise ValueError("genie lamp random item pool is unresolved")
            item_table = ", ".join(str(item_id) for item_id in random_item_pool)
            lines.append(f"RegisterEvent({event_id}, {lua_string(hint)}, function()")
            lines.append("    local effect = evt.RandomBetween(0, 4, 1)")
            lines.append("    if effect == 0 then")
            lines.append("        AddValue(Gold, evt.RandomBetween(100, 1000, 2))")
            lines.append("    elseif effect == 1 then")
            lines.append("        AddValue(Experience, evt.RandomBetween(100, 1000, 3))")
            lines.append("    elseif effect == 2 then")
            lines.append(f"        local itemPool = {{{item_table}}}")
            lines.append("        GiveItem(itemPool[evt.RandomBetween(1, #itemPool, 4)])")
            lines.append("    elseif effect == 3 then")
            lines.append("        AddValue(HP, evt.RandomBetween(100, 1000, 5))")
            lines.append("    else")
            lines.append("        evt.ApplyPartyPrimaryStatBuff(")
            lines.append("            evt.RandomBetween(0, 5, 6), evt.RandomBetween(1, 2, 7), 3000)")
            lines.append("    end")
            lines.append(f"end, {lua_string(hint)})")
            lines.append("")
        else:
            raise ValueError(f"persistent item mechanism {source_id} has unknown handler {handler}")

    if persistent_init_lines:
        lines.append('RegisterMapOnLoadEvent(65000, "MM9 item mechanism state", function()')
        lines.extend(persistent_init_lines)
        lines.append('end, "")')
        lines.append("")

    for container in event_data.get("loot_containers", []) or []:
        if not isinstance(container, dict) or container.get("kind") != "chest":
            continue
        source_object_index = container.get("source_object_index")
        container_id = container.get("container_id")
        if not isinstance(source_object_index, int) or not isinstance(container_id, int):
            continue
        event_id = mechanism_event_id(source_object_index)
        if event_id <= 0 or event_id > 0xffff:
            continue
        hint = str(container.get("source_name", "")) or "Chest"
        lines.append(f"RegisterEvent({event_id}, {lua_string(hint)}, function()")
        lines.append(f"    evt.OpenChest({container_id})")
        lines.append(f"end, {lua_string(hint)})")
        lines.append("")

    for source in event_data.get("spawned_loot_containers", []) or []:
        if not isinstance(source, dict) or source.get("kind") != "treasure_bag":
            continue
        source_object_index = source.get("source_object_index")
        source_id = source.get("source_id")
        if not isinstance(source_object_index, int) or not isinstance(source_id, str):
            continue
        event_id = mechanism_event_id(source_object_index)
        if event_id <= 0 or event_id > 0xffff:
            continue
        hint = str(source.get("source_name", "")) or "Break"
        lines.append(f"RegisterEvent({event_id}, {lua_string(hint)}, function()")
        lines.append(f"    evt.SpawnLootContainer({lua_string(source_id)})")
        lines.append(f"end, {lua_string(hint)})")
        lines.append("")

    for source in event_data.get("searchable_loot_props", []) or []:
        if not isinstance(source, dict) or source.get("kind") != "bone_pile":
            continue
        source_object_index = source.get("source_object_index")
        source_id = source.get("source_id")
        if not isinstance(source_object_index, int) or not isinstance(source_id, str):
            continue
        event_id = mechanism_event_id(source_object_index)
        if event_id <= 0 or event_id > 0xffff:
            continue
        hint = str(source.get("source_name", "")) or "Bone Pile"
        lines.append(f"RegisterEvent({event_id}, {lua_string(hint)}, function()")
        lines.append(f"    evt.SearchLootProp({lua_string(source_id)})")
        lines.append(f"end, {lua_string(hint)})")
        lines.append("")


def append_map_lua_world_item_callback(
    lines: list[str],
    event_id: int,
    source: dict[str, Any],
    callback: str,
    event_data: dict[str, Any],
) -> None:
    source_id = str(source["source_id"])
    hint = str(source.get("source_name", "")) or "Pick up"
    grant_items = source.get("grant_items", []) or []
    item_ids = [
        int(grant.get("item_id", 0))
        for grant in grant_items
        if isinstance(grant, dict)
    ]
    if any(item_id <= 0 for item_id in item_ids):
        raise ValueError(f"{source_id}: pickup callback has an unresolved item id")

    def item(index: int) -> int:
        if index >= len(item_ids):
            raise ValueError(f"{source_id}: pickup callback {callback} is missing grant item {index}")
        return item_ids[index]

    def qbit(raw_qbit: int) -> int:
        return 90000 + raw_qbit

    def give_and_consume(item_id: int, indent: str = "    ") -> None:
        lines.append(f"{indent}GiveItem({item_id})")
        lines.append(f"{indent}evt.ConsumeWorldItem({lua_string(source_id)})")

    actor_bindings = [
        actor
        for actor in event_data.get("actor_bindings", []) or []
        if isinstance(actor, dict) and isinstance(actor.get("actor_index"), int)
    ]

    def actor_index_by_name(source_name: str) -> int | None:
        for actor in actor_bindings:
            if actor.get("source_name") == source_name:
                return int(actor["actor_index"])
        return None

    def actor_indices_by_class_fragment(fragment: str) -> list[int]:
        normalized_fragment = fragment.lower()
        return [
            int(actor["actor_index"])
            for actor in actor_bindings
            if normalized_fragment in str(actor.get("source_class", "")).lower()
        ]

    def make_honks_hostile(indent: str) -> None:
        for actor_index in actor_indices_by_class_fragment("honk"):
            lines.append(f"{indent}evt.SetActorBit({actor_index}, ActorAttribute.Hostile, 1)")

    lines.append(f"RegisterEvent({event_id}, {lua_string(hint)}, function()")

    if callback == "beethoven_manuscript":
        lines.append(f"    if IsQBitSet({qbit(14)}) and not IsQBitSet({qbit(16)}) then")
        lines.append(f"        SetQBit({qbit(16)})")
        give_and_consume(item(0), "        ")
        lines.append(f"    elseif not IsQBitSet({qbit(110)}) then")
        lines.append(f"        SetQBit({qbit(110)})")
        give_and_consume(item(0), "        ")
        lines.append("    end")
    elif callback == "crona_kiga":
        petrified_mummy_index = actor_index_by_name("PetrifiedMummy16")
        if petrified_mummy_index is not None:
            lines.append(f"    evt.SetActorBit({petrified_mummy_index}, ActorAttribute.Active, 1)")
        lines.append(f"    if IsQBitSet({qbit(46)}) and not IsQBitSet({qbit(48)}) then")
        lines.append(f"        SetQBit({qbit(48)})")
        lines.append(f"        GiveItem({item(0)})")
        lines.append("        AddValue(Experience, 10000)")
        lines.append(f"        evt.ConsumeWorldItem({lua_string(source_id)})")
        lines.append(f"    elseif not IsQBitSet({qbit(169)}) then")
        lines.append(f"        SetQBit({qbit(169)})")
        lines.append(f"        GiveItem({item(0)})")
        lines.append("        AddValue(Experience, 10000)")
        lines.append(f"        evt.ConsumeWorldItem({lua_string(source_id)})")
        lines.append("    end")
    elif callback == "real_verhoffin_book":
        required_items = source.get("required_items", []) or []
        if len(required_items) != 1 or int(required_items[0]) <= 0:
            raise ValueError(f"{source_id}: real book callback requires one translated prerequisite item")
        prerequisite_item = int(required_items[0])
        lines.append(
            f"    if not IsQBitSet({qbit(283)}) and HasItemAnywhere({prerequisite_item}) then")
        lines.append(f"        RemoveItem({prerequisite_item})")
        lines.append(f"        GiveItem({item(0)})")
        lines.append(f"        GiveItem({item(1)})")
        lines.append(f"        SetQBit({qbit(283)})")
        lines.append(f"        SetQBit({qbit(290)})")
        lines.append(f"        evt.ConsumeWorldItem({lua_string(source_id)})")
        lines.append("    end")
    elif callback == "blackheart_alarm":
        lines.append(f"    if not IsQBitSet({qbit(223)}) then")
        lines.append(f"        SetQBit({qbit(223)})")
        lines.append(f"        GiveItem({item(0)})")
        lines.append("        evt.PlaySoundName(\"sounds/events/alarmbell.wav\")")
        lines.append(f"        evt.ConsumeWorldItem({lua_string(source_id)})")
        lines.append("    end")
    elif callback == "thjorad":
        monk_actor_indices = actor_indices_by_class_fragment("monk")
        lines.append("    local monkHostile = false")
        for actor_index in monk_actor_indices:
            lines.append(
                f"    monkHostile = monkHostile or evt.IsMapActorHostile({actor_index})")
        lines.append(f"    if monkHostile and IsQBitSet({qbit(2)}) and not IsQBitSet({qbit(31)}) then")
        lines.append(f"        SetQBit({qbit(31)})")
        lines.append(f"        GiveItem({item(0)})")
        lines.append("        AddValue(Experience, 1000)")
        lines.append(f"        evt.ConsumeWorldItem({lua_string(source_id)})")
        lines.append(f"    elseif monkHostile and not IsQBitSet({qbit(162)}) then")
        lines.append(f"        SetQBit({qbit(162)})")
        lines.append(f"        GiveItem({item(0)})")
        lines.append("        AddValue(Experience, 1000)")
        lines.append(f"        evt.ConsumeWorldItem({lua_string(source_id)})")
        lines.append("    end")
    elif callback == "book_of_rules":
        lines.append(f"    if IsQBitSet({qbit(57)}) and not IsQBitSet({qbit(59)}) then")
        lines.append(f"        SetQBit({qbit(59)})")
        lines.append(f"        GiveItem({item(0)})")
        lines.append("        AddValue(Experience, 5000)")
        lines.append(f"        evt.ConsumeWorldItem({lua_string(source_id)})")
        lines.append(f"    elseif not IsQBitSet({qbit(166)}) then")
        lines.append(f"        SetQBit({qbit(166)})")
        lines.append(f"        GiveItem({item(0)})")
        lines.append("        AddValue(Experience, 5000)")
        lines.append(f"        evt.ConsumeWorldItem({lua_string(source_id)})")
        lines.append("    end")
    elif callback == "accountant_key":
        accountant_index = actor_index_by_name("Accountant")
        lines.append(f"    if not IsQBitSet({qbit(7000)}) then")
        lines.append(f"        SetQBit({qbit(7000)})")
        give_and_consume(item(0), "        ")
        if accountant_index is not None:
            lines.append(
                f"        if evt.IsMapActorWithinPartyDistance({accountant_index}, 512) then")
            lines.append(
                f"            evt.SetActorBit({accountant_index}, ActorAttribute.Hostile, 1)")
            lines.append("        end")
        lines.append("    end")
    elif callback == "golden_honk":
        lines.append(f"    if IsQBitSet({qbit(343)}) and not IsQBitSet({qbit(344)}) then")
        lines.append(f"        SetQBit({qbit(344)})")
        give_and_consume(item(0), "        ")
        make_honks_hostile("        ")
        lines.append(f"    elseif not IsQBitSet({qbit(345)}) then")
        lines.append(f"        SetQBit({qbit(345)})")
        give_and_consume(item(0), "        ")
        make_honks_hostile("        ")
        lines.append("    end")
    elif callback == "great_book_key":
        lines.append("    if HasItemAnywhere(10243) then")
        lines.append(f"        GiveItem({item(0)})")
        lines.append(f"        GiveItem({item(1)})")
        lines.append(f"        GiveItem({item(2)})")
        lines.append(f"        SetQBit({qbit(374)})")
        lines.append(f"        evt.ConsumeWorldItem({lua_string(source_id)})")
        lines.append("    else")
        lines.append(f"        GiveItem({item(1)})")
        lines.append("    end")
    elif callback == "saints_relic":
        lines.append(f"    if IsQBitSet({qbit(338)}) and not IsQBitSet({qbit(340)}) then")
        lines.append(f"        SetQBit({qbit(340)})")
        give_and_consume(item(0), "        ")
        lines.append(f"    elseif not IsQBitSet({qbit(339)}) then")
        lines.append(f"        SetQBit({qbit(339)})")
        give_and_consume(item(0), "        ")
        lines.append("    end")
    elif callback == "yanmirs_key":
        lines.append(f"    if not IsQBitSet({qbit(7001)}) then")
        lines.append(f"        SetQBit({qbit(7001)})")
        give_and_consume(item(0), "        ")
        lines.append("    end")
    else:
        raise ValueError(f"{source_id}: unknown pickup callback {callback}")

    lines.append(f"end, {lua_string(hint)})")
    lines.append("")

def map_lua_text(
    map_id: str,
    script_irs: dict[str, ScriptIr],
    event_data: dict[str, Any] | None = None,
    dialogue_callbacks: list[CompiledRudeExit] | None = None,
) -> str:
    lines: list[str] = [
        "-- generated from MM9 event sidecars; do not edit by hand",
        "local map = {}",
        f"map.map_id = {lua_string(map_id)}",
        "map.scripts = {}",
        "",
    ]
    append_map_lua_start_points(lines, event_data or {})
    append_map_lua_actor_bindings(lines, event_data or {})
    append_map_lua_mechanisms(lines, event_data or {})
    append_map_lua_classic_event_handlers(lines, event_data or {})
    append_map_lua_item_source_handlers(lines, event_data or {})
    callbacks = dialogue_callbacks or []
    if callbacks:
        for callback in callbacks:
            lines.extend(callback.lua_lines)
            lines.append("")
    for script_id, ir in sorted(script_irs.items()):
        lines.append(f"map.scripts[{lua_string(script_id)}] = {{")
        lines.append(f"    source = {lua_string(ir.source_path.name)},")
        lines.append("    registered_triggers = {")
        for trigger in ir.registered_triggers:
            lines.append(
                "        { line = "
                + str(trigger["line"])
                + ", message = "
                + lua_string(trigger["message"])
                + ", callback = "
                + lua_string(trigger["callback"])
                + " },"
            )
        lines.append("    },")
        lines.append("    movement_commands = {")
        for command in ir.movement_commands:
            lines.append(
                "        { line = "
                + str(command["line"])
                + ", command = "
                + lua_string(command["command"])
                + ", arguments = "
                + lua_string(command["arguments_raw"])
                + " },"
            )
        lines.append("    },")
        lines.append("}")
    lines.extend(
        [
            "",
            "function map.register(ctx)",
            "    if ctx == nil or ctx.registerMm9MapEvents == nil then",
            "        return",
            "    end",
            "    ctx:registerMm9MapEvents(map)",
            "end",
            "",
        ]
    )
    lua_text = "\n".join(lines)
    registered_event_ids = [
        int(match.group(1))
        for match in re.finditer(r"(?m)^RegisterEvent\((\d+),", lua_text)
    ]
    duplicate_event_ids = sorted({
        event_id
        for event_id in registered_event_ids
        if registered_event_ids.count(event_id) > 1
    })
    if duplicate_event_ids:
        raise ValueError(
            f"{map_id}: duplicate generated interaction event ids: {duplicate_event_ids}"
        )
    return lua_text


def write_map_lua(
    path: Path,
    map_id: str,
    script_irs: dict[str, ScriptIr],
    event_data: dict[str, Any] | None = None,
    dialogue_callbacks: list[CompiledRudeExit] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        map_lua_text(map_id, script_irs, event_data, dialogue_callbacks),
        encoding="utf-8")


def map_script_ir_data(map_id: str, scripts_root: Path, script_irs: dict[str, ScriptIr]) -> dict[str, Any]:
    return {
        "format_version": 1,
        "kind": "mm9_script_ir",
        "map_id": map_id,
        "generated": {
            "tool": "tools/mm9_import_discovery/generate_mm9_events.py",
        },
        "scripts": [
            script_ir_to_yaml(ir, scripts_root)
            for _, ir in sorted(script_irs.items())
        ],
        "validation": {
            "script_count": len(script_irs),
        },
    }


def write_map_script_ir(path: Path, map_id: str, scripts_root: Path, script_irs: dict[str, ScriptIr]) -> None:
    write_yaml(path, map_script_ir_data(map_id, scripts_root, script_irs))


def source_object_id(map_id: str, object_index: int) -> str:
    return f"mm9:{map_id}:object:{object_index}"


def property_refs(object_node: dict[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for index, property_node in enumerate(object_node.get("properties", [])):
        refs.append(
            {
                "property_index": index,
                "name": property_node.get("name", ""),
                "decoded": bool(property_node.get("decoded", False)),
                "code": property_node.get("code", 0),
                "flags": property_node.get("flags", 0),
                "raw_ref": f"properties[{index}]",
            }
        )
    return refs


def normalized_properties(values: dict[str, Any]) -> dict[str, Any]:
    return {key: values[key] for key in sorted(values) if key in KNOWN_NORMALIZED_PROPERTIES}


def collect_trigger_outputs(values: dict[str, Any]) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    for slot in range(1, 11):
        target = values.get(f"TargetName{slot}", "")
        message = values.get(f"MessageName{slot}", "")
        if target or message:
            outputs.append({"phase": "trigger", "slot": slot, "target_name": target or "", "message_name": message or ""})
    for phase, target_prefix, message_prefix in (
        ("open", "OpenTriggerTarget", "OpenTrigger"),
        ("close", "CloseTriggerTarget", "CloseTrigger"),
    ):
        for slot in range(4):
            target = values.get(f"{target_prefix}{slot}", "")
            message = values.get(f"{message_prefix}{slot}", "")
            if target or message:
                outputs.append({"phase": phase, "slot": slot, "target_name": target or "", "message_name": message or ""})
    return outputs


def mechanism_motion(values: dict[str, Any], mechanism_kind: str) -> dict[str, Any]:
    motion: dict[str, Any] = {"kind": mechanism_kind, "source_units": "lithtech_mm9"}
    linear: dict[str, Any] = {}
    for source_key, target_key in (
        ("MoveDir", "move_dir_lt"),
        ("MoveDist", "move_dist_lt"),
        ("Speed", "open_speed_lt_per_sec"),
        ("ClosingSpeed", "close_speed_lt_per_sec"),
    ):
        if source_key in values:
            linear[target_key] = values[source_key]
    if linear:
        motion["linear"] = linear

    rotation: dict[str, Any] = {}
    for source_key, target_key in (
        ("RotationPoint", "rotation_point_lt"),
        ("RotationAngles", "rotation_angles_deg"),
        ("OpenAway", "open_away"),
    ):
        if source_key in values:
            rotation[target_key] = values[source_key]
    if rotation:
        motion["rotation"] = rotation

    timing: dict[str, Any] = {}
    for source_key, target_key in (
        ("MoveDelay", "move_delay_seconds_source"),
        ("OpenWaitTime", "open_wait_seconds_source"),
    ):
        if source_key in values:
            timing[target_key] = values[source_key]
    if timing:
        motion["timing"] = timing
    return motion


def activation(values: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in (
        "StartOpen",
        "StartOn",
        "PushOpen",
        "TouchToOpen",
        "AutoTrigger",
        "Locked",
        "ReopenOnContact",
        "DoubleDoorName",
    ):
        if key in values:
            snake = re.sub(r"(?<!^)([A-Z])", r"_\1", key).lower()
            result[snake] = values[key]
    return result


def mechanism_sounds(values: dict[str, Any]) -> list[dict[str, Any]]:
    sounds: list[dict[str, Any]] = []
    sound_position = values.get("SoundPos")
    position = (
        lt_position_to_openyamm(sound_position)
        if isinstance(sound_position, list) and len(sound_position) >= 3
        else None
    )
    for phase, property_name in (
        ("open", "OpenSoundName"),
        ("close", "CloseSoundName"),
        ("open_start", "OpenStartSound"),
        ("open_busy", "OpenBusySound"),
        ("open_stop", "OpenStopSound"),
        ("close_start", "CloseStartSound"),
        ("close_busy", "CloseBusySound"),
        ("close_stop", "CloseStopSound"),
        ("jiggle", "JiggleSound"),
    ):
        if property_name not in values:
            continue

        source_sound_name = values.get(property_name, "")
        sound_name = normalize_mm9_sound_name(source_sound_name)
        entry = {
            "phase": phase,
            "source_property": property_name,
            "source_sound_name": source_sound_name or "",
            "sound_name": sound_name,
            "authored": True,
        }
        if position is not None:
            entry["position"] = position
        sounds.append(entry)
    return sounds


def build_scene_model_instance_bindings(scene_path: Path) -> dict[int, list[dict[str, Any]]]:
    if not scene_path.exists():
        return {}
    scene = load_yaml(scene_path)
    bindings: dict[int, list[dict[str, Any]]] = {}
    for instance in scene.get("model_instances", []) or []:
        if not isinstance(instance, dict):
            continue
        source_index = instance.get("source_object_index")
        if not isinstance(source_index, int):
            continue
        bindings.setdefault(source_index, []).append(
            {
                "target_kind": "model_instance",
                "target_id": instance.get("instance_id", ""),
                "confidence": "exact_source_object_index",
            }
        )
    return bindings


def load_scene_indoor_door_ids(scene_path: Path) -> set[int]:
    if not scene_path.exists():
        return set()

    scene = load_yaml(scene_path)
    initial_state = scene.get("initial_state", {})
    if not isinstance(initial_state, dict):
        return set()

    door_ids: set[int] = set()
    for door in initial_state.get("doors", []) or []:
        if not isinstance(door, dict):
            continue
        door_id = door.get("door_id")
        if isinstance(door_id, int):
            door_ids.add(door_id)

    return door_ids


def load_scene_classic_event_face_ids(scene_path: Path) -> set[int]:
    if not scene_path.exists():
        return set()

    scene = load_yaml(scene_path)
    event_ids: set[int] = set()

    bmodel_faces = scene.get("bmodel_faces", {})
    if isinstance(bmodel_faces, dict):
        for face in bmodel_faces.get("interactive_faces", []) or []:
            if not isinstance(face, dict):
                continue
            event_id = face.get("cog_number")
            if isinstance(event_id, int):
                event_ids.add(event_id)

    initial_state = scene.get("initial_state", {})
    if isinstance(initial_state, dict):
        for override in initial_state.get("face_attribute_overrides", []) or []:
            if not isinstance(override, dict):
                continue
            event_id = override.get("cog_number")
            if isinstance(event_id, int):
                event_ids.add(event_id)

    return event_ids


def load_scene_mm9_actor_indices(scene_path: Path) -> dict[int, int]:
    if not scene_path.exists():
        return {}

    scene = load_yaml(scene_path)
    initial_state = scene.get("initial_state", {})
    if not isinstance(initial_state, dict):
        return {}

    result: dict[int, int] = {}
    for actor_index, actor in enumerate(initial_state.get("actors", []) or []):
        if not isinstance(actor, dict):
            continue
        source_object_index = actor.get("mm9_source_object_index")
        if isinstance(source_object_index, int):
            result[source_object_index] = actor_index
    return result


def build_mm9_bmodel_bindings(metadata_path: Path) -> dict[str, list[dict[str, Any]]]:
    if not metadata_path.exists():
        return {}
    bindings: dict[str, list[dict[str, Any]]] = {}
    current: dict[str, Any] | None = None
    in_bmodels = False
    scalar_pattern = re.compile(r"^\s*(name|source_model_name):\s+\"?(.*?)\"?\s*$")

    def flush_current() -> None:
        if current is None:
            return
        bmodel_index = current.get("bmodel_index")
        if not isinstance(bmodel_index, int):
            return
        bmodel_name = str(current.get("name", current.get("source_model_name", "")))
        source_model_name = str(current.get("source_model_name", bmodel_name))
        for name, confidence in (
            (source_model_name, "exact_source_model_name"),
            (bmodel_name, "exact_bmodel_name"),
        ):
            if not name:
                continue
            target = {
                "target_kind": "odm_bmodel",
                "target_id": f"odm:bmodel:{bmodel_index}",
                "confidence": confidence,
                "bmodel_index": bmodel_index,
                "bmodel_name": bmodel_name,
                "source_model_name": source_model_name,
            }
            if target not in bindings.setdefault(name, []):
                bindings[name].append(target)

    for line in metadata_path.read_text(encoding="utf-8").splitlines():
        if line == "bmodels:":
            in_bmodels = True
            continue
        if not in_bmodels:
            continue
        if line and not line.startswith("  ") and not line.startswith("-"):
            flush_current()
            break
        index_match = re.match(r"^\s*-\s+bmodel_index:\s+([0-9]+)\s*$", line)
        if index_match:
            flush_current()
            current = {"bmodel_index": int(index_match.group(1))}
            continue
        if current is None:
            continue
        scalar_match = scalar_pattern.match(line)
        if scalar_match:
            current[scalar_match.group(1)] = scalar_match.group(2)
    flush_current()
    return bindings


def load_world_model_polygon_groups(dat_world_path: Path) -> dict[int, dict[str, Any]]:
    if not dat_world_path.exists():
        return {}

    dat_world = load_yaml(dat_world_path)
    groups: dict[int, dict[str, Any]] = {}

    for model in dat_world.get("world_models", []) or []:
        if not isinstance(model, dict):
            continue

        source_model_index = model.get("source_model_index")
        if not isinstance(source_model_index, int):
            continue

        group: dict[str, Any] = {
            "source_model_index": source_model_index,
            "source_model_name": str(model.get("source_name", "")),
            "source_poly_count": int(model.get("poly_count", 0) or 0),
            "source_surface_count": int(model.get("surface_count", 0) or 0),
        }

        bounds_min = vector3(model.get("bounds_min_lt"))
        bounds_max = vector3(model.get("bounds_max_lt"))
        if bounds_min is not None:
            group["bounds_min_lt"] = list(bounds_min)
        if bounds_max is not None:
            group["bounds_max_lt"] = list(bounds_max)

        roles = model.get("roles")
        if isinstance(roles, dict):
            group["roles"] = {
                str(key): bool(value)
                for key, value in roles.items()
                if isinstance(value, bool)
            }

        groups[source_model_index] = group

    return groups


def attach_source_polygon_group(
    target: dict[str, Any],
    world_model_polygon_groups: dict[int, dict[str, Any]],
) -> None:
    if target.get("target_kind") != "odm_bmodel":
        return

    bmodel_index = target.get("bmodel_index")
    if not isinstance(bmodel_index, int):
        return

    group = world_model_polygon_groups.get(bmodel_index)
    if group is None:
        return

    target["source_polygon_group"] = dict(group)


def vector3(value: Any) -> tuple[float, float, float] | None:
    if not isinstance(value, list) or len(value) < 3:
        return None
    try:
        return (float(value[0]), float(value[1]), float(value[2]))
    except (TypeError, ValueError):
        return None


def distance3(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return (
        (left[0] - right[0]) ** 2
        + (left[1] - right[1]) ** 2
        + (left[2] - right[2]) ** 2
    ) ** 0.5


def same_point3(left: Any, right: Any, epsilon: float = 0.001) -> bool:
    left_vector = vector3(left)
    right_vector = vector3(right)
    if left_vector is None or right_vector is None:
        return False
    return distance3(left_vector, right_vector) <= epsilon


def load_movable_world_models(dat_world_path: Path) -> list[dict[str, Any]]:
    if not dat_world_path.exists():
        return []

    dat_world = load_yaml(dat_world_path)
    models: list[dict[str, Any]] = []

    for model in dat_world.get("world_models", []) or []:
        if not isinstance(model, dict):
            continue
        roles = model.get("roles") if isinstance(model.get("roles"), dict) else {}
        if not roles.get("movable"):
            continue
        translation = vector3(model.get("world_translation_lt"))
        if translation is None:
            continue
        source_model_index = model.get("source_model_index")
        if not isinstance(source_model_index, int):
            continue
        models.append(
            {
                "source_model_index": source_model_index,
                "source_name": str(model.get("source_name", "")),
                "world_translation_lt": list(translation),
                "movable": True,
            }
        )

    return models


def nearest_movable_world_model_evidence(
    movable_world_models: list[dict[str, Any]],
    point_lt: Any,
    distance_key: str,
    exact_claims_by_source_model_index: dict[int, list[dict[str, Any]]] | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    point = vector3(point_lt)
    if point is None or limit <= 0:
        return []

    candidates: list[dict[str, Any]] = []
    for model in movable_world_models:
        translation = vector3(model.get("world_translation_lt"))
        if translation is None:
            continue
        candidate = {
            "source_model_index": model["source_model_index"],
            "source_name": model["source_name"],
            "movable": True,
            "world_translation_lt": model["world_translation_lt"],
            distance_key: round(distance3(point, translation), 3),
        }
        claims = (exact_claims_by_source_model_index or {}).get(model["source_model_index"], [])
        if claims:
            candidate["claimed_by_exact_bindings"] = claims
        candidates.append(candidate)

    candidates.sort(key=lambda item: item[distance_key])
    return candidates[:limit]


def collect_exact_world_model_claims(
    raw_objects: list[Any],
    bmodel_bindings: dict[str, list[dict[str, Any]]],
) -> dict[int, list[dict[str, Any]]]:
    claims: dict[int, list[dict[str, Any]]] = {}

    for fallback_index, object_node in enumerate(raw_objects):
        if not isinstance(object_node, dict):
            continue

        values, _ = object_properties(object_node)
        object_name = str(values.get("Name", ""))

        if not object_name:
            continue

        object_index = int(object_node.get("object_index", fallback_index))

        for binding in bmodel_bindings.get(object_name, []):
            if binding.get("target_kind") != "odm_bmodel":
                continue

            bmodel_index = binding.get("bmodel_index")

            if not isinstance(bmodel_index, int):
                continue

            claim = {
                "source_object_index": object_index,
                "source_name": object_name,
                "confidence": binding.get("confidence", ""),
            }
            source_position = vector3(values.get("Pos"))
            if source_position is not None:
                claim["source_position_lt"] = list(source_position)
            for key in (
                "target_kind",
                "target_id",
                "bmodel_index",
                "bmodel_name",
                "source_model_name",
                "source_polygon_group",
            ):
                if key in binding:
                    claim[key] = binding[key]

            if claim not in claims.setdefault(bmodel_index, []):
                claims[bmodel_index].append(claim)

    return claims


def shared_rotation_point_world_model_binding(
    object_class: str,
    values: dict[str, Any],
    movable_world_models: list[dict[str, Any]],
    exact_claims_by_source_model_index: dict[int, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    if object_class != "RotatingDoor":
        return None

    rotation_point = values.get("RotationPoint")
    if vector3(rotation_point) is None:
        return None

    nearest_by_rotation = nearest_movable_world_model_evidence(
        movable_world_models,
        rotation_point,
        "distance_from_rotation_point_lt",
        exact_claims_by_source_model_index,
        limit=1,
    )
    if not nearest_by_rotation:
        return None

    candidate = nearest_by_rotation[0]
    claims = candidate.get("claimed_by_exact_bindings", [])
    if not isinstance(claims, list):
        return None

    for claim in claims:
        if not isinstance(claim, dict):
            continue
        if not same_point3(rotation_point, claim.get("source_position_lt")):
            continue

        bmodel_index = claim.get("bmodel_index", candidate.get("source_model_index"))
        if not isinstance(bmodel_index, int):
            continue

        source_model_name = str(claim.get("source_model_name", candidate.get("source_name", "")))
        bmodel_name = str(claim.get("bmodel_name", source_model_name))

        target = {
            "target_kind": "odm_bmodel",
            "target_id": f"odm:bmodel:{bmodel_index}",
            "confidence": "shared_rotation_point_exact_source_object_position",
            "bmodel_index": bmodel_index,
            "bmodel_name": bmodel_name,
            "source_model_name": source_model_name,
            "shared_with_source_object_index": claim.get("source_object_index"),
            "shared_with_source_name": claim.get("source_name", ""),
            "rotation_point_lt": list(vector3(rotation_point) or ()),
        }
        if "source_polygon_group" in claim:
            target["source_polygon_group"] = claim["source_polygon_group"]
        return target

    return None


def build_events_for_map(
    raw_objects_path: Path,
    scripts_root: Path,
    events_root: Path,
    scene_path: Path | None = None,
    metadata_path: Path | None = None,
    dat_world_path: Path | None = None,
) -> tuple[dict[str, Any], dict[str, ScriptIr], list[CompiledRudeExit]]:
    raw = load_yaml(raw_objects_path)
    map_id = remove_suffix(raw_objects_path.name, ".raw_objects.yml")
    script_index = build_script_index(scripts_root)
    resolved_scene_path = scene_path or raw_objects_path.with_name(f"{map_id}.scene.yml")
    scene_bindings = build_scene_model_instance_bindings(resolved_scene_path)
    scene_indoor_door_ids = load_scene_indoor_door_ids(resolved_scene_path)
    scene_classic_event_face_ids = load_scene_classic_event_face_ids(resolved_scene_path)
    actor_indices_by_source_object = load_scene_mm9_actor_indices(resolved_scene_path)
    scene_data = load_yaml(resolved_scene_path) if resolved_scene_path.exists() else {}
    resolved_dat_world_path = dat_world_path or raw_objects_path.with_name(f"{map_id}.dat_world.yml")
    world_model_polygon_groups = load_world_model_polygon_groups(resolved_dat_world_path)
    bmodel_bindings = build_mm9_bmodel_bindings(metadata_path or raw_objects_path.with_name(f"{map_id}.mm9.yml"))
    for binding_targets in bmodel_bindings.values():
        for target in binding_targets:
            attach_source_polygon_group(target, world_model_polygon_groups)
    movable_world_models = load_movable_world_models(resolved_dat_world_path)
    raw_objects = raw.get("objects", []) or []
    actor_handles: dict[str, int] = {}
    actor_bindings: list[dict[str, Any]] = []
    for object_node in raw_objects:
        if not isinstance(object_node, dict):
            continue
        object_index = int(object_node.get("object_index", -1))
        actor_index = actor_indices_by_source_object.get(object_index)
        if actor_index is None:
            continue
        values, _ = object_properties(object_node)
        object_name = values.get("Name")
        if isinstance(object_name, str) and object_name:
            actor_handles[object_name] = actor_index
        actor_bindings.append({
            "actor_index": actor_index,
            "source_object_index": object_index,
            "source_class": str(object_node.get("name", "")),
            "source_name": str(object_name or ""),
        })
    exact_world_model_claims = collect_exact_world_model_claims(raw_objects, bmodel_bindings)

    object_names: set[str] = set()
    object_entries: list[dict[str, Any]] = []
    mechanisms: list[dict[str, Any]] = []
    start_points: list[dict[str, Any]] = []
    triggers: list[dict[str, Any]] = []
    interactions: list[dict[str, Any]] = []
    travel_triggers: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    referenced_scripts: dict[str, ScriptIr] = {}
    dialogue_callbacks: list[CompiledRudeExit] = []
    class_counts: dict[str, int] = {}

    for object_node in raw_objects:
        if not isinstance(object_node, dict):
            continue
        object_index = int(object_node.get("object_index", len(object_entries)))
        object_class = str(object_node.get("name", ""))
        class_counts[object_class] = class_counts.get(object_class, 0) + 1
        values, _ = object_properties(object_node)
        object_name = str(values.get("Name", ""))
        if object_name:
            object_names.add(object_name)
        object_id = source_object_id(map_id, object_index)
        script_name = str(values.get("ScriptName", "") or "")
        script_id = normalized_script_name(script_name) if script_name else ""
        script_exists = False
        if script_id:
            script_path = script_index.get(script_id)
            if script_path is not None:
                script_exists = True
                referenced_scripts.setdefault(script_id, parse_script_ir(script_path))
            else:
                unresolved.append(
                    {
                        "kind": "missing_script",
                        "source_object_index": object_index,
                        "source_name": object_name,
                        "script_name": script_name,
                        "severity": "warning",
                    }
                )

        if bool_property(values.get("DoRude"), False) and script_exists:
            script_path = script_index[script_id]
            try:
                callback = compile_rude_exit(
                    script_path.read_text(encoding="latin-1"),
                    script_path.name,
                    object_index,
                    collect_script_include_sources(script_path, script_index),
                    split_arguments(str(values.get("ScriptParams", "") or "")),
                    actor_handles,
                    actor_indices_by_source_object.get(object_index))
            except ScrCompileError as exception:
                unresolved.append(
                    {
                        "kind": "dialogue_scr_compile_error",
                        "source_object_index": object_index,
                        "source_name": object_name,
                        "script_name": script_name,
                        "error": str(exception),
                        "severity": "error",
                    }
                )
            else:
                if callback is not None:
                    dialogue_callbacks.append(callback)

        classifications: list[str] = []
        if object_class in MECHANISM_CLASS_KINDS:
            classifications.append("mechanism")
        if object_class == "Trigger":
            classifications.append("trigger")
        if object_class in TRAVEL_TRIGGER_CLASSES:
            classifications.append("travel")
        if object_class in SCRIPTED_INTERACTION_CLASSES or object_class in TRAVEL_TRIGGER_CLASSES or script_name:
            classifications.append("interaction")

        raw_properties = property_refs(object_node)
        object_entry: dict[str, Any] = {
            "object_id": object_id,
            "source_object_index": object_index,
            "source_class": object_class,
            "source_name": object_name,
            "classifications": classifications,
            "raw_object_ref": f"{raw_objects_path.name}#objects[{object_index}]",
            "raw_property_count": len(raw_properties),
            "raw_properties": raw_properties,
            "normalized_properties": normalized_properties(values),
        }
        if script_name:
            object_entry["script"] = {
                "script_name": script_name,
                "script_id": script_id,
                "script_exists": script_exists,
                "script_params_raw": values.get("ScriptParams", ""),
            }
        object_entries.append(object_entry)

        object_bindings = list(scene_bindings.get(object_index, []))
        if object_name:
            object_bindings.extend(bmodel_bindings.get(object_name, []))
        if object_class in VOLUME_CLASS_KINDS and "Pos" in values and "Dims" in values:
            object_bindings.append(
                {
                    "target_kind": VOLUME_CLASS_KINDS[object_class],
                    "target_id": f"{object_id}:volume",
                    "confidence": "source_object_volume",
                    "pos_lt": values.get("Pos"),
                    "dims_lt": values.get("Dims"),
                }
            )
        if object_bindings:
            bindings.append({"object_id": object_id, "source_object_index": object_index, "targets": object_bindings})

        if object_class == "StartPoint":
            start_point = start_point_entry(object_index, object_name, values, len(start_points))
            if start_point is not None:
                start_points.append(start_point)
        elif object_class in MECHANISM_CLASS_KINDS:
            shared_rotation_binding = shared_rotation_point_world_model_binding(
                object_class,
                values,
                movable_world_models,
                exact_world_model_claims,
            )
            if shared_rotation_binding is not None:
                bindings.append(
                    {
                        "object_id": object_id,
                        "source_object_index": object_index,
                        "targets": [shared_rotation_binding],
                    }
                )
            else:
                unresolved_target = {"target_kind": "unresolved", "confidence": "unresolved"}
                unresolved_evidence: dict[str, Any] = {}
                nearest_by_rotation = nearest_movable_world_model_evidence(
                    movable_world_models,
                    values.get("RotationPoint"),
                    "distance_from_rotation_point_lt",
                    exact_world_model_claims,
                )
                if nearest_by_rotation:
                    unresolved_evidence["nearest_movable_world_models_by_rotation_point"] = nearest_by_rotation
                    unresolved_target["nearest_movable_world_models_by_rotation_point"] = nearest_by_rotation
                nearest_by_position = nearest_movable_world_model_evidence(
                    movable_world_models,
                    values.get("Pos"),
                    "distance_from_position_lt",
                    exact_world_model_claims,
                )
                if nearest_by_position:
                    unresolved_evidence["nearest_movable_world_models_by_position"] = nearest_by_position
                    unresolved_target["nearest_movable_world_models_by_position"] = nearest_by_position
                bindings.append(
                    {
                        "object_id": object_id,
                        "source_object_index": object_index,
                        "targets": [unresolved_target],
                    }
                )
                unresolved_entry = {
                    "kind": "unresolved_binding",
                    "source_object_index": object_index,
                    "source_name": object_name,
                    "source_class": object_class,
                    "severity": "warning",
                }
                if unresolved_evidence:
                    unresolved_entry["evidence"] = unresolved_evidence
                unresolved.append(unresolved_entry)

        outputs = collect_trigger_outputs(values)
        for output in outputs:
            target_name = output.get("target_name", "")
            if target_name and target_name not in object_names:
                # Resolution is finalized after all objects are scanned below.
                output["resolution"] = "pending"

        if object_class in MECHANISM_CLASS_KINDS:
            runtime_mechanism_id = classic_mechanism_runtime_id(object_index)
            runtime_event_id = mechanism_event_id(object_index)
            classic_runtime: dict[str, Any] | None = None
            if runtime_mechanism_id in scene_indoor_door_ids:
                classic_runtime = {
                    "target_kind": "indoor_door",
                    "door_id": runtime_mechanism_id,
                    "binding_source": "compiled_blv_scene_door",
                }

            mechanism_entry = {
                "mechanism_id": f"{object_id}:mechanism",
                "runtime_mechanism_id": runtime_mechanism_id,
                "runtime_event_id": runtime_event_id,
                "object_id": object_id,
                "source_object_index": object_index,
                "source_class": object_class,
                "source_name": object_name,
                "mechanism": mechanism_motion(values, MECHANISM_CLASS_KINDS[object_class]),
                "activation": activation(values),
                "sounds": mechanism_sounds(values),
                "trigger_outputs": outputs,
                **({"classic_runtime": classic_runtime} if classic_runtime is not None else {}),
            }
            if (
                MECHANISM_CLASS_KINDS[object_class] in MM9_INTERACTIVE_MECHANISM_KINDS
                and runtime_event_id in scene_classic_event_face_ids
                and runtime_event_id <= 0xffff
            ):
                mechanism_entry["classic_event_face"] = {
                    "event_id": runtime_event_id,
                    "cog_number": runtime_event_id,
                    "cog_triggered": runtime_event_id,
                    "cog_trigger_type": 0,
                    "hint": object_name or object_class,
                }
            mechanisms.append(mechanism_entry)

        if object_class == "Trigger":
            triggers.append(
                {
                    "trigger_id": f"{object_id}:trigger",
                    "object_id": object_id,
                    "source_object_index": object_index,
                    "source_name": object_name,
                    "dims_lt": values.get("Dims"),
                    "start_on": values.get("StartOn"),
                    "outputs": outputs,
                }
            )

        if object_class in TRAVEL_TRIGGER_CLASSES:
            travel = {
                "travel_id": f"{object_id}:travel",
                "object_id": object_id,
                "source_object_index": object_index,
                "source_name": object_name,
                "destination_world": str(values.get("DestinationWorld", "") or ""),
                "start_point_name": str(values.get("StartPointName", "") or ""),
                "ask_player": bool_property(values.get("AskPlayer"), False),
                "travel_days": int_property(values.get("TravelDays"), 0),
                "load_screen": str(values.get("LoadScreen", "") or ""),
            }
            travel_triggers.append(travel)

        if object_class in SCRIPTED_INTERACTION_CLASSES or object_class in TRAVEL_TRIGGER_CLASSES or script_name or outputs:
            travel_target = None
            if object_class in TRAVEL_TRIGGER_CLASSES:
                travel_target = {
                    "destination_world": str(values.get("DestinationWorld", "") or ""),
                    "start_point_name": str(values.get("StartPointName", "") or ""),
                }
            interactions.append(
                {
                    "interaction_id": f"{object_id}:interaction",
                    "object_id": object_id,
                    "source_object_index": object_index,
                    "source_class": object_class,
                    "source_name": object_name,
                    "activation": {
                        "use": bool(script_name or values.get("TouchToOpen") or object_class in {"Door", "RotatingDoor"}),
                        "touch": bool(object_class == "Trigger" or values.get("TriggerTouch") or values.get("TouchToOpen")),
                    },
                    "script_id": script_id,
                    "travel": travel_target,
                    "sends": outputs,
                }
            )

    for container_name, entries in (("mechanism", mechanisms), ("trigger", triggers), ("interaction", interactions)):
        for entry in entries:
            outputs = entry.get("trigger_outputs", entry.get("outputs", entry.get("sends", []))) or []
            for output in outputs:
                target_name = output.get("target_name", "")
                if target_name and target_name not in object_names:
                    unresolved.append(
                        {
                            "kind": "unresolved_target_name",
                            "source": container_name,
                            "source_object_index": entry.get("source_object_index"),
                            "target_name": target_name,
                            "message_name": output.get("message_name", ""),
                            "severity": "warning",
                        }
                    )
                    output["resolution"] = "unresolved"
                elif target_name:
                    output["resolution"] = "resolved"

    lua_path = events_root / f"{map_id}.lua"
    event_data: dict[str, Any] = {
        "format_version": 1,
        "kind": "mm9_events",
        "source_dat": raw.get("source_dat", ""),
        "source_raw_objects": raw_objects_path.name,
        "coordinate_system": {
            "source": "lithtech_mm9",
            "openyamm_mapping": ["x", "z", "y"],
            "scale": 2.56,
        },
        "generated": {
            "tool": "tools/mm9_import_discovery/generate_mm9_events.py",
            "lua": Path("..") / "events" / lua_path.name,
            "script_ir": Path("..") / "events" / f"{map_id}.script_ir.yml",
        },
        "objects": object_entries,
        "actor_bindings": actor_bindings,
        "start_points": start_points,
        "mechanisms": mechanisms,
        "triggers": triggers,
        "travel_triggers": travel_triggers,
        "interactions": interactions,
        "world_items": scene_data.get("world_items", []) or [],
        "loot_containers": scene_data.get("loot_containers", []) or [],
        "searchable_loot_props": scene_data.get("searchable_loot_props", []) or [],
        "actor_loot_overrides": scene_data.get("actor_loot_overrides", []) or [],
        "spawned_loot_containers": scene_data.get("spawned_loot_containers", []) or [],
        "persistent_item_mechanisms": scene_data.get("persistent_item_mechanisms", []) or [],
        "bindings": bindings,
        "scripts": [
            script_ir_to_yaml(ir, scripts_root)
            for _, ir in sorted(referenced_scripts.items())
        ],
        "dialogue_callbacks": [
            {
                "source_object_index": callback.source_object_index,
                "script_name": callback.source_name,
                "callback_routine": callback.callback_routine,
                "event_id": callback.event_id,
                "use_event_id": callback.use_event_id,
                "found_player_event_id": callback.found_player_event_id,
                "excluded_operations": callback.excluded_operations,
            }
            for callback in dialogue_callbacks
        ],
        "unresolved": unresolved,
        "validation": {
            "raw_object_count": len(raw.get("objects", []) or []),
            "event_object_count": len(object_entries),
            "class_counts": dict(sorted(class_counts.items())),
            "mechanism_count": len(mechanisms),
            "start_point_count": len(start_points),
            "trigger_count": len(triggers),
            "travel_trigger_count": len(travel_triggers),
            "interaction_count": len(interactions),
            "script_count": len(referenced_scripts),
            "unresolved_count": len(unresolved),
        },
    }
    event_data["generated"]["lua"] = event_data["generated"]["lua"].as_posix()
    event_data["generated"]["script_ir"] = event_data["generated"]["script_ir"].as_posix()
    return event_data, referenced_scripts, dialogue_callbacks


def validate_event_data(raw_objects_path: Path, event_data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    raw = load_yaml(raw_objects_path)
    raw_objects = raw.get("objects", []) or []
    event_objects = event_data.get("objects", []) or []
    raw_indices = [int(obj.get("object_index", index)) for index, obj in enumerate(raw_objects) if isinstance(obj, dict)]
    event_indices = [int(obj.get("source_object_index", -1)) for obj in event_objects if isinstance(obj, dict)]
    if sorted(raw_indices) != sorted(event_indices):
        errors.append(f"{raw_objects_path.name}: event objects do not preserve every raw object index")
    by_index = {int(obj.get("source_object_index", -1)): obj for obj in event_objects if isinstance(obj, dict)}
    for raw_index, raw_object in zip(raw_indices, raw_objects):
        event_object = by_index.get(raw_index)
        if event_object is None:
            errors.append(f"{raw_objects_path.name}: missing event object for raw index {raw_index}")
            continue
        raw_property_count = len(raw_object.get("properties", []) or [])
        if int(event_object.get("raw_property_count", -1)) != raw_property_count:
            errors.append(f"{raw_objects_path.name}: property count mismatch for raw object {raw_index}")
        event_property_refs = event_object.get("raw_properties", []) or []
        if len(event_property_refs) != raw_property_count:
            errors.append(f"{raw_objects_path.name}: property refs mismatch for raw object {raw_index}")
    for unresolved in event_data.get("unresolved", []) or []:
        if isinstance(unresolved, dict) and unresolved.get("severity") == "error":
            errors.append(
                f"{raw_objects_path.name}: object {unresolved.get('source_object_index', '?')}: "
                f"{unresolved.get('error', unresolved.get('kind', 'unknown error'))}")
    return errors


def selected_raw_object_paths(maps_root: Path, only_maps: list[str]) -> list[Path]:
    requested = {value.lower() for value in only_maps}
    paths = sorted(maps_root.glob("*.raw_objects.yml"))
    if not requested:
        return paths
    return [path for path in paths if remove_suffix(path.name, ".raw_objects.yml").lower() in requested]


def check_generated_text(path: Path, expected_text: str) -> str | None:
    if not path.exists():
        return f"{path}: generated file is missing"
    actual_text = path.read_text(encoding="utf-8")
    if actual_text != expected_text:
        return f"{path}: generated file is stale"
    return None


def load_mm9_item_id_map(path: Path) -> dict[int, int]:
    if not path.exists():
        raise ValueError(f"MM9 item id map is missing: {path}")

    data = load_yaml(path)
    mappings = data.get("mappings", []) or []
    if not isinstance(mappings, list):
        raise ValueError(f"MM9 item id map has invalid mappings: {path}")

    result: dict[int, int] = {}
    for index, mapping in enumerate(mappings):
        if not isinstance(mapping, dict):
            raise ValueError(f"MM9 item id map entry {index} is not a mapping: {path}")
        raw_item_id = mapping.get("raw_mm9_id")
        item_id = mapping.get("item_id")
        if not isinstance(raw_item_id, int) or raw_item_id <= 0:
            raise ValueError(f"MM9 item id map entry {index} has invalid raw_mm9_id: {path}")
        if not isinstance(item_id, int) or item_id <= 0:
            raise ValueError(f"MM9 item id map entry {index} has invalid item_id: {path}")
        if raw_item_id in result:
            raise ValueError(f"MM9 item id map contains duplicate raw id {raw_item_id}: {path}")
        result[raw_item_id] = item_id
    return result


def mm9_world_common_lua_text(item_id_map: dict[int, int]) -> str:
    lines = [
        "-- generated from worlds/mm9/state/item_ids.yml; do not edit by hand",
        "MM9 = MM9 or {}",
        "MM9.ItemIds = {",
    ]
    for raw_item_id, item_id in sorted(item_id_map.items()):
        lines.append(f"    [{raw_item_id}] = {item_id},")
    lines.extend(["}", ""])
    return "\n".join(lines)


def build_source_sound_index(source_sounds_root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    if not source_sounds_root.is_dir():
        return index

    for path in source_sounds_root.rglob("*.wav"):
        if not path.is_file():
            continue

        relative = path.relative_to(source_sounds_root).as_posix()
        key = normalize_mm9_sound_name(relative).lower()
        index.setdefault(key, path)
        if key.endswith(".wav"):
            index.setdefault(key[:-4], path)
        index.setdefault(path.name.lower(), path)
        index.setdefault(path.stem.lower(), path)

    return index


def referenced_sound_names(event_data: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for mechanism in event_data.get("mechanisms", []) or []:
        if not isinstance(mechanism, dict):
            continue
        for sound in mechanism.get("sounds", []) or []:
            if not isinstance(sound, dict):
                continue
            sound_name = normalize_mm9_sound_name(sound.get("sound_name", ""))
            if sound_name:
                names.add(sound_name)
    for object_entry in event_data.get("objects", []) or []:
        if not isinstance(object_entry, dict):
            continue
        properties = object_entry.get("normalized_properties", {}) or {}
        if not isinstance(properties, dict):
            continue
        greeting_sound = normalize_mm9_sound_name(properties.get("GreetingSound", ""))
        if greeting_sound:
            names.add(greeting_sound)
    return names


def find_source_sound_path(source_sound_index: dict[str, Path], sound_name: str) -> Path | None:
    key = normalize_mm9_sound_name(sound_name).lower()
    if not key:
        return None

    candidates = [key]
    if key.endswith(".wav"):
        candidates.append(key[:-4])
    path_name = Path(key).name
    if path_name != key:
        candidates.append(path_name)
        if path_name.endswith(".wav"):
            candidates.append(path_name[:-4])
    alias = MM9_SOUND_SOURCE_ALIASES.get(key)
    if alias is not None:
        candidates.append(alias)
        if alias.endswith(".wav"):
            candidates.append(alias[:-4])

    for candidate in candidates:
        source_path = source_sound_index.get(candidate)
        if source_path is not None:
            return source_path
    return None


def synthetic_note_frequency(note_name: str, sharp: str, octave_text: str) -> float:
    semitones = {
        "c": -9,
        "d": -7,
        "e": -5,
        "f": -4,
        "g": -2,
        "a": 0,
        "b": 2,
    }
    octave = int(octave_text) - 1
    half_steps = semitones[note_name] + (1 if sharp else 0) + octave * 12
    return 440.0 * (2.0 ** (half_steps / 12.0))


def synthetic_mm9_sound_bytes(sound_name: str) -> bytes | None:
    key = normalize_mm9_sound_name(sound_name).lower()
    match = MM9_SYNTHETIC_NOTE_PATTERN.match(key)
    if match is None:
        return None

    frequency = synthetic_note_frequency(match.group(1), match.group(2), match.group(3))
    sample_rate = 22050
    duration_seconds = 0.45
    sample_count = int(sample_rate * duration_seconds)
    fade_samples = max(1, int(sample_rate * 0.025))
    amplitude = 11000

    payload = bytearray()
    for index in range(sample_count):
        envelope = 1.0
        if index < fade_samples:
            envelope = index / fade_samples
        elif index >= sample_count - fade_samples:
            envelope = (sample_count - index - 1) / fade_samples
        sample = int(round(math.sin((2.0 * math.pi * frequency * index) / sample_rate) * amplitude * envelope))
        payload.extend(sample.to_bytes(2, byteorder="little", signed=True))

    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(bytes(payload))
    return output.getvalue()


def copy_referenced_sounds(
    event_data: dict[str, Any],
    source_sound_index: dict[str, Path],
    audio_root: Path,
) -> tuple[int, int]:
    copied = 0
    missing = 0

    for sound_name in sorted(referenced_sound_names(event_data)):
        key = sound_name.lower()
        destination = audio_root / key
        source_path = find_source_sound_path(source_sound_index, sound_name)
        if source_path is None:
            source_bytes = synthetic_mm9_sound_bytes(sound_name)
            if source_bytes is None:
                if destination.is_file():
                    continue
                missing += 1
                continue
        else:
            source_bytes = source_path.read_bytes()

        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists() or source_bytes != destination.read_bytes():
            destination.write_bytes(source_bytes)
            copied += 1

    return copied, missing


def run_generation(args: argparse.Namespace) -> int:
    raw_paths = selected_raw_object_paths(args.maps_root, args.only_map)
    world_common_only = getattr(args, "world_common_only", False)
    if not raw_paths and not world_common_only:
        print("no raw object sidecars selected", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    generated = 0
    checked = 0
    sounds_copied = 0
    sounds_missing = 0
    try:
        item_id_map = load_mm9_item_id_map(args.item_id_map)
    except ValueError as exception:
        print(str(exception), file=sys.stderr)
        return 1

    world_common_lua_path = args.events_root.parent / "common" / "world_common.lua"
    world_common_lua = mm9_world_common_lua_text(item_id_map)
    if args.check_idempotent:
        check_error = check_generated_text(world_common_lua_path, world_common_lua)
        if check_error is not None:
            all_errors.append(check_error)
    elif not args.validate_only:
        world_common_lua_path.parent.mkdir(parents=True, exist_ok=True)
        world_common_lua_path.write_text(world_common_lua, encoding="utf-8")
        print(f"wrote {world_common_lua_path}")

    if world_common_only:
        if all_errors:
            for error in all_errors:
                print(error, file=sys.stderr)
            return 1
        print("mm9 world common item mapping generated")
        return 0

    source_sound_index = build_source_sound_index(args.source_sounds_root) if args.audio_root is not None else {}
    for raw_path in raw_paths:
        event_data, script_irs, dialogue_callbacks = build_events_for_map(
            raw_path,
            args.scripts_root,
            args.events_root)
        errors = validate_event_data(raw_path, event_data)
        all_errors.extend(errors)
        if errors and (args.validate_only or args.check_idempotent):
            continue
        map_id = remove_suffix(raw_path.name, ".raw_objects.yml")
        events_path = args.maps_root / f"{map_id}.events.yml"
        lua_path = args.events_root / f"{map_id}.lua"
        script_ir_path = args.events_root / f"{map_id}.script_ir.yml"
        if args.check_idempotent:
            expected_files = [
                (events_path, yaml_text(event_data)),
                (lua_path, map_lua_text(map_id, script_irs, event_data, dialogue_callbacks)),
                (script_ir_path, yaml_text(map_script_ir_data(map_id, args.scripts_root, script_irs))),
            ]
            for path, expected_text in expected_files:
                check_error = check_generated_text(path, expected_text)
                if check_error is not None:
                    all_errors.append(check_error)
            checked += 1
        elif not args.validate_only:
            events_path = args.maps_root / f"{map_id}.events.yml"
            write_yaml(events_path, event_data)
            write_map_lua(lua_path, map_id, script_irs, event_data, dialogue_callbacks)
            write_map_script_ir(
                script_ir_path,
                map_id,
                args.scripts_root,
                script_irs,
            )
            print(f"wrote {events_path}")
            print(f"wrote {lua_path}")
            print(f"wrote {script_ir_path}")
            if args.audio_root is not None:
                copied, missing = copy_referenced_sounds(event_data, source_sound_index, args.audio_root)
                sounds_copied += copied
                sounds_missing += missing
            generated += 1

    if all_errors:
        for error in all_errors:
            print(error, file=sys.stderr)
        return 1

    sound_summary = ""
    if args.audio_root is not None:
        sound_summary = f" sounds_copied={sounds_copied} sounds_missing={sounds_missing}"
    print(f"mm9 events generated={generated} checked={checked} validated={len(raw_paths)}{sound_summary}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate lossless MM9 map event sidecars and generated Lua.")
    parser.add_argument("--maps-root", type=Path, default=Path("assets_editor_dev/worlds/mm9/maps"))
    parser.add_argument("--scripts-root", type=Path, default=Path("mm9/extracted/SCRIPTS/SCRIPTS"))
    parser.add_argument("--events-root", type=Path, default=Path("assets_dev/worlds/mm9/events/maps"))
    parser.add_argument("--source-sounds-root", type=Path, default=Path("mm9/extracted/SOUNDS/SOUNDS"))
    parser.add_argument(
        "--item-id-map",
        type=Path,
        default=Path("assets_dev/worlds/mm9/state/item_ids.yml"))
    parser.add_argument("--audio-root", type=Path)
    parser.add_argument("--only-map", action="append", default=[])
    parser.add_argument(
        "--world-common-only",
        action="store_true",
        help="Regenerate only events/common/world_common.lua from the current item id map.",
    )
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument(
        "--check-idempotent",
        action="store_true",
        help="Validate that regenerated event, Lua, and script-IR outputs match the existing files byte-for-byte.",
    )
    args = parser.parse_args()
    if args.validate_only and args.check_idempotent:
        parser.error("--validate-only and --check-idempotent are mutually exclusive")
    return run_generation(args)


if __name__ == "__main__":
    raise SystemExit(main())
