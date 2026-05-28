#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import re
import struct
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
MM9_TOOLS_DIR = REPO_ROOT / "tools" / "mm9_import_discovery"
sys.path.insert(0, MM9_TOOLS_DIR.as_posix())

from transcode_mm9_dat_to_odm import read_dat_world  # noqa: E402


YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
YAML_DUMPER = getattr(yaml, "CSafeDumper", yaml.SafeDumper)

DEFAULT_WORLD_ROOT = Path("assets_dev/worlds/mm9")
DEFAULT_EXTRACTED_ROOT = Path("mm9/extracted")
DEFAULT_OUTPUT = Path("assets_dev/worlds/mm9/upscaling/mm9_dtx_upscale_policies.yml")

ACTOR_SKIN_POLICY = "actor"
MODEL_SKIN_POLICY = "object"
OBJECT_POLICY = "object"
SURFACE_TILE_POLICY = "surface-tile"

OBJECT_HINTS = (
    "door",
    "doors",
    "sign",
    "signs",
    "window",
    "windows",
    "banner",
    "banners",
    "painting",
    "picture",
    "portrait",
    "panel",
    "panels",
    "tapestry",
    "poster",
    "plaque",
    "button",
    "switch",
    "lever",
    "chest",
    "crate",
    "barrel",
    "furniture",
    "props",
)

SURFACE_TILE_HINTS = (
    "detailtextures",
    "terrain",
    "terrains",
    "wall",
    "walls",
    "floor",
    "floors",
    "ceiling",
    "ceilings",
    "roof",
    "roofs",
    "rock",
    "rocks",
    "cliff",
    "grass",
    "dirt",
    "sand",
    "snow",
    "stone",
    "brick",
    "wood",
    "plaster",
    "metal",
    "tile",
    "tiles",
)


@dataclass
class Evidence:
    policy: str
    score: float
    reason: str
    source: str = ""


@dataclass
class TextureStats:
    aliases: set[str] = field(default_factory=set)
    source_textures: set[str] = field(default_factory=set)
    maps: set[str] = field(default_factory=set)
    width: int = 0
    height: int = 0
    dtx_bpp: int | None = None
    dtx_flags: int | None = None
    dtx_surface_flag: int | None = None
    dtx_command_string: str = ""
    surface_count: int = 0
    repeated_surface_count: int = 0
    single_image_surface_count: int = 0
    max_u_span_textures: float = 0.0
    max_v_span_textures: float = 0.0
    evidence: list[Evidence] = field(default_factory=list)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as stream:
        loaded = yaml.load(stream, Loader=YAML_LOADER)
    return loaded if isinstance(loaded, dict) else {}


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        yaml.dump(
            data,
            stream,
            Dumper=YAML_DUMPER,
            sort_keys=False,
            allow_unicode=False,
            width=120,
            default_flow_style=False,
        )


def normalize_path_key(value: str) -> str:
    return value.replace("\\", "/").strip().lower()


def remove_prefix(value: str, prefix: str) -> str:
    return value[len(prefix):] if value.startswith(prefix) else value


def remove_suffix(value: str, suffix: str) -> str:
    return value[:-len(suffix)] if value.endswith(suffix) else value


def normalized_tokens(value: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", normalize_path_key(value)) if token]


def has_token_hint(value: str, hints: tuple[str, ...]) -> bool:
    tokens = set(normalized_tokens(value))
    stem_tokens = set(normalized_tokens(Path(value.replace("\\", "/")).stem))
    all_tokens = tokens | stem_tokens
    return any(hint in all_tokens for hint in hints)


def dtx_header_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:12]
    if len(data) < 12:
        return 0, 0
    resource_type, version, height, width = struct.unpack_from("<IiHH", data, 0)
    if resource_type != 0 or version != -5:
        return 0, 0
    return width, height


def add_name_hint_evidence(entries: dict[str, TextureStats], path: Path, reason_source: str) -> None:
    stats = entries[entry_key(path)]
    width, height = dtx_header_size(path)
    if width > 0 and height > 0:
        stats.width = stats.width or width
        stats.height = stats.height or height
    path_text = path.as_posix()
    if "detailtextures" in normalize_path_key(path_text):
        stats.evidence.append(
            Evidence(policy=SURFACE_TILE_POLICY, score=1.0, reason="detail_texture_directory", source=reason_source),
        )
    elif has_token_hint(path_text, OBJECT_HINTS):
        stats.evidence.append(
            Evidence(policy=OBJECT_POLICY, score=0.65, reason="name_hint_object", source=reason_source),
        )
    elif has_token_hint(path_text, SURFACE_TILE_HINTS):
        stats.evidence.append(
            Evidence(
                policy=SURFACE_TILE_POLICY,
                score=0.55,
                reason="name_hint_surface_tile",
                source=reason_source,
            ),
        )


