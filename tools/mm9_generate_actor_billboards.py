#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import struct
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from PIL import Image, ImageChops, ImageDraw, ImageStat


SCHEMA = "openyamm.mm9.scripted_billboard_visual.v1"
TOOL_VERSION = "0.1"
DEFAULT_OUTPUT_ROOT = Path("assets_dev/worlds/mm9/rendering/scripted_billboards")
DEFAULT_REGISTRY = Path("assets_dev/worlds/mm9/models/model_registry.yml")
DEFAULT_MAP_ROOT = Path("assets_dev/worlds/mm9/maps")
DEFAULT_WORLD_ROOT = Path("assets_dev/worlds/mm9")
ANGLE_NAMES = ["front", "front_right", "right", "back_right", "back", "back_left", "left", "front_left"]
SEMANTIC_FALLBACKS = {
    "idle": "idle",
    "stand": "idle",
    "walk": "walk",
    "run": "run",
    "fly": "fly",
    "death": "death",
    "die": "death",
    "pain": "pain",
    "hit": "pain",
    "attack": "melee_attack",
    "rattack": "ranged_attack",
    "wingattack": "special_attack",
    "hang": "idle",
    "coffin": "scripted",
}


@dataclass
class VariantInfo:
    model_id: str
    variant_id: str
    source_model: str
    source_skins: list[str]
    model_asset: str
    model_asset_path: Path
    actor_rows: list[dict[str, Any]] = field(default_factory=list)
    animations: list[dict[str, Any]] = field(default_factory=list)
    bounds_min: list[float] | None = None
    bounds_max: list[float] | None = None


@dataclass
class PlacedObjectRef:
    map_id: str
    object_id: str
    source_object_index: int
    source_class: str
    source_name: str
    source_model: str
    source_skins: list[str]
    model_asset: str
    script_name: str
    script_params: str


@dataclass
class ResolvedVisual:
    variant: VariantInfo
    used_by: list[PlacedObjectRef] = field(default_factory=list)


@dataclass
class FrameDiagnostic:
    path: str
    width: int = 0
    height: int = 0
    nontransparent_pixels: int = 0
    fully_transparent: bool = False
    blank: bool = False
    error: str = ""
    transparent_bbox: list[int] | None = None
    anchor_x: float | None = None
    anchor_y: float | None = None
    original_width: int | None = None
    original_height: int | None = None
    trim_bbox: list[int] | None = None


def normalize_ref(value: str) -> str:
    return value.replace("\\", "/").strip().lower()


def normalize_model_ref(value: str) -> str:
    normalized = normalize_ref(value)
    if not normalized:
        return ""
    if "/" not in normalized:
        normalized = "models/" + normalized
    return normalized


def normalize_skin_refs(value: str) -> list[str]:
    refs = []
    for part in value.replace("\\", "/").split(";"):
        normalized = part.strip().lower()
        if not normalized:
            continue
        if "/" not in normalized:
            normalized = "skins/" + normalized
        refs.append(normalized)
    return refs


def slug(value: str) -> str:
    output = []
    previous_underscore = False
    for char in value.lower():
        if char.isalnum():
            output.append(char)
            previous_underscore = False
        elif not previous_underscore:
            output.append("_")
            previous_underscore = True
    return "".join(output).strip("_")


def actor_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower()).rstrip("0123456789")


def type_picture_keys(value: str) -> list[str]:
    key = actor_key(value)
    if not key:
        return []
    keys = [key]
    if key.startswith("peasant"):
        keys.append(key[len("peasant"):])
    for prefix in ("peasant", ""):
        candidate = key[len(prefix):] if prefix and key.startswith(prefix) else key
        if candidate and candidate[-1:] in ("a", "b", "c", "d"):
            keys.append(candidate[:-1])
    return [item for index, item in enumerate(keys) if item and item not in keys[:index]]


def source_class_type_picture_keys(value: str) -> list[str]:
    source_key = actor_key(value)
    if not source_key:
        return []

    role_codes = {
        "commoner": "a",
        "town": "b",
        "shopkeeper": "c",
        "prisoner": "d",
    }

    role_code = ""
    remainder = source_key
    for role, code in role_codes.items():
        if source_key.startswith(role):
            role_code = code
            remainder = source_key[len(role):]
            break

    race = ""
    race_remainder = remainder
    for prefix, value in (
        ("human2", "human2"),
        ("human", "human1"),
        ("elf", "elf"),
        ("dwarf", "dwarf"),
        ("halforc", "halforc"),
    ):
        if race_remainder.startswith(prefix):
            race = value
            race_remainder = race_remainder[len(prefix):]
            break

    gender = ""
    gender_remainder = race_remainder
    for prefix in ("female", "male"):
        if gender_remainder.startswith(prefix):
            gender = prefix
            gender_remainder = gender_remainder[len(prefix):]
            break

    if not race or not gender or len(gender_remainder) != 1 or gender_remainder not in "abcd":
        return []

    variant_code = gender_remainder
    keys = []
    if race == "halforc":
        keys.append(f"peasant{race}{gender}{variant_code}")
    if role_code:
        keys.append(f"peasant{race}{gender}{role_code}{variant_code}")
    keys.extend(key[len("peasant"):] for key in list(keys))
    return [item for index, item in enumerate(keys) if item and item not in keys[:index]]


def visual_id_for_variant(variant_id: str) -> str:
    value = slug(variant_id)
    if value.startswith("mm9_"):
        return value
    return "mm9_" + value


def read_glb_json(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 20:
        raise ValueError(f"{path} is too small to be a GLB")
    magic, version, total_length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67:
        raise ValueError(f"{path} does not start with GLB magic")
    if version != 2:
        raise ValueError(f"{path} has unsupported GLB version {version}")
    if total_length > len(data):
        raise ValueError(f"{path} header length exceeds file length")
    offset = 12
    while offset + 8 <= len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset : offset + chunk_length]
        offset += chunk_length
        if chunk_type == 0x4E4F534A:
            return json.loads(chunk.rstrip(b" \t\r\n\0").decode("utf-8"))
    raise ValueError(f"{path} has no JSON chunk")


def accessor_duration(gltf: dict[str, Any], accessor_index: int | None) -> float:
    if accessor_index is None:
        return 0.0
    accessors = gltf.get("accessors") or []
    if accessor_index < 0 or accessor_index >= len(accessors):
        return 0.0
    accessor = accessors[accessor_index]
    maximum = accessor.get("max") or []
    if not maximum:
        return 0.0
    try:
        return float(maximum[0])
    except (TypeError, ValueError):
        return 0.0


