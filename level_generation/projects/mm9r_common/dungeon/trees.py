"""
MM9's trees on the cities and dungeons as MM6-MM8 3D trees (DECORATIONS_AND_GRASS.md step 3: trees are never MM9's),
as the outdoor regions have them: a props.json entry whose decoration is one of MM9's tree models (`mm9_tree04_x100`,
`mm9_tree05`: the cities' props projects placed MM9's own models) is drawn as the region vegetation's
`mm9v_<ours>_<height>` row instead (level_generation/props/mm9_outdoor_regions_claude/scripts/vegetation.py: the same
species choice, weights and MM9 height), set `sink` units into the ground. Unique story trees (the Green Man's tree,
the Tree of Life) are not MM9 tree models and stay.

The rows must exist before a conversion (content.py refuses a decoration without one):

    python3 level_generation/projects/mm9r_common/dungeon/trees.py [map ...]   # writes the missing rows

writes the rows the listed maps' props.json need (default: every mm9r_* project with MM9 trees) into assets_dev
(rows.py) and copies the changed tables into the review roots.
"""

from __future__ import annotations

import copy
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.append(str(REPO / "level_generation/props/mm9_outdoor_regions_claude/scripts"))
import vegetation  # noqa: E402

TREE_DECORATION = re.compile(r"mm9_(tree\w+?)(?:_x(\d+))?")
_ENGINE_BINDINGS = []       # vegetation.engine_bindings(), parsed once per process (once per tree took 6 s on a city)


def _engine_binding(name: str) -> dict:
    """{name: a fresh copy of the engine's binding of that decoration}, as vegetation.row reads it."""
    if not _ENGINE_BINDINGS:
        _ENGINE_BINDINGS.append(vegetation.engine_bindings())
    return {name: copy.deepcopy(_ENGINE_BINDINGS[0][name])}


def swap(entry: dict, stem: str) -> tuple[str, dict] | None:
    """(our decoration, its row) for an entry drawn with one of MM9's tree models, else None. The species is picked by
    the MM9 object index and the map's stem, so a reconversion keeps each tree's species."""
    match = TREE_DECORATION.fullmatch((entry.get("decoration") or "").lower())
    if match is None or match.group(1) not in vegetation.CHOICES:
        return None
    species, scale = match.group(1), int(match.group(2) or 100) / 100
    ours = vegetation.pick(species, int(entry["source_object"]), stem)
    row = vegetation.row(species, ours, scale, _engine_binding(ours.lower()))
    return row["name"], row


def main(argv: list[str]) -> int:
    import rows  # noqa: E402 (the regions' row writer)
    projects = [REPO / f"level_generation/projects/mm9r_{name}" for name in argv] or \
        sorted((REPO / "level_generation/projects").glob("mm9r_*"))
    needed = {}
    for project in projects:
        props = project / "props.json"
        if not props.exists():
            continue
        stem = project.name.removeprefix("mm9r_")
        for entry in json.loads(props.read_text()):
            swapped = swap(entry, stem)
            if swapped is not None:
                needed[swapped[0]] = swapped[1]
    added = rows.ensure(list(needed.values()))
    print(f"{len(needed)} tree rows needed, {len(added)} added: {', '.join(added) or '-'}")
    if added:
        tables = [rows.DECORATIONS, rows.SPRITES, rows.BINDINGS]
        for root in ("output/mm9_rework/assets_dev", "output/mm9_rework/isleofashes_blv_root"):
            for table in tables:
                target = REPO / root / table.relative_to(REPO / "assets_dev")
                temporary = target.with_name(target.name + ".trees")
                shutil.copyfile(table, temporary)
                temporary.chmod(0o644)
                temporary.replace(target)
        print("copied the tables into both review roots")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
