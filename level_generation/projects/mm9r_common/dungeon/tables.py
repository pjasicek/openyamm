"""
The map's rows in the review root's shared tables and the install of the built map:

- engine/data_tables/map_stats.txt: the row of the old map names the BLV;
- worlds/mm9/data_tables/map_transitions.txt: exits from the map and arrivals into it (moved into the BLV's frame by
  overrides.yml `offset`; arrivals land on the floor; overrides.yml `exits` can reach an exit volume down to a floor);
- worlds/mm9/ui/maps/catalog.yml: the map's painted MM9 map (its 2x image, bounds and floor heights) in the BLV's
  frame. Every map keeps it (user, 2026-11-09); the Map style setting picks it or the line map where the BLV has
  outlines.

Shared tables are changed only inside `flock -x locks/review_tables.lock` (fcntl on the same file), read and
written with newline="" (map_stats mixes CRLF and LF rows: every line keeps its own ending), and installed with
review_root.install (temporary file, then rename; the path is recorded as owned).
"""

from __future__ import annotations

import fcntl
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

import yaml

import review_root

from .source import ROOT, SCALE, floor_below

LOCKS = Path(__file__).resolve().parents[1] / "locks"
OLD_SIDECARS = (".odm", ".render", ".render.yml", ".nav", ".nav.yml", ".lighting", ".mm9.yml", ".model_assets.yml",
                ".raw_objects.yml", ".material_aliases.yml", ".events.yml", "_authored.scene.yml")
OLD_EVENT_SIDECARS = (".script_ir.yml", "_authored.lua")     # beside the map's Lua; an `_authored` file replaces it


