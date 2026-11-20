#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = TOOLS_DIR.parent.parent
sys.path.insert(0, str(TOOLS_DIR))

from mm9_item_sources import Mm9ItemIdMap, build_mm9_item_source_manifest  # noqa: E402
from transcode_mm9_dat_to_odm import read_dat_world  # noqa: E402


def markdown_audit(dat_root: Path, item_id_map_path: Path) -> str:
    item_ids = Mm9ItemIdMap.load(item_id_map_path)
    rows: list[tuple[str, int, int, int, int, int, int, int]] = []
    unresolved_rows: list[tuple[str, int, int, str, bool]] = []

    for dat_path in sorted(dat_root.glob("*.dat"), key=lambda path: path.stem.lower()):
        map_id = dat_path.stem.lower()
        manifest = build_mm9_item_source_manifest(
            map_id,
            read_dat_world(dat_path).objects,
            item_ids,
            1.0,
        )
        chests = sum(source.kind == "chest" for source in manifest.loot_containers)
        bags = sum(source.kind == "treasure_bag" for source in manifest.loot_containers)
        rows.append((
            map_id,
            len(manifest.world_items),
            chests,
            bags,
            len(manifest.searchable_loot_props),
            len(manifest.spawned_loot_containers),
            len(manifest.persistent_item_mechanisms),
            sum(source.procedural_death_loot for source in manifest.actor_loot_overrides),
        ))
        unresolved_rows.extend(
            (
                map_id,
                source.source_object_index,
                source.raw_mm9_item_id,
                source.reason,
                source.blocks_generation,
            )
            for source in manifest.unresolved_item_references
        )

    totals = tuple(sum(row[index] for row in rows) for index in range(1, 8))
    lines = [
        "# Generated MM9 Item-Source Audit",
        "",
        "Generated from the original 45 MM9 `WORLDS/*.dat` files by the shared semantic importer. Do not edit the",
        "counts by hand; regenerate this report after importer or item-id-map changes.",
        "",
        "| Map | World items | Chests | Authored bags | Bone piles | Spawned bags | Item mechanisms | "
        "GiveTreasure actors |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    lines.extend(
        f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} | {row[7]} |"
        for row in rows
    )
    lines.extend([
        f"| **Total ({len(rows)} maps)** | **{totals[0]}** | **{totals[1]}** | **{totals[2]}** | "
        f"**{totals[3]}** | **{totals[4]}** | **{totals[5]}** | **{totals[6]}** |",
        "",
        "## Unresolved Item References",
        "",
    ])
    if unresolved_rows:
        lines.extend([
            "These sources remain visible until each raw MM9 item has an explicit canonical mapping. A reviewed",
            "unsupported-content disposition may preserve the broken reference without blocking unrelated generation.",
            "",
            "| Map | Source object | Raw MM9 item | Blocks generation | Reason |",
            "|---|---:|---:|:---:|---|",
        ])
        lines.extend(
            f"| {map_id} | {object_index} | {raw_item_id} | {'yes' if blocks_generation else 'no'} | {reason} |"
            for map_id, object_index, raw_item_id, reason, blocks_generation in unresolved_rows
        )
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the MM9 semantic item-source census.")
    parser.add_argument(
        "--dat-root",
        type=Path,
        default=REPOSITORY_ROOT / "mm9/extracted/WORLDS/WORLDS",
    )
    parser.add_argument(
        "--item-id-map",
        type=Path,
        default=REPOSITORY_ROOT / "assets_dev/worlds/mm9/state/item_ids.yml",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPOSITORY_ROOT / "devdocs/mm9/MM9_ITEM_SOURCE_AUDIT.md",
    )
    arguments = parser.parse_args()

    output_text = markdown_audit(arguments.dat_root, arguments.item_id_map)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(output_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
