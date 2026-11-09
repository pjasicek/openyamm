#!/usr/bin/env python3
"""Install the MM9 item art repainted in MM7/MM8 style (2026-11-05) at the engine's x2 icon scale.

The art project (git-ignored, default level_generation/ui/mm9_item_icons_20261104/) owns the paintings:
``designs.json`` and ``items/<design>/icon_a_x2.png`` for the inventory icons, ``paperdoll/runtime/`` for the fitted
paperdoll files of worn equipment and their complex_item_pictures rows. This tool writes:

- ``generated_item_art_x2/mm9_item_<id>.png`` (git-ignored) and the committed manifest ``mm9_item_generated_art.yml``
  that ``import_mm9_items.py`` installs into ``assets_dev/worlds/mm9/icons_x2/``;
- the paperdoll files into ``assets_dev/worlds/mm9/icons_x2/`` and their rows into
  ``assets_dev/worlds/mm9/data_tables/complex_item_pictures.txt``.

Then run ``generate_mm9_item_equipment_visuals.py`` (weapon and shield grips) and ``import_mm9_items.py``; see
``level_generation/ui/mm9_item_icons_20261104/HANDOFF.md``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import yaml
from PIL import Image


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
TOOL_ROOT = Path(__file__).resolve().parent
DEFAULT_PROJECT = REPOSITORY_ROOT / "level_generation/ui/mm9_item_icons_20261104"
ART_DIRECTORY = TOOL_ROOT / "generated_item_art_x2"
MANIFEST = TOOL_ROOT / "mm9_item_generated_art.yml"
WORLD_ROOT = REPOSITORY_ROOT / "assets_dev/worlds/mm9"
DOLL_SUFFIXES = ("v1", "v2", "v3", "v4", "v5", "v6", "v1a", "v2a", "v3a", "v4a", "v5a", "v6a")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install_icons(project: Path) -> int:
    designs = json.loads((project / "designs.json").read_text(encoding="utf-8"))
    if ART_DIRECTORY.exists():
        shutil.rmtree(ART_DIRECTORY)
    ART_DIRECTORY.mkdir()
    items: dict[int, dict[str, object]] = {}
    for design in designs:
        source = project / "items" / str(design["design_id"]) / "icon_a_x2.png"
        with Image.open(source) as image:
            if image.mode != "RGBA" or image.getchannel("A").getextrema()[0] == 255:
                raise ValueError(f"{source} has no transparent alpha")
            size = list(image.size)
        for item_id in design["item_ids"]:
            target = ART_DIRECTORY / f"mm9_item_{item_id}.png"
            shutil.copyfile(source, target)
            items[item_id - 10000] = {
                "item_id": item_id,
                "asset": target.relative_to(TOOL_ROOT).as_posix(),
                "asset_sha256": sha256_file(target),
                "size_x2": size,
                "design_id": design["design_id"],
                "source": f"{design['pcx']}",
            }
    document = {
        "format_version": 2,
        "kind": "mm9_generated_inventory_art",
        "scale": 2,
        "project": project.relative_to(REPOSITORY_ROOT).as_posix(),
        "method": "Codex image generation per source PCX design (MM7/MM8 inventory style), keyed, fitted to the "
                  "family's MM7/MM8 x2 canvas; see the project's README.md",
        "items": dict(sorted(items.items())),
    }
    MANIFEST.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    return len(items)


def install_dolls(project: Path) -> tuple[int, int]:
    runtime = project / "paperdoll/runtime"
    icons = WORLD_ROOT / "icons_x2"
    icons.mkdir(parents=True, exist_ok=True)
    files = sorted(runtime.glob("icons_x2/mm9_item_*.png"))
    for file in files:
        if not file.stem.endswith(DOLL_SUFFIXES):
            raise ValueError(f"unexpected paperdoll file {file.name}")
        shutil.copyfile(file, icons / file.name)
    rows = (runtime / "complex_item_pictures.txt").read_text(encoding="utf-8").splitlines()
    header = rows[0].split("\t")
    header[2] = "MM9 equipment"
    table = ["\t".join(header), rows[1]] + rows[2:]
    (WORLD_ROOT / "data_tables/complex_item_pictures.txt").write_text("\n".join(table) + "\n", encoding="utf-8")
    return len(files), len(rows) - 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    arguments = parser.parse_args()
    project = arguments.project.resolve()
    icons = install_icons(project)
    dolls, rows = install_dolls(project)
    print(f"{icons} inventory icons staged for import_mm9_items.py; {dolls} paperdoll files and {rows} "
          "complex_item_pictures rows installed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
