#!/usr/bin/env python3
"""
Classify MM9 DAT worlds by source geometry structure for OpenYAMM runtime planning.

This is a discovery/reporting tool. It does not transcode maps and it does not
decide MM6-MM8 behavior. It reads the parsed MM9 DAT structures directly and
emits a markdown report describing which maps look outdoor-like, BLV-like, or
DAT-BSP/portal-like.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from transcode_mm9_dat_to_odm import LT_SURFACE_FLAG_INVISIBLE, DatWorld, WorldBsp, read_dat_world


DEFAULT_DAT_DIR = Path("mm9/extracted/WORLDS/WORLDS")
DEFAULT_MAP_DIR = Path("assets_dev/worlds/mm9/maps")
DEFAULT_REPORT_PATH = Path("docs/mm9/MM9_MAP_RUNTIME_CLASSIFICATION.md")

HELPER_MODEL_NAMES = {"physicsbsp", "visbsp"}
SKY_MODEL_PREFIXES = ("tod_sky", "sky")
TERRAIN_MODEL_PREFIXES = ("terrain", "ground", "cliff")
WATER_MODEL_PREFIXES = ("ocean", "bluewater", "water")
INVISIBLE_TEXTURE_STEMS = {"invisible", "soundonly", "greenscreen", "firethrough"}


@dataclass
class MapMetrics:
    map_id: str
    dat_file: str
    current_export: str
    model_count: int
    object_count: int
    source_polies: int
    visible_candidate_polies: int
    helper_polies: int
    terrain_polies: int
    sky_water_polies: int
    invisible_polies: int
    visbsp_polies: int
    physicsbsp_polies: int
    visbsp_leaves: int
    visbsp_leaf_entries: int
    user_portals: int
    total_leaves: int
    total_leaf_entries: int
    largest_model_name: str
    largest_model_polies: int
    recommendation: str
    confidence: str
    reason: str

    @property
    def helper_ratio(self) -> float:
        return self.helper_polies / self.source_polies if self.source_polies else 0.0

    @property
    def terrain_ratio(self) -> float:
        return self.terrain_polies / self.source_polies if self.source_polies else 0.0

    @property
    def visible_candidate_ratio(self) -> float:
        return self.visible_candidate_polies / self.source_polies if self.source_polies else 0.0


def normalized_name(name: str) -> str:
    return name.strip().lower()


def texture_stem(texture_name: str) -> str:
    return Path(texture_name.replace("\\", "/")).stem.lower()


def model_poly_count(model: WorldBsp) -> int:
    return len(model.polies)


def model_leaf_entry_count(model: WorldBsp) -> int:
    return sum(len(leaf.polygon_entries) for leaf in model.leaves)


def is_helper_model(model: WorldBsp) -> bool:
    return normalized_name(model.name) in HELPER_MODEL_NAMES


def is_terrain_model(model: WorldBsp) -> bool:
    name = normalized_name(model.name)
    return name.startswith(TERRAIN_MODEL_PREFIXES)


def is_sky_or_water_model(model: WorldBsp) -> bool:
    name = normalized_name(model.name)
    return name.startswith(SKY_MODEL_PREFIXES) or name.startswith(WATER_MODEL_PREFIXES)


def poly_texture_name(model: WorldBsp, poly_index: int) -> str:
    poly = model.polies[poly_index]
    if poly.surface_index >= len(model.surfaces):
        return ""
    surface = model.surfaces[poly.surface_index]
    if surface.texture_index >= len(model.textures):
        return ""
    return model.textures[surface.texture_index]


def poly_surface_flags(model: WorldBsp, poly_index: int) -> int:
    poly = model.polies[poly_index]
    if poly.surface_index >= len(model.surfaces):
        return 0
    return model.surfaces[poly.surface_index].flags


def is_invisible_poly(model: WorldBsp, poly_index: int) -> bool:
    flags = poly_surface_flags(model, poly_index)
    if (flags & LT_SURFACE_FLAG_INVISIBLE) != 0:
        return True

    stem = texture_stem(poly_texture_name(model, poly_index))
    return stem.startswith("invisib") or stem in INVISIBLE_TEXTURE_STEMS


def current_export_kind(map_dir: Path, map_id: str) -> str:
    kinds: list[str] = []
    if (map_dir / f"{map_id}.odm").exists():
        kinds.append("odm")
    if (map_dir / f"{map_id}.blv").exists():
        kinds.append("blv")
    if (map_dir / f"{map_id}.bsp.yml").exists():
        kinds.append("bsp.yml")
    return "+".join(kinds) if kinds else "none"


def classify_metrics(metrics: MapMetrics) -> tuple[str, str, str]:
    if metrics.user_portals >= 5 and metrics.visbsp_leaves >= 250:
        return (
            "dat_bsp_portal_like",
            "high",
            "has named UserPortal records plus dense VisBSP leaves; treat as DAT BSP/portal map, not plain ODM",
        )

    if metrics.terrain_ratio >= 0.45 and metrics.user_portals == 0:
        return (
            "outdoor_like",
            "high",
            "terrain model dominates source polygons and no UserPortal records were found",
        )

    if metrics.terrain_ratio >= 0.30 and metrics.user_portals <= 2 and metrics.visbsp_leaves < 500:
        return (
            "outdoor_like",
            "medium",
            "terrain is a major source component and portal data is absent or minimal",
        )

    if metrics.user_portals > 0 or metrics.visbsp_leaves >= 500:
        return (
            "dat_bsp_like",
            "medium",
            "BSP leaves or portals are significant but the map is not terrain-dominated",
        )

    if metrics.terrain_ratio < 0.20 and metrics.current_export.startswith("blv"):
        return (
            "indoor_like",
            "medium",
            "not terrain-dominated and already imported through the BLV/BSP path",
        )

    if metrics.terrain_ratio < 0.20 and metrics.helper_ratio >= 0.10:
        return (
            "indoor_like",
            "medium",
            "not terrain-dominated and carries meaningful helper BSP geometry",
        )

    return (
        "needs_review",
        "low",
        "does not clearly match outdoor terrain, city portal, or imported BLV/BSP patterns",
    )


def collect_metrics(dat_path: Path, map_dir: Path) -> MapMetrics:
    world = read_dat_world(dat_path)
    map_id = dat_path.stem.lower()
    source_polies = sum(model_poly_count(model) for model in world.world_models)
    helper_polies = sum(model_poly_count(model) for model in world.world_models if is_helper_model(model))
    terrain_polies = sum(model_poly_count(model) for model in world.world_models if is_terrain_model(model))
    sky_water_polies = sum(model_poly_count(model) for model in world.world_models if is_sky_or_water_model(model))
    total_leaves = sum(len(model.leaves) for model in world.world_models)
    total_leaf_entries = sum(model_leaf_entry_count(model) for model in world.world_models)
    user_portals = sum(len(model.user_portals) for model in world.world_models)
    invisible_polies = 0
    visible_candidate_polies = 0

    visbsp_polies = 0
    physicsbsp_polies = 0
    visbsp_leaves = 0
    visbsp_leaf_entries = 0
    largest_model_name = ""
    largest_model_polies = 0

    for model in world.world_models:
        poly_count = model_poly_count(model)
        if poly_count > largest_model_polies:
            largest_model_name = model.name
            largest_model_polies = poly_count

        model_name = normalized_name(model.name)
        if model_name == "visbsp":
            visbsp_polies += poly_count
            visbsp_leaves += len(model.leaves)
            visbsp_leaf_entries += model_leaf_entry_count(model)
        elif model_name == "physicsbsp":
            physicsbsp_polies += poly_count

        model_is_helper = is_helper_model(model)
        model_is_sky_or_water = is_sky_or_water_model(model)
        for poly_index in range(poly_count):
            poly_is_invisible = is_invisible_poly(model, poly_index)
            if poly_is_invisible:
                invisible_polies += 1
            if not model_is_helper and not model_is_sky_or_water and not poly_is_invisible:
                visible_candidate_polies += 1

    metrics = MapMetrics(
        map_id=map_id,
        dat_file=dat_path.name,
        current_export=current_export_kind(map_dir, map_id),
        model_count=len(world.world_models),
        object_count=len(world.objects),
        source_polies=source_polies,
        visible_candidate_polies=visible_candidate_polies,
        helper_polies=helper_polies,
        terrain_polies=terrain_polies,
        sky_water_polies=sky_water_polies,
        invisible_polies=invisible_polies,
        visbsp_polies=visbsp_polies,
        physicsbsp_polies=physicsbsp_polies,
        visbsp_leaves=visbsp_leaves,
        visbsp_leaf_entries=visbsp_leaf_entries,
        user_portals=user_portals,
        total_leaves=total_leaves,
        total_leaf_entries=total_leaf_entries,
        largest_model_name=largest_model_name,
        largest_model_polies=largest_model_polies,
        recommendation="",
        confidence="",
        reason="",
    )
    recommendation, confidence, reason = classify_metrics(metrics)
    metrics.recommendation = recommendation
    metrics.confidence = confidence
    metrics.reason = reason
    return metrics


def pct(value: float) -> str:
    return f"{value * 100.0:.1f}%"


def fmt_int(value: int) -> str:
    return f"{value:,}"


def make_markdown(metrics: list[MapMetrics], dat_dir: Path, map_dir: Path) -> str:
    counts = Counter(metric.recommendation for metric in metrics)
    current_mismatches = [
        metric for metric in metrics
        if metric.recommendation == "dat_bsp_portal_like" and metric.current_export == "odm"
    ]
    secondary_mismatches = [
        metric for metric in metrics
        if metric.current_export == "odm" and metric.recommendation in {"dat_bsp_like", "indoor_like"}
    ]

    lines: list[str] = []
    lines.append("# MM9 Map Runtime Classification")
    lines.append("")
    lines.append("Generated by `tools/mm9_import_discovery/classify_mm9_maps.py` from local MM9 DAT v66 files.")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(f"- DAT input directory: `{dat_dir}`")
    lines.append(f"- OpenYAMM MM9 map directory checked for current exports: `{map_dir}`")
    lines.append(f"- DAT maps scanned: `{len(metrics)}`")
    lines.append("- Purpose: classify MM9 maps by source DAT structure so the runtime/editor can choose the right")
    lines.append("  representation without forcing every MM9 map into MM6-MM8 ODM/BLV assumptions.")
    lines.append("")
    lines.append("## Classification Contract")
    lines.append("")
    lines.append("- `outdoor_like`: terrain world models dominate, no meaningful UserPortal data; this can stay closest to")
    lines.append("  the existing ODM-style terrain/runtime path after helper BSPs are filtered out.")
    lines.append("- `dat_bsp_portal_like`: named `UserPortal` records plus dense `VisBSP` leaves; this should use a DAT")
    lines.append("  BSP/portal or BLV-like sector runtime instead of plain ODM.")
    lines.append("- `dat_bsp_like`: significant BSP leaves or portals but not clearly a terrain map; preserve DAT BSP metadata and")
    lines.append("  route through an indoor/BSP-capable runtime path.")
    lines.append("- `indoor_like`: not terrain-dominated and already structurally aligned with the generated BLV/BSP path.")
    lines.append("- `needs_review`: insufficient structural signal for an automatic runtime decision.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    for key in ["outdoor_like", "dat_bsp_portal_like", "dat_bsp_like", "indoor_like", "needs_review"]:
        lines.append(f"- `{key}`: `{counts.get(key, 0)}`")
    lines.append("")

    if current_mismatches:
        lines.append("## High Priority Runtime Mismatches")
        lines.append("")
        lines.append("These maps are currently exported as `.odm` but source DAT structure says they need DAT BSP/portal treatment:")
        lines.append("")
        lines.append("| Map | Current | User portals | VisBSP leaves | VisBSP leaf refs | Helper ratio | Reason |")
        lines.append("| --- | --- | ---: | ---: | ---: | ---: | --- |")
        for metric in current_mismatches:
            lines.append(
                f"| `{metric.map_id}` | `{metric.current_export}` | {metric.user_portals} | "
                f"{fmt_int(metric.visbsp_leaves)} | {fmt_int(metric.visbsp_leaf_entries)} | "
                f"{pct(metric.helper_ratio)} | {metric.reason} |"
            )
        lines.append("")

    if secondary_mismatches:
        lines.append("## Secondary Runtime Mismatches")
        lines.append("")
        lines.append("These maps are currently exported as `.odm` but do not structurally classify as outdoor terrain maps:")
        lines.append("")
        lines.append("| Map | Current | Recommendation | Visible candidate | Helper ratio | Reason |")
        lines.append("| --- | --- | --- | ---: | ---: | --- |")
        for metric in secondary_mismatches:
            lines.append(
                f"| `{metric.map_id}` | `{metric.current_export}` | `{metric.recommendation}` | "
                f"{fmt_int(metric.visible_candidate_polies)} ({pct(metric.visible_candidate_ratio)}) | "
                f"{pct(metric.helper_ratio)} | {metric.reason} |"
            )
        lines.append("")

    lines.append("## Full Map Table")
    lines.append("")
    lines.append(
        "| Map | Recommendation | Confidence | Current export | Models | Objects | Source polys | "
        "Visible candidate | Terrain | Helper | User portals | VisBSP leaves | Largest model | Reason |"
    )
    lines.append(
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |"
    )
    for metric in metrics:
        largest = f"{metric.largest_model_name} ({fmt_int(metric.largest_model_polies)})"
        lines.append(
            f"| `{metric.map_id}` | `{metric.recommendation}` | `{metric.confidence}` | "
            f"`{metric.current_export}` | {fmt_int(metric.model_count)} | {fmt_int(metric.object_count)} | "
            f"{fmt_int(metric.source_polies)} | {fmt_int(metric.visible_candidate_polies)} "
            f"({pct(metric.visible_candidate_ratio)}) | {fmt_int(metric.terrain_polies)} "
            f"({pct(metric.terrain_ratio)}) | {fmt_int(metric.helper_polies)} ({pct(metric.helper_ratio)}) | "
            f"{metric.user_portals} | {fmt_int(metric.visbsp_leaves)} | `{largest}` | {metric.reason} |"
        )
    lines.append("")

    lines.append("## Implementation Implications")
    lines.append("")
    lines.append("- Do not change the MM6-MM8 default ODM/BLV semantics for this classification. Treat these results as MM9")
    lines.append("  import/runtime metadata.")
    lines.append("- DAT helper models named `PhysicsBSP` and `VisBSP` must be preserved losslessly in source metadata, but should")
    lines.append("  not leak as visible ODM faces. They are collision/visibility source structures.")
    lines.append("- Portalized DAT maps with `UserPortal` records need a DAT BSP/portal or BLV-like runtime path for visibility,")
    lines.append("  collision, door/portal behavior, and editor picking. Flattening them into ODM is likely both less faithful")
    lines.append("  and less efficient.")
    lines.append("- Outdoor-like maps can keep the ODM-compatible terrain path short term, but should still retain DAT sidecars for")
    lines.append("  original model names, surfaces, texture flags, objects, mechanisms/events, and helper BSP metadata.")
    lines.append("- `needs_review` maps should be opened in the editor after helper BSP filtering to decide whether they are special")
    lines.append("  arenas/interiors or importer edge cases.")
    lines.append("")
    lines.append("## Rebuild Command")
    lines.append("")
    lines.append("```bash")
    lines.append("python3 tools/mm9_import_discovery/classify_mm9_maps.py")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dat-dir", type=Path, default=DEFAULT_DAT_DIR)
    parser.add_argument("--map-dir", type=Path, default=DEFAULT_MAP_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dat_paths = sorted(args.dat_dir.glob("*.dat"))
    if not dat_paths:
        raise SystemExit(f"no DAT files found under {args.dat_dir}")

    metrics = [collect_metrics(dat_path, args.map_dir) for dat_path in dat_paths]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(make_markdown(metrics, args.dat_dir, args.map_dir), encoding="utf-8")
    print(f"wrote {args.output} from {len(metrics)} DAT maps")


if __name__ == "__main__":
    main()