def index_dtx_files(extracted_root: Path) -> dict[str, list[Path]]:
    result: dict[str, list[Path]] = defaultdict(list)
    for root_name in ("SKINS/SKINS", "TEXTURES/TEXTURES"):
        root = extracted_root / root_name
        if not root.exists():
            continue
        for path in root.rglob("*.dtx"):
            relative = path.relative_to(root).as_posix()
            keys = {
                normalize_path_key(relative),
                normalize_path_key(Path(relative).with_suffix("").as_posix()),
                normalize_path_key(path.name),
                normalize_path_key(path.stem),
            }
            for key in keys:
                result[key].append(path)
    return result


def collect_all_dtx_baseline(extracted_root: Path, entries: dict[str, TextureStats]) -> None:
    for root_name in ("SKINS/SKINS", "TEXTURES/TEXTURES"):
        root = extracted_root / root_name
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.dtx")):
            add_name_hint_evidence(entries, path, "path_hint")


def resolve_source_skin(source_skin: str, dtx_index: dict[str, list[Path]]) -> list[Path]:
    normalized = normalize_path_key(source_skin)
    candidates = [
        normalized,
        remove_prefix(normalized, "skins/"),
        remove_prefix(normalized, "textures/"),
        Path(normalized).name,
        Path(normalized).stem,
    ]
    paths: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        for path in dtx_index.get(candidate, []):
            if path not in seen:
                paths.append(path)
                seen.add(path)
    return paths


def entry_key(path: Path) -> str:
    return path.as_posix()


def add_evidence(entries: dict[str, TextureStats], path: Path, evidence: Evidence) -> None:
    entries[entry_key(path)].evidence.append(evidence)


def collect_model_set_evidence(
    world_root: Path,
    dtx_index: dict[str, list[Path]],
    entries: dict[str, TextureStats],
) -> None:
    models_root = world_root / "models"
    for model_set_path in sorted(models_root.rglob("model_set.yml")):
        model_set = load_yaml(model_set_path)
        if not model_set:
            continue
        is_actor = "/actors/" in model_set_path.as_posix()
        policy = ACTOR_SKIN_POLICY if is_actor else MODEL_SKIN_POLICY
        reason = "actor_model_source_skin" if is_actor else "model_source_skin"
        score = 1.0 if is_actor else 0.9
        for variant in model_set.get("variants") or []:
            if not isinstance(variant, dict):
                continue
            for source_skin in variant.get("source_skins") or []:
                for path in resolve_source_skin(str(source_skin), dtx_index):
                    add_evidence(
                        entries,
                        path,
                        Evidence(policy=policy, score=score, reason=reason, source=model_set_path.as_posix()),
                    )


def update_stats_from_alias(stats: TextureStats, texture: dict[str, Any], map_id: str) -> None:
    stats.aliases.add(str(texture.get("alias") or ""))
    stats.source_textures.add(str(texture.get("source_texture") or ""))
    stats.maps.add(map_id)
    stats.width = int(texture.get("width") or stats.width or 0)
    stats.height = int(texture.get("height") or stats.height or 0)
    if "dtx_bpp" in texture:
        stats.dtx_bpp = int(texture["dtx_bpp"])
    if "dtx_flags" in texture:
        stats.dtx_flags = int(texture["dtx_flags"])
    if "dtx_surface_flag" in texture:
        stats.dtx_surface_flag = int(texture["dtx_surface_flag"])
    if texture.get("dtx_command_string"):
        stats.dtx_command_string = str(texture["dtx_command_string"])


