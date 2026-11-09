#!/usr/bin/env python3
"""Generate MM9 positioned map transitions and a source-to-runtime audit."""

from __future__ import annotations

import argparse
import csv
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
COORDINATE_SCALE = 2.56
TABLE_COLUMNS = [
    "CanonicalId",
    "SourceMap",
    "SourceMapFile",
    "SourceObjectIndex",
    "SourceName",
    "SourceClass",
    "CenterX",
    "CenterY",
    "CenterZ",
    "HalfExtentX",
    "HalfExtentY",
    "HalfExtentZ",
    "DestinationMap",
    "DestinationMapFile",
    "SourceStartPoint",
    "ResolvedStartPoint",
    "ArrivalX",
    "ArrivalY",
    "ArrivalZ",
    "FacingDegrees",
    "FacingYawUnits",
    "MovePlayerToFloor",
    "AskPlayer",
    "TravelDays",
    "TravelDaysSentinel",
    "LoadScreen",
    "SourceDat",
    "OverrideId",
    "Provenance",
]


@dataclass(frozen=True)
class MapSource:
    stem: str
    runtime_file: str
    source_dat: str
    objects: list[dict[str, Any]]


class GenerationError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.load(path.read_text(encoding="utf-8"), Loader=YAML_LOADER)
    if not isinstance(loaded, dict):
        raise GenerationError(f"{path}: expected a YAML mapping")
    return loaded


def property_value(prop: dict[str, Any]) -> Any:
    value_json = prop.get("value_json")
    if value_json is None:
        return None
    value = json.loads(str(value_json))
    if str(prop.get("name", "")).casefold() == "traveldays" and int(prop.get("code", -1)) == 6:
        raw_hex = str(prop.get("raw_hex", ""))
        if len(raw_hex) == 8:
            decoded = struct.unpack("<f", bytes.fromhex(raw_hex))[0]
            if math.isfinite(decoded) and decoded.is_integer():
                return int(decoded)
    return value


def object_properties(obj: dict[str, Any]) -> dict[str, Any]:
    return {
        str(prop.get("name", "")): property_value(prop)
        for prop in obj.get("properties", [])
        if isinstance(prop, dict) and bool(prop.get("decoded", False))
    }


def openyamm_position(value: Any) -> tuple[int, int, int] | None:
    if not isinstance(value, list) or len(value) < 3:
        return None
    return (
        int(round(float(value[0]) * COORDINATE_SCALE)),
        int(round(float(value[2]) * COORDINATE_SCALE)),
        int(round(float(value[1]) * COORDINATE_SCALE)),
    )


def openyamm_half_extents(value: Any) -> tuple[int, int, int] | None:
    converted = openyamm_position(value)
    if converted is None:
        return None
    return tuple(abs(component) for component in converted)


def facing(value: Any) -> tuple[float, int]:
    if not isinstance(value, list) or len(value) < 2:
        return 0.0, 0
    degrees = (-math.degrees(float(value[1]))) % 360.0
    return degrees, int(round(degrees * 2048.0 / 360.0)) % 2048


def runtime_map_file(maps_dir: Path, stem: str) -> str:
    for extension in (".odm", ".blv"):
        if (maps_dir / f"{stem}{extension}").is_file():
            return f"{stem}{extension}"
    raise GenerationError(f"{stem}: generated runtime map file is missing")


def load_maps(maps_dir: Path) -> dict[str, MapSource]:
    result: dict[str, MapSource] = {}
    for path in sorted(maps_dir.glob("*.raw_objects.yml"), key=lambda item: item.name.casefold()):
        stem = path.name[:-len(".raw_objects.yml")].casefold()
        data = load_yaml(path)
        objects = data.get("objects")
        if not isinstance(objects, list):
            raise GenerationError(f"{path}: objects must be a sequence")
        if stem in result:
            raise GenerationError(f"duplicate MM9 map source: {stem}")
        result[stem] = MapSource(
            stem=stem,
            runtime_file=runtime_map_file(maps_dir, stem),
            source_dat=str(data.get("source_dat", "")),
            objects=objects,
        )
    if not result:
        raise GenerationError(f"{maps_dir}: no raw MM9 map objects found")
    return result


