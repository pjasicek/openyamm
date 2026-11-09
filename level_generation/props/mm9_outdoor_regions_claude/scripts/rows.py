"""
MM9 world decoration rows added by the outdoor regions' props (placements.py): one per new (model, height) a region
needs: the swapped vegetation (MM6-MM8 tree, bush and flower models at MM9's own heights, vegetation.py) and the
props' scale variants no other map placed yet. Written into assets_dev (temporary file, then rename: the files are
hard-linked into the review roots, which need review_root.refresh() afterwards), as the props projects' tables.py:

  - worlds/mm9/data_tables/decoration_data.txt: the row (next free number of the world range 2001-2999);
  - worlds/mm9/rendering/sprite_frame_data_world_decorations.yml: a 'pending' sprite;
  - worlds/mm9/models/indoor_decorations.yml: the binding (the regions are BLVs).

A row already present keeps its number and binding.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[4]
WORLD = REPO / "assets_dev/worlds/mm9"
DECORATIONS = WORLD / "data_tables/decoration_data.txt"
SPRITES = WORLD / "rendering/sprite_frame_data_world_decorations.yml"
BINDINGS = WORLD / "models/indoor_decorations.yml"
ROW_RANGE = (2001, 2999)


def write(path: Path, text: str) -> None:
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".")
    with os.fdopen(fd, "w", encoding="latin-1" if path.suffix == ".txt" else "utf-8", newline="") as handle:
        handle.write(text)
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def table_rows() -> dict:
    """Name (lower case) -> the row's cells, for the MM9 world range."""
    out = {}
    for line in DECORATIONS.read_text(encoding="latin-1").split("\n"):
        cells = line.split("\t")
        if len(cells) >= 13 and cells[0].strip().isdigit() and ROW_RANGE[0] <= int(cells[0]) <= ROW_RANGE[1]:
            out[cells[1].strip().lower()] = cells
    return out


def bindings() -> list[dict]:
    return yaml.safe_load(BINDINGS.read_text())["decorations"]


def ensure(rows: list[dict]) -> list[str]:
    """rows: {name, hint, radius, height, binding: {model, height, ...}}; adds the missing ones, returns their names."""
    existing = table_rows()
    bound = {b["name"].lower() for b in bindings()}
    lines = DECORATIONS.read_text(encoding="latin-1").split("\n")
    trailing = lines[-1] == ""
    body = lines[:-1] if trailing else lines
    numbers = [int(c[0]) for c in existing.values()]
    sprite_ids = [int(c[12]) for c in existing.values()]
    sprites = SPRITES.read_text()
    binding_text = BINDINGS.read_text()
    added = []
    for row in rows:
        name = row["name"]
        if name.lower() not in existing:
            number, sprite = max(numbers) + 1, max(sprite_ids) + 1
            assert number <= ROW_RANGE[1], "the MM9 world decoration range is full"
            numbers.append(number)
            sprite_ids.append(sprite)
            body.append("\t".join([str(number), name, row["hint"], "0", str(int(row["radius"])),
                                   str(int(round(row["height"]))), "0", "0", "0", "0", "0", "0", str(sprite), "-"]))
            sprites = sprites.rstrip("\n") + (f"\n  - sprite_id: {sprite}\n    sprite_name: \"{name}\"\n    frames:\n"
                                              f"      - texture_name: \"pending\"\n        frame_length_raw: 0\n"
                                              f"        flags: [First]\n        scale: 1.0\n")
            added.append(name)
        if name.lower() not in bound and not re.search(rf"^  - name: {re.escape(name)}$", binding_text, re.M):
            block = yaml.safe_dump([dict({"name": name}, **row["binding"])], sort_keys=False)
            binding_text = binding_text.rstrip("\n") + "\n" + "".join("  " + line + "\n" for line in block.splitlines())
            bound.add(name.lower())
    if added:
        write(DECORATIONS, "\n".join(body) + ("\n" if trailing else ""))
        write(SPRITES, sprites)
    if binding_text != BINDINGS.read_text():
        write(BINDINGS, binding_text)
    return added