def collect_alias_evidence(world_root: Path, entries: dict[str, TextureStats]) -> dict[str, dict[str, Path]]:
    maps_root = world_root / "maps"
    aliases_by_map: dict[str, dict[str, Path]] = {}

    for alias_path in sorted(maps_root.glob("*.material_aliases.yml")):
        map_id = remove_suffix(alias_path.name, ".material_aliases.yml")
        aliases_by_map[map_id] = {}
        data = load_yaml(alias_path)
        for texture in data.get("textures") or []:
            if not isinstance(texture, dict):
                continue
            physical_path = str(texture.get("physical_path") or "")
            if not physical_path:
                continue
            path = Path(physical_path)
            stats = entries[entry_key(path)]
            update_stats_from_alias(stats, texture, map_id)

            source_texture = normalize_path_key(str(texture.get("source_texture") or ""))
            if source_texture:
                aliases_by_map[map_id][source_texture] = path
                aliases_by_map[map_id][remove_prefix(source_texture, "textures/")] = path
            command = str(texture.get("dtx_command_string") or "")
            if "detailtex" in command.lower():
                stats.evidence.append(
                    Evidence(
                        policy=SURFACE_TILE_POLICY,
                        score=0.35,
                        reason="has_detail_texture_command",
                        source=alias_path.as_posix(),
                    ),
                )
            joined = " ".join([physical_path, str(texture.get("source_texture") or "")])
            if "detailtextures" in normalize_path_key(joined):
                stats.evidence.append(
                    Evidence(
                        policy=SURFACE_TILE_POLICY,
                        score=1.0,
                        reason="detail_texture_directory",
                        source=alias_path.as_posix(),
                    ),
                )
            elif has_token_hint(joined, OBJECT_HINTS):
                stats.evidence.append(
                    Evidence(policy=OBJECT_POLICY, score=0.75, reason="name_hint_object", source=alias_path.as_posix()),
                )
            elif has_token_hint(joined, SURFACE_TILE_HINTS):
                stats.evidence.append(
                    Evidence(
                        policy=SURFACE_TILE_POLICY,
                        score=0.65,
                        reason="name_hint_surface_tile",
                        source=alias_path.as_posix(),
                    ),
                )
    return aliases_by_map