def load_overrides(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    data = load_yaml(path)
    if int(data.get("format_version", 0)) != 1 or not isinstance(data.get("transitions"), list):
        raise GenerationError(f"{path}: expected format_version 1 and transitions sequence")
    result: dict[tuple[str, int], dict[str, Any]] = {}
    for entry in data["transitions"]:
        if not isinstance(entry, dict):
            raise GenerationError(f"{path}: transition override must be a mapping")
        key = (str(entry.get("source_map", "")).casefold(), int(entry.get("source_object_index", -1)))
        if not key[0] or key[1] < 0 or key in result:
            raise GenerationError(f"{path}: invalid or duplicate transition override {key}")
        if entry.get("review_state") != "reviewed":
            raise GenerationError(f"{path}: override {key} is not reviewed")
        result[key] = entry
    return result


def starts_by_map(maps: dict[str, MapSource]) -> dict[str, dict[str, tuple[dict[str, Any], dict[str, Any]]]]:
    result: dict[str, dict[str, tuple[dict[str, Any], dict[str, Any]]]] = {}
    for stem, source in maps.items():
        starts: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
        for obj in source.objects:
            if not isinstance(obj, dict) or obj.get("name") != "StartPoint":
                continue
            values = object_properties(obj)
            name = str(values.get("Name", ""))
            key = name.casefold()
            if not key or key in starts:
                raise GenerationError(f"{stem}: invalid or duplicate StartPoint name {name!r}")
            starts[key] = (obj, values)
        result[stem] = starts
    return result


def transition_record(
    source: MapSource,
    obj: dict[str, Any],
    values: dict[str, Any],
    maps: dict[str, MapSource],
    starts: dict[str, dict[str, tuple[dict[str, Any], dict[str, Any]]]],
    override: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    object_index = int(obj.get("object_index", -1))
    canonical_id = f"mm9:transition/{source.stem}/{object_index}"
    source_start_name = str(values.get("StartPointName", ""))
    destination_source_name = str(values.get("DestinationWorld", ""))
    destination_stem = destination_source_name.casefold()
    disposition = str((override or {}).get("disposition", "supported"))
    override_id = str((override or {}).get("id", ""))
    reason = str((override or {}).get("reason", ""))
    resolved_start_name = str((override or {}).get("resolved_start_point", source_start_name))
    errors: list[str] = []

    if disposition == "intentionally_unsupported":
        if not reason:
            errors.append("unsupported override has no reviewed reason")
    elif disposition != "supported":
        errors.append(f"unsupported disposition {disposition!r}")

    center = openyamm_position(values.get("Pos"))
    half_extents = openyamm_half_extents(values.get("Dims"))
    if center is None:
        errors.append("missing or invalid Pos")
    if half_extents is None or any(value <= 0 for value in half_extents):
        errors.append("missing or invalid Dims")

    destination = maps.get(destination_stem)
    if destination is None:
        errors.append(f"destination map {destination_source_name!r} is unresolved")

    start_entry = starts.get(destination_stem, {}).get(resolved_start_name.casefold())
    if disposition == "supported" and start_entry is None:
        errors.append(f"destination start point {resolved_start_name!r} is unresolved")

    raw_travel_days = values.get("TravelDays", 0)
    if not isinstance(raw_travel_days, (int, float)) or int(raw_travel_days) != raw_travel_days:
        errors.append(f"invalid TravelDays value {raw_travel_days!r}")
        travel_days = 0
    else:
        travel_days = int(raw_travel_days)
    if travel_days < -1:
        errors.append(f"unsupported TravelDays value {travel_days}")
    travel_days_sentinel = "source_default" if travel_days == -1 else ""

    audit = {
        "canonical_id": canonical_id,
        "source_map": source.stem,
        "source_dat": source.source_dat,
        "source_object_index": object_index,
        "source_name": str(values.get("Name", "")),
        "source_class": str(obj.get("name", "")),
        "destination_source_name": destination_source_name,
        "destination_map": destination_stem,
        "source_start_point": source_start_name,
        "resolved_start_point": resolved_start_name,
        "ask_player": bool(values.get("AskPlayer", False)),
        "travel_days": travel_days,
        "travel_days_raw_hex": next(
            (str(prop.get("raw_hex", "")) for prop in obj.get("properties", []) if prop.get("name") == "TravelDays"),
            "",
        ),
        "disposition": disposition,
        "override_id": override_id,
        "review_state": str((override or {}).get("review_state", "source_proven")),
        "reason": reason,
        "errors": errors,
    }
    if errors or disposition == "intentionally_unsupported":
        return None, audit

    assert center is not None and half_extents is not None and destination is not None and start_entry is not None
    _, start_values = start_entry
    arrival = openyamm_position(start_values.get("Pos"))
    if arrival is None:
        audit["errors"].append("resolved start point has invalid Pos")
        return None, audit
    facing_degrees, facing_units = facing(start_values.get("Rotation"))
    provenance = "dat"
    if override_id:
        provenance += f"+reviewed_override:{override_id}"
    record = {
        "CanonicalId": canonical_id,
        "SourceMap": f"world.mm9.map.{source.stem}",
        "SourceMapFile": source.runtime_file,
        "SourceObjectIndex": object_index,
        "SourceName": str(values.get("Name", "")),
        "SourceClass": str(obj.get("name", "")),
        "CenterX": center[0],
        "CenterY": center[1],
        "CenterZ": center[2],
        "HalfExtentX": half_extents[0],
        "HalfExtentY": half_extents[1],
        "HalfExtentZ": half_extents[2],
        "DestinationMap": f"world.mm9.map.{destination.stem}",
        "DestinationMapFile": destination.runtime_file,
        "SourceStartPoint": source_start_name,
        "ResolvedStartPoint": resolved_start_name,
        "ArrivalX": arrival[0],
        "ArrivalY": arrival[1],
        "ArrivalZ": arrival[2],
        "FacingDegrees": f"{facing_degrees:.8g}",
        "FacingYawUnits": facing_units,
        "MovePlayerToFloor": 1 if bool(start_values.get("MovePlayerToFloor", True)) else 0,
        "AskPlayer": 1 if bool(values.get("AskPlayer", False)) else 0,
        "TravelDays": travel_days,
        "TravelDaysSentinel": travel_days_sentinel,
        "LoadScreen": str(values.get("LoadScreen", "")),
        "SourceDat": source.source_dat,
        "OverrideId": override_id,
        "Provenance": provenance,
    }
    return record, audit


def generate(
    maps_dir: Path,
    overrides_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    maps = load_maps(maps_dir)
    starts = starts_by_map(maps)
    overrides = load_overrides(overrides_path)
    records: list[dict[str, Any]] = []
    audit_records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_owners: set[tuple[str, int]] = set()

    for source in maps.values():
        for obj in source.objects:
            if not isinstance(obj, dict):
                continue
            values = object_properties(obj)
            has_destination = bool(str(values.get("DestinationWorld", "")))
            if obj.get("name") != "ExitTrigger" and has_destination:
                audit_records.append({
                    "canonical_id": "",
                    "source_map": source.stem,
                    "source_dat": source.source_dat,
                    "source_object_index": int(obj.get("object_index", -1)),
                    "source_name": str(values.get("Name", "")),
                    "source_class": str(obj.get("name", "")),
                    "disposition": "invalid_destination_owner",
                    "errors": ["DestinationWorld is owned by a non-ExitTrigger object"],
                })
                continue
            if obj.get("name") != "ExitTrigger":
                continue
            object_index = int(obj.get("object_index", -1))
            owner = (source.stem, object_index)
            record, audit = transition_record(source, obj, values, maps, starts, overrides.get(owner))
            if audit["canonical_id"] in seen_ids:
                audit["errors"].append("duplicate canonical transition id")
            if owner in seen_owners:
                audit["errors"].append("duplicate source object ownership")
            seen_ids.add(audit["canonical_id"])
            seen_owners.add(owner)
            audit_records.append(audit)
            if record is not None and not audit["errors"]:
                records.append(record)

    unused_overrides = sorted(f"{key[0]}:{key[1]}" for key in overrides.keys() - seen_owners)
    source_maps_with_exits = {record["source_map"] for record in audit_records if record.get("canonical_id")}
    summary = {
        "map_count": len(maps),
        "source_maps_with_exits": len(source_maps_with_exits),
        "exit_trigger_count": sum(1 for record in audit_records if record.get("canonical_id")),
        "supported_count": len(records),
        "intentionally_unsupported_count": sum(
            1 for record in audit_records if record.get("disposition") == "intentionally_unsupported"
        ),
        "ask_player_count": sum(1 for record in audit_records if record.get("ask_player")),
        "automatic_count": sum(
            1 for record in audit_records if record.get("canonical_id") and not record.get("ask_player")
        ),
        "travel_days_zero_count": sum(1 for record in audit_records if record.get("travel_days") == 0),
        "travel_days_sentinel_count": sum(1 for record in audit_records if record.get("travel_days") == -1),
        "error_count": sum(len(record.get("errors", [])) for record in audit_records),
        "unused_overrides": unused_overrides,
    }
    audit = {
        "format_version": 1,
        "kind": "mm9_map_transition_audit",
        "generated_from": "DAT raw-object discovery plus reviewed transition overrides",
        "summary": summary,
        "records": audit_records,
    }
    if summary["error_count"] or unused_overrides:
        raise GenerationError(
            f"transition audit contains {summary['error_count']} errors and {len(unused_overrides)} unused overrides"
        )
    return records, audit


def write_table(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, TABLE_COLUMNS, dialect="excel-tab", lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def write_audit(path: Path, audit: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(audit, sort_keys=False, width=120), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maps-dir", type=Path, default=Path("assets_editor_dev/worlds/mm9/maps"))
    parser.add_argument(
        "--overrides",
        type=Path,
        default=Path("tools/mm9_import_discovery/mm9_transition_overrides.yml"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("level_generation/projects/mm9r_common/original_tables/map_transitions.txt"),
    )
    parser.add_argument(
        "--audit",
        type=Path,
        default=Path("assets_dev/worlds/mm9/import/map_transition_audit.yml"),
    )
    args = parser.parse_args()
    try:
        records, audit = generate(args.maps_dir, args.overrides)
        write_table(args.output, records)
        write_audit(args.audit, audit)
    except (GenerationError, OSError, ValueError, yaml.YAMLError) as exception:
        parser.error(str(exception))
    print(f"wrote {args.output} ({len(records)} supported transitions)")
    print(f"wrote {args.audit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