@contextmanager
def locked(name: str):
    """An exclusive lock on locks/<name> (the same lock `flock -x locks/<name> <command>` takes)."""
    LOCKS.mkdir(exist_ok=True)
    with open(LOCKS / name, "a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


# The old import's original tables, frozen before the rebuilt maps were promoted into assets_dev (P1, 2026-11-06):
# assets_dev now holds the rebuilt rows (original_tables/README.md).
ORIGINAL_TABLES = Path(__file__).resolve().parents[1] / "original_tables"


def read_lines(path: Path) -> list[str]:
    with open(path, newline="") as stream:
        return stream.read().split("\n")


def map_stats_text(project, current_text: str) -> str:
    """The current map_stats.txt with the old map's rows (by id, from the frozen original) naming the BLV, with the
    balance's treasure level and disarm difficulty where it sets them (tools/mm9_import_discovery/mm9_chest_balance.py
    MAP_TREASURE_LEVEL, MAP_DISARM_DIFFICULTY)."""
    from mm9_chest_balance import (MAP_DISARM_DIFFICULTY, MAP_STATS_LOCK_COLUMN, MAP_STATS_TREASURE_COLUMN,
                                   MAP_TREASURE_LEVEL)
    replacements = {}
    for line in read_lines(ORIGINAL_TABLES / "map_stats.txt"):
        cells = line.split("\t")
        if len(cells) > 2 and cells[2] == project.old_map:
            cells[2] = project.map
            if project.stem in MAP_TREASURE_LEVEL:
                cells[MAP_STATS_TREASURE_COLUMN] = str(MAP_TREASURE_LEVEL[project.stem])
            if project.stem in MAP_DISARM_DIFFICULTY:
                cells[MAP_STATS_LOCK_COLUMN] = str(MAP_DISARM_DIFFICULTY[project.stem])
            replacements[cells[0]] = "\t".join(cells)
    if not replacements:
        raise SystemExit(f"map_stats.txt has no row for {project.old_map}")
    out = []
    for line in current_text.split("\n"):
        cells = line.split("\t")
        out.append(replacements.get(cells[0], line) if len(cells) > 2 and cells[0] in replacements else line)
    return "\n".join(out)


def relayed_exits(project) -> dict:
    """Exits the party reaches through a trigger elsewhere: a player-triggerable Trigger that sends an ExitTrigger
    `trigger` (Boot Camp's dock Trigger0 fires ExitTrigger0, which sits far out at sea). {exit name (lower case):
    (centre, half extents)} in the old import's frame (LT x 2.56, as the original rows): the relay's own box."""
    from transcode_mm9_dat_to_odm import read_dat_world
    objects = [(o.name, {x.name: x.value for x in o.properties}) for o in read_dat_world(project.dat).objects]
    exits = {str(p.get("Name", "")).lower() for kind, p in objects if kind == "ExitTrigger"}
    relays = {}
    for kind, p in objects:
        if kind != "Trigger" or not p.get("PlayerTriggerable") or "Pos" not in p or "Dims" not in p:
            continue
        for k in range(1, 11):
            target = str(p.get(f"TargetName{k}") or "").lower()
            if target in exits and str(p.get(f"MessageName{k}") or "").strip().lower() == "trigger":
                pos, dims = p["Pos"], p["Dims"]
                relays.setdefault(target, ([pos[0] * SCALE, pos[2] * SCALE, pos[1] * SCALE],
                                           [dims[0] * SCALE, dims[2] * SCALE, dims[1] * SCALE]))
    return relays


def transitions_text(project, polygons, current_text: str, facings: dict | None = None) -> tuple[str, list]:
    """The current map_transitions.txt with the map's exits and arrivals changed (computed from the assets_dev
    originals, merged by row id so other maps' changes stay). facings: DAT start name (lower case) -> native yaw;
    an arrival at that start faces it (the old rows carry the old importer's quarter-turned -ry)."""
    exit_bottoms = {name: rule["bottom_lt"] for name, rule in (project.overrides.get("exits") or {}).items()
                    if "bottom_lt" in rule}
    relays = relayed_exits(project)
    original = read_lines(ORIGINAL_TABLES / "map_transitions.txt")
    header = original[0].split("\t")
    column = {name: i for i, name in enumerate(header)}
    replacements, changes = {}, []
    # A row two converted maps share (an exit of one into the other) is changed by both: start from the review root's
    # current row, so the other map's end of it stays (Thousand Terrors' ExitTrigger1 into the Hall of the Gods lost
    # its source BLV to the Hall's rebuild, and the game refused the table), and rebuild this map's own end from the
    # original, so its exit and arrival settings apply on every install, not only the first.
    source_side = range(column["SourceMap"], column["HalfExtentZ"] + 1)
    destination_side = range(column["DestinationMap"], column["FacingYawUnits"] + 1)
    current_rows = {line.split("\t")[0]: line for line in current_text.split("\n") if line}
    # Rows another conversion added (not in the originals: Arslegard City's transition 638 into the Thjorgard
    # wilderness) are this map's too where they name it: their current text stands in for the original.
    original_ids = {line.split("\t")[0] for line in original[1:]}
    added = [line for row_id, line in current_rows.items() if row_id not in original_ids and row_id != header[0]]
    for line in original[1:] + added:
        original_cells = line.split("\t")
        if len(original_cells) < len(header):
            continue
        cells = list(original_cells)
        current_row = current_rows.get(cells[0])
        if current_row is not None and len(current_row.split("\t")) == len(cells):
            cells = current_row.split("\t")
        owns_source = original_cells[column["SourceMapFile"]] == project.old_map
        owns_destination = original_cells[column["DestinationMapFile"]] == project.old_map
        for side, owned in ((source_side, owns_source), (destination_side, owns_destination)):
            if owned:
                for i in side:
                    cells[i] = original_cells[i]
        changed = False
        if owns_source:
            cells[column["SourceMapFile"]] = project.map
            relay = relays.get(cells[column["SourceName"]].lower())
            if relay is not None:               # the exit's volume is the trigger that fires it
                for axis, name in enumerate("XYZ"):
                    cells[column[f"Center{name}"]] = str(int(round(relay[0][axis])))
                    cells[column[f"HalfExtent{name}"]] = str(int(round(relay[1][axis])))
            # the rows (and relays) are in the old map's frame; the BLV's frame is shifted by overrides.yml `offset`
            for axis, name in enumerate("XYZ"):
                cells[column[f"Center{name}"]] = str(int(round(float(cells[column[f"Center{name}"]])
                                                               - project.offset[axis])))
            bottom = exit_bottoms.get(cells[column["SourceName"]])
            if bottom is not None:              # the volume reaches down to the floor the party stands on
                top = float(cells[column["CenterZ"]]) + float(cells[column["HalfExtentZ"]])
                low = bottom * SCALE - project.offset[2]
                cells[column["CenterZ"]] = str(int(round((top + low) / 2)))
                cells[column["HalfExtentZ"]] = str(int(round((top - low) / 2)))
            changed = True
        if owns_destination:
            cells[column["DestinationMapFile"]] = project.map
            # the arrival in the BLV's frame (the old map's frame shifted by overrides.yml `offset`), on the floor below
            arrival = [float(cells[column[f"Arrival{name}"]]) - project.offset[axis] for axis, name in enumerate("XYZ")]
            for axis, name in enumerate("XYZ"):
                cells[column[f"Arrival{name}"]] = str(int(round(arrival[axis])))
            floor = floor_below(polygons, project.lt_from_native(arrival))
            if floor is not None:
                cells[column["ArrivalZ"]] = str(int(round(floor * SCALE - project.offset[2])) + 1)
            facing = (facings or {}).get(cells[column["ResolvedStartPoint"]].lower())
            if facing is not None:
                cells[column["FacingDegrees"]] = f"{facing:g}"
                cells[column["FacingYawUnits"]] = str(int(round(facing / 360 * 2048)) % 2048)
            changed = True
        if changed:
            replacements[cells[0]] = "\t".join(cells)
            changes.append({"id": cells[0], "source": cells[column["SourceMapFile"]], "name": cells[column["SourceName"]],
                            "facing": cells[column["FacingDegrees"]],
                            "destination": cells[column["DestinationMapFile"]],
                            "centre": [cells[column[k]] for k in ("CenterX", "CenterY", "CenterZ")]
                            if "CenterX" in column else None,
                            "arrival": [cells[column["ArrivalX"]], cells[column["ArrivalY"]], cells[column["ArrivalZ"]]]})
    out = [replacements.get(line.split("\t")[0], line) for line in current_text.split("\n")]
    return "\n".join(out), changes


# The old import's painted-map catalog: world bounds and floor heights in the old map's frame (LT x 2.56).
ORIGINAL_CATALOG = ORIGINAL_TABLES / "catalog.yml"
# Bounds measured against the rebuilt map where MM9's painting does not match MM9's own bounds (same frame).
MAP_IMAGE_FIT = ORIGINAL_TABLES / "map_image_fit.yml"


def _catalog_entries(text: str) -> tuple[list[str], dict[str, list[str]]]:
    """The catalog's header lines and each map's entry lines, by map stem."""
    header, entries, current = [], {}, None
    for line in text.split("\n"):
        if not line.strip():
            continue
        if line.startswith("  - map: "):
            current = line.split(":", 1)[1].strip()
            entries[current] = []
        (header if current is None else entries[current]).append(line)
    return header, entries


def _fitted_entry(stem: str, lines: list[str]) -> list[str]:
    """The entry with its world bounds replaced by the measured ones in map_image_fit.yml, if the map has them."""
    fitted = (yaml.safe_load(MAP_IMAGE_FIT.read_text()) or {}).get("maps", {}) if MAP_IMAGE_FIT.exists() else {}
    if stem not in fitted:
        return lines
    bounds = fitted[stem]["world_bounds"]
    out = []
    for line in lines:
        key = line.strip().partition(":")[0]
        if key in bounds:
            indent = line[:len(line) - len(line.lstrip())]
            line = f"{indent}{key}: {bounds[key]:.2f}".rstrip("0").rstrip(".")
        out.append(line)
    return out


def _offset_entry(lines: list[str], offset) -> list[str]:
    """A catalog entry moved into the BLV's frame: the converter places every point at old - offset, so the painted
    map's bounds (x, y) and floor heights (z) move by the same amount. The texture is the 2x PNG
    (level_generation/minimaps/mm9_esrgan_20261109); width and height stay the native sizes, which set the zoom."""
    keys = {"min_x": 0, "max_x": 0, "min_y": 1, "max_y": 1, "minimum_z": 2, "maximum_z": 2}
    out = []
    for line in lines:
        key, _, value = line.strip().partition(": ")
        indent = line[:len(line) - len(line.lstrip())]
        if key in keys and value:
            moved = f"{float(value) - offset[keys[key]]:.2f}".rstrip("0").rstrip(".")
            line = f"{indent}{key}: {moved}"
        elif key == "- texture" and value.endswith(".pcx"):
            line = f"{indent}- texture: {value[:-4]}.png"
        out.append(line)
    return out


def catalog_text(project, current_text: str) -> str:
    """The current minimap catalog with the map's entry (its painted MM9 map) rewritten from the old import's catalog
    and moved by the project's offset: the indoor minimap and the journal map draw the painted map (IndoorWorldRuntime;
    the Map style setting may choose the line map instead where the BLV has outlines) and place the party on it by
    those bounds. Checked against the built floors by tools/mm9_import_discovery/check_mm9_map_images.py, whose
    --refine measures the bounds of the maps MM9 painted off its own extent (map_image_fit.yml)."""
    header, entries = _catalog_entries(current_text)
    _, original = _catalog_entries(ORIGINAL_CATALOG.read_text())
    entries[project.stem] = _offset_entry(_fitted_entry(project.stem, original[project.stem]), project.offset)
    return "\n".join(header + [line for stem in sorted(entries) for line in entries[stem]]) + "\n"


TABLES = {"engine/data_tables/map_stats.txt": "stats", "worlds/mm9/data_tables/map_transitions.txt": "transitions",
          "worlds/mm9/ui/maps/catalog.yml": "catalog"}


def update_tables(project, polygons, write: bool = True, facings: dict | None = None) -> tuple[dict, list]:
    """Reads the review root's current tables and installs the map's rows, all inside the review tables lock.
    write=False computes the texts only (scratch builds)."""
    texts, changes = {}, []
    with locked("review_tables.lock"):
        for relative, kind in TABLES.items():
            current = "\n".join(read_lines(review_root.mirror_path(relative)))
            if kind == "stats":
                texts[relative] = map_stats_text(project, current)
            elif kind == "transitions":
                texts[relative], changes = transitions_text(project, polygons, current, facings)
            else:
                texts[relative] = catalog_text(project, current)
            if write and texts[relative] != current:
                review_root.install(relative, texts[relative].encode())
    return texts, changes


def install_map(project, runtime: Path) -> None:
    """The BLV, scene and Lua into the review root; the old map's sidecars and script IR removed from the mirror. The
    BLV's own baked lighting (an indoor OYILIT1 file) shares the old map's .lighting name and is kept (the game
    ignores it once a rebuild changes the BLV; bake again)."""
    maps = Path("worlds/mm9/maps")
    stem = project.stem
    for suffix in OLD_SIDECARS:
        target = review_root.mirror_path(maps / f"{stem}{suffix}")
        if suffix == ".lighting" and target.is_file() and target.read_bytes()[:8] == b"OYILIT1\0":
            continue
        review_root.remove(maps / f"{stem}{suffix}")
    for suffix in OLD_EVENT_SIDECARS:
        review_root.remove(Path("worlds/mm9/events/maps") / f"{stem}{suffix}")
    review_root.install_file(maps / project.map, runtime / project.map)
    review_root.install_file(maps / f"{stem}.scene.yml", runtime / f"{stem}.scene.yml")
    review_root.install_file(Path("worlds/mm9/events/maps") / f"{stem}.lua", runtime / f"{stem}.lua")


def install_original_comparison(project) -> None:
    """The original map may forbid saving, which the isolated launcher needs: the second mirror
    (output/mm9_rework/assets_original) gets a copy of the old scene that allows it (temporary file, then rename)."""
    mirror = ROOT / "output/mm9_rework/assets_original"
    target = mirror / f"worlds/mm9/maps/{project.stem}.scene.yml"
    if not mirror.exists():
        print(f"note: {mirror} is missing; the comparison tour cannot run")
        return
    text = (ROOT / f"assets_editor_dev/worlds/mm9/maps/{project.stem}.scene.yml").read_text()
    text = text.replace("  allow_save_game: false", "  allow_save_game: true", 1)
    if target.exists() and target.read_text() == text:
        return
    handle, temporary = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.")
    with os.fdopen(handle, "w") as stream:
        stream.write(text)
    os.chmod(temporary, 0o644)
    os.replace(temporary, target)
