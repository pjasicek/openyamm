#!/usr/bin/env python3
"""Compile selected immutable MM9 FXF recipes into the shared typed effect schema."""

from __future__ import annotations

import argparse
import hashlib
import math
from pathlib import Path
import sys

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "re_mm8" / "mm9_vfx"))

from inspect_assets import read_fxf  # noqa: E402


EMISSION_SHAPES = ("point", "plane", "sphere", "plane_in", "plane_out", "cone", "circle")
MM9_TO_OPENYAMM_SCALE = 2.56
# Recipes whose emitters MM9 anchors to a body node (UpdatePos 2-9: hands, feet, head, user nodes) that the rework's
# scripts play anyway (DoClientFX in Wizard's Lab and Dragon Stadium; devdocs/mm9_rework/scr_audit/client_fx.md). OpenYAMM
# effects have no body anchors: their anchored emitters emit at the effect's origin, which the caller places (the
# shooter or the apprentice's chest for the dots, the dragon's snout for its smoke).
ORIGIN_ANCHOR_RECIPES = frozenset({"bluedots", "greenyeldots", "dragon smoke"})


def body_anchored(group: dict) -> bool:
    return any(int(properties(key).get("UpdatePos", 0)) >= 2 for key in group["keys"])


def world_vector(value: list[float]) -> list[float]:
    return [
        value[0] * MM9_TO_OPENYAMM_SCALE,
        value[2] * MM9_TO_OPENYAMM_SCALE,
        value[1] * MM9_TO_OPENYAMM_SCALE,
    ]


def world_direction(value: list[float]) -> list[float]:
    return [value[0], value[2], value[1]]


def world_rotation(value: list[float]) -> list[float]:
    return [-value[0], -value[2], -value[1]]


def vector_cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def vector_unit(value: list[float], fallback: list[float]) -> list[float]:
    value_length = math.sqrt(sum(component * component for component in value))
    return [component / value_length for component in value] if value_length > 1.0e-9 else fallback.copy()


def sprite_orientation(props: dict[str, object], fixed_sprite: bool) -> dict:
    facing = int(props.get("Facing", 0))
    if facing == 0:
        return {"alignment": "camera_facing"}

    if fixed_sprite:
        direction = props.get("Normal", [0.0, 0.0, 1.0])
    elif facing == 3:
        direction = props.get("FacingDir", [0.0, 0.0, 1.0])
    else:
        direction = props.get("PlaneDir", props.get("Normal", [0.0, 0.0, 1.0]))
    forward = vector_unit(direction, [0.0, 0.0, 1.0])
    reference = [1.0, 0.0, 0.0] if abs(forward[1]) > 0.99 else [0.0, 1.0, 0.0]
    right = vector_unit(vector_cross(reference, forward), [1.0, 0.0, 0.0])
    up = vector_cross(forward, right)
    return {
        "alignment": "world_plane",
        "plane_right": world_direction(right),
        "plane_up": world_direction(up),
    }


def normalized_reference(value: str) -> str:
    return value.split("|", 1)[-1].replace("\\", "/").lower()


def properties(key: dict) -> dict[str, object]:
    result: dict[str, object] = {"Ck": [], "Sk": [], "Mk": []}
    for prop in key["properties"]:
        if prop["name"] in ("Ck", "Sk", "Mk"):
            result[prop["name"]].append(prop["value"])
        else:
            result[prop["name"]] = prop.get("numeric_selection", prop["value"])
    result["Ck"].sort(key=lambda entry: entry["time"])
    result["Sk"].sort(key=lambda entry: entry[0])
    result["Mk"].sort(key=lambda entry: entry[0])
    return result


def binding_resource(bindings: dict[str, dict], value: str, expected_kind: str) -> str:
    legacy = normalized_reference(value)
    binding = bindings.get(legacy)
    if binding is None:
        raise ValueError(f"no explicit resource binding for {legacy}")
    if binding["kind"] != expected_kind:
        raise ValueError(f"binding for {legacy} is {binding['kind']}, expected {expected_kind}")
    if binding["status"] != "bound":
        raise ValueError(f"resource {legacy} is {binding['status']}")
    return binding["resource"]


