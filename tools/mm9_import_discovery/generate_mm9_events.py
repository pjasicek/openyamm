#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


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


def map_lua_text(map_id: str, script_irs: dict[str, ScriptIr]) -> str:
    lines: list[str] = [
        "-- generated from MM9 event sidecars; do not edit by hand",
        "local map = {}",
        f"map.map_id = {lua_string(map_id)}",
        "map.scripts = {}",
        "",
    ]
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
            "return map",
            "",
        ]
    )
    return "\n".join(lines)


def write_map_lua(path: Path, map_id: str, script_irs: dict[str, ScriptIr]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(map_lua_text(map_id, script_irs), encoding="utf-8")


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
) -> tuple[dict[str, Any], dict[str, ScriptIr]]:
    raw = load_yaml(raw_objects_path)
    map_id = remove_suffix(raw_objects_path.name, ".raw_objects.yml")
    script_index = build_script_index(scripts_root)
    scene_bindings = build_scene_model_instance_bindings(scene_path or raw_objects_path.with_name(f"{map_id}.scene.yml"))
    resolved_dat_world_path = dat_world_path or raw_objects_path.with_name(f"{map_id}.dat_world.yml")
    world_model_polygon_groups = load_world_model_polygon_groups(resolved_dat_world_path)
    bmodel_bindings = build_mm9_bmodel_bindings(metadata_path or raw_objects_path.with_name(f"{map_id}.mm9.yml"))
    for binding_targets in bmodel_bindings.values():
        for target in binding_targets:
            attach_source_polygon_group(target, world_model_polygon_groups)
    movable_world_models = load_movable_world_models(resolved_dat_world_path)
    raw_objects = raw.get("objects", []) or []
    exact_world_model_claims = collect_exact_world_model_claims(raw_objects, bmodel_bindings)

    object_names: set[str] = set()
    object_entries: list[dict[str, Any]] = []
    mechanisms: list[dict[str, Any]] = []
    triggers: list[dict[str, Any]] = []
    interactions: list[dict[str, Any]] = []
    bindings: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    referenced_scripts: dict[str, ScriptIr] = {}
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

        classifications: list[str] = []
        if object_class in MECHANISM_CLASS_KINDS:
            classifications.append("mechanism")
        if object_class == "Trigger":
            classifications.append("trigger")
        if object_class in SCRIPTED_INTERACTION_CLASSES or script_name:
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
            mechanisms.append(
                {
                    "mechanism_id": f"{object_id}:mechanism",
                    "object_id": object_id,
                    "source_object_index": object_index,
                    "source_class": object_class,
                    "source_name": object_name,
                    "mechanism": mechanism_motion(values, MECHANISM_CLASS_KINDS[object_class]),
                    "activation": activation(values),
                    "trigger_outputs": outputs,
                }
            )

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

        if object_class in SCRIPTED_INTERACTION_CLASSES or script_name or outputs:
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
        "mechanisms": mechanisms,
        "triggers": triggers,
        "interactions": interactions,
        "bindings": bindings,
        "scripts": [
            script_ir_to_yaml(ir, scripts_root)
            for _, ir in sorted(referenced_scripts.items())
        ],
        "unresolved": unresolved,
        "validation": {
            "raw_object_count": len(raw.get("objects", []) or []),
            "event_object_count": len(object_entries),
            "class_counts": dict(sorted(class_counts.items())),
            "mechanism_count": len(mechanisms),
            "trigger_count": len(triggers),
            "interaction_count": len(interactions),
            "script_count": len(referenced_scripts),
            "unresolved_count": len(unresolved),
        },
    }
    event_data["generated"]["lua"] = event_data["generated"]["lua"].as_posix()
    event_data["generated"]["script_ir"] = event_data["generated"]["script_ir"].as_posix()
    return event_data, referenced_scripts


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


def run_generation(args: argparse.Namespace) -> int:
    raw_paths = selected_raw_object_paths(args.maps_root, args.only_map)
    if not raw_paths:
        print("no raw object sidecars selected", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    generated = 0
    checked = 0
    for raw_path in raw_paths:
        event_data, script_irs = build_events_for_map(raw_path, args.scripts_root, args.events_root)
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
                (lua_path, map_lua_text(map_id, script_irs)),
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
            write_map_lua(lua_path, map_id, script_irs)
            write_map_script_ir(
                script_ir_path,
                map_id,
                args.scripts_root,
                script_irs,
            )
            print(f"wrote {events_path}")
            print(f"wrote {lua_path}")
            print(f"wrote {script_ir_path}")
            generated += 1

    if all_errors:
        for error in all_errors:
            print(error, file=sys.stderr)
        return 1

    print(f"mm9 events generated={generated} checked={checked} validated={len(raw_paths)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate lossless MM9 map event sidecars and generated Lua.")
    parser.add_argument("--maps-root", type=Path, default=Path("assets_dev/worlds/mm9/maps"))
    parser.add_argument("--scripts-root", type=Path, default=Path("mm9/extracted/SCRIPTS/SCRIPTS"))
    parser.add_argument("--events-root", type=Path, default=Path("assets_dev/worlds/mm9/events"))
    parser.add_argument("--only-map", action="append", default=[])
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