def collect_glb_metadata(path: Path) -> tuple[list[dict[str, Any]], list[float] | None, list[float] | None]:
    gltf = read_glb_json(path)
    animations = []
    for index, animation in enumerate(gltf.get("animations") or []):
        duration = 0.0
        for sampler in animation.get("samplers") or []:
            duration = max(duration, accessor_duration(gltf, sampler.get("input")))
        name = str(animation.get("name") or f"animation_{index}")
        animations.append({"name": name, "duration_seconds": round(duration, 4)})

    bounds_min: list[float] | None = None
    bounds_max: list[float] | None = None
    for accessor in gltf.get("accessors") or []:
        if accessor.get("type") != "VEC3" or "min" not in accessor or "max" not in accessor:
            continue
        current_min = [float(value) for value in accessor["min"][:3]]
        current_max = [float(value) for value in accessor["max"][:3]]
        if bounds_min is None:
            bounds_min = current_min
            bounds_max = current_max
        else:
            bounds_min = [min(bounds_min[i], current_min[i]) for i in range(3)]
            bounds_max = [max(bounds_max[i], current_max[i]) for i in range(3)]
    return animations, bounds_min, bounds_max


def populate_variant_metadata(variant: VariantInfo) -> None:
    if variant.animations or variant.bounds_min is not None or variant.bounds_max is not None:
        return
    if not variant.model_asset_path.exists():
        variant.animations = [
            {
                "name": "idle",
                "duration_seconds": 0.0,
                "warning": f"missing GLB: {variant.model_asset_path.as_posix()}",
            }
        ]
        return
    try:
        animations, bounds_min, bounds_max = collect_glb_metadata(variant.model_asset_path)
        variant.animations = animations
        variant.bounds_min = bounds_min
        variant.bounds_max = bounds_max
    except ValueError as exc:
        variant.animations = [{"name": "idle", "duration_seconds": 0.0, "warning": str(exc)}]


def load_registry(path: Path, world_root: Path) -> list[VariantInfo]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    variants: list[VariantInfo] = []
    for model in data.get("models") or []:
        roles = model.get("roles") or []
        is_actor_model = model.get("kind") == "actor_model" or "actor_model" in roles
        if not is_actor_model:
            continue
        source_model = normalize_model_ref(str(model.get("source_model") or ""))
        model_id = str(model.get("model_id") or "")
        model_asset = str(model.get("model_asset") or "")
        bindings = model.get("skin_bindings")
        if bindings is None and model.get("variants") is not None:
            bindings = model.get("variants")
        if not bindings:
            bindings = [{"id": model_id, "source_skins": model.get("source_skins") or [], "actor_rows": []}]
        for variant in bindings or []:
            if not isinstance(variant, dict):
                continue
            variant_asset = str(variant.get("model_asset") or model_asset)
            if not variant_asset:
                continue
            model_asset_path = world_root / variant_asset
            variants.append(
                VariantInfo(
                    model_id=model_id,
                    variant_id=str(variant.get("id") or ""),
                    source_model=source_model,
                    source_skins=[normalize_ref(str(skin)) for skin in (variant.get("source_skins") or [])],
                    model_asset=variant_asset,
                    model_asset_path=model_asset_path,
                    actor_rows=variant.get("actor_rows") or [],
                )
            )
    return variants


def index_variants(variants: list[VariantInfo]) -> tuple[dict[tuple[str, tuple[str, ...]], VariantInfo], dict[str, list[VariantInfo]]]:
    by_model_and_skin: dict[tuple[str, tuple[str, ...]], VariantInfo] = {}
    by_model: dict[str, list[VariantInfo]] = {}
    for variant in variants:
        by_model.setdefault(variant.source_model, []).append(variant)
        by_model_and_skin[(variant.source_model, tuple(variant.source_skins))] = variant
    return by_model_and_skin, by_model


def unique_variant(variants: list[VariantInfo]) -> VariantInfo | None:
    unique = {variant.variant_id: variant for variant in variants}
    if len(unique) == 1:
        return next(iter(unique.values()))
    return None


def actor_lookup_indexes(
    variants: list[VariantInfo],
) -> tuple[dict[str, list[VariantInfo]], dict[str, dict[str, list[VariantInfo]]], dict[tuple[str, str], list[VariantInfo]]]:
    by_actor_key: dict[str, list[VariantInfo]] = {}
    type_keys_by_source_model: dict[str, dict[str, list[VariantInfo]]] = {}
    by_source_model_and_actor_key: dict[tuple[str, str], list[VariantInfo]] = {}
    for variant in variants:
        for row in variant.actor_rows:
            key = actor_key(str(row.get("monster_name") or ""))
            if key:
                by_actor_key.setdefault(key, []).append(variant)
                by_source_model_and_actor_key.setdefault((variant.source_model, key), []).append(variant)
            for type_key in type_picture_keys(str(row.get("type_picture") or "")):
                type_keys_by_source_model.setdefault(variant.source_model, {}).setdefault(type_key, []).append(variant)
    return by_actor_key, type_keys_by_source_model, by_source_model_and_actor_key


def resolve_variant(
    source_model: str,
    source_skins: list[str],
    source_class: str,
    by_model_and_skin: dict[tuple[str, tuple[str, ...]], VariantInfo],
    by_model: dict[str, list[VariantInfo]],
    by_actor_key: dict[str, list[VariantInfo]],
    type_keys_by_source_model: dict[str, dict[str, list[VariantInfo]]],
    by_source_model_and_actor_key: dict[tuple[str, str], list[VariantInfo]],
) -> tuple[VariantInfo | None, str]:
    exact = by_model_and_skin.get((source_model, tuple(source_skins)))
    if exact is not None:
        return exact, "exact_model_and_skin"

    class_key = actor_key(source_class)
    if class_key:
        class_entry = unique_variant(by_actor_key.get(class_key, []))
        if class_entry is not None:
            return class_entry, "unique_actor_class"

        type_matches: list[VariantInfo] = []
        for type_key in source_class_type_picture_keys(source_class):
            type_matches.extend(type_keys_by_source_model.get(source_model, {}).get(type_key, []))
        type_entry = unique_variant(type_matches)
        if type_entry is not None:
            return type_entry, "source_class_type_picture"

        class_entry = unique_variant(by_source_model_and_actor_key.get((source_model, class_key), []))
        if class_entry is not None:
            return class_entry, "source_model_actor_class"

        type_matches = []
        for type_key, entries in type_keys_by_source_model.get(source_model, {}).items():
            if class_key.endswith(type_key):
                type_matches.extend(entries)
        type_entry = unique_variant(type_matches)
        if type_entry is not None:
            return type_entry, "source_model_type_suffix"

    candidates = by_model.get(source_model) or []
    if len(candidates) == 1:
        return candidates[0], "single_model_variant"
    if not source_skins:
        empty_skin = by_model_and_skin.get((source_model, ()))
        if empty_skin is not None:
            return empty_skin, "empty_skin_variant"
    return None, "unresolved"


def load_map_objects(map_id: str, map_root: Path, source: str) -> list[PlacedObjectRef]:
    scene_path = map_root / f"{map_id}.scene.yml"
    events_path = map_root / f"{map_id}.events.yml"
    raw_path = map_root / f"{map_id}.raw_objects.yml"
    if source == "scene" and scene_path.exists():
        data = yaml.safe_load(scene_path.read_text(encoding="utf-8")) or {}
        return load_scene_objects(map_id, data)
    if source == "events" and events_path.exists():
        data = yaml.safe_load(events_path.read_text(encoding="utf-8")) or {}
        return load_event_objects(map_id, data)
    if source == "raw" and raw_path.exists():
        data = yaml.safe_load(raw_path.read_text(encoding="utf-8")) or {}
        return load_raw_objects(map_id, data)
    raise FileNotFoundError(f"No MM9 {source} sidecar found for map {map_id}")