def component_link(key: dict) -> dict:
    if not key["linked"]:
        return {}
    if not key["linked_node"]:
        raise ValueError(f"linked component {key['id']} has no linked node")
    return {
        "linked_component_id": key["linked_id"],
        "linked_node": key["linked_node"],
    }


def compile_sprite_system(key: dict, bindings: dict[str, dict]) -> dict:
    props = properties(key)
    emission = int(props.get("EmissionType", 0))
    if emission < 0 or emission >= len(EMISSION_SHAPES):
        raise ValueError(f"component {key['id']} has unknown native emission opcode {emission}")
    color_keys = []
    for entry in props["Ck"]:
        red, green, blue, transparency = entry["rgb_transparency"]
        color_keys.append(
            {
                "time": entry["time"],
                "rgb": [red, green, blue],
                "transparency": transparency,
            }
        )
    scale_keys = [
        {"time": entry[0], "value": entry[1] * MM9_TO_OPENYAMM_SCALE}
        for entry in props["Sk"]
    ]
    motion_keys = [{"time": entry[0], "value": world_vector(entry[1:4])} for entry in props["Mk"]]
    return {
        "type": "sprite_system",
        "id": key["id"],
        "start_seconds": key["start"],
        "end_seconds": key["end"],
        "repeat_count": key["repeat"],
        "sprite_resource": binding_resource(bindings, props["Sprite"], "sprite"),
        "sprites_per_emission": int(props.get("SpritesPerEmission", 1)),
        "emission_interval_seconds": float(props.get("EmissionInterval", 0.0)),
        "particle_lifetime_seconds": float(props.get("SpriteLifespan", 1.0)),
        "emission_shape": EMISSION_SHAPES[emission],
        "radius": float(props.get("Radius", 0.0)) * MM9_TO_OPENYAMM_SCALE,
        "plane_direction": world_direction(props.get("PlaneDir", [0.0, 1.0, 0.0])),
        "velocity": float(props.get("Velocity", 0.0)) * MM9_TO_OPENYAMM_SCALE,
        "wind_direction": world_vector(props.get("WindDir", [0.0, 0.0, 0.0])),
        "wind_amount": float(props.get("WindAmount", 0.0)),
        "offset": world_vector(props.get("Offset", [0.0, 0.0, 0.0])),
        "rotation_per_tick": world_rotation(props.get("RotateAdd", [0.0, 0.0, 0.0])),
        "stretch_u": float(props.get("StretchU", 1.0)),
        "stretch_v": float(props.get("StretchV", 1.0)),
        "blend": "additive" if int(props.get("AType", 0)) == 1 else "alpha",
        "particle_space": "world",
        **sprite_orientation(props, fixed_sprite=False),
        "color_keys": color_keys,
        "scale_keys": scale_keys,
        "motion_keys": motion_keys,
        **component_link(key),
    }


def compile_model_path(key: dict, bindings: dict[str, dict]) -> dict:
    props = properties(key)
    model_reference = normalized_reference(props["Model"])
    return {
        "type": "model_path",
        "id": key["id"],
        "start_seconds": key["start"],
        "end_seconds": key["end"],
        "repeat_count": key["repeat"],
        "model_resource": binding_resource(bindings, props["Model"], "model"),
        "animation_clip": Path(model_reference).stem,
        "offset": world_vector(props.get("Offset", [0.0, 0.0, 0.0])),
        "visible": not str(props.get("Skin", "")).endswith("|..."),
        **component_link(key),
    }


def compile_null(key: dict) -> dict:
    props = properties(key)
    return {
        "type": "null_transform",
        "id": key["id"],
        "start_seconds": key["start"],
        "end_seconds": key["end"],
        "repeat_count": key["repeat"],
        "offset": world_vector(props.get("Offset", [0.0, 0.0, 0.0])),
        "rotation_per_tick": world_rotation(props.get("RotateAdd", [0.0, 0.0, 0.0])),
        "scale_keys": [
            {"time": entry[0], "value": entry[1] * MM9_TO_OPENYAMM_SCALE}
            for entry in props["Sk"]
        ],
        "motion_keys": [
            {"time": entry[0], "value": world_vector(entry[1:4])}
            for entry in props["Mk"]
        ],
        **component_link(key),
    }