def dot3(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return left[0] * right[0] + left[1] * right[1] + left[2] * right[2]


def uv_span_for_poly(
    model: Any,
    surface: Any,
    point_indices: list[int],
    width: int,
    height: int,
) -> tuple[float, float]:
    values_u: list[float] = []
    values_v: list[float] = []
    for point_index in point_indices:
        point = model.points[point_index]
        relative = (
            point[0] - surface.uv_origin[0],
            point[1] - surface.uv_origin[1],
            point[2] - surface.uv_origin[2],
        )
        values_u.append(dot3(relative, surface.uv_u) / max(1, width))
        values_v.append(dot3(relative, surface.uv_v) / max(1, height))
    if not values_u or not values_v:
        return 0.0, 0.0
    return max(values_u) - min(values_u), max(values_v) - min(values_v)


def collect_dat_uv_evidence(
    world_root: Path,
    entries: dict[str, TextureStats],
    aliases_by_map: dict[str, dict[str, Path]],
    maps: set[str] | None,
) -> None:
    maps_root = world_root / "maps"
    for dat_sidecar in sorted(maps_root.glob("*.dat_world.yml")):
        map_id = remove_suffix(dat_sidecar.name, ".dat_world.yml")
        if maps is not None and map_id not in maps:
            continue
        sidecar = load_yaml(dat_sidecar)
        source_dat = sidecar.get("source_dat")
        if not isinstance(source_dat, str) or not source_dat:
            continue
        dat_path = Path(source_dat)
        if not dat_path.exists() and isinstance(sidecar.get("original_source_dat"), str):
            dat_path = Path(str(sidecar["original_source_dat"]))
        if not dat_path.exists():
            continue
        alias_map = aliases_by_map.get(map_id) or {}
        if not alias_map:
            continue

        world = read_dat_world(dat_path)
        for model in world.world_models:
            for poly in model.polies:
                if poly.surface_index >= len(model.surfaces):
                    continue
                surface = model.surfaces[poly.surface_index]
                if surface.texture_index >= len(model.textures):
                    continue
                texture_name = normalize_path_key(model.textures[surface.texture_index])
                path = alias_map.get(texture_name) or alias_map.get(remove_prefix(texture_name, "textures/"))
                if path is None:
                    continue
                stats = entries[entry_key(path)]
                if stats.width <= 0 or stats.height <= 0:
                    width, height = dtx_header_size(path)
                else:
                    width, height = stats.width, stats.height
                if width <= 0 or height <= 0:
                    continue
                point_indices = [disk_vert.vertex_index for disk_vert in poly.disk_verts]
                if any(point_index >= len(model.points) for point_index in point_indices):
                    continue
                u_span, v_span = uv_span_for_poly(model, surface, point_indices, width, height)
                stats.surface_count += 1
                stats.max_u_span_textures = max(stats.max_u_span_textures, u_span)
                stats.max_v_span_textures = max(stats.max_v_span_textures, v_span)
                if max(u_span, v_span) > 1.15:
                    stats.repeated_surface_count += 1
                elif max(u_span, v_span) <= 1.05:
                    stats.single_image_surface_count += 1


def add_dat_summary_evidence(entries: dict[str, TextureStats]) -> None:
    for path_key, stats in entries.items():
        if stats.repeated_surface_count > 0:
            ratio = stats.repeated_surface_count / max(1, stats.surface_count)
            score = min(0.95, 0.65 + ratio * 0.3)
            stats.evidence.append(
                Evidence(
                    policy=SURFACE_TILE_POLICY,
                    score=score,
                    reason="dat_surface_uv_repeats",
                    source=f"{stats.repeated_surface_count}/{stats.surface_count} surfaces",
                ),
            )
        if stats.surface_count >= 12:
            stats.evidence.append(
                Evidence(
                    policy=SURFACE_TILE_POLICY,
                    score=min(0.85, 0.45 + math.log10(stats.surface_count) * 0.2),
                    reason="used_on_many_dat_surfaces",
                    source=f"{stats.surface_count} surfaces",
                ),
            )
        if stats.single_image_surface_count > 0 and stats.repeated_surface_count == 0:
            ratio = stats.single_image_surface_count / max(1, stats.surface_count)
            if ratio >= 0.8:
                stats.evidence.append(
                    Evidence(
                        policy=OBJECT_POLICY,
                        score=0.55,
                        reason="dat_surface_uv_single_image",
                        source=f"{stats.single_image_surface_count}/{stats.surface_count} surfaces",
                    ),
                )


def load_overrides(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    data = load_yaml(path)
    overrides = data.get("overrides") if isinstance(data.get("overrides"), dict) else data
    if not isinstance(overrides, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for key, value in overrides.items():
        if isinstance(value, str):
            result[normalize_path_key(str(key))] = {"policy": value}
        elif isinstance(value, dict):
            result[normalize_path_key(str(key))] = value
    return result


def match_override(path_key: str, overrides: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    normalized = normalize_path_key(path_key)
    for pattern, value in overrides.items():
        if pattern == normalized:
            return value
        if pattern.startswith("**/") and normalized.endswith(pattern[3:]):
            return value
        if pattern.endswith("/**") and normalized.startswith(pattern[:-3]):
            return value
    return None


def decide_policy(
    path_key: str,
    stats: TextureStats,
    overrides: dict[str, dict[str, Any]],
) -> tuple[str, float, list[dict[str, Any]], bool]:
    override = match_override(path_key, overrides)
    if override is not None and override.get("policy"):
        return str(override["policy"]), 1.0, [{"policy": override["policy"], "score": 1.0, "reason": "override"}], False

    scores: Counter[str] = Counter()
    reasons_by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for evidence in stats.evidence:
        scores[evidence.policy] += evidence.score
        reasons_by_policy[evidence.policy].append(
            {
                "reason": evidence.reason,
                "score": round(evidence.score, 3),
                **({"source": evidence.source} if evidence.source else {}),
            },
        )

    if not scores:
        return OBJECT_POLICY, 0.25, [{"policy": OBJECT_POLICY, "score": 0.25, "reason": "default"}], True

    ranked = scores.most_common()
    best_policy, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    confidence = min(1.0, best_score / max(best_score + second_score, 1.0))
    ambiguous = confidence < 0.67 or (second_score > 0 and best_score - second_score < 0.25)

    candidates = []
    for policy, score in ranked:
        candidates.append(
            {
                "policy": policy,
                "score": round(float(score), 3),
                "reasons": reasons_by_policy[policy],
            },
        )
    return best_policy, round(confidence, 3), candidates, ambiguous


def output_path_for(source_path: str, output_root: Path, scale: int) -> str:
    path = Path(source_path)
    relative_parts = list(path.parts)
    lowered = [part.lower() for part in relative_parts]
    if "skins" in lowered:
        skin_indexes = [index for index, part in enumerate(lowered) if part == "skins"]
        if len(skin_indexes) >= 2:
            relative = Path(*relative_parts[skin_indexes[1] + 1:])
        elif skin_indexes:
            relative = Path(*relative_parts[skin_indexes[0] + 1:])
        else:
            relative = Path(path.name)
        base = output_root / "skins" / relative
    elif "textures" in lowered:
        texture_indexes = [index for index, part in enumerate(lowered) if part == "textures"]
        if len(texture_indexes) >= 2:
            relative = Path(*relative_parts[texture_indexes[1] + 1:])
        elif texture_indexes:
            relative = Path(*relative_parts[texture_indexes[0] + 1:])
        else:
            relative = Path(path.name)
        base = output_root / "textures" / relative
    else:
        base = output_root / path.name
    return base.with_name(f"{base.stem}_x{scale}{base.suffix}").as_posix()


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    dtx_index = index_dtx_files(args.extracted_root)
    entries: dict[str, TextureStats] = defaultdict(TextureStats)
    collect_all_dtx_baseline(args.extracted_root, entries)
    collect_model_set_evidence(args.world_root, dtx_index, entries)
    aliases_by_map = collect_alias_evidence(args.world_root, entries)
    map_filter = set(args.maps.split(",")) if args.maps else None
    if not args.skip_dat_uv:
        collect_dat_uv_evidence(args.world_root, entries, aliases_by_map, map_filter)
    add_dat_summary_evidence(entries)
    overrides = load_overrides(args.overrides)

    output_entries: dict[str, Any] = {}
    ambiguous: dict[str, Any] = {}
    for path_key in sorted(entries):
        stats = entries[path_key]
        policy, confidence, candidates, is_ambiguous = decide_policy(path_key, stats, overrides)
        item = {
            "policy": policy,
            "confidence": confidence,
            "output": output_path_for(path_key, args.output_root, args.scale),
            "maps": sorted(item for item in stats.maps if item),
            "source_textures": sorted(item for item in stats.source_textures if item),
            "dimensions": {"width": stats.width, "height": stats.height},
            "dtx": {
                "bpp": stats.dtx_bpp,
                "flags": stats.dtx_flags,
                "surface_flag": stats.dtx_surface_flag,
                "command_string": stats.dtx_command_string,
            },
            "dat_usage": {
                "surface_count": stats.surface_count,
                "repeated_surface_count": stats.repeated_surface_count,
                "single_image_surface_count": stats.single_image_surface_count,
                "max_u_span_textures": round(stats.max_u_span_textures, 3),
                "max_v_span_textures": round(stats.max_v_span_textures, 3),
            },
            "candidates": candidates,
        }
        if is_ambiguous:
            ambiguous[path_key] = item
            if args.skip_ambiguous:
                continue
        output_entries[path_key] = item

    return {
        "schema": "openyamm.mm9.dtx_upscale_policy.v1",
        "scale": args.scale,
        "default_policy": OBJECT_POLICY,
        "metadata_policy": "copied_except_dimensions_and_mips",
        "source_roots": {
            "world_root": args.world_root.as_posix(),
            "extracted_root": args.extracted_root.as_posix(),
        },
        "stats": {
            "entries": len(output_entries),
            "ambiguous": len(ambiguous),
        },
        "entries": output_entries,
        "ambiguous": ambiguous,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify MM9 DTX files for HD upscaling policies.")
    parser.add_argument("--world-root", type=Path, default=DEFAULT_WORLD_ROOT)
    parser.add_argument("--extracted-root", type=Path, default=DEFAULT_EXTRACTED_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--output-root", type=Path, default=Path("assets_dev/worlds/mm9_hd"))
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument("--overrides", type=Path, help="Optional YAML overrides map.")
    parser.add_argument("--maps", help="Comma-separated map ids for DAT UV analysis.")
    parser.add_argument("--skip-dat-uv", action="store_true", help="Skip expensive DAT UV analysis.")
    parser.add_argument("--skip-ambiguous", action="store_true", help="Exclude ambiguous entries from entries.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_manifest(args)
    write_yaml(args.output, manifest)
    print(f"wrote: {args.output}")
    print(f"entries: {manifest['stats']['entries']}")
    print(f"ambiguous: {manifest['stats']['ambiguous']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
