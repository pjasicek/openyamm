#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from classify_mm9_maps import collect_metrics
from transcode_mm9_dat_to_odm import DatWorld, WorldBsp, read_dat_world


YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
YAML_DUMPER = getattr(yaml, "CSafeDumper", yaml.SafeDumper)

DEFAULT_MANIFEST = Path("assets_dev/worlds/mm9/maps/mm9_map_import.yml")
DEFAULT_OUTPUT_ROOT = Path("assets_dev/worlds/mm9/maps")
DEFAULT_SOURCE_ROOT = Path("assets_dev/worlds/mm9/source")
ORIGINAL_EXTRACTED_ROOT = Path("mm9/extracted")
SCALE = 2.56

HELPER_MODEL_NAMES = {"physicsbsp", "visbsp"}
SKY_MODEL_PREFIXES = ("tod_sky", "sky", "skybox")
TERRAIN_MODEL_PREFIXES = ("terrain", "ground", "cliff")
WATER_MODEL_PREFIXES = ("ocean", "bluewater", "water")
VOLUME_MODEL_PREFIXES = (
    "trigger",
    "invisiblebrush",
    "aibarrier",
    "perceptionbrush",
    "ladder",
    "volume",
    "sound",
    "weather",
    "rain",
    "poison",
    "corrosive",
)


def load_yaml(path: Path) -> dict[str, Any]:
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


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel_from_maps(path: Path) -> str:
    return f"../source/worlds/{path.name}"


def normalized_name(name: str) -> str:
    return name.strip().lower()


def histogram(values: list[int]) -> dict[int, int]:
    return dict(sorted(Counter(values).items()))


def model_roles(model: WorldBsp) -> dict[str, bool]:
    name = normalized_name(model.name)
    is_physics = name == "physicsbsp"
    is_vis = name == "visbsp"
    is_sky = name.startswith(SKY_MODEL_PREFIXES)
    is_water = name.startswith(WATER_MODEL_PREFIXES)
    is_terrain = name.startswith(TERRAIN_MODEL_PREFIXES)
    is_volume = name.startswith(VOLUME_MODEL_PREFIXES)
    is_helper = name in HELPER_MODEL_NAMES
    movable = bool(model.counts.get("world_info_flags", 0) & (1 << 1))
    return {
        "visible": not is_helper and not is_volume,
        "terrain": is_terrain,
        "physics_bsp": is_physics,
        "vis_bsp": is_vis,
        "sky": is_sky,
        "water": is_water,
        "trigger_or_volume": is_volume,
        "movable": movable,
    }


def model_summary(index: int, model: WorldBsp) -> dict[str, Any]:
    surface_flags: list[int] = [surface.flags for surface in model.surfaces]
    texture_flags: list[int] = [surface.texture_flags for surface in model.surfaces]
    return {
        "source_model_index": index,
        "source_name": model.name,
        "world_info_flags": model.counts.get("world_info_flags", 0),
        "kind": classify_model_kind(model),
        "point_count": len(model.points),
        "plane_count": len(model.planes),
        "surface_count": len(model.surfaces),
        "poly_count": len(model.polies),
        "leaf_count": len(model.leaves),
        "node_count": len(model.nodes),
        "user_portal_count": len(model.user_portals),
        "bsp_counts": {
            "vert_count": model.counts.get("vert_count", 0),
            "total_vis_list_size": model.counts.get("total_vis_list_size", 0),
            "leaf_list_count": model.counts.get("leaf_list_count", 0),
            "texture_name_length": model.counts.get("name_length", 0),
            "texture_count": model.counts.get("texture_count", len(model.textures)),
        },
        "root_node_index": model.root_node_index,
        "section_count": model.section_count,
        "unknown_values": {
            "world_bsp_unknown_value": model.counts.get("unknown_value", 0),
            "world_bsp_unknown_value_2": model.counts.get("unknown_value_2", 0),
            "world_bsp_unknown_value_3": model.counts.get("unknown_value_3", 0),
        },
        "pblock_table": {
            "preserved_in_source_dat": True,
            "decoded_summary": True,
            "dimensions": [
                model.pblock_table.dim_a,
                model.pblock_table.dim_b,
                model.pblock_table.dim_c,
            ],
            "bounds_lt": {
                "min": list(model.pblock_table.min_box),
                "max": list(model.pblock_table.max_box),
            },
            "record_count": model.pblock_table.record_count,
        },
        "bounds_lt": {
            "min": list(model.min_box),
            "max": list(model.max_box),
        },
        "world_translation_lt": list(model.world_translation),
        "textures": [
            {
                "texture_index": texture_index,
                "source_texture": texture_name,
            }
            for texture_index, texture_name in enumerate(model.textures)
        ],
        "surface_flag_histogram": histogram(surface_flags),
        "texture_user_flag_histogram": histogram(texture_flags),
        "roles": model_roles(model),
    }