def compile_sprite(key: dict, bindings: dict[str, dict]) -> dict:
    props = properties(key)
    red_keys = []
    for entry in props["Ck"]:
        red, green, blue, transparency = entry["rgb_transparency"]
        red_keys.append(
            {
                "time": entry["time"],
                "rgb": [red, green, blue],
                "transparency": transparency,
            }
        )
    return {
        "type": "sprite",
        "id": key["id"],
        "start_seconds": key["start"],
        "end_seconds": key["end"],
        "repeat_count": key["repeat"],
        "sprite_resource": binding_resource(bindings, props["Sprite"], "sprite"),
        "offset": world_vector(props.get("Offset", [0.0, 0.0, 0.0])),
        "stretch_u": 1.0,
        "stretch_v": 1.0,
        "blend": "additive",
        **sprite_orientation(props, fixed_sprite=True),
        "color_keys": red_keys,
        "scale_keys": [
            {"time": entry[0], "value": entry[1] * MM9_TO_OPENYAMM_SCALE}
            for entry in props["Sk"]
        ],
        "motion_keys": [
            {"time": entry[0], "value": world_vector(entry[1:4])}
            for entry in props["Mk"]
        ],
        **component_link(key),
    }


def compile_sound(key: dict, bindings: dict[str, dict]) -> dict:
    props = properties(key)
    return {
        "type": "sound",
        "id": key["id"],
        "start_seconds": key["start"],
        "end_seconds": key["end"],
        "sound_resource": binding_resource(bindings, props["Sound"], "sound"),
        "spatial": int(props.get("PlayLocal", 0)) == 0,
        "loop": int(props.get("Loop", 0)) != 0,
        "volume": float(props.get("Volume", 100)) / 100.0,
        "pitch": float(props.get("PitchShift", 1.0)),
        "inner_radius": float(props.get("InnerRadius", 100.0)) * MM9_TO_OPENYAMM_SCALE,
        "outer_radius": float(props.get("OuterRadius", 500.0)) * MM9_TO_OPENYAMM_SCALE,
        "follows_emitter": int(props.get("UpdatePos", 0)) != 0,
    }


def effect_id(name: str) -> str:
    normalized = name.removeprefix("spell-").replace(" ", "_")
    return f"mm9:{normalized}"


def hardcoded_melee_blood_effect(bindings: dict[str, dict]) -> dict:
    """Compile the verified non-FXF flesh-contact feedback into the shared effect schema."""
    return {
        "id": "mm9:melee_blood",
        "source_name": "hardcoded melee-contact flesh selector",
        "source_evidence": "re_mm8/mm9_vfx/MELEE_HIT_EFFECTS.md",
        "duration_seconds": 1.0,
        "compatibility_profile": "mm9_native_60hz",
        "support": "supported_approximation",
        "capabilities": ["sprite", "sprite_system"],
        "components": [
            {
                "type": "sprite",
                "id": 1001,
                "start_seconds": 0.0,
                "end_seconds": 0.1,
                "repeat_count": 1,
                "sprite_resource": binding_resource(
                    bindings, "sprites/bloodhit1.spr", "sprite"
                ),
                "offset": [0.0, 0.0, 4.0 * MM9_TO_OPENYAMM_SCALE],
                "stretch_u": 1.0,
                "stretch_v": 1.0,
                "blend": "alpha",
                "alignment": "world_plane",
                "plane_right": [1.0, 0.0, 0.0],
                "plane_up": [0.0, 1.0, 0.0],
                "color_keys": [
                    {"time": 0.0, "rgb": [255, 255, 255], "transparency": 0},
                    {"time": 1.0, "rgb": [255, 255, 255], "transparency": 0},
                ],
                "scale_keys": [
                    {"time": 0.0, "value": MM9_TO_OPENYAMM_SCALE},
                    {"time": 1.0, "value": MM9_TO_OPENYAMM_SCALE},
                ],
                "motion_keys": [],
            },
            {
                "type": "sprite_system",
                "id": 1002,
                "start_seconds": 0.0,
                # One 60 Hz-compatible batch: it emits at 2/60 s, then the window closes.
                "end_seconds": 0.034,
                "repeat_count": 1,
                "sprite_resource": binding_resource(
                    bindings, "sprites/bloodspray1.spr", "sprite"
                ),
                "sprites_per_emission": 10,
                "emission_interval_seconds": 0.019,
                "particle_lifetime_seconds": 1.0,
                "emission_shape": "cone",
                "radius": 100.0,
                "plane_direction": [0.0, 0.0, 1.0],
                "velocity": 100.0 * MM9_TO_OPENYAMM_SCALE,
                "wind_direction": [0.0, 0.0, 0.0],
                "wind_amount": 0.0,
                "offset": [0.0, 0.0, 0.0],
                "rotation_per_tick": [0.0, 0.0, 0.0],
                "stretch_u": 1.0,
                "stretch_v": 1.0,
                "blend": "alpha",
                "particle_space": "world",
                "alignment": "camera_facing",
                "color_keys": [
                    {"time": 0.0, "rgb": [255, 255, 255], "transparency": 0},
                    {"time": 1.0, "rgb": [255, 255, 255], "transparency": 255},
                ],
                "scale_keys": [
                    {"time": 0.0, "value": MM9_TO_OPENYAMM_SCALE},
                    {"time": 1.0, "value": MM9_TO_OPENYAMM_SCALE},
                ],
                "motion_keys": [],
            },
        ],
    }