def load_scene_objects(map_id: str, data: dict[str, Any]) -> list[PlacedObjectRef]:
    refs = []
    for entry in data.get("model_instances") or []:
        source_model = normalize_model_ref(str(entry.get("source_model") or ""))
        if not source_model:
            continue
        object_index = int(entry.get("source_object_index") or 0)
        refs.append(
            PlacedObjectRef(
                map_id=map_id,
                object_id=str(entry.get("instance_id") or f"mm9:{map_id}:object:{object_index}"),
                source_object_index=object_index,
                source_class=str(entry.get("source_class") or ""),
                source_name=str(entry.get("source_name") or ""),
                source_model=source_model,
                source_skins=normalize_skin_refs(str(entry.get("source_skin") or "")),
                model_asset=str(entry.get("model_asset") or ""),
                script_name="",
                script_params="",
            )
        )
    return refs


def load_event_objects(map_id: str, data: dict[str, Any]) -> list[PlacedObjectRef]:
    refs = []
    for entry in data.get("objects") or []:
        props = entry.get("normalized_properties") or {}
        source_model = normalize_model_ref(str(props.get("Filename") or ""))
        if not source_model:
            continue
        refs.append(
            PlacedObjectRef(
                map_id=map_id,
                object_id=str(entry.get("object_id") or f"mm9:{map_id}:object:{entry.get('source_object_index', 0)}"),
                source_object_index=int(entry.get("source_object_index") or 0),
                source_class=str(entry.get("source_class") or ""),
                source_name=str(entry.get("source_name") or props.get("Name") or ""),
                source_model=source_model,
                source_skins=normalize_skin_refs(str(props.get("Skin") or "")),
                model_asset="",
                script_name=str(props.get("ScriptName") or ""),
                script_params=str(props.get("ScriptParams") or ""),
            )
        )
    return refs


def property_values(object_node: dict[str, Any]) -> dict[str, Any]:
    values = {}
    for prop in object_node.get("properties") or []:
        name = prop.get("name")
        if not name:
            continue
        if "value_json" in prop:
            try:
                values[name] = json.loads(prop["value_json"])
            except json.JSONDecodeError:
                values[name] = prop["value_json"]
    return values


def load_raw_objects(map_id: str, data: dict[str, Any]) -> list[PlacedObjectRef]:
    refs = []
    for object_node in data.get("objects") or []:
        props = property_values(object_node)
        source_model = normalize_model_ref(str(props.get("Filename") or ""))
        if not source_model:
            continue
        object_index = int(object_node.get("object_index") or 0)
        refs.append(
            PlacedObjectRef(
                map_id=map_id,
                object_id=f"mm9:{map_id}:object:{object_index}",
                source_object_index=object_index,
                source_class=str(object_node.get("name") or ""),
                source_name=str(props.get("Name") or ""),
                source_model=source_model,
                source_skins=normalize_skin_refs(str(props.get("Skin") or "")),
                model_asset="",
                script_name=str(props.get("ScriptName") or ""),
                script_params=str(props.get("ScriptParams") or ""),
            )
        )
    return refs


def semantic_for_clip(name: str) -> str:
    normalized = slug(name).replace("_", "")
    for prefix, semantic in SEMANTIC_FALLBACKS.items():
        if normalized.startswith(prefix):
            return semantic
    if "attack" in normalized:
        return "melee_attack"
    if "walk" in normalized:
        return "walk"
    if "run" in normalized:
        return "run"
    if "fly" in normalized:
        return "fly"
    return "scripted"


def normalized_duration_ms(duration_seconds: float) -> int:
    if not math.isfinite(duration_seconds) or duration_seconds <= 0.0 or duration_seconds > 120.0:
        duration_seconds = 1.0
    return max(100, int(round(duration_seconds * 1000.0)))


def animation_sample_count(duration_ms: int, frames_per_second: float, max_frames_per_clip: int) -> int:
    if frames_per_second <= 0.0:
        frames_per_second = 8.0
    if max_frames_per_clip <= 0:
        max_frames_per_clip = 1
    estimated = max(1, int(math.ceil((duration_ms / 1000.0) * frames_per_second)))
    return max(1, min(max_frames_per_clip, estimated))


def generated_collision(variant: VariantInfo) -> dict[str, Any]:
    if variant.bounds_min is None or variant.bounds_max is None:
        return {"radius": 32, "height": 128, "vertical_offset": 0, "anchor": "feet", "source": "fallback"}
    min_x, min_y, min_z = variant.bounds_min
    max_x, max_y, max_z = variant.bounds_max
    radius = max(max_x - min_x, max_y - min_y) / 2.0
    height = max_z - min_z
    return {
        "radius": max(1, int(math.ceil(radius))),
        "height": max(1, int(math.ceil(height))),
        "vertical_offset": int(math.floor(min_z)),
        "anchor": "feet",
        "source": "glb_bounds",
    }


def frame_entries_for_clip(
    visual_id: str,
    clip_name: str,
    duration_ms: int,
    angles: int,
    mode: str,
    frame_count: int,
) -> list[dict[str, Any]]:
    if mode == "metadata":
        return []

    if mode == "placeholder":
        texture_name = f"{visual_id}_{slug(clip_name)}_placeholder"
        return [{"texture": texture_name, "duration_ms": duration_ms, "angle": "front"}]

    if mode != "render":
        raise ValueError(f"unsupported frame generation mode: {mode}")

    entries = []
    frame_duration_ms = max(33, int(round(duration_ms / max(1, frame_count))))
    for angle_index, angle_name in enumerate(ANGLE_NAMES[:angles]):
        for frame_index in range(frame_count):
            sample_fraction = 0.0 if frame_count == 1 else float(frame_index) / float(frame_count)
            texture_name = f"{visual_id}_{slug(clip_name)}_{angle_index:03d}_{frame_index:03d}"
            entries.append(
                {
                    "texture": texture_name,
                    "duration_ms": frame_duration_ms,
                    "angle": angle_name,
                    "frame_index": frame_index,
                    "sample_fraction": round(sample_fraction, 6),
                    "sample_time_ms": int(round(duration_ms * sample_fraction)),
                    "path": f"frames/{visual_id}/{texture_name}.png",
                }
            )
    return entries