def model_reference_validation(model: WorldBsp) -> dict[str, int]:
    invalid_surface_texture_refs = sum(
        1
        for surface in model.surfaces
        if surface.texture_index >= len(model.textures)
    )
    invalid_poly_surface_refs = sum(
        1
        for poly in model.polies
        if poly.surface_index >= len(model.surfaces)
    )
    invalid_poly_plane_refs = sum(
        1
        for poly in model.polies
        if poly.plane_index >= len(model.planes)
    )
    invalid_poly_vertex_refs = sum(
        1
        for poly in model.polies
        for disk_vert in poly.disk_verts
        if disk_vert.vertex_index >= len(model.points)
    )
    invalid_node_poly_refs = sum(
        1
        for node in model.nodes
        if node.poly_index >= len(model.polies)
    )
    invalid_root_node_refs = 0

    if model.nodes and model.root_node_index >= len(model.nodes):
        invalid_root_node_refs = 1

    return {
        "invalid_surface_texture_refs": invalid_surface_texture_refs,
        "invalid_poly_surface_refs": invalid_poly_surface_refs,
        "invalid_poly_plane_refs": invalid_poly_plane_refs,
        "invalid_poly_vertex_refs": invalid_poly_vertex_refs,
        "invalid_node_poly_refs": invalid_node_poly_refs,
        "invalid_root_node_refs": invalid_root_node_refs,
    }


def classify_model_kind(model: WorldBsp) -> str:
    roles = model_roles(model)
    if roles["physics_bsp"]:
        return "physics_bsp"
    if roles["vis_bsp"]:
        return "vis_bsp"
    if roles["sky"]:
        return "sky"
    if roles["water"]:
        return "water"
    if roles["trigger_or_volume"]:
        return "volume"
    if roles["terrain"]:
        return "terrain"
    return "visible_geometry" if roles["visible"] else "helper"


def count_invalid_leaf_refs(world: DatWorld) -> tuple[int, int]:
    total_refs = 0
    invalid_refs = 0
    for model in world.world_models:
        for leaf in model.leaves:
            for ref in leaf.polygon_refs():
                total_refs += 1
                if ref.world_model_index >= len(world.world_models):
                    invalid_refs += 1
                    continue
                target_model = world.world_models[ref.world_model_index]
                if ref.poly_index >= len(target_model.polies):
                    invalid_refs += 1
    return total_refs, invalid_refs


def user_portal_summaries(world: DatWorld) -> list[dict[str, Any]]:
    portals: list[dict[str, Any]] = []
    for model_index, model in enumerate(world.world_models):
        for portal_index, portal in enumerate(model.user_portals):
            portals.append(
                {
                    "source_model_index": model_index,
                    "source_model_name": model.name,
                    "portal_index": portal_index,
                    "name": portal.name,
                    "center_lt": list(portal.center),
                    "dims_lt": list(portal.dims),
                    "raw_unknowns": {
                        "unknown_int_1": portal.unknown_int_1,
                        "unknown_short": portal.unknown_short,
                    },
                }
            )
    return portals


def dat_world_sidecar(
    map_id: str,
    dat_path: Path,
    package_dat_path: Path,
    world: DatWorld,
    metrics: Any,
) -> dict[str, Any]:
    total_leaf_refs, invalid_leaf_refs = count_invalid_leaf_refs(world)
    return {
        "format_version": 1,
        "kind": "mm9_dat_world",
        "map_id": map_id,
        "source_dat": rel_from_maps(package_dat_path),
        "original_source_dat": dat_path.as_posix(),
        "source_hash": file_sha256(package_dat_path),
        "dat_version": world.version,
        "coordinate_system": {
            "source": "lithtech_mm9",
            "openyamm_mapping": ["x", "z", "y"],
            "scale": SCALE,
        },
        "world_info": {
            "property_string": world.world_info.properties,
            "light_map_grid_size": world.world_info.light_map_grid_size,
            "extents_min_lt": list(world.world_info.extents_min),
            "extents_max_lt": list(world.world_info.extents_max),
        },
        "classification": {
            "recommendation": metrics.recommendation,
            "confidence": metrics.confidence,
            "reason": metrics.reason,
        },
        "totals": {
            "world_model_count": len(world.world_models),
            "object_count": len(world.objects),
            "source_poly_count": sum(len(model.polies) for model in world.world_models),
            "surface_count": sum(len(model.surfaces) for model in world.world_models),
            "user_portal_count": sum(len(model.user_portals) for model in world.world_models),
            "leaf_count": sum(len(model.leaves) for model in world.world_models),
            "leaf_reference_count": total_leaf_refs,
            "invalid_leaf_reference_count": invalid_leaf_refs,
        },
        "world_models": [
            {
                **model_summary(model_index, model),
                "reference_validation": model_reference_validation(model),
            }
            for model_index, model in enumerate(world.world_models)
        ],
        "user_portals": user_portal_summaries(world),
        "leaf_references": {
            "decode": "world_model_index_low16_poly_index_high16",
            "total_refs": total_leaf_refs,
            "invalid_refs": invalid_leaf_refs,
        },
        "validation": {
            "parse_status": "ok",
            "unknown_field_policy": "preserved_in_source_dat",
            "pblock_summary_status": "summary_decoded_records_preserved_in_source_dat",
        },
    }