def compile_group(group: dict, bindings: dict[str, dict]) -> dict:
    components = []
    for key in group["keys"]:
        component_type = key["component_ref"].split(";", 1)[0]
        if component_type == "SpriteSystem":
            components.append(compile_sprite_system(key, bindings))
        elif component_type == "Model":
            components.append(compile_model_path(key, bindings))
        elif component_type == "Sprite":
            components.append(compile_sprite(key, bindings))
        elif component_type == "PlaySound":
            components.append(compile_sound(key, bindings))
        elif component_type == "Null":
            components.append(compile_null(key))
        else:
            raise ValueError(
                f"effect {group['name']} component {key['id']} uses unsupported type {component_type}"
            )
    source_phase_seconds = group["phase_ms"] / 1000.0
    duration_seconds = max(
        [source_phase_seconds, *(float(key["end"]) for key in group["keys"])],
    )
    anchor_fallback = {}
    if body_anchored(group):
        if group["name"] not in ORIGIN_ANCHOR_RECIPES:
            raise ValueError(f"effect {group['name']} anchors emitters to body nodes")
        anchor_fallback = {"anchor_fallback": "origin"}
    return {
        "id": effect_id(group["name"]),
        "source_name": group["name"],
        "source_offset": group["offset"],
        "source_phase_seconds": source_phase_seconds,
        "duration_seconds": duration_seconds,
        "compatibility_profile": "mm9_native_60hz",
        "support": "supported",
        **anchor_fallback,
        "capabilities": sorted({component["type"] for component in components}),
        "components": components,
    }


def compile_library(fxf_path: Path, manifest_path: Path, effect_names: list[str]) -> dict:
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    bindings = {entry["legacy"]: entry for entry in manifest["bindings"]}
    groups = {group["name"]: group for group in read_fxf(fxf_path)}
    unknown = sorted(set(effect_names) - groups.keys())
    if unknown:
        raise ValueError(f"unknown FXF effect names: {unknown}")
    source_bytes = fxf_path.read_bytes()
    return {
        "schema": "openyamm.effectLibrary.v1",
        "source": {
            "recipe": "engine/effects/mm9/source/spells.fxf",
            "sha256": hashlib.sha256(source_bytes).hexdigest(),
            "resource_bindings": "engine/effects/mm9/resource_bindings.yml",
            "coordinate_policy": "MM9 Y-up to OpenYAMM Z-up (X,Z,Y), source units multiplied by 2.56",
        },
        "effects": [
            *(compile_group(groups[name], bindings) for name in effect_names),
            hardcoded_melee_blood_effect(bindings),
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fxf", type=Path, required=True)
    parser.add_argument("--bindings", type=Path, required=True)
    parser.add_argument("--effect", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    library = compile_library(args.fxf, args.bindings, args.effect)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(library, sort_keys=False), encoding="utf-8")
    print(yaml.safe_dump({"output": str(args.output), "effects": len(library["effects"])}, sort_keys=False).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