def build_visual_yaml(
    resolved: ResolvedVisual,
    output_root: Path,
    angles: int,
    frame_mode: str,
    frames_per_second: float,
    max_frames_per_clip: int,
) -> dict[str, Any]:
    variant = resolved.variant
    visual_id = visual_id_for_variant(variant.variant_id)
    clips = {}
    animations = variant.animations or [{"name": "idle", "duration_seconds": 1.0}]
    for animation in animations:
        clip_name = str(animation.get("name") or "idle")
        duration_seconds = float(animation.get("duration_seconds") or 1.0)
        duration_ms = normalized_duration_ms(duration_seconds)
        frame_count = animation_sample_count(duration_ms, frames_per_second, max_frames_per_clip)
        clips[clip_name] = {
            "semantic": semantic_for_clip(clip_name),
            "angles": angles,
            "duration_ms": duration_ms,
            "frame_count": frame_count,
            "frames": frame_entries_for_clip(visual_id, clip_name, duration_ms, angles, frame_mode, frame_count),
        }
        if clip_name.lower() != "idle":
            clips[clip_name]["fallback"] = "idle"
    if "idle" not in {name.lower() for name in clips}:
        first_clip_name = next(iter(clips))
        first_clip = clips[first_clip_name]
        clips["idle"] = {
            "semantic": "idle",
            "angles": angles,
            "duration_ms": first_clip.get("duration_ms", 100),
            "frame_count": first_clip.get("frame_count", 1),
            "frames": [dict(frame) for frame in (first_clip.get("frames") or [])],
            "source_clip": first_clip_name,
        }

    return {
        "schema": SCHEMA,
        "visual_id": visual_id,
        "source_model": variant.source_model,
        "source_glb": str(variant.model_asset_path.as_posix()),
        "source_skins": variant.source_skins,
        "variant_id": variant.variant_id,
        "model_id": variant.model_id,
        "angle_count": angles,
        "angle_names": ANGLE_NAMES[:angles],
        "clips": clips,
        "collision": generated_collision(variant),
        "used_by": [
            {
                "map": ref.map_id,
                "object_id": ref.object_id,
                "source_object_index": ref.source_object_index,
                "source_class": ref.source_class,
                "source_name": ref.source_name,
                "script_name": ref.script_name,
                "script_params": ref.script_params,
            }
            for ref in resolved.used_by
        ],
        "provenance": {
            "tool": "tools/mm9_generate_actor_billboards.py",
            "tool_version": TOOL_VERSION,
            "generated_frames_root": str((output_root / "frames" / visual_id).as_posix()),
            "mode": frame_mode,
        },
    }


