#!/usr/bin/env python3
"""Generate MM9 transport routes from shops, RUDE, the boat schedule, and reviewed DLL recovery."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
COORDINATE_SCALE = 2.56
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
TABLE_COLUMNS = [
    "CanonicalId", "DockNpcId", "ShopId", "DockName", "ServiceClassification", "SourceRudeRowIndex",
    "SourceLine", "DestinationName", "DestinationMap", "DestinationMapFile", "DestinationStartPoint",
    "ArrivalX", "ArrivalY", "ArrivalZ", "FacingDegrees", "FacingYawUnits", "MovePlayerToFloor",
    "AvailableWeekday", "SourceDayIndex", "TravelDays", "BasePrice", "PriceMultiplier", "RequiredRawKeys",
    "ForbiddenRawKeys", "RouteOrder", "SourceShop", "SourceRude", "ScheduleSource", "ExecutableRva",
    "ReviewState", "Provenance",
]


class GenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class RudeService:
    rude_id: int
    row_index: int
    source_line: int
    required_keys: tuple[int, ...]
    forbidden_keys: tuple[int, ...]
    source: str


def parse_int(value: str, source: str) -> int:
    try:
        return int(value.strip(), 0)
    except ValueError as exception:
        raise GenerationError(f"{source}: invalid integer {value!r}") from exception


def load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.load(path.read_text(encoding="utf-8"), Loader=YAML_LOADER)
    if not isinstance(loaded, dict):
        raise GenerationError(f"{path}: expected a YAML mapping")
    return loaded


def nonzero_keys(row: list[str], columns: tuple[int, ...], source: str) -> tuple[int, ...]:
    return tuple(value for column in columns if (value := parse_int(row[column], source)) != 0)


def load_rude_services(rude_dir: Path) -> dict[int, RudeService]:
    result: dict[int, RudeService] = {}
    for path in sorted(rude_dir.glob("NPC*.rude"), key=lambda item: item.name.casefold()):
        match = re.fullmatch(r"NPC(\d+)\.rude", path.name, re.IGNORECASE)
        if match is None:
            continue
        rude_id = int(match.group(1))
        with path.open(encoding="utf-8", errors="replace", newline="") as stream:
            for row_index, row in enumerate(csv.reader(stream)):
                source_line = row_index + 1
                source = f"{path}:{source_line}"
                if len(row) < 30:
                    raise GenerationError(f"{source}: expected at least 30 RUDE columns")
                if parse_int(row[0], source) != rude_id:
                    raise GenerationError(f"{source}: RUDE id does not match filename")
                if row[5].strip() != "-5":
                    continue
                if rude_id in result:
                    raise GenerationError(f"{source}: duplicate RUDE -5 service for NPC {rude_id}")
                result[rude_id] = RudeService(
                    rude_id=rude_id,
                    row_index=row_index,
                    source_line=source_line,
                    required_keys=nonzero_keys(row, (6, 8, 10, 12, 14), source),
                    forbidden_keys=nonzero_keys(row, (20, 21, 22, 23, 24), source),
                    source=path.as_posix(),
                )
    if not result:
        raise GenerationError(f"{rude_dir}: no RUDE -5 services found")
    return result


def load_shops(path: Path) -> dict[int, dict[str, str]]:
    result: dict[int, dict[str, str]] = {}
    with path.open(encoding="latin1", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            shop_id = parse_int(row["Shop (NPC) ID"], path.as_posix())
            if shop_id in result:
                raise GenerationError(f"{path}: duplicate shop id {shop_id}")
            result[shop_id] = row
    return result


def load_boat_schedule(path: Path) -> dict[str, dict[str, str | None]]:
    text = ""
    with path.open(encoding="latin1", newline="") as stream:
        for row in csv.reader(stream):
            if row and row[0].strip() == "562":
                text = row[2]
                break
    if not text:
        raise GenerationError(f"{path}: source item 562 Boat Schedule is missing")

    result: dict[str, dict[str, str | None]] = {}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for index in range(0, len(lines), 2):
        if index + 1 >= len(lines) or not lines[index].casefold().startswith("from:"):
            raise GenerationError(f"{path}: invalid Boat Schedule section near line {index + 1}")
        origin = lines[index].split(":", 1)[1].strip()
        tokens = re.split(r"\s+(?=(?:M|Tu|W|Th|F|Sa|Su)\s+)", lines[index + 1], flags=re.IGNORECASE)
        if len(tokens) != 7:
            raise GenerationError(f"{path}: expected seven weekdays for {origin}")
        schedule: dict[str, str | None] = {}
        for weekday, token in zip(WEEKDAYS, tokens):
            parts = token.split(maxsplit=1)
            if len(parts) != 2:
                raise GenerationError(f"{path}: invalid {origin} {weekday} route")
            destination = " ".join(parts[1].split())
            schedule[weekday] = None if destination.casefold() == "no boat" else destination
        result[origin] = schedule
    return result


def property_value(block: str, name: str) -> Any:
    match = re.search(
        rf'- name: "{re.escape(name)}"\n(?:.*\n){{0,8}}?\s+value_json: (.*)',
        block,
    )
    if match is None:
        raise GenerationError(f"StartPoint block has no decoded {name} property")
    encoded = yaml.safe_load(match.group(1))
    if not isinstance(encoded, str):
        raise GenerationError(f"StartPoint block has invalid {name} value_json")
    return json.loads(encoded)


def resolve_start(maps_dir: Path, stem: str, start_name: str) -> dict[str, Any]:
    path = maps_dir / f"{stem}.raw_objects.yml"
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(
        r'^  - object_index: (\d+)\n    name: "StartPoint"\n(?P<body>.*?)(?=^  - object_index:|\Z)',
        text,
        flags=re.MULTILINE | re.DOTALL,
    ):
        body = match.group("body")
        if str(property_value(body, "Name")).casefold() != start_name.casefold():
            continue
        position = property_value(body, "Pos")
        rotation = property_value(body, "Rotation")
        move_to_floor = bool(property_value(body, "MovePlayerToFloor"))
        if not isinstance(position, list) or len(position) < 3 or not isinstance(rotation, list) or len(rotation) < 2:
            raise GenerationError(f"{path}: invalid {start_name} transform")
        degrees = (-math.degrees(float(rotation[1]))) % 360.0
        return {
            "x": int(round(float(position[0]) * COORDINATE_SCALE)),
            "y": int(round(float(position[2]) * COORDINATE_SCALE)),
            "z": int(round(float(position[1]) * COORDINATE_SCALE)),
            "facing_degrees": degrees,
            "facing_units": int(round(degrees * 2048.0 / 360.0)) % 2048,
            "move_to_floor": move_to_floor,
            "source_object_index": int(match.group(1)),
        }
    raise GenerationError(f"{path}: unresolved StartPoint {start_name!r}")


def raw_keys(values: Any, source: str) -> tuple[int, ...]:
    if values is None:
        return ()
    if not isinstance(values, list):
        raise GenerationError(f"{source}: raw keys must be a sequence")
    keys = tuple(int(value) for value in values)
    if any(value <= 0 or value > 9999 for value in keys):
        raise GenerationError(f"{source}: raw key is outside 1-9999")
    return keys


def generate(
    shops_path: Path,
    rude_dir: Path,
    books_path: Path,
    maps_dir: Path,
    recovery_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    shops = load_shops(shops_path)
    rude_services = load_rude_services(rude_dir)
    boat_schedule = load_boat_schedule(books_path)
    recovery = load_yaml(recovery_path)
    if recovery.get("format_version") != 1 or recovery.get("review_state") != "executable_backed":
        raise GenerationError(f"{recovery_path}: recovery must be reviewed executable-backed format version 1")
    services = recovery.get("services")
    destinations = recovery.get("destinations")
    day_index_names = recovery.get("day_index_names")
    if not isinstance(services, dict) or not isinstance(destinations, dict) or day_index_names != list(day_index_names or []):
        raise GenerationError(f"{recovery_path}: invalid services, destinations, or day index names")
    if tuple(day_index_names) != ("Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"):
        raise GenerationError(f"{recovery_path}: unexpected executable day-index mapping")

    records: list[dict[str, Any]] = []
    audit_services: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    dock_ids = {shop_id for shop_id, row in shops.items() if row["Shop Type"].casefold() == "dock"}
    for rude_id, rude in sorted(rude_services.items()):
        shop = shops.get(rude_id)
        recovered = services.get(rude_id)
        errors: list[str] = []
        if shop is None:
            errors.append("RUDE -5 service has no MMIXSHOPS row")
        if not isinstance(recovered, dict):
            errors.append("RUDE -5 service has no reviewed route recovery")
        classification = str((recovered or {}).get("classification", "dock"))
        if rude_id in dock_ids and classification != "dock":
            errors.append("Dock shop is not classified as dock")
        if rude_id not in dock_ids and classification == "dock":
            errors.append("non-Dock shop is classified as dock")

        service_record_count = 0
        recovered_days = (recovered or {}).get("days", {})
        origin_by_npc = {18: "Thjorgard", 60: "Sturmford", 103: "Drangheim", 144: "Guberland",
                         209: "Frosgard", 257: "Thronheim", 288: "Lindisfarne"}
        origin = origin_by_npc.get(rude_id)
        if classification == "dock" and origin not in boat_schedule:
            errors.append("Dock has no source Boat Schedule section")
        if not isinstance(recovered_days, dict) or set(recovered_days) != set(WEEKDAYS):
            errors.append("reviewed recovery must define all seven weekdays")

        if not errors:
            assert shop is not None and isinstance(recovered, dict) and isinstance(recovered_days, dict)
            for route_order, weekday in enumerate(WEEKDAYS):
                route_data = recovered_days[weekday]
                schedule_destination = boat_schedule[origin][weekday] if origin is not None else None
                if classification == "dock":
                    recovered_destination = route_data[0] if isinstance(route_data, list) else None
                    if recovered_destination != schedule_destination:
                        errors.append(
                            f"{weekday}: Boat Schedule {schedule_destination!r} disagrees with reviewed recovery "
                            f"{recovered_destination!r}")
                        continue
                if route_data is None:
                    continue
                if not isinstance(route_data, list) or len(route_data) != 2:
                    errors.append(f"{weekday}: route must contain destination and travel days")
                    continue
                destination_name = str(route_data[0])
                travel_days = int(route_data[1])
                destination = destinations.get(destination_name)
                if not isinstance(destination, dict) or travel_days <= 0:
                    errors.append(f"{weekday}: invalid destination or travel days")
                    continue
                map_stem = str(destination.get("runtime_map", "")).casefold()
                start_name = str(destination.get("start_point", ""))
                map_file = next((f"{map_stem}{extension}" for extension in (".odm", ".blv")
                                 if (maps_dir / f"{map_stem}{extension}").is_file()), "")
                if not map_file:
                    errors.append(f"{weekday}: destination runtime map {map_stem!r} is unresolved")
                    continue
                arrival = resolve_start(maps_dir, map_stem, start_name)
                required = tuple(dict.fromkeys(rude.required_keys + raw_keys(
                    destination.get("required_raw_keys"), f"{recovery_path}:{destination_name}")))
                forbidden = tuple(dict.fromkeys(rude.forbidden_keys + raw_keys(
                    destination.get("forbidden_raw_keys"), f"{recovery_path}:{destination_name}")))
                canonical_id = f"mm9:transport/{rude_id}/{weekday.casefold()}"
                if canonical_id in seen_ids:
                    errors.append(f"{weekday}: duplicate canonical route id")
                    continue
                seen_ids.add(canonical_id)
                source_day_index = list(day_index_names).index(weekday)
                records.append({
                    "CanonicalId": canonical_id,
                    "DockNpcId": rude_id,
                    "ShopId": rude_id,
                    "DockName": shop["Shop Name"],
                    "ServiceClassification": classification,
                    "SourceRudeRowIndex": rude.row_index,
                    "SourceLine": rude.source_line,
                    "DestinationName": destination_name,
                    "DestinationMap": f"world.mm9.map.{map_stem}",
                    "DestinationMapFile": map_file,
                    "DestinationStartPoint": start_name,
                    "ArrivalX": arrival["x"],
                    "ArrivalY": arrival["y"],
                    "ArrivalZ": arrival["z"],
                    "FacingDegrees": arrival["facing_degrees"],
                    "FacingYawUnits": arrival["facing_units"],
                    "MovePlayerToFloor": int(arrival["move_to_floor"]),
                    "AvailableWeekday": weekday,
                    "SourceDayIndex": source_day_index,
                    "TravelDays": travel_days,
                    "BasePrice": int(recovery["base_price"]),
                    "PriceMultiplier": shop["Merchant base"],
                    "RequiredRawKeys": "|".join(map(str, required)),
                    "ForbiddenRawKeys": "|".join(map(str, forbidden)),
                    "RouteOrder": route_order,
                    "SourceShop": shops_path.as_posix(),
                    "SourceRude": rude.source,
                    "ScheduleSource": books_path.as_posix() if classification == "dock" else "",
                    "ExecutableRva": f"0x{int(recovered['switch_table_rva']):08x}[{source_day_index}]",
                    "ReviewState": recovery["review_state"],
                    "Provenance": "MMIXSHOPS+RUDE+BoatSchedule+cshell.dll" if classification == "dock"
                        else "MMIXSHOPS+RUDE+cshell.dll",
                })
                service_record_count += 1

        audit_services.append({
            "rude_id": rude_id,
            "shop_name": shop["Shop Name"] if shop is not None else "",
            "shop_type": shop["Shop Type"] if shop is not None else "",
            "classification": classification,
            "source_rude": rude.source,
            "source_line": rude.source_line,
            "required_raw_keys": list(rude.required_keys),
            "forbidden_raw_keys": list(rude.forbidden_keys),
            "route_count": service_record_count,
            "errors": errors,
        })

    unused_recoveries = sorted(int(service_id) for service_id in services if int(service_id) not in rude_services)
    missing_docks = sorted(dock_ids - rude_services.keys())
    error_count = sum(len(record["errors"]) for record in audit_services) + len(unused_recoveries) + len(missing_docks)
    audit = {
        "format_version": 1,
        "kind": "mm9_transport_route_audit",
        "generated_from": "MMIXSHOPS, RUDE -5 rows, Boat Schedule item 562, and reviewed cshell.dll recovery",
        "summary": {
            "dock_count": len(dock_ids),
            "rude_service_count": len(rude_services),
            "route_count": len(records),
            "dock_route_count": sum(1 for record in records if record["ServiceClassification"] == "dock"),
            "special_passage_route_count": sum(
                1 for record in records if record["ServiceClassification"] == "special_passage"),
            "zero_route_services": [record["rude_id"] for record in audit_services if record["route_count"] == 0],
            "missing_docks": missing_docks,
            "unused_recoveries": unused_recoveries,
            "unresolved_price_count": 0,
            "unresolved_schedule_count": 0,
            "unresolved_destination_count": 0,
            "error_count": error_count,
        },
        "services": audit_services,
    }
    if error_count:
        raise GenerationError(f"transport audit contains {error_count} errors")
    return records, audit


def write_table(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, TABLE_COLUMNS, dialect="excel-tab", lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shops", type=Path, default=Path("mm9/extracted/DATA/DATA/MMIXSHOPS.txt"))
    parser.add_argument("--rude-dir", type=Path, default=Path("mm9/extracted/RUDE/RUDE"))
    parser.add_argument("--books", type=Path, default=Path("mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"))
    parser.add_argument("--maps-dir", type=Path, default=Path("assets_editor_dev/worlds/mm9/maps"))
    parser.add_argument("--recovery", type=Path,
                        default=Path("tools/mm9_import_discovery/mm9_transport_route_recovery.yml"))
    parser.add_argument("--output", type=Path,
                        default=Path("level_generation/projects/mm9r_common/original_tables/transport_routes.txt"))
    parser.add_argument("--audit", type=Path,
                        default=Path("assets_dev/worlds/mm9/import/transport_route_audit.yml"))
    args = parser.parse_args()
    try:
        records, audit = generate(args.shops, args.rude_dir, args.books, args.maps_dir, args.recovery)
        write_table(args.output, records)
        args.audit.parent.mkdir(parents=True, exist_ok=True)
        args.audit.write_text(yaml.safe_dump(audit, sort_keys=False, width=120), encoding="utf-8")
    except (GenerationError, OSError, ValueError, yaml.YAMLError) as exception:
        parser.error(str(exception))
    print(f"wrote {args.output} ({len(records)} routes)")
    print(f"wrote {args.audit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
