#!/usr/bin/env python3
from __future__ import annotations

import argparse
import struct
from collections import Counter
from pathlib import Path

import yaml


YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

ACTIVE_SLICE_EXPECTATIONS = {
    "bootcamp": {
        "geometry_file": "bootcamp.odm",
        "event_ids": {32000, 32001, 32002, 32003, 32004, 32010},
        "replaced_event_ids": {30563, 30564},
        "interactive_event_ids": {32000, 32001, 32002, 32003, 32004},
        "entity_event_id": 32010,
        "minimum_actors": 9,
        "minimum_chests": 5,
        "mm9_dialogue_bindings": {207: 436, 209: 101, 210: 204, 211: 206},
    },
}

KNOWN_AUDIT_ONLY_MECHANISMS = {
    ("InvisibleBrush", "collision_volume"): "script-linked collision volume",
    ("RotatingBrush", "rotating_brush"): "continuous axis/revolution-time rotation",
}


def mm9_map_rows(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines() if "\tmm9\t" in line]


def row_map_id(row: str) -> str:
    return row.split("\t", 1)[0]


def fnv1a64(data: bytes) -> int:
    value = 14695981039346656037
    for byte in data:
        value ^= byte
        value = (value * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return value


def synchronize_editor_map_stats(source_path: Path, editor_path: Path) -> None:
    source_rows = mm9_map_rows(source_path)
    source_ids = {row_map_id(row) for row in source_rows}
    editor_lines = editor_path.read_text(encoding="utf-8").splitlines()
    retained_lines = [
        line
        for line in editor_lines
        if not (line and row_map_id(line) in source_ids)
    ]
    insertion_index = len(retained_lines)

    while insertion_index > 0 and not retained_lines[insertion_index - 1]:
        insertion_index -= 1

    synchronized_lines = retained_lines[:insertion_index] + source_rows + retained_lines[insertion_index:]
    editor_path.write_text("\n".join(synchronized_lines) + "\n", encoding="utf-8")


def validate_active_slice(maps_root: Path, events_root: Path) -> list[str]:
    failures: list[str] = []

    for map_stem, expectation in ACTIVE_SLICE_EXPECTATIONS.items():
        scene_path = maps_root / f"{map_stem}_authored.scene.yml"
        base_scene_path = maps_root / f"{map_stem}.scene.yml"
        event_path = events_root / f"{map_stem}_authored.lua"
        geometry_path = maps_root / expectation["geometry_file"]
        lighting_path = maps_root / f"{map_stem}.lighting"

        if not scene_path.is_file():
            failures.append(f"active slice {map_stem}: missing authored scene {scene_path}")
            continue
        if not base_scene_path.is_file():
            failures.append(f"active slice {map_stem}: missing generated scene {base_scene_path}")
            continue

        if not lighting_path.is_file():
            failures.append(f"active slice {map_stem}: missing binary lighting sidecar {lighting_path}")
        else:
            lighting_bytes = lighting_path.read_bytes()
            if len(lighting_bytes) < 96 or lighting_bytes[:8] != b"OYMLIT1\0":
                failures.append(f"active slice {map_stem}: invalid binary lighting header")
            else:
                header = struct.unpack_from("<IIQ13I", lighting_bytes, 8)
                version, header_size, geometry_hash = header[:3]
                page_count, face_count, vertex_count, light_count = header[5:9]
                page_offset, face_offset, vertex_offset, light_offset, pixel_offset, file_size = header[9:15]
                expected_face_offset = header_size + page_count * 16
                expected_vertex_offset = expected_face_offset + face_count * 24
                expected_light_offset = expected_vertex_offset + vertex_count * 12
                expected_pixel_offset = expected_light_offset + light_count * 80
                if (
                    version != 3
                    or header_size != 96
                    or page_count == 0
                    or face_count == 0
                    or light_count == 0
                    or page_offset != header_size
                    or face_offset != expected_face_offset
                    or vertex_offset != expected_vertex_offset
                    or light_offset != expected_light_offset
                    or pixel_offset != expected_pixel_offset
                    or file_size != len(lighting_bytes)
                    or not geometry_path.is_file()
                    or geometry_hash != fnv1a64(geometry_path.read_bytes())
                ):
                    failures.append(f"active slice {map_stem}: inconsistent binary lighting layout")

        scene = yaml.load(scene_path.read_text(encoding="utf-8"), Loader=YAML_LOADER)
        base_scene = yaml.load(base_scene_path.read_text(encoding="utf-8"), Loader=YAML_LOADER)
        source = scene.get("source", {})
        runtime_restrictions = scene.get("runtime_restrictions", {})
        authored_content = scene.get("authored_content", {})
        interactive_faces = scene.get("bmodel_faces", {}).get("interactive_faces", [])
        actors = base_scene.get("initial_state", {}).get("actors", []) + authored_content.get("actors", [])
        spawns = authored_content.get("spawns", [])
        entities = authored_content.get("entities", [])
        chests = authored_content.get("chests", [])

        if scene.get("kind") != "outdoor_scene_overlay":
            failures.append(f"active slice {map_stem}: authored scene has the wrong kind")
        if source.get("geometry_file", "").lower() != expectation["geometry_file"]:
            failures.append(f"active slice {map_stem}: authored scene targets the wrong geometry")
        if runtime_restrictions.get("allow_save_game") is not True:
            failures.append(f"active slice {map_stem}: normal saving is not enabled")
        if len(actors) < expectation["minimum_actors"]:
            failures.append(f"active slice {map_stem}: authored actors are missing")
        if len(spawns) < expectation.get("minimum_spawns", 0):
            failures.append(f"active slice {map_stem}: authored encounter spawns are missing")
        if len(chests) < expectation.get("minimum_chests", 1):
            failures.append(f"active slice {map_stem}: authored chests are missing")

        interactive_event_ids = {
            face.get("cog_triggered_number")
            for face in interactive_faces
        }
        if not expectation.get("interactive_event_ids", set()).issubset(interactive_event_ids):
            failures.append(f"active slice {map_stem}: chest interaction events are missing")
        if not any(
            entity.get("event_id_primary") == expectation["entity_event_id"]
            for entity in entities
        ):
            failures.append(f"active slice {map_stem}: map-transition entity is missing")

        if not event_path.is_file():
            failures.append(f"active slice {map_stem}: missing authored event script {event_path}")
            continue

        event_text = event_path.read_text(encoding="utf-8")
        for event_id in expectation["event_ids"]:
            if f"RegisterEvent({event_id}," not in event_text:
                failures.append(f"active slice {map_stem}: event {event_id} is not registered")

        for event_id in expectation.get("on_load_event_ids", set()):
            if f"RegisterMapOnLoadEvent({event_id}," not in event_text:
                failures.append(f"active slice {map_stem}: on-load event {event_id} is not registered")

        for event_id in expectation.get("replaced_event_ids", set()):
            if f"ReplaceMapEvent({event_id}," not in event_text:
                failures.append(f"active slice {map_stem}: event {event_id} is not replaced")

        dialogue_actors = {
            actor.get("mm9_source_object_index"): actor
            for actor in actors
            if actor.get("mm9_rude_id") is not None
        }
        for source_object_index, rude_id in expectation.get("mm9_dialogue_bindings", {}).items():
            actor = dialogue_actors.get(source_object_index)
            if actor is None:
                failures.append(
                    f"active slice {map_stem}: MM9 dialogue object {source_object_index} is missing"
                )
            elif actor.get("mm9_rude_id") != rude_id:
                failures.append(
                    f"active slice {map_stem}: MM9 dialogue object {source_object_index} has wrong RUDE id"
                )
            elif actor.get("npc_id") != 0 or actor.get("immobile") is not True:
                failures.append(
                    f"active slice {map_stem}: MM9 dialogue object {source_object_index} is not a stationary placeholder"
                )

    return failures


def validate_package(maps_root: Path, events_root: Path, map_stats_path: Path) -> list[str]:
    failures: list[str] = []
    rows = mm9_map_rows(map_stats_path)

    for row in rows:
        columns = row.split("\t")
        map_id = columns[0]
        map_name = columns[1]
        file_name = columns[2]
        map_stem = Path(file_name).stem.lower()
        scene_path = maps_root / f"{map_stem}.scene.yml"
        geometry_path = maps_root / file_name.lower()
        event_path = events_root / f"{map_stem}.lua"
        navigation_path = maps_root / f"{map_stem}.nav"
        navigation_metadata_path = maps_root / f"{map_stem}.nav.yml"
        render_path = maps_root / f"{map_stem}.render"
        render_metadata_path = maps_root / f"{map_stem}.render.yml"
        script_ir_path = events_root / f"{map_stem}.script_ir.yml"

        if Path(file_name).suffix.lower() != ".odm":
            failures.append(f"map {map_id} {map_name}: expected ODM filename, got {file_name}")
        if not geometry_path.is_file():
            failures.append(f"map {map_id} {map_name}: missing geometry {geometry_path}")
        if not scene_path.is_file():
            failures.append(f"map {map_id} {map_name}: missing scene {scene_path}")
        else:
            scene = yaml.load(scene_path.read_text(encoding="utf-8"), Loader=YAML_LOADER)
            if scene.get("scene_profile") != "bmodel_world":
                failures.append(f"map {map_id} {map_name}: scene_profile is not bmodel_world")
            location_type = scene.get("environment", {}).get("location_type")
            if location_type not in {"exterior", "enclosed"}:
                failures.append(f"map {map_id} {map_name}: invalid location_type {location_type!r}")
            for mechanism in scene.get("mechanisms", []):
                motion = mechanism.get("motion", {})
                if motion.get("unsupported") is not True:
                    continue

                classification = (mechanism.get("source_class"), mechanism.get("kind"))
                if classification not in KNOWN_AUDIT_ONLY_MECHANISMS:
                    failures.append(
                        f"map {map_id} {map_name}: unclassified unsupported mechanism {classification!r}"
                    )
        if not event_path.is_file():
            failures.append(f"map {map_id} {map_name}: missing generated event script {event_path}")
        else:
            event_lines = event_path.read_text(encoding="utf-8").splitlines()
            if any(line.strip() == "return map" for line in event_lines):
                failures.append(
                    f"map {map_id} {map_name}: generated event script prevents authored overlays from executing"
                )
        if not script_ir_path.is_file():
            failures.append(f"map {map_id} {map_name}: missing source-script audit IR {script_ir_path}")
        if not navigation_path.is_file():
            failures.append(f"map {map_id} {map_name}: missing cooked navigation {navigation_path}")
        else:
            navigation_bytes = navigation_path.read_bytes()
            if len(navigation_bytes) < 48 or navigation_bytes[:8] != b"OYMNAV1\0":
                failures.append(f"map {map_id} {map_name}: invalid cooked navigation header")
            else:
                version, header_size, record_size, _, _, _, _, facet_count, reserved = struct.unpack_from(
                    "<IIIIQIIII", navigation_bytes, 8
                )
                expected_size = header_size + facet_count * record_size
                if (
                    version != 1
                    or header_size != 48
                    or record_size != 24
                    or reserved != 0
                    or len(navigation_bytes) != expected_size
                ):
                    failures.append(f"map {map_id} {map_name}: inconsistent cooked navigation layout")
                elif not navigation_metadata_path.is_file():
                    failures.append(
                        f"map {map_id} {map_name}: missing navigation metadata {navigation_metadata_path}"
                    )
                else:
                    navigation_metadata = yaml.load(
                        navigation_metadata_path.read_text(encoding="utf-8"),
                        Loader=YAML_LOADER,
                    )
                    navigation_source = navigation_metadata.get("source", {})
                    navigation_stats = navigation_metadata.get("stats", {})
                    if (
                        navigation_metadata.get("kind") != "outdoor_navigation_metadata"
                        or navigation_source.get("geometry_file", "").lower() != file_name.lower()
                        or navigation_source.get("navigation_file", "").lower() != navigation_path.name.lower()
                        or navigation_source.get("geometry_fnv1a64")
                        != struct.unpack_from("<Q", navigation_bytes, 24)[0]
                        or navigation_stats.get("navigation_cooked_facets") != facet_count
                    ):
                        failures.append(f"map {map_id} {map_name}: inconsistent navigation metadata")

        if not render_path.is_file():
            failures.append(f"map {map_id} {map_name}: missing cooked render data {render_path}")
        else:
            render_bytes = render_path.read_bytes()
            if len(render_bytes) < 48 or render_bytes[:8] != b"OYMREN1\0":
                failures.append(f"map {map_id} {map_name}: invalid cooked render data header")
            else:
                version, header_size, record_size, cell_size, geometry_hash, _, _, face_count, reserved = (
                    struct.unpack_from("<IIIIQIIII", render_bytes, 8)
                )
                expected_size = header_size + face_count * record_size
                if (
                    version != 1
                    or header_size != 48
                    or record_size != 24
                    or cell_size < 256
                    or reserved != 0
                    or len(render_bytes) != expected_size
                ):
                    failures.append(f"map {map_id} {map_name}: inconsistent cooked render data layout")
                elif not render_metadata_path.is_file():
                    failures.append(f"map {map_id} {map_name}: missing render metadata {render_metadata_path}")
                else:
                    render_metadata = yaml.load(
                        render_metadata_path.read_text(encoding="utf-8"),
                        Loader=YAML_LOADER,
                    )
                    render_source = render_metadata.get("source", {})
                    render_stats = render_metadata.get("stats", {})
                    if (
                        render_metadata.get("kind") != "outdoor_render_data_metadata"
                        or render_source.get("geometry_file", "").lower() != file_name.lower()
                        or render_source.get("render_file", "").lower() != render_path.name.lower()
                        or render_source.get("geometry_fnv1a64") != geometry_hash
                        or render_stats.get("render_cooked_faces") != face_count
                    ):
                        failures.append(f"map {map_id} {map_name}: inconsistent render metadata")

    failures.extend(validate_active_slice(maps_root, events_root))
    return failures


def audit_only_mechanism_counts(maps_root: Path, rows: list[str]) -> Counter[tuple[str, str]]:
    counts: Counter[tuple[str, str]] = Counter()

    for row in rows:
        file_name = row.split("\t")[2]
        map_stem = Path(file_name).stem.lower()
        scene_path = maps_root / f"{map_stem}.scene.yml"
        scene = yaml.load(scene_path.read_text(encoding="utf-8"), Loader=YAML_LOADER)
        for mechanism in scene.get("mechanisms", []):
            if mechanism.get("motion", {}).get("unsupported") is not True:
                continue

            counts[(mechanism.get("source_class", ""), mechanism.get("kind", ""))] += 1

    return counts


def source_script_audit_counts(events_root: Path, rows: list[str]) -> tuple[int, int, int]:
    script_count = 0
    command_count = 0
    unknown_command_count = 0

    for row in rows:
        file_name = row.split("\t")[2]
        map_stem = Path(file_name).stem.lower()
        script_ir_path = events_root / f"{map_stem}.script_ir.yml"
        script_ir = yaml.load(script_ir_path.read_text(encoding="utf-8"), Loader=YAML_LOADER)

        for script in script_ir.get("scripts", []):
            script_count += 1
            command_count += int(script.get("command_count", 0))
            unknown_command_count += len(script.get("unknown_commands", []))

    return script_count, command_count, unknown_command_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the generated MM9 ODM BModel-world package.")
    parser.add_argument("--maps-root", type=Path, default=Path("assets_dev/worlds/mm9/maps"))
    parser.add_argument("--events-root", type=Path, default=Path("assets_dev/worlds/mm9/events/maps"))
    parser.add_argument(
        "--map-stats",
        type=Path,
        default=Path("assets_dev/engine/data_tables/map_stats.txt"),
    )
    parser.add_argument(
        "--editor-map-stats",
        type=Path,
        default=Path("assets_editor_dev/engine/data_tables/map_stats.txt"),
    )
    parser.add_argument("--sync-editor-map-stats", action="store_true")
    args = parser.parse_args()

    if args.sync_editor_map_stats:
        synchronize_editor_map_stats(args.map_stats, args.editor_map_stats)

    failures = validate_package(args.maps_root, args.events_root, args.map_stats)
    if failures:
        for failure in failures:
            print(failure)
        return 1

    source_rows = mm9_map_rows(args.map_stats)
    editor_rows = mm9_map_rows(args.editor_map_stats)
    if editor_rows != source_rows:
        print("editor map_stats MM9 rows do not match the engine table")
        return 1

    print(f"MM9 BModel-world package valid: maps={len(source_rows)}")
    for classification, count in sorted(audit_only_mechanism_counts(args.maps_root, source_rows).items()):
        description = KNOWN_AUDIT_ONLY_MECHANISMS[classification]
        print(
            "  audit-only mechanisms: "
            f"source_class={classification[0]} kind={classification[1]} count={count} reason={description}"
        )

    script_count, command_count, unknown_command_count = source_script_audit_counts(args.events_root, source_rows)
    print(
        "  source-script audit IR (non-executable): "
        f"scripts={script_count} commands={command_count} unknown_commands={unknown_command_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