def write_placeholder_png(path: Path, visual_id: str, clip_name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (96, 160), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((28, 20, 68, 145), fill=(0, 180, 180, 180), outline=(0, 255, 255, 255))
    draw.ellipse((34, 8, 62, 36), fill=(0, 120, 120, 220), outline=(0, 255, 255, 255))
    label = visual_id[4:] if visual_id.startswith("mm9_") else visual_id
    label = label[:12]
    draw.text((6, 146), label, fill=(255, 255, 255, 255))
    image.save(path)


def trim_frame_preserving_anchor(path: Path) -> dict[str, Any] | None:
    with Image.open(path) as image:
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        original_width = image.width
        original_height = image.height
        alpha = image.getchannel("A")
        bbox = alpha.getbbox()
        if bbox is None:
            return None

        left, top, right, bottom = bbox
        if left != 0 or top != 0 or right != original_width or bottom != original_height:
            image = image.crop(bbox)
            image.save(path)

        return {
            "anchor_x": round((original_width * 0.5) - left, 3),
            "anchor_y": round(float(bottom - top), 3),
            "original_width": original_width,
            "original_height": original_height,
            "trim_bbox": [int(left), int(top), int(right), int(bottom)],
        }


def trim_visual_frames(output_root: Path, visual: dict[str, Any]) -> None:
    trim_metadata_by_path: dict[str, dict[str, Any] | None] = {}
    for clip in (visual.get("clips") or {}).values():
        for frame in clip.get("frames") or []:
            relative_path = frame.get("path")
            if not relative_path:
                continue
            relative_path = str(relative_path)
            if relative_path not in trim_metadata_by_path:
                frame_path = output_root / relative_path
                trim_metadata_by_path[relative_path] = (
                    trim_frame_preserving_anchor(frame_path) if frame_path.exists() else None
                )

            trim_metadata = trim_metadata_by_path[relative_path]
            if trim_metadata is None:
                continue
            frame.update(
                {
                    key: (list(value) if isinstance(value, list) else value)
                    for key, value in trim_metadata.items()
                }
            )


def trim_visual_files(output_root: Path, resolved: list[ResolvedVisual]) -> None:
    for item in resolved:
        visual_id = visual_id_for_variant(item.variant.variant_id)
        visual_path = output_root / f"{visual_id}.yml"
        if not visual_path.exists():
            continue
        visual = yaml.safe_load(visual_path.read_text(encoding="utf-8")) or {}
        trim_visual_frames(output_root, visual)
        visual_path.write_text(yaml.safe_dump(visual, sort_keys=False), encoding="utf-8")


def analyze_frame(path: Path, output_root: Path) -> FrameDiagnostic:
    try:
        relative_path = path.relative_to(output_root).as_posix()
    except ValueError:
        relative_path = path.as_posix()
    diagnostic = FrameDiagnostic(path=relative_path)
    try:
        with Image.open(path) as image:
            if image.mode != "RGBA":
                image = image.convert("RGBA")
            diagnostic.width = image.width
            diagnostic.height = image.height
            alpha = image.getchannel("A")
            bbox = alpha.getbbox()
            if bbox is None:
                diagnostic.fully_transparent = True
                diagnostic.blank = True
                return diagnostic
            diagnostic.transparent_bbox = [int(value) for value in bbox]

            first_visible_pixel: tuple[int, int, int, int] | None = None
            has_different_visible_pixel = False
            for pixel in image.getdata():
                if pixel[3] == 0:
                    continue
                diagnostic.nontransparent_pixels += 1
                if first_visible_pixel is None:
                    first_visible_pixel = pixel
                elif pixel != first_visible_pixel:
                    has_different_visible_pixel = True

            if diagnostic.nontransparent_pixels == 0:
                diagnostic.fully_transparent = True
                diagnostic.blank = True
            else:
                diagnostic.blank = not has_different_visible_pixel
            return diagnostic
    except OSError as exc:
        diagnostic.error = str(exc)
        diagnostic.blank = True
        return diagnostic


def frame_diagnostic_to_dict(diagnostic: FrameDiagnostic) -> dict[str, Any]:
    data: dict[str, Any] = {
        "path": diagnostic.path,
        "width": diagnostic.width,
        "height": diagnostic.height,
        "nontransparent_pixels": diagnostic.nontransparent_pixels,
        "fully_transparent": diagnostic.fully_transparent,
        "blank": diagnostic.blank,
    }
    if diagnostic.transparent_bbox is not None:
        data["transparent_bbox"] = diagnostic.transparent_bbox
    if diagnostic.anchor_x is not None:
        data["anchor_x"] = diagnostic.anchor_x
    if diagnostic.anchor_y is not None:
        data["anchor_y"] = diagnostic.anchor_y
    if diagnostic.original_width is not None:
        data["original_width"] = diagnostic.original_width
    if diagnostic.original_height is not None:
        data["original_height"] = diagnostic.original_height
    if diagnostic.trim_bbox is not None:
        data["trim_bbox"] = diagnostic.trim_bbox
    if diagnostic.error:
        data["error"] = diagnostic.error
    return data


def normalized_frame_for_motion(path: Path) -> Image.Image:
    with Image.open(path) as image:
        image = image.convert("RGBA")
        image.thumbnail((96, 128), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (96, 128), (0, 0, 0, 0))
        x = (canvas.width - image.width) // 2
        y = canvas.height - image.height
        canvas.alpha_composite(image, (x, y))
        return canvas


def motion_difference_ratio(base: Image.Image, frame: Image.Image) -> float:
    diff = ImageChops.difference(base, frame)
    stat = ImageStat.Stat(diff)
    max_sum = 255.0 * 4.0 * float(diff.width * diff.height)
    if max_sum <= 0.0:
        return 0.0
    return float(sum(stat.sum)) / max_sum


def collect_static_clip_diagnostics(output_root: Path, visual: dict[str, Any]) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for clip_name, clip in (visual.get("clips") or {}).items():
        front_frames = [
            output_root / str(frame["path"])
            for frame in (clip.get("frames") or [])
            if frame.get("angle") == "front" and frame.get("path")
        ]
        front_frames = [path for path in front_frames if path.exists()]
        if len(front_frames) <= 1:
            continue

        base = normalized_frame_for_motion(front_frames[0])
        max_difference = 0.0
        for frame_path in front_frames[1:]:
            max_difference = max(max_difference, motion_difference_ratio(base, normalized_frame_for_motion(frame_path)))

        if max_difference < 0.01:
            diagnostics.append(
                {
                    "clip": str(clip_name),
                    "front_frame_count": len(front_frames),
                    "max_difference_ratio": round(max_difference, 6),
                    "warning": "front-angle sampled frames are visually static; check for bind-pose/source clip issues",
                }
            )
    return diagnostics


def collect_frame_diagnostics(output_root: Path, visual: dict[str, Any]) -> list[FrameDiagnostic]:
    diagnostics: list[FrameDiagnostic] = []
    for clip in (visual.get("clips") or {}).values():
        for frame in clip.get("frames") or []:
            relative_path = frame.get("path")
            if not relative_path:
                continue
            diagnostic = analyze_frame(output_root / str(relative_path), output_root)
            if "anchor_x" in frame:
                diagnostic.anchor_x = float(frame["anchor_x"])
            if "anchor_y" in frame:
                diagnostic.anchor_y = float(frame["anchor_y"])
            if "original_width" in frame:
                diagnostic.original_width = int(frame["original_width"])
            if "original_height" in frame:
                diagnostic.original_height = int(frame["original_height"])
            if "trim_bbox" in frame and isinstance(frame["trim_bbox"], list):
                diagnostic.trim_bbox = [int(value) for value in frame["trim_bbox"]]
            diagnostics.append(diagnostic)
    return diagnostics


def write_visuals(
    resolved: list[ResolvedVisual],
    output_root: Path,
    angles: int,
    frame_mode: str,
    frames_per_second: float,
    max_frames_per_clip: int,
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    for item in resolved:
        visual = build_visual_yaml(item, output_root, angles, frame_mode, frames_per_second, max_frames_per_clip)
        visual_id = str(visual["visual_id"])
        if frame_mode == "placeholder":
            for clip_name, clip in visual["clips"].items():
                frames = clip.get("frames") or []
                if not frames:
                    continue
                texture = frames[0]["texture"]
                png_path = output_root / "frames" / visual_id / f"{texture}.png"
                write_placeholder_png(png_path, visual_id, clip_name)
                frames[0]["path"] = png_path.relative_to(output_root).as_posix()
        output_path = output_root / f"{visual_id}.yml"
        output_path.write_text(yaml.safe_dump(visual, sort_keys=False), encoding="utf-8")


def write_report(
    path: Path,
    resolved: list[ResolvedVisual],
    unresolved: list[dict[str, Any]],
    output_root: Path,
    args: argparse.Namespace,
) -> None:
    frame_diagnostics_by_visual: dict[str, list[dict[str, Any]]] = {}
    static_clip_diagnostics_by_visual: dict[str, list[dict[str, Any]]] = {}
    blank_frame_diagnostics = []
    static_clip_diagnostics = []

    for item in resolved:
        visual_id = visual_id_for_variant(item.variant.variant_id)
        visual_path = output_root / f"{visual_id}.yml"
        if not visual_path.exists():
            continue
        visual = yaml.safe_load(visual_path.read_text(encoding="utf-8")) or {}
        diagnostics = [frame_diagnostic_to_dict(item) for item in collect_frame_diagnostics(output_root, visual)]
        static_diagnostics = collect_static_clip_diagnostics(output_root, visual)
        frame_diagnostics_by_visual[visual_id] = diagnostics
        static_clip_diagnostics_by_visual[visual_id] = static_diagnostics
        blank_frame_diagnostics.extend(
            diagnostic for diagnostic in diagnostics if diagnostic.get("fully_transparent") or diagnostic.get("blank")
        )
        static_clip_diagnostics.extend(
            {"visual_id": visual_id, **diagnostic}
            for diagnostic in static_diagnostics
        )

    report = {
        "schema": "openyamm.mm9.scripted_billboard_generation_report.v1",
        "tool_version": TOOL_VERSION,
        "output_root": output_root.as_posix(),
        "map": args.map,
        "resolved_visuals": [
            {
                "visual_id": visual_id_for_variant(item.variant.variant_id),
                "variant_id": item.variant.variant_id,
                "source_model": item.variant.source_model,
                "source_skins": item.variant.source_skins,
                "source_glb": item.variant.model_asset_path.as_posix(),
                "clips_discovered": [str(animation.get("name") or "idle") for animation in item.variant.animations],
                "clips_generated": [str(animation.get("name") or "idle") for animation in item.variant.animations],
                "clips_skipped": [],
                "fallback_assignments": {
                    str(animation.get("name") or "idle"): (
                        "idle" if str(animation.get("name") or "idle").lower() != "idle" else ""
                    )
                    for animation in item.variant.animations
                },
                "animations": item.variant.animations,
                "collision": generated_collision(item.variant),
                "used_by_count": len(item.used_by),
                "frame_diagnostics": frame_diagnostics_by_visual.get(
                    visual_id_for_variant(item.variant.variant_id),
                    [],
                ),
                "static_clip_diagnostics": static_clip_diagnostics_by_visual.get(
                    visual_id_for_variant(item.variant.variant_id),
                    [],
                ),
            }
            for item in resolved
        ],
        "blank_frame_diagnostics": blank_frame_diagnostics,
        "static_clip_diagnostics": static_clip_diagnostics,
        "unresolved_objects": unresolved,
        "generation": {
            "angles": args.angles,
            "frames_per_second": args.frames_per_second,
            "max_frames_per_clip": args.max_frames_per_clip,
            "render": args.render,
            "placeholder_png": args.placeholder_png,
            "only_visual": args.only_visual,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")


def write_contact_sheets(output_root: Path, resolved: list[ResolvedVisual]) -> None:
    sheet_root = output_root / "contact_sheets"
    sheet_root.mkdir(parents=True, exist_ok=True)

    for item in resolved:
        visual_id = visual_id_for_variant(item.variant.variant_id)
        visual_path = output_root / f"{visual_id}.yml"
        if not visual_path.exists():
            continue

        visual = yaml.safe_load(visual_path.read_text(encoding="utf-8")) or {}
        rows: list[tuple[str, list[Path]]] = []
        max_frame_count = 0
        for clip_name, clip in (visual.get("clips") or {}).items():
            front_frames = [
                output_root / str(frame["path"])
                for frame in (clip.get("frames") or [])
                if frame.get("angle") == "front" and frame.get("path")
            ]
            front_frames = [path for path in front_frames if path.exists()]
            if not front_frames:
                continue
            rows.append((str(clip_name), front_frames))
            max_frame_count = max(max_frame_count, len(front_frames))

        if not rows:
            continue

        thumb_w = 96
        thumb_h = 128
        label_w = 160
        row_h = thumb_h + 8
        width = label_w + max_frame_count * (thumb_w + 8) + 8
        height = 8 + len(rows) * row_h
        sheet = Image.new("RGBA", (width, height), (24, 24, 24, 255))
        draw = ImageDraw.Draw(sheet)

        for row_index, (clip_name, frame_paths) in enumerate(rows):
            y = 8 + row_index * row_h
            draw.text((8, y + 8), clip_name[:24], fill=(255, 255, 255, 255))
            for frame_index, frame_path in enumerate(frame_paths):
                with Image.open(frame_path) as image:
                    image = image.convert("RGBA")
                    image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                    x = label_w + frame_index * (thumb_w + 8)
                    paste_y = y + max(0, (thumb_h - image.height) // 2)
                    sheet.alpha_composite(image, (x, paste_y))

        sheet.save(sheet_root / f"{visual_id}_front.png")


def verify_output(output_root: Path) -> int:
    failures = []
    visual_count = 0
    frame_count = 0
    for path in sorted(output_root.glob("mm9_*.yml")):
        visual_count += 1
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        visual_id = str(data.get("visual_id") or "")
        if data.get("schema") != SCHEMA:
            failures.append(f"{path}: unexpected schema {data.get('schema')}")
        if not visual_id.startswith("mm9_"):
            failures.append(f"{path}: visual_id does not use mm9_ prefix")
        clips = data.get("clips") or {}
        if not clips:
            failures.append(f"{path}: no clips")
            continue
        if "idle" not in {str(name).lower() for name in clips}:
            failures.append(f"{path}: no idle fallback clip")
        for clip_name, clip in clips.items():
            frames = clip.get("frames") or []
            if not frames:
                failures.append(f"{path}: clip {clip_name} has no frames")
                continue
            for frame in frames:
                relative_path = frame.get("path")
                if not relative_path:
                    failures.append(f"{path}: clip {clip_name} frame has no path")
                    continue
                frame_path = output_root / str(relative_path)
                if not frame_path.exists():
                    failures.append(f"{path}: missing frame {frame_path}")
                    continue
                frame_count += 1
                diagnostic = analyze_frame(frame_path, output_root)
                if diagnostic.error:
                    failures.append(f"{path}: cannot read frame {frame_path}: {diagnostic.error}")
                    continue
                if diagnostic.fully_transparent:
                    failures.append(f"{path}: fully transparent frame {frame_path}")
                elif diagnostic.blank:
                    failures.append(f"{path}: blank frame {frame_path}")
    if visual_count == 0:
        failures.append(f"{output_root}: no mm9_*.yml visual files")
    for failure in failures:
        print(f"verify: {failure}")
    print(f"verified visuals: {visual_count}")
    print(f"verified frame refs: {frame_count}")
    return 1 if failures else 0


def render_with_blender(
    resolved: list[ResolvedVisual],
    output_root: Path,
    angles: int,
    blender: str,
    frames_per_second: float,
    max_frames_per_clip: int,
    render_resolution: int,
    lighting_mode: str,
    texture_override_root: Path | None,
) -> None:
    blender_path = shutil.which(blender)
    if blender_path is None:
        raise FileNotFoundError(f"Blender executable not found: {blender}")
    with tempfile.TemporaryDirectory(prefix="openyamm_mm9_billboard_") as tmp:
        driver_path = Path(tmp) / "render_mm9_billboards.py"
        jobs = [
            {
                "visual_id": visual_id_for_variant(item.variant.variant_id),
                "glb": item.variant.model_asset_path.resolve().as_posix(),
                "output": (output_root / "frames" / visual_id_for_variant(item.variant.variant_id)).resolve().as_posix(),
                "animations": [
                    {
                        "name": str(animation.get("name") or "idle"),
                        "slug": slug(str(animation.get("name") or "idle")),
                        "frame_count": animation_sample_count(
                            normalized_duration_ms(float(animation.get("duration_seconds") or 1.0)),
                            frames_per_second,
                            max_frames_per_clip,
                        ),
                    }
                    for animation in item.variant.animations
                ] or [{"name": "idle", "slug": "idle", "frame_count": 1}],
                "angles": angles,
                "resolution": max(64, render_resolution),
                "lighting_mode": lighting_mode,
                "texture_override_root": texture_override_root.resolve().as_posix() if texture_override_root else "",
            }
            for item in resolved
        ]
        driver_path.write_text(BLENDER_DRIVER.replace("__JOBS_JSON__", json.dumps(jobs)), encoding="utf-8")
        subprocess.run([blender_path, "--background", "--python", str(driver_path)], check=True)


BLENDER_DRIVER = r'''
import json
import math
import os
import bpy
import mathutils

jobs = json.loads("""__JOBS_JSON__""")

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for action in list(bpy.data.actions):
        bpy.data.actions.remove(action)
    for collection in (
        bpy.data.meshes,
        bpy.data.armatures,
        bpy.data.materials,
        bpy.data.images,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for datablock in list(collection):
            if datablock.users == 0:
                collection.remove(datablock)

def set_color_management():
    view_settings = bpy.context.scene.view_settings
    try:
        view_settings.view_transform = 'Standard'
    except TypeError:
        pass
    try:
        view_settings.look = 'None'
    except TypeError:
        pass
    view_settings.exposure = 0.0
    view_settings.gamma = 1.0

def material_base_color(material):
    color = material.diffuse_color
    if material.use_nodes and material.node_tree is not None:
        for node in material.node_tree.nodes:
            if node.bl_idname == 'ShaderNodeBsdfPrincipled':
                base_color = node.inputs.get('Base Color')
                if base_color is not None:
                    color = base_color.default_value
                break
    return color

def first_material_image(material):
    if not material.use_nodes or material.node_tree is None:
        return None
    for node in material.node_tree.nodes:
        if node.bl_idname == 'ShaderNodeTexImage' and node.image is not None:
            return node.image
    return None

def make_materials_unlit():
    for material in bpy.data.materials:
        base_color = material_base_color(material)
        image = first_material_image(material)
        material.use_nodes = True
        material.node_tree.nodes.clear()
        material.node_tree.links.clear()
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (400, 0)
        emission = nodes.new(type='ShaderNodeEmission')
        emission.location = (150, 0)
        emission.inputs['Color'].default_value = base_color
        emission.inputs['Strength'].default_value = 1.0
        surface_output = emission.outputs[0]
        if image is not None:
            texture = nodes.new(type='ShaderNodeTexImage')
            texture.location = (-120, 0)
            texture.image = image
            links.new(texture.outputs['Color'], emission.inputs['Color'])
            transparent = nodes.new(type='ShaderNodeBsdfTransparent')
            transparent.location = (150, -180)
            mix = nodes.new(type='ShaderNodeMixShader')
            mix.location = (400, -60)
            links.new(texture.outputs['Alpha'], mix.inputs['Fac'])
            links.new(transparent.outputs[0], mix.inputs[1])
            links.new(emission.outputs[0], mix.inputs[2])
            surface_output = mix.outputs[0]
        links.new(surface_output, output.inputs['Surface'])
        material.blend_method = 'BLEND'
        material.use_backface_culling = False

def apply_texture_overrides(job):
    override_root = job.get("texture_override_root") or ""
    if not override_root:
        return
    for image in bpy.data.images:
        image_path = bpy.path.abspath(image.filepath) if image.filepath else image.name
        basename = os.path.basename(image_path)
        if not basename:
            continue
        override_path = os.path.join(override_root, basename)
        if not os.path.exists(override_path):
            continue
        image.filepath = override_path
        image.reload()

def setup_scene(job):
    engines = [item.identifier for item in bpy.context.scene.render.bl_rna.properties['engine'].enum_items]
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
    set_color_management()
    bpy.context.scene.render.film_transparent = True
    resolution = int(job.get("resolution", 512))
    bpy.context.scene.render.resolution_x = resolution
    bpy.context.scene.render.resolution_y = resolution
    bpy.context.scene.eevee.taa_render_samples = 16
    if job.get("lighting_mode", "flat") == "lit":
        light_data = bpy.data.lights.new("Key", type='SUN')
        light_obj = bpy.data.objects.new("Key", light_data)
        bpy.context.collection.objects.link(light_obj)
        light_obj.rotation_euler = (math.radians(45), 0, math.radians(35))
    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam_data.type = 'ORTHO'
    return cam

def object_bounds():
    mins = [1e9, 1e9, 1e9]
    maxs = [-1e9, -1e9, -1e9]
    found = False
    for obj in bpy.context.scene.objects:
        if obj.type not in {'MESH', 'ARMATURE'}:
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            for i in range(3):
                mins[i] = min(mins[i], world[i])
                maxs[i] = max(maxs[i], world[i])
            found = True
    if not found:
        return [0, 0, 0], [1, 1, 1]
    return mins, maxs

def mute_imported_nla_tracks():
    for obj in bpy.context.scene.objects:
        animation_data = obj.animation_data
        if animation_data is None:
            continue
        for track in animation_data.nla_tracks:
            track.mute = True

def apply_action(action):
    for obj in bpy.context.scene.objects:
        animation_data = obj.animation_data
        if animation_data is None:
            continue
        for track in animation_data.nla_tracks:
            track.mute = True
        animation_data.action = action

for job in jobs:
    clear_scene()
    bpy.ops.import_scene.gltf(filepath=job["glb"])
    apply_texture_overrides(job)
    mute_imported_nla_tracks()
    if job.get("lighting_mode", "flat") == "flat":
        make_materials_unlit()
    cam = setup_scene(job)
    mins = [999999, 999999, 999999]
    maxs = [-999999, -999999, -999999]
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ mathutils.Vector(corner)
            for i in range(3):
                mins[i] = min(mins[i], world[i])
                maxs[i] = max(maxs[i], world[i])
    center = [(mins[i] + maxs[i]) * 0.5 for i in range(3)]
    height = max(maxs[2] - mins[2], 1.0)
    radius = max(maxs[0] - mins[0], maxs[1] - mins[1], 1.0)
    cam.data.ortho_scale = max(height, radius) * 1.25
    actions = {action.name: action for action in bpy.data.actions}
    if not actions:
        actions = {"idle": None}
    os.makedirs(job["output"], exist_ok=True)
    for animation in job["animations"]:
        clip_name = animation["name"]
        clip_slug = animation["slug"]
        action = actions.get(clip_name)
        if action is not None:
            start, end = action.frame_range
            bpy.context.scene.frame_start = int(start)
            bpy.context.scene.frame_end = int(math.ceil(end))
            apply_action(action)
            bpy.context.view_layer.update()
        else:
            bpy.context.scene.frame_start = 1
            bpy.context.scene.frame_end = 1
        frame_count = max(1, int(animation.get("frame_count", 1)))
        for angle in range(job["angles"]):
            theta = math.pi + (2.0 * math.pi * angle) / job["angles"]
            distance = max(height, radius) * 3.0
            cam.location = (
                center[0] + math.sin(theta) * distance,
                center[1] + math.cos(theta) * distance,
                center[2] + height * 0.05,
            )
            direction = mathutils.Vector((
                center[0] - cam.location.x,
                center[1] - cam.location.y,
                center[2] + height * 0.05 - cam.location.z,
            ))
            cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
            for frame_index in range(frame_count):
                if frame_count == 1:
                    sample_frame = float(bpy.context.scene.frame_start)
                else:
                    fraction = frame_index / float(frame_count)
                    start = float(bpy.context.scene.frame_start)
                    end = float(bpy.context.scene.frame_end)
                    sample_frame = start + (end - start) * fraction
                frame = int(math.floor(sample_frame))
                subframe = sample_frame - float(frame)
                bpy.context.scene.frame_set(frame, subframe=subframe)
                bpy.context.view_layer.update()
                filename = f"{job['visual_id']}_{clip_slug}_{angle:03d}_{frame_index:03d}.png"
                bpy.context.scene.render.filepath = os.path.join(job["output"], filename)
                bpy.ops.render.render(write_still=True)
'''


def build_resolution(args: argparse.Namespace) -> tuple[list[ResolvedVisual], list[dict[str, Any]]]:
    variants = load_registry(args.registry, args.world_root)
    by_model_and_skin, by_model = index_variants(variants)
    by_actor_key, type_keys_by_source_model, by_source_model_and_actor_key = actor_lookup_indexes(variants)
    if args.map:
        placed_objects = load_map_objects(args.map, args.map_root, args.map_source)
    else:
        placed_objects = []
    resolved_by_variant: dict[str, ResolvedVisual] = {}
    unresolved = []
    synthetic_variants: dict[str, VariantInfo] = {}

    if args.all:
        for variant in variants:
            resolved_by_variant[variant.variant_id] = ResolvedVisual(variant=variant)

    for placed in placed_objects:
        variant, reason = resolve_variant(
            placed.source_model,
            placed.source_skins,
            placed.source_class,
            by_model_and_skin,
            by_model,
            by_actor_key,
            type_keys_by_source_model,
            by_source_model_and_actor_key,
        )
        if variant is None:
            if placed.model_asset:
                synthetic_key = normalize_ref(placed.model_asset)
                synthetic = synthetic_variants.get(synthetic_key)
                if synthetic is None:
                    variant_id = slug(Path(synthetic_key).stem)
                    synthetic = VariantInfo(
                        model_id=variant_id,
                        variant_id=variant_id,
                        source_model=placed.source_model,
                        source_skins=placed.source_skins,
                        model_asset=placed.model_asset,
                        model_asset_path=args.world_root / placed.model_asset,
                    )
                    synthetic_variants[synthetic_key] = synthetic
                item = resolved_by_variant.setdefault(synthetic.variant_id, ResolvedVisual(variant=synthetic))
                item.used_by.append(placed)
                continue
            if placed.source_model in by_model:
                unresolved.append(
                    {
                        "object_id": placed.object_id,
                        "source_object_index": placed.source_object_index,
                        "source_class": placed.source_class,
                        "source_name": placed.source_name,
                        "source_model": placed.source_model,
                        "source_skins": placed.source_skins,
                        "script_name": placed.script_name,
                        "reason": reason,
                    }
                )
            continue
        item = resolved_by_variant.setdefault(variant.variant_id, ResolvedVisual(variant=variant))
        item.used_by.append(placed)

    return sorted(resolved_by_variant.values(), key=lambda item: item.variant.variant_id), unresolved


def filter_resolved_visuals(resolved: list[ResolvedVisual], only_visual: str) -> list[ResolvedVisual]:
    if not only_visual:
        return resolved

    requested = {slug(item) for item in only_visual.split(",") if item.strip()}
    if not requested:
        return resolved

    return [
        item
        for item in resolved
        if slug(item.variant.variant_id) in requested or visual_id_for_variant(item.variant.variant_id) in requested
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or inventory MM9 actor billboard visual assets.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--world-root", type=Path, default=DEFAULT_WORLD_ROOT)
    parser.add_argument("--map-root", type=Path, default=DEFAULT_MAP_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--map", help="Generate/inventory only actor visuals referenced by this MM9 map id.")
    parser.add_argument(
        "--map-source",
        choices=["scene", "events", "raw"],
        default="scene",
        help="Sidecar type used to find model instances for map-scoped visual generation.",
    )
    parser.add_argument("--all", action="store_true", help="Include all registry actor variants.")
    parser.add_argument("--dry-run", action="store_true", help="Only print inventory; do not write visual YAML.")
    parser.add_argument("--write-yaml", action="store_true", help="Write MM9 billboard visual YAML files.")
    parser.add_argument("--placeholder-png", action="store_true", help="Write placeholder PNG frames for each visual clip.")
    parser.add_argument("--render", action="store_true", help="Render frames through Blender after writing YAML.")
    parser.add_argument("--verify-output", action="store_true", help="Verify generated visual YAML and referenced PNGs.")
    parser.add_argument("--contact-sheets", action="store_true", help="Write front-angle contact sheets for visual review.")
    parser.add_argument("--fail-on-unresolved", action="store_true", help="Fail if map actor model objects cannot resolve.")
    parser.add_argument("--blender", default="blender", help="Blender executable name/path.")
    parser.add_argument("--angles", type=int, default=8, choices=[1, 2, 4, 8])
    parser.add_argument("--frames-per-second", type=float, default=8.0)
    parser.add_argument("--max-frames-per-clip", type=int, default=8)
    parser.add_argument(
        "--render-resolution",
        type=int,
        default=512,
        help="Square Blender render resolution before transparent trimming.",
    )
    parser.add_argument(
        "--lighting-mode",
        choices=["flat", "lit"],
        default="flat",
        help="Use flat unlit materials by default; 'lit' preserves Blender light/material shading.",
    )
    parser.add_argument(
        "--texture-override-root",
        type=Path,
        help="Directory of PNG files that override imported model textures by basename during Blender rendering.",
    )
    parser.add_argument(
        "--only-visual",
        default="",
        help="Comma-separated visual or variant ids to generate after map/all resolution.",
    )
    parser.add_argument("--report", type=Path, help="Write a YAML generation report.")
    args = parser.parse_args()

    if args.verify_output and not args.map and not args.all:
        return verify_output(args.output_root)

    if not args.map and not args.all:
        parser.error("Specify --map <map> or --all")
    if args.placeholder_png and not args.write_yaml:
        parser.error("--placeholder-png requires --write-yaml")
    if args.render and not args.write_yaml:
        parser.error("--render requires --write-yaml")

    resolved, unresolved = build_resolution(args)
    resolved = filter_resolved_visuals(resolved, args.only_visual)
    for item in resolved:
        populate_variant_metadata(item.variant)
    print(f"resolved visuals: {len(resolved)}")
    print(f"unresolved actor-model objects: {len(unresolved)}")
    for item in resolved:
        print(
            f"{visual_id_for_variant(item.variant.variant_id)} "
            f"objects={len(item.used_by)} clips={len(item.variant.animations)} glb={item.variant.model_asset}"
        )
    if unresolved:
        print("unresolved:")
        for item in unresolved[:50]:
            print(
                f"  {item['object_id']} class={item['source_class']} name={item['source_name']} "
                f"model={item['source_model']} skins={';'.join(item['source_skins'])}"
            )
        if len(unresolved) > 50:
            print(f"  ... {len(unresolved) - 50} more")
        if args.fail_on_unresolved:
            return 1

    if not args.dry_run and args.write_yaml:
        frame_mode = "render" if args.render else ("placeholder" if args.placeholder_png else "metadata")
        write_visuals(
            resolved,
            args.output_root,
            args.angles,
            frame_mode,
            args.frames_per_second,
            args.max_frames_per_clip,
        )
        if frame_mode == "placeholder":
            trim_visual_files(args.output_root, resolved)
            print(f"trimmed placeholder frames: {args.output_root / 'frames'}")
        print(f"wrote visual YAML: {args.output_root}")
    if args.render:
        render_with_blender(
            resolved,
            args.output_root,
            args.angles,
            args.blender,
            args.frames_per_second,
            args.max_frames_per_clip,
            args.render_resolution,
            args.lighting_mode,
            args.texture_override_root,
        )
        trim_visual_files(args.output_root, resolved)
        print(f"trimmed rendered frames: {args.output_root / 'frames'}")
        print(f"rendered billboard frames: {args.output_root / 'frames'}")
    if args.contact_sheets:
        write_contact_sheets(args.output_root, resolved)
        print(f"contact sheets: {args.output_root / 'contact_sheets'}")
    if args.report:
        write_report(args.report, resolved, unresolved, args.output_root, args)
        print(f"report: {args.report}")
    if args.verify_output:
        return verify_output(args.output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