def existing_sidecar(path: Path) -> str | None:
    return path.name if path.exists() else None


def existing_level_sidecar_value(path: Path, key: str) -> str | None:
    if not path.exists():
        return None

    level = load_yaml(path)
    sidecars = level.get("sidecars")
    if not isinstance(sidecars, dict):
        return None

    value = sidecars.get(key)
    return value if isinstance(value, str) and value else None


def existing_outdoor_scene_sidecar(path: Path) -> str | None:
    if not path.exists():
        return None

    scene = load_yaml(path)
    return path.name if scene.get("kind") == "outdoor_scene" else None


def level_sidecar(
    map_entry: dict[str, Any],
    package_dat_path: Path,
    metrics: Any,
    output_root: Path,
) -> dict[str, Any]:
    map_id = str(map_entry["id"])
    display_name = str(map_entry.get("display_name", map_id))
    sky = metrics.recommendation in {"outdoor_like", "dat_bsp_portal_like", "dat_bsp_like"}
    sidecars: dict[str, Any] = {
        "dat_world": f"{map_id}.dat_world.yml",
        "raw_objects": existing_sidecar(output_root / f"{map_id}.raw_objects.yml"),
        "materials": existing_sidecar(output_root / f"{map_id}.material_aliases.yml"),
        "events": existing_sidecar(output_root / f"{map_id}.events.yml"),
        "scene_compat": existing_outdoor_scene_sidecar(output_root / f"{map_id}.scene.yml"),
        "source_metadata_compat": existing_sidecar(output_root / f"{map_id}.mm9.yml"),
        "bsp_compat": existing_sidecar(output_root / f"{map_id}.bsp.yml"),
        "geometry_compat": existing_sidecar(output_root / f"{map_id}.geometry.yml"),
        "model_assets_compat": existing_sidecar(output_root / f"{map_id}.model_assets.yml"),
        "odm_compat": existing_sidecar(output_root / f"{map_id}.odm"),
        "blv_compat": existing_sidecar(output_root / f"{map_id}.blv"),
    }
    source_asset_aliases = existing_level_sidecar_value(output_root / f"{map_id}.level.yml", "source_asset_aliases")
    if source_asset_aliases is not None:
        sidecars["source_asset_aliases"] = source_asset_aliases

    return {
        "format_version": 1,
        "kind": "mm9_level",
        "map_id": map_id,
        "display_name": display_name,
        "source": {
            "dat": rel_from_maps(package_dat_path),
            "manifest": "../source/manifest.yml",
            "original_dat": (ORIGINAL_EXTRACTED_ROOT / "WORLDS/WORLDS" / map_entry["source_dat"]).as_posix(),
            "source_game": "mm9",
            "dat_version": 66,
            "content_hash": file_sha256(package_dat_path),
        },
        "runtime": {
            "world_backend": "dat_world",
            "classification": metrics.recommendation,
            "classification_confidence": metrics.confidence,
            "visibility": visibility_backend(metrics.recommendation),
            "collision": "dat_physics_bsp",
            "render": "dat_render_world",
            "sky": sky,
        },
        "sidecars": sidecars,
        "scripts": {
            "level": f"../events/{map_id}.lua",
            "script_ir": f"../events/{map_id}.script_ir.yml",
        },
        "compatibility": {
            "legacy_target_format": map_entry.get("target_format"),
            "generated_odm_blv_are_derived": True,
        },
        "generated": {
            "tool": "tools/mm9_import_discovery/generate_mm9_dat_native_sidecars.py",
        },
    }


def visibility_backend(recommendation: str) -> str:
    if recommendation == "outdoor_like":
        return "dat_spatial"
    if recommendation in {"dat_bsp_portal_like", "dat_bsp_like", "indoor_like"}:
        return "dat_bsp_portal"
    return "dat_spatial"


def generate_sidecars(manifest_path: Path, output_root: Path, source_root: Path) -> None:
    manifest = load_yaml(manifest_path)
    maps = manifest.get("maps", [])
    if not isinstance(maps, list):
        raise RuntimeError(f"{manifest_path} has no maps list")

    for map_entry in maps:
        if not isinstance(map_entry, dict):
            continue
        map_id = str(map_entry["id"])
        source_dat_name = str(map_entry["source_dat"])
        original_dat_path = ORIGINAL_EXTRACTED_ROOT / "WORLDS/WORLDS" / source_dat_name
        package_dat_path = source_root / "worlds" / source_dat_name
        if not package_dat_path.exists():
            raise RuntimeError(f"missing mirrored DAT source: {package_dat_path}")

        world = read_dat_world(package_dat_path)
        metrics = collect_metrics(original_dat_path, output_root)
        write_yaml(output_root / f"{map_id}.dat_world.yml", dat_world_sidecar(
            map_id,
            original_dat_path,
            package_dat_path,
            world,
            metrics,
        ))
        write_yaml(output_root / f"{map_id}.level.yml", level_sidecar(
            map_entry,
            package_dat_path,
            metrics,
            output_root,
        ))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    generate_sidecars(args.manifest, args.output_root, args.source_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
