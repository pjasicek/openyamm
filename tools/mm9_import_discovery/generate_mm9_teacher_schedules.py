#!/usr/bin/env python3
"""Generate resolved MM9 teacher schedules without guessing missing DAT markers."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import yaml


COLUMNS = [
    "CanonicalId", "SourceMap", "SourceMapFile", "RudeId", "SourceObjectIndex", "GroupIndex",
    "WorkMinute", "MiscMinute", "ReturnWorkMinute", "HomeMinute",
    "WorkX", "WorkY", "WorkZ", "MiscX", "MiscY", "MiscZ", "HomeX", "HomeY", "HomeZ",
    "SourceScript", "OverrideId", "ReviewState", "Provenance",
]
ARRAY_ENTRY = re.compile(r"ArrayPut\s+aGroup([1-4]),\s*\d+\s*,\s*(\d+)", re.IGNORECASE)
TIMED_ACTION = re.compile(
    r"@M\s+(\d+)\s*:\s*(\d+)\s+Group([1-4])_Go(Work|Misc|Home)\b",
    re.IGNORECASE,
)


class GenerationError(RuntimeError):
    pass


def load_schedule_script(path: Path) -> tuple[dict[int, int], dict[int, tuple[int, int, int, int]]]:
    groups: dict[int, int] = {}
    action_minutes: dict[tuple[int, str], list[int]] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";"):
            continue
        if match := ARRAY_ENTRY.search(line):
            group = int(match.group(1))
            rude_id = int(match.group(2))
            if rude_id in groups and groups[rude_id] != group:
                raise GenerationError(f"{path}: RUDE {rude_id} occurs in multiple schedule groups")
            groups[rude_id] = group
        if match := TIMED_ACTION.search(line):
            minute = int(match.group(1)) * 60 + int(match.group(2))
            key = (int(match.group(3)), match.group(4).casefold())
            action_minutes.setdefault(key, []).append(minute)

    schedules: dict[int, tuple[int, int, int, int]] = {}
    for group in range(1, 5):
        work = sorted(action_minutes.get((group, "work"), []))
        misc = action_minutes.get((group, "misc"), [])
        home = action_minutes.get((group, "home"), [])
        if len(work) != 2 or len(misc) != 1 or len(home) != 1:
            raise GenerationError(f"{path}: incomplete timed actions for group {group}")
        schedules[group] = (work[0], misc[0], work[1], home[0])
    return groups, schedules


def find_scene_actor(value: object, rude_id: int) -> dict[str, object] | None:
    if isinstance(value, dict):
        if value.get("mm9_rude_id") == rude_id:
            return value
        for child in value.values():
            if actor := find_scene_actor(child, rude_id):
                return actor
    elif isinstance(value, list):
        for child in value:
            if actor := find_scene_actor(child, rude_id):
                return actor
    return None


def position(value: object, source: str) -> tuple[int, int, int]:
    if not isinstance(value, dict) or set(value) != {"x", "y", "z"}:
        raise GenerationError(f"{source}: expected x/y/z position")
    coordinates = tuple(value[key] for key in ("x", "y", "z"))
    if not all(isinstance(coordinate, int) for coordinate in coordinates):
        raise GenerationError(f"{source}: position coordinates must be integers")
    return coordinates


def generate(
    trainer_audit_path: Path,
    scripts_dir: Path,
    maps_dir: Path,
    override_path: Path,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    trainer_audit = yaml.safe_load(trainer_audit_path.read_text(encoding="utf-8"))
    override_document = yaml.safe_load(override_path.read_text(encoding="utf-8"))
    overrides = {int(record["rude_id"]): record for record in override_document.get("overrides", [])}
    scheduled: dict[int, dict[str, object]] = {}
    for record in trainer_audit["records"]:
        if record["actor_ownership"] == "scheduled":
            scheduled.setdefault(int(record["rude_id"]), record)

    script_cache: dict[str, tuple[dict[int, int], dict[int, tuple[int, int, int, int]]]] = {}
    scene_cache: dict[str, object] = {}
    table_records: list[dict[str, object]] = []
    audit_records: list[dict[str, object]] = []
    errors: list[str] = []

    for rude_id, trainer in sorted(scheduled.items()):
        region = str(trainer["expected_region"])
        map_stem = region.casefold()
        script_name = f"MM_{region.upper()}.scr"
        script_path = scripts_dir / script_name
        if script_name not in script_cache:
            script_cache[script_name] = load_schedule_script(script_path)
        groups, schedules = script_cache[script_name]
        group = groups.get(rude_id)

        scene_path = maps_dir / f"{map_stem}.scene.yml"
        if map_stem not in scene_cache:
            scene_cache[map_stem] = yaml.safe_load(scene_path.read_text(encoding="utf-8"))
        actor = find_scene_actor(scene_cache[map_stem], rude_id)
        source_object_index = actor.get("mm9_source_object_index") if actor else None

        entry_errors: list[str] = []
        if group is None:
            entry_errors.append("RUDE id is absent from the canonical mundane schedule group")
        if not isinstance(source_object_index, int):
            entry_errors.append("scene actor with stable RUDE/source-object ids is missing")

        override = overrides.get(rude_id)
        resolved = override is not None and not entry_errors
        markers = list(trainer["schedule_destination_markers"])
        missing_markers = list(trainer["missing_schedule_destination_markers"])
        if resolved:
            work = position(override.get("work"), f"override RUDE {rude_id} work")
            misc = position(override.get("misc"), f"override RUDE {rude_id} misc")
            home = position(override.get("home"), f"override RUDE {rude_id} home")
            override_id = str(override.get("id", ""))
            provenance = str(override.get("provenance", ""))
            if not override_id or not provenance or override.get("review_state") != "reviewed":
                raise GenerationError(f"override RUDE {rude_id}: reviewed id and provenance are required")
            times = schedules[group]
            values = work + misc + home
            table_records.append(dict(zip(COLUMNS, [
                f"mm9:teacher_schedule/{map_stem}/{rude_id}", f"mm9:map/{map_stem}",
                f"{map_stem}.odm", rude_id, source_object_index, group, *times, *values,
                script_name, override_id, "reviewed_override", provenance,
            ])))

        errors.extend(f"RUDE {rude_id}: {error}" for error in entry_errors)
        audit_records.append({
            "rude_id": rude_id,
            "region": region,
            "source_object_index": source_object_index,
            "group_index": group,
            "schedule_minutes": list(schedules[group]) if group else [],
            "required_markers": markers,
            "missing_markers": missing_markers,
            "status": "resolved_reviewed_override" if resolved else trainer["schedule_destination_status"],
            "reason": "reviewed override" if resolved else trainer["schedule_destination_reason"],
            "errors": entry_errors,
        })

    unused_overrides = sorted(set(overrides) - set(scheduled))
    errors.extend(f"unused override RUDE {rude_id}" for rude_id in unused_overrides)
    audit = {
        "format_version": 1,
        "kind": "mm9_teacher_schedule_audit",
        "generated_from": "skill trainer audit + canonical mundane SCR + scene actor identities + reviewed overrides",
        "summary": {
            "scheduled_teacher_count": len(scheduled),
            "resolved_schedule_count": len(table_records),
            "unresolved_schedule_count": len(scheduled) - len(table_records),
            "error_count": len(errors),
        },
        "errors": errors,
        "records": audit_records,
    }
    return table_records, audit


def write_table(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--trainer-audit", type=Path,
                        default=root / "assets_dev/worlds/mm9/import/skill_trainer_audit.yml")
    parser.add_argument("--scripts-dir", type=Path, default=root / "mm9/extracted/SCRIPTS/SCRIPTS")
    parser.add_argument("--maps-dir", type=Path, default=root / "assets_editor_dev/worlds/mm9/maps")
    parser.add_argument("--overrides", type=Path,
                        default=root / "tools/mm9_import_discovery/mm9_teacher_schedule_overrides.yml")
    parser.add_argument("--output", type=Path,
                        default=root / "assets_dev/worlds/mm9/data_tables/teacher_schedules.txt")
    parser.add_argument("--audit-output", type=Path,
                        default=root / "assets_dev/worlds/mm9/import/teacher_schedule_audit.yml")
    args = parser.parse_args()

    records, audit = generate(args.trainer_audit, args.scripts_dir, args.maps_dir, args.overrides)
    write_table(args.output, records)
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.write_text(yaml.safe_dump(audit, sort_keys=False), encoding="utf-8")
    if audit["summary"]["error_count"]:
        raise GenerationError("teacher schedule generation found structural errors")
    print(
        f"Generated {len(records)} resolved teacher schedules; "
        f"{audit['summary']['unresolved_schedule_count']} remain unresolved."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
