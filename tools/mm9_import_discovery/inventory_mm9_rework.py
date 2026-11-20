#!/usr/bin/env python3
"""
Write the Phase 0 inventory of the MM9 rework (devdocs/mm9_rework/INVENTORY.md).

Reads the original MM9 data (mm9/extracted), the generated MM9 world sidecars (assets_dev/worlds/mm9) and the
MM6-MM8 scenes and tables for the balance baselines. Reporting only: it changes no game data.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from convert_abc_model import read_abc
from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE

ROOT = Path(__file__).resolve().parents[2]
MM9_SOURCE = ROOT / "mm9/extracted"
MM9_WORLD = ROOT / "assets_dev/worlds/mm9"
ENGINE_TABLES = ROOT / "assets_dev/engine/data_tables"
DEFAULT_OUTPUT = ROOT / "devdocs/mm9_rework/INVENTORY.md"

SCALE = MM9_TO_OPENYAMM_COORDINATE_SCALE

# Object classes that describe the map rather than content; left out of the extent measurement.
NON_SPATIAL_CLASSES = {
    "SkyPointer", "TOD_Sky", "DemoSkyWorldModel", "WorldProperties", "OutsideDef", "Terrain", "Camera", "DirLight",
}
DOOR_CLASSES = {"Door", "RotatingDoor"}
WATER_CLASSES = {"BlueWater", "ClearWater", "CorrosiveFluid"}
WEATHER_CLASSES = {"Snow", "Rain", "Fog", "WeatherMan", "EarthQuake"}
PROP_CLASSES = {"Prop", "WorldObject", "CandleProp", "DestructableProp", "Brazier", "WallTorch", "Torch", "BonePile"}

# The MM9 starting chapter, in route order.
STARTING_CHAPTER = [
    "bootcamp", "isleofashes", "sturmford", "sturmfordcity", "beethoven", "anskramkeep", "verhoffinruins",
]

# MM6-MM8 starting areas the party leaves at a known level, with the dungeons reached from them.
BASELINES = [
    ("MM7", "mm7", ["7out01.odm", "7d06.blv", "7d28.blv"]),
    ("MM6", "mm6", ["oute3.odm", "6d01.blv", "6d02.blv", "6d18.blv"]),
    ("MM8", "mm8", ["out01.odm", "d05.blv", "d06.blv", "d40.blv"]),
]

# Spawn tier mix per encounter difficulty, as in OutdoorWorldRuntime's EncounterDifficultyTierWeights.
TIER_WEIGHTS = [(100, 0, 0), (90, 8, 2), (70, 20, 10), (50, 30, 20), (30, 40, 30), (10, 50, 40)]


def read_tsv(path: Path) -> list[list[str]]:
    with path.open(encoding="latin-1", newline="") as handle:
        return list(csv.reader(handle, delimiter="\t"))


def class_key(name: str) -> str:
    return name.replace(" ", "").replace("'", "").replace("-", "").lower()


@dataclass
class Mm9Monster:
    number: int
    name: str
    model: str
    skins: tuple[str, ...]
    level: int
    hp: int
    experience: int
    is_monster: bool


def load_mm9_monsters() -> list[Mm9Monster]:
    rows = read_tsv(MM9_SOURCE / "DATA/DATA/MONSTERS.txt")
    header = rows[0]
    monster_column = next(index for index, name in enumerate(header) if name.startswith("IsMons"))
    monsters = []
    for row in rows[1:]:
        if len(row) <= monster_column or not row[0].strip().isdigit():
            continue
        monsters.append(
            Mm9Monster(
                number=int(row[0]),
                name=row[1].strip(),
                model=row[2].strip().lower(),
                skins=tuple(skin.strip().lower() for skin in row[3:6] if skin.strip()),
                level=int(row[7] or 0),
                hp=int(row[8] or 0),
                experience=int(row[10] or 0),
                is_monster=row[monster_column].strip() == "1",
            )
        )
    return monsters


@dataclass
class MapObject:
    object_class: str
    properties: dict[str, object]


def load_raw_objects(path: Path) -> list[MapObject]:
    objects: list[MapObject] = []
    current: MapObject | None = None
    property_name: str | None = None
    for line in path.open(encoding="utf-8"):
        if line.startswith("  - object_index"):
            current = None
            property_name = None
            continue
        if current is None and line.startswith("    name: "):
            current = MapObject(json.loads(line[len("    name: "):]), {})
            objects.append(current)
            continue
        stripped = line.strip()
        if stripped.startswith('- name: "'):
            property_name = stripped[len('- name: "'):-1]
        elif stripped.startswith("value_json: ") and current is not None and property_name is not None:
            try:
                current.properties[property_name] = json.loads(json.loads(stripped[len("value_json: "):]))
            except json.JSONDecodeError:
                pass
            property_name = None
    return objects


@dataclass
class MapReport:
    map_id: str
    location: str
    width: int = 0
    depth: int = 0
    height_range: int = 0
    source_polies: int = 0
    classes: Counter = field(default_factory=Counter)
    monsters: Counter = field(default_factory=Counter)
    npc_actors: int = 0
    terrain_textures: list[str] = field(default_factory=list)
    textures: list[tuple[str, int, int]] = field(default_factory=list)
    exits: list[tuple[str, str]] = field(default_factory=list)
    quests: set[int] = field(default_factory=set)


def percentile_span(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    ordered = sorted(values)
    low = ordered[int(len(ordered) * 0.01)]
    high = ordered[max(0, int(len(ordered) * 0.99) - 1)]
    return (high - low) * SCALE


def read_location_type(scene_path: Path) -> str:
    for line in scene_path.open(encoding="utf-8"):
        if "location_type:" in line:
            return line.split(":", 1)[1].strip().strip('"')
    return "?"


def read_source_polies(metadata_path: Path) -> int:
    for line in metadata_path.open(encoding="utf-8"):
        match = re.match(r"\s+source_polies: (\d+)", line)
        if match:
            return int(match.group(1))
        if line.startswith("bmodels:"):
            break
    return 0


def read_textures(alias_path: Path) -> tuple[list[tuple[str, int, int]], list[str]]:
    data = yaml.load(alias_path.read_text(encoding="utf-8"), Loader=yaml.CSafeLoader)
    textures = []
    terrain = []
    for entry in data.get("textures") or []:
        source = entry.get("source_texture", "").replace("\\", "/")
        textures.append((source, int(entry.get("width", 0)), int(entry.get("height", 0))))
        if "/terrain/" in source.lower():
            terrain.append(source.rsplit("/", 1)[-1].rsplit(".", 1)[0].lower())
    return textures, sorted(set(terrain))


def build_map_reports(monster_by_class: dict[str, Mm9Monster]) -> dict[str, MapReport]:
    maps_dir = MM9_WORLD / "maps"
    reports: dict[str, MapReport] = {}
    for raw_path in sorted(maps_dir.glob("*.raw_objects.yml")):
        map_id = raw_path.name.split(".")[0]
        report = MapReport(map_id, read_location_type(maps_dir / f"{map_id}.scene.yml"))
        objects = load_raw_objects(raw_path)
        xs, ys, zs = [], [], []
        for item in objects:
            report.classes[item.object_class] += 1
            key = class_key(item.object_class)
            if key in monster_by_class:
                if monster_by_class[key].is_monster:
                    report.monsters[monster_by_class[key].name] += 1
                else:
                    report.npc_actors += 1
            position = item.properties.get("Pos")
            if item.object_class not in NON_SPATIAL_CLASSES and isinstance(position, list) and len(position) == 3:
                xs.append(position[0])
                ys.append(position[1])
                zs.append(position[2])
        report.width = int(percentile_span(xs))
        report.depth = int(percentile_span(zs))
        report.height_range = int(percentile_span(ys))
        report.source_polies = read_source_polies(maps_dir / f"{map_id}.mm9.yml")
        report.textures, report.terrain_textures = read_textures(maps_dir / f"{map_id}.material_aliases.yml")
        reports[map_id] = report
    return reports


def attach_exits(reports: dict[str, MapReport]) -> None:
    rows = read_tsv(MM9_WORLD / "data_tables/map_transitions.txt")
    header = rows[0]
    source_column = header.index("SourceMapFile")
    destination_column = header.index("DestinationMapFile")
    days_column = header.index("TravelDays")
    for row in rows[1:]:
        if len(row) <= days_column or not row[source_column]:
            continue
        map_id = row[source_column].removesuffix(".odm")
        destination = row[destination_column].removesuffix(".odm")
        days = row[days_column].strip()
        if map_id in reports:
            reports[map_id].exits.append((destination, days))


def attach_quests(reports: dict[str, MapReport]) -> None:
    data = yaml.load((MM9_WORLD / "state/quest_interactions.yml").read_text(encoding="utf-8"), Loader=yaml.CSafeLoader)
    for interaction in data.get("interactions") or []:
        entries = interaction.get("journal_entries") or []
        for binding in interaction.get("bindings") or []:
            map_id = binding.get("map_id")
            if map_id in reports:
                reports[map_id].quests.update(entries)


@dataclass
class ModelReport:
    model: str
    joints: int
    triangles: int
    clips: list[str]
    events: Counter


def load_model_reports(models: set[str]) -> dict[str, ModelReport]:
    reports = {}
    for path in sorted((MM9_SOURCE / "MODELS/MODELS").glob("*.abc")):
        model = path.name.lower()
        if model not in models:
            continue
        abc = read_abc(path)
        triangles = sum(len(piece.lods[0].faces) for piece in abc.pieces if piece.lods)
        events: Counter = Counter()
        for animation in abc.animations:
            for keyframe in animation.keyframes:
                for event in keyframe.event.split(";"):
                    event = event.strip().split(" ")[0]
                    if event:
                        events[event.lower()] += 1
        reports[model] = ModelReport(model, len(abc.nodes), triangles, [a.name for a in abc.animations], events)
    return reports


# MM6-MM8 baselines


@dataclass
class EngineMonster:
    number: int
    name: str
    picture: str
    level: int
    experience: int


def load_engine_monsters() -> tuple[dict[int, EngineMonster], dict[str, EngineMonster]]:
    by_number: dict[int, EngineMonster] = {}
    by_picture: dict[str, EngineMonster] = {}
    for row in read_tsv(ENGINE_TABLES / "monster_data.txt"):
        if len(row) < 7 or not row[0].strip().isdigit():
            continue
        try:
            monster = EngineMonster(int(row[0]), row[1].strip(), row[2].strip(), int(row[3]), int(row[6]))
        except ValueError:
            continue
        by_number[monster.number] = monster
        by_picture.setdefault(monster.picture.lower(), monster)
    return by_number, by_picture


@dataclass
class Encounter:
    picture: str
    difficulty: int
    count_low: int
    count_high: int


def load_map_stats() -> dict[str, tuple[str, list[Encounter]]]:
    stats = {}
    for row in read_tsv(ENGINE_TABLES / "map_stats.txt")[3:]:
        if len(row) < 28 or not row[2].strip():
            continue
        encounters = []
        for picture_column in (16, 20, 24):
            match = re.match(r"\s*(\d+)\s*-\s*(\d+)", row[picture_column + 3] or "")
            low, high = (int(match.group(1)), int(match.group(2))) if match else (0, 0)
            difficulty = int(row[picture_column + 2]) if row[picture_column + 2].strip().isdigit() else 0
            encounters.append(Encounter(row[picture_column].strip(), difficulty, low, high))
        stats[row[2].strip().lower()] = (row[1].strip(), encounters)
    return stats


@dataclass
class BaselineReport:
    file_name: str
    name: str
    spawn_points: int
    spawned: dict[str, float]
    spawned_experience: float
    placed: Counter
    placed_experience: int
    chests: int
    levels: list[int]


def tier_monster(by_picture: dict[str, EngineMonster], picture: str, tier: str) -> EngineMonster | None:
    return by_picture.get(f"{picture} {tier}".lower())


def baseline_report(world: str, file_name: str, map_stats, by_number, by_picture) -> BaselineReport | None:
    scene_path = ROOT / f"assets_dev/worlds/{world}/maps/{Path(file_name).stem}.scene.yml"
    if not scene_path.exists():
        return None
    scene = yaml.load(scene_path.read_text(encoding="utf-8"), Loader=yaml.CSafeLoader)
    name, encounters = map_stats.get(file_name.lower(), (file_name, []))
    spawned: dict[str, float] = defaultdict(float)
    spawned_experience = 0.0
    levels: list[int] = []
    spawn_points = 0
    for spawn in scene.get("spawns") or []:
        if spawn.get("type_id") != 3:
            continue
        index = int(spawn.get("index", 0))
        if 1 <= index <= 3:
            slot, fixed_tier = index, None
        elif 4 <= index <= 12:
            slot, fixed_tier = (index - 4) % 3 + 1, "ABC"[(index - 4) // 3]
        else:
            continue
        if slot > len(encounters) or not encounters[slot - 1].picture or encounters[slot - 1].picture == "0":
            continue
        spawn_points += 1
        encounter = encounters[slot - 1]
        count = (encounter.count_low + encounter.count_high) / 2
        weights = TIER_WEIGHTS[min(max(encounter.difficulty, 0), 5)]
        tiers = [(fixed_tier, 1.0)] if fixed_tier else [(t, w / 100) for t, w in zip("ABC", weights) if w]
        for tier, share in tiers:
            monster = tier_monster(by_picture, encounter.picture, tier)
            label = monster.name if monster else f"{encounter.picture} {tier}"
            spawned[label] += count * share
            spawned_experience += count * share * (monster.experience if monster else 0)
            if monster:
                levels.append(monster.level)
    placed: Counter = Counter()
    placed_experience = 0
    state = scene.get("initial_state") or {}
    for actor in state.get("actors") or []:
        monster = by_number.get(int(actor.get("monster_info_id", 0)))
        if monster is None or "peasant" in monster.picture.lower():
            continue
        placed[monster.name] += 1
        placed_experience += monster.experience
        levels.append(monster.level)
    # Every scene carries the fixed 20-slot chest table; count the chests its map script opens.
    script_path = ROOT / f"assets_dev/worlds/{world}/events/maps/{Path(file_name).stem}.lua"
    script = script_path.read_text(encoding="utf-8", errors="replace") if script_path.exists() else ""
    chests = len(set(re.findall(r"OpenChest\((\d+)\)", script)))
    return BaselineReport(file_name, name, spawn_points, dict(spawned), spawned_experience, placed, placed_experience,
                          chests, levels)


# Report


def format_monsters(counter: Counter, info: dict[str, Mm9Monster]) -> str:
    parts = []
    for name, count in sorted(counter.items(), key=lambda item: (info[item[0]].level, item[0])):
        monster = info[name]
        parts.append(f"{count}× {name} (L{monster.level}, {monster.experience} XP)")
    return "; ".join(parts)


def write_report(output: Path) -> None:
    monsters = load_mm9_monsters()
    # A DAT class name resolves to the first table row of that name; later duplicates are reported below.
    monster_by_class: dict[str, Mm9Monster] = {}
    duplicate_names: dict[str, list[Mm9Monster]] = defaultdict(list)
    for monster in monsters:
        duplicate_names[monster.name].append(monster)
        monster_by_class.setdefault(class_key(monster.name), monster)
    monster_by_name = {monster.name: monster for monster in reversed(monsters)}

    reports = build_map_reports(monster_by_class)
    attach_exits(reports)
    attach_quests(reports)

    lines: list[str] = []
    out = lines.append
    out("# MM9 rework: Phase 0 inventory")
    out("")
    out("Generated by `tools/mm9_import_discovery/inventory_mm9_rework.py`; do not edit by hand. Sizes are in OpenYAMM")
    out(f"units (MM9 × {SCALE}), measured as the 1st–99th percentile span of placed objects. Monster counts are the")
    out("monsters placed in the DAT world; a class name resolves to the first `MONSTERS.txt` row of that name.")
    out("Quests are the journal entries of quest interactions bound to NPCs placed on the map")
    out("(`state/quest_interactions.yml`).")
    out("")

    out("## Maps")
    out("")
    out("| Map | Kind | Size (W×D) | Height | Source polys | Monsters | Level range | Monster XP | NPCs | Quests "
        "| Chests | Doors | Exits to |")
    out("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for map_id, report in sorted(reports.items()):
        count = sum(report.monsters.values())
        levels = [monster_by_name[name].level for name in report.monsters]
        level_range = f"{min(levels)}–{max(levels)}" if levels else "–"
        experience = sum(monster_by_name[name].experience * n for name, n in report.monsters.items())
        doors = sum(report.classes[name] for name in DOOR_CLASSES)
        exits = ", ".join(sorted({destination for destination, _ in report.exits}))
        out(f"| {map_id} | {report.location} | {report.width // 1000}×{report.depth // 1000}k "
            f"| {report.height_range} | {report.source_polies} | {count} | {level_range} | {experience} "
            f"| {report.npc_actors} | {len(report.quests)} | {report.classes['TreasureChest']} | {doors} | {exits} |")
    out("")
    out("Totals: " + ", ".join([
        f"{len(reports)} maps",
        f"{sum(sum(r.monsters.values()) for r in reports.values())} placed monsters",
        f"{sum(r.npc_actors for r in reports.values())} NPC actors",
        f"{sum(r.classes['TreasureChest'] for r in reports.values())} chests",
        f"{len(set().union(*(r.quests for r in reports.values())))} distinct bound journal entries",
    ]) + ".")
    out("")

    out("## Starting chapter")
    out("")
    for map_id in STARTING_CHAPTER:
        report = reports[map_id]
        experience = sum(monster_by_name[name].experience * n for name, n in report.monsters.items())
        out(f"- **{map_id}** ({report.location}, {sum(report.monsters.values())} monsters, {experience} XP, "
            f"{len(report.quests)} quests): {format_monsters(report.monsters, monster_by_name) or 'none'}")
    out("")

    out("## World graph")
    out("")
    out("Exit triggers from `data_tables/map_transitions.txt`; travel days in brackets where the source sets them.")
    out("")
    for map_id, report in sorted(reports.items()):
        if not report.exits:
            continue
        targets = Counter(report.exits)
        text = ", ".join(
            f"{destination}{f' [{days} d]' if days not in ('', '0', '-1') else ''}{f' ×{n}' if n > 1 else ''}"
            for (destination, days), n in sorted(targets.items()))
        out(f"- {map_id} → {text}")
    routes = read_tsv(MM9_WORLD / "data_tables/transport_routes.txt")
    route_header = routes[0]
    dock_column = route_header.index("DockName")
    destination_column = route_header.index("DestinationName")
    docks: dict[str, set[str]] = defaultdict(set)
    for row in routes[1:]:
        if len(row) > destination_column:
            docks[row[dock_column]].add(row[destination_column])
    out("")
    out("Transport routes: " + "; ".join(f"{dock} → {', '.join(sorted(targets))}"
                                       for dock, targets in sorted(docks.items())) + ".")
    out("")

    out("## Map content")
    out("")
    out("| Map | Props | Lights | Triggers | Script objects | Invisible brushes | Destructibles | Ladders | Water "
        "| Weather | Terrain textures |")
    out("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for map_id, report in sorted(reports.items()):
        classes = report.classes
        weather = ", ".join(f"{name} {classes[name]}" for name in sorted(WEATHER_CLASSES) if classes[name])
        water = sum(classes[name] for name in WATER_CLASSES)
        out(f"| {map_id} | {sum(classes[name] for name in PROP_CLASSES)} "
            f"| {classes['Light'] + classes['ObjectLight'] + classes['GlowingLight']} | {classes['Trigger']} "
            f"| {classes['ScriptObject']} | {classes['InvisibleBrush']} "
            f"| {classes['DestructableBrush'] + classes['DestructableProp']} | {classes['Ladder']} | {water} "
            f"| {weather or '–'} | {', '.join(report.terrain_textures) or '–'} |")
    out("")

    out("## Textures")
    out("")
    all_textures: dict[str, tuple[int, int]] = {}
    usage: Counter = Counter()
    for report in reports.values():
        for source, width, height in report.textures:
            all_textures[source.lower()] = (width, height)
            usage[source.lower()] += 1
    sizes = Counter(f"{w}×{h}" for w, h in all_textures.values())
    folders = Counter(source.split("/")[1] if source.count("/") > 1 else "(root)" for source in all_textures)
    out(f"{len(all_textures)} distinct source textures across all maps; sizes: "
        + ", ".join(f"{size} {count}" for size, count in sizes.most_common(8)) + ".")
    out("")
    out("By source folder: " + ", ".join(f"{folder} {count}" for folder, count in folders.most_common()) + ".")
    out("")
    out(f"Shared by five or more maps: {sum(1 for n in usage.values() if n >= 5)}; used by one map only: "
        f"{sum(1 for n in usage.values() if n == 1)}.")
    out("")

    out("## Creatures")
    out("")
    placed_by_name: Counter = Counter()
    maps_by_name: dict[str, set[str]] = defaultdict(set)
    for report in reports.values():
        for name, count in report.monsters.items():
            placed_by_name[name] += count
            maps_by_name[name].add(report.map_id)
    monster_models = sorted({m.model for m in monsters if m.is_monster and m.model.endswith(".abc")})
    model_reports = load_model_reports(set(monster_models))
    out("Monster bodies from `MONSTERS.txt` rows with `IsMonster` 1. Clips and events come from the ABC files; events")
    out("are timed keyframe strings (contact, footstep, sound and effect cues).")
    out("")
    out("| Model | Joints | Tris | Clips | Rows (level, placed count) | Skin sets | Maps | Events |")
    out("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for model in monster_models:
        rows = [m for m in monsters if m.model == model and m.is_monster]
        model_report = model_reports.get(model)
        names = "; ".join(f"{m.name} L{m.level}" + (f" ({placed_by_name[m.name]})" if placed_by_name[m.name] and
                                                     monster_by_name[m.name] is m else "") for m in rows)
        skins = len({m.skins for m in rows})
        used = len(set().union(*(maps_by_name[m.name] for m in rows)))
        events = ", ".join(f"{e} {n}" for e, n in model_report.events.most_common(6)) if model_report else ""
        joints = model_report.joints if model_report else "?"
        triangles = model_report.triangles if model_report else "?"
        clips = len(model_report.clips) if model_report else "?"
        out(f"| {model.removesuffix('.abc')} | {joints} | {triangles} | {clips} | {names} | {skins} | {used} "
            f"| {events} |")
    out("")
    duplicates = {name: rows for name, rows in duplicate_names.items()
                  if len(rows) > 1 and any(row.is_monster for row in rows)}
    if duplicates:
        out("Monster names used by more than one row (DAT placement resolves to the first): "
            + "; ".join(f"{name} " + "/".join(f"#{r.number} L{r.level}" for r in rows)
                        for name, rows in sorted(duplicates.items())) + ".")
        out("")

    out("## MM6–MM8 starting-area baselines")
    out("")
    out("Spawn points expand to the mean of the map-stats appear range, split over tiers by the encounter difficulty")
    out("weights the runtime uses. Placed actors exclude peasants. Quest experience is not included.")
    out("")
    by_number, by_picture = load_engine_monsters()
    map_stats = load_map_stats()
    for game, world, files in BASELINES:
        for file_name in files:
            baseline = baseline_report(world, file_name, map_stats, by_number, by_picture)
            if baseline is None:
                out(f"- {game} {file_name}: scene not found")
                continue
            expected = sum(baseline.spawned.values())
            top = ", ".join(f"{name} {count:.0f}" for name, count in
                            sorted(baseline.spawned.items(), key=lambda item: -item[1])[:6])
            placed = ", ".join(f"{name} {count}" for name, count in baseline.placed.most_common(5))
            level_range = f"L{min(baseline.levels)}–{max(baseline.levels)}" if baseline.levels else "no monsters"
            out(f"- **{game} {baseline.name}** (`{file_name}`, {level_range}): {baseline.spawn_points} spawn points → about "
                f"{expected:.0f} monsters, {baseline.spawned_experience:.0f} XP ({top}); "
                f"placed {sum(baseline.placed.values())} ({baseline.placed_experience} XP{': ' + placed if placed else ''}); "
                f"{baseline.chests} chests opened by the map script.")
    out("")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    write_report(arguments.output)
    print(f"wrote {arguments.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
