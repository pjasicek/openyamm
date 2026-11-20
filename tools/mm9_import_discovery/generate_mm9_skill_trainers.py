#!/usr/bin/env python3
"""Generate MM9 mastery-trainer services from RUDE rows and teacher hints."""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml


# MM9's 23 trainer skills in RUDE payload order (three payload ids per skill), each with the separate OpenYAMM skills
# it covers (user decision 2026-11-05: no composite skills; MM9 Blade is Sword, Dagger and Axe, Cudgel is Mace and
# Staff, Armor the three armour skills, Elemental the four elemental schools). Every skill is its own training choice.
SKILL_GROUPS = [
    ("Blade", "Sword|Dagger|Axe"),
    ("Cudgel", "Mace|Staff"),
    ("Spear", "Spear"),
    ("Bow", "Bow"),
    ("Thrown", "Throwing"),
    ("Armsmaster", "Armsmaster"),
    ("Unarmed", "Unarmed"),
    ("Armor", "LeatherArmor|ChainArmor|PlateArmor"),
    ("Shield", "Shield"),
    ("Dodging", "Dodging"),
    ("Elemental", "FireMagic|AirMagic|WaterMagic|EarthMagic"),
    ("Light", "LightMagic"),
    ("Dark", "DarkMagic"),
    ("Spirit", "SpiritMagic"),
    ("Meditation", "Meditation"),
    ("DisarmTrap", "DisarmTraps"),
    ("Merchant", "Merchant"),
    ("Perception", "Perception"),
    ("RepairItem", "RepairItem"),
    ("IdentifyItem", "IdentifyItem"),
    ("IdentifyMonster", "IdentifyMonster"),
    ("BodyBuilding", "Bodybuilding"),
    ("Learning", "Learning"),
]
# MM6-MM8 skills MM9 has no trainer for, taught by the MM9 trainers of the closest MM9 skill at the same masteries
# (the user allows more MM9 teachers; these need no map change): MM9's Spirit school is MM6-MM8's self magic, Disarm
# Trap is the thief's craft, Body Building the endurance skill and Identify Item the lore of items and potions.
ADDED_SKILLS = {
    "Spirit": "MindMagic|BodyMagic",
    "DisarmTrap": "Stealing",
    "BodyBuilding": "Regeneration",
    "IdentifyItem": "Alchemy",
}
# Every MM6-MM8 skill MMerge's teachers train to Expert, Master and Grandmaster (assets_dev/engine/data_tables/
# teacher_topics.txt skill ids 0-38) plus Throwing. The MM9 world trains each of them at each mastery, except the
# reviewed exceptions below, which need new MM9 trainer NPCs (devdocs/mm9/MM9_RUDE_SCR_INTEGRATION.md "Skills And
# Mastery").
TRAINABLE_SKILLS = (
    "Staff", "Sword", "Dagger", "Axe", "Spear", "Bow", "Mace", "Blaster", "Shield",
    "LeatherArmor", "ChainArmor", "PlateArmor",
    "FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "SpiritMagic", "MindMagic", "BodyMagic",
    "LightMagic", "DarkMagic", "DarkElfAbility", "VampireAbility", "DragonAbility",
    "IdentifyItem", "Merchant", "RepairItem", "Bodybuilding", "Meditation", "Perception", "Regeneration",
    "DisarmTraps", "Dodging", "Unarmed", "IdentifyMonster", "Armsmaster", "Stealing", "Alchemy", "Learning",
    "Throwing",
)
UNTAUGHT_SKILLS = {
    "Blaster": "no MM9 skill or teacher is close; proposed new trainer NPC",
    "DarkElfAbility": "MM8 racial ability; taught by the racial trainers (dialogue/racial_trainers.yml)",
    "VampireAbility": "MM8 racial ability; taught by the racial trainers (dialogue/racial_trainers.yml)",
    "DragonAbility": "MM8 racial ability; taught by the racial trainers (dialogue/racial_trainers.yml)",
}
MASTERIES = ("Expert", "Master", "Grandmaster")
REGIONS = (
    "Sturmford", "Drangheim", "Thjorgard", "Guberland",
    "Thronheim", "Lindisfarne", "Frosgard", "Yorwick",
)
SCHEDULE_OWNED_REGIONS = {"Lindisfarne", "Yorwick"}
TABLE_COLUMNS = [
    "CanonicalId",
    "RudeId",
    "RudeRowIndex",
    "SourceLine",
    "ChoiceSlot",
    "RawTrainerId",
    "Mm9Skill",
    "SharedSkills",
    "TargetMastery",
    "RequiredSkillRank",
    "RequiredGold",
    "RequiredRawKeys",
    "ForbiddenRawKeys",
    "ExpectedRegion",
    "SourceDisplayNames",
    "Npc998Hint",
    "ActorOwnership",
    "ActorSources",
    "SourceRude",
    "Provenance",
]
NPC_FILE = re.compile(r"NPC(\d+)\.rude", re.IGNORECASE)
STATIC_RUDE_ID = re.compile(r"^\s+mm9_rude_id:\s+(\d+)\s*$", re.MULTILINE)
SCHEDULE_RUDE_ID = re.compile(r"ArrayPut\s+aGroup\d+,\d+,(\d+)", re.IGNORECASE)
SCHEDULE_MARKER_KINDS = ("Work", "Home", "Misc")


class GenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class RudeService:
    rude_id: int
    row_index: int
    source_line: int
    choice_slot: int
    prompt: str
    raw_trainer_id: int
    required_keys: tuple[int, ...]
    forbidden_keys: tuple[int, ...]
    source: str


def parse_int(value: str, source: str) -> int:
    try:
        return int(value)
    except ValueError as exception:
        raise GenerationError(f"{source}: expected integer, got {value!r}") from exception


def nonzero_columns(row: list[str], columns: Iterable[int], source: str) -> tuple[int, ...]:
    return tuple(value for column in columns if (value := parse_int(row[column], source)) != 0)


def load_rude_services(rude_dir: Path) -> list[RudeService]:
    services: list[RudeService] = []
    for path in sorted(rude_dir.glob("NPC*.rude"), key=lambda item: item.name.casefold()):
        match = NPC_FILE.fullmatch(path.name)
        if match is None:
            continue
        rude_id = int(match.group(1))
        row_index = 0
        with path.open(encoding="utf-8", errors="replace", newline="") as stream:
            for source_line, row in enumerate(csv.reader(stream), 1):
                if len(row) < 30:
                    raise GenerationError(f"{path}:{source_line}: expected at least 30 RUDE columns")
                if parse_int(row[0], f"{path}:{source_line}") != rude_id:
                    raise GenerationError(f"{path}:{source_line}: RUDE id does not match filename")
                if row[5] == "-4":
                    services.append(RudeService(
                        rude_id=rude_id,
                        row_index=row_index,
                        source_line=source_line,
                        choice_slot=parse_int(row[2], f"{path}:{source_line}"),
                        prompt=row[3],
                        raw_trainer_id=parse_int(row[15], f"{path}:{source_line}"),
                        required_keys=nonzero_columns(row, (6, 8, 10, 12, 14), f"{path}:{source_line}"),
                        forbidden_keys=nonzero_columns(row, (20, 21, 22, 23, 24), f"{path}:{source_line}"),
                        source=path.as_posix(),
                    ))
                row_index += 1
    if not services:
        raise GenerationError(f"{rude_dir}: no RUDE -4 mastery services found")
    return services


def load_npc_names(path: Path) -> dict[int, str]:
    result: dict[int, str] = {}
    with path.open(encoding="utf-8", errors="replace", newline="") as stream:
        for source_line, row in enumerate(csv.reader(stream), 1):
            if len(row) < 2:
                raise GenerationError(f"{path}:{source_line}: expected NPC id and name")
            rude_id = parse_int(row[0], f"{path}:{source_line}")
            if rude_id in result:
                raise GenerationError(f"{path}:{source_line}: duplicate NPC id {rude_id}")
            result[rude_id] = row[1]
    return result


def load_teacher_hints(path: Path) -> dict[int, str]:
    result: dict[int, str] = {}
    with path.open(encoding="utf-8", errors="replace", newline="") as stream:
        for source_line, row in enumerate(csv.reader(stream), 1):
            if len(row) < 7:
                raise GenerationError(f"{path}:{source_line}: expected at least 7 RUDE columns")
            topic_id = parse_int(row[6], f"{path}:{source_line}")
            if not 2006 <= topic_id <= 2074:
                continue
            if topic_id in result:
                raise GenerationError(f"{path}:{source_line}: duplicate teacher hint {topic_id}")
            result[topic_id] = row[3]
    return result


def load_actor_sources(maps_dir: Path, scripts_dir: Path) -> tuple[dict[int, list[str]], dict[int, list[str]]]:
    static_sources: dict[int, list[str]] = {}
    for path in sorted(maps_dir.glob("*.scene.yml"), key=lambda item: item.name.casefold()):
        for match in STATIC_RUDE_ID.finditer(path.read_text(encoding="utf-8", errors="replace")):
            rude_id = int(match.group(1))
            if rude_id:
                static_sources.setdefault(rude_id, []).append(path.as_posix())

    schedule_sources: dict[int, list[str]] = {}
    for path in sorted(scripts_dir.glob("MM_*.scr"), key=lambda item: item.name.casefold()):
        for match in SCHEDULE_RUDE_ID.finditer(path.read_text(encoding="utf-8", errors="replace")):
            rude_id = int(match.group(1))
            sources = schedule_sources.setdefault(rude_id, [])
            if path.as_posix() not in sources:
                sources.append(path.as_posix())
    return static_sources, schedule_sources


def audit_schedule_destinations(
    maps_dir: Path,
    region: str,
    rude_id: int,
) -> tuple[str, list[str], list[str], str]:
    expected_markers = [f"Marker_{kind}_{rude_id}" for kind in SCHEDULE_MARKER_KINDS]
    if region not in SCHEDULE_OWNED_REGIONS:
        return "not_schedule_owned", expected_markers, [], ""

    raw_objects_path = maps_dir / f"{region.casefold()}.raw_objects.yml"
    if not raw_objects_path.is_file():
        return (
            "unresolved_missing_raw_object_inventory",
            expected_markers,
            expected_markers,
            f"{raw_objects_path.as_posix()} is missing",
        )

    raw_objects = raw_objects_path.read_text(encoding="utf-8", errors="replace")
    missing_markers = [
        marker
        for marker in expected_markers
        if f'value_json: "\\"{marker}\\""' not in raw_objects
    ]
    if missing_markers:
        return (
            "unresolved_missing_destination_markers",
            expected_markers,
            missing_markers,
            "mundane SCR names schedule destinations that are absent from the source DAT raw-object inventory",
        )
    return "resolved", expected_markers, [], ""


def trainer_skills(skill: str) -> tuple[str, str]:
    """The separate skills MM9's skill covers and the MM6-MM8 skills added to its trainers."""
    split_skills = dict(SKILL_GROUPS)[skill]
    return split_skills, ADDED_SKILLS.get(skill, "")


def topic_definition(raw_trainer_id: int, choice_slot: int) -> tuple[str, str, str, int]:
    if not 2006 <= raw_trainer_id <= 2074:
        raise GenerationError(f"trainer topic {raw_trainer_id} is outside 2006-2074")
    offset = raw_trainer_id - 2006
    skill_index = offset // 3
    variant = offset % 3
    skill = SKILL_GROUPS[skill_index][0]
    shared_skills = "|".join(filter(None, trainer_skills(skill)))
    if variant == 2:
        mastery = "Grandmaster"
        required_rank = 10
    elif choice_slot == 1:
        mastery = "Expert"
        required_rank = 4
    elif choice_slot == 2:
        mastery = "Master"
        required_rank = 7
    else:
        raise GenerationError(f"trainer topic {raw_trainer_id} has unsupported choice slot {choice_slot}")
    return skill, shared_skills, mastery, required_rank


def hint_region(hint: str) -> str:
    matches = [region for region in REGIONS if re.search(rf"\b{re.escape(region)}\b", hint, re.IGNORECASE)]
    if len(matches) != 1:
        raise GenerationError(f"teacher hint has {len(matches)} expected regions: {hint!r}")
    return matches[0]


def hint_name(hint: str, region: str) -> str:
    marker = re.search(rf"\s+of\s+{re.escape(region)}\b", hint, re.IGNORECASE)
    if marker is None:
        raise GenerationError(f"teacher hint has no name/region separator: {hint!r}")
    return hint[:marker.start()].strip()


def skill_hint_matches(skill: str, hint: str) -> bool:
    expected = {
        "DisarmTrap": "Disarm Trap",
        "RepairItem": "Repair Item",
        "IdentifyItem": "Identify Item",
        "IdentifyMonster": ("Identify Monster", "ID Monster"),
        "BodyBuilding": ("Body Building", "Bodybuilding"),
        "Elemental": "Elemental",
        "Light": "Light",
        "Dark": "Dark",
        "Spirit": "Spirit",
        "Thrown": "Thrown",
        "Dodging": "Dodge",
    }.get(skill, skill)
    needles = expected if isinstance(expected, tuple) else (expected,)
    return any(needle.casefold() in hint.casefold() for needle in needles)


def generate(
    rude_dir: Path,
    maps_dir: Path,
    scripts_dir: Path,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    services = load_rude_services(rude_dir)
    npc_names = load_npc_names(rude_dir / "NPCNAME.rude")
    hints = load_teacher_hints(rude_dir / "NPC998.rude")
    static_sources, schedule_sources = load_actor_sources(maps_dir, scripts_dir)
    records: list[dict[str, object]] = []
    audit_records: list[dict[str, object]] = []
    seen_ids: set[str] = set()

    for service in services:
        errors: list[str] = []
        try:
            skill, shared_skills, mastery, required_rank = topic_definition(
                service.raw_trainer_id, service.choice_slot)
        except GenerationError as exception:
            errors.append(str(exception))
            skill, shared_skills, mastery, required_rank = "", "", "", 0
        hint = hints.get(service.raw_trainer_id, "")
        if not hint:
            errors.append("NPC998 teacher hint is missing")
            region = ""
            hinted_name = ""
        else:
            try:
                region = hint_region(hint)
                hinted_name = hint_name(hint, region)
            except GenerationError as exception:
                errors.append(str(exception))
                region = ""
                hinted_name = ""
            if skill and not skill_hint_matches(skill, hint):
                errors.append(f"NPC998 hint does not identify {skill}")

        source_name = npc_names.get(service.rude_id, "")
        if not source_name:
            errors.append("NPCNAME display name is missing")
        display_names = list(dict.fromkeys(name for name in (source_name, hinted_name) if name))
        static = static_sources.get(service.rude_id, [])
        scheduled = schedule_sources.get(service.rude_id, [])
        if scheduled and region in SCHEDULE_OWNED_REGIONS:
            actor_ownership = "scheduled"
            actor_sources = static + scheduled
        elif static:
            actor_ownership = "static"
            actor_sources = static
        elif scheduled:
            actor_ownership = "scheduled"
            actor_sources = scheduled
        else:
            actor_ownership = "missing"
            actor_sources = []
            errors.append("trainer has neither static actor nor schedule ownership")

        schedule_status, schedule_markers, missing_schedule_markers, schedule_reason = (
            audit_schedule_destinations(maps_dir, region, service.rude_id)
            if actor_ownership == "scheduled"
            else ("not_schedule_owned", [], [], "")
        )

        canonical_id = f"mm9:trainer/{service.rude_id}/{service.source_line}"
        if canonical_id in seen_ids:
            errors.append("duplicate trainer service id")
        seen_ids.add(canonical_id)
        record = {
            "CanonicalId": canonical_id,
            "RudeId": service.rude_id,
            "RudeRowIndex": service.row_index,
            "SourceLine": service.source_line,
            "ChoiceSlot": service.choice_slot,
            "RawTrainerId": service.raw_trainer_id,
            "Mm9Skill": skill,
            "SharedSkills": shared_skills,
            "TargetMastery": mastery,
            "RequiredSkillRank": required_rank,
            "RequiredGold": 0,
            "RequiredRawKeys": "|".join(map(str, service.required_keys)),
            "ForbiddenRawKeys": "|".join(map(str, service.forbidden_keys)),
            "ExpectedRegion": region,
            "SourceDisplayNames": "|".join(display_names),
            "Npc998Hint": hint,
            "ActorOwnership": actor_ownership,
            "ActorSources": "|".join(actor_sources),
            "SourceRude": service.source,
            "Provenance": "rude:-4+npc998_crosscheck+actor_ownership_audit",
        }
        records.append(record)
        audit_records.append({
            "canonical_id": canonical_id,
            "rude_id": service.rude_id,
            "source_line": service.source_line,
            "raw_trainer_id": service.raw_trainer_id,
            "skill": skill,
            "split_skills": trainer_skills(skill)[0].split("|") if skill else [],
            "added_skills": [name for name in trainer_skills(skill)[1].split("|") if name] if skill else [],
            "mastery": mastery,
            "expected_region": region,
            "source_display_names": display_names,
            "actor_ownership": actor_ownership,
            "actor_sources": actor_sources,
            "schedule_sources": scheduled,
            "schedule_destination_status": schedule_status,
            "schedule_destination_markers": schedule_markers,
            "missing_schedule_destination_markers": missing_schedule_markers,
            "schedule_destination_reason": schedule_reason,
            "errors": errors,
        })

    coverage, untaught = skill_coverage(records)

    used_topics = {service.raw_trainer_id for service in services}
    unused_hints = sorted(set(hints) - used_topics)
    summary = {
        "service_row_count": len(records),
        "trainer_npc_count": len({service.rude_id for service in services}),
        "trainer_topic_count": len(used_topics),
        "skill_group_count": len({record["Mm9Skill"] for record in records}),
        "expert_count": sum(record["TargetMastery"] == "Expert" for record in records),
        "master_count": sum(record["TargetMastery"] == "Master" for record in records),
        "grandmaster_count": sum(record["TargetMastery"] == "Grandmaster" for record in records),
        "static_trainer_count": len({
            int(record["rude_id"])
            for record in audit_records
            if record["actor_ownership"] == "static"
        }),
        "scheduled_trainer_count": len({
            service.rude_id for service in services if service.rude_id in schedule_sources
        }),
        "scheduled_only_trainer_count": len({
            int(record["rude_id"])
            for record in audit_records
            if record["actor_ownership"] == "scheduled"
        }),
        "unresolved_schedule_destination_count": len({
            int(record["rude_id"])
            for record in audit_records
            if str(record["schedule_destination_status"]).startswith("unresolved_")
        }),
        "missing_actor_count": len({
            service.rude_id for service in services
            if service.rude_id not in static_sources and service.rude_id not in schedule_sources
        }),
        "error_count": sum(len(record["errors"]) for record in audit_records),
        "unused_npc998_hints": unused_hints,
        "untaught_skill_masteries": untaught,
    }
    audit = {
        "format_version": 1,
        "kind": "mm9_skill_trainer_audit",
        "generated_from": "RUDE -4 rows, NPC998 teacher hints, scene actors, and mundane-task scripts",
        "summary": summary,
        "coverage": coverage,
        "records": audit_records,
    }
    if summary["error_count"] or unused_hints:
        raise GenerationError(
            f"trainer audit contains {summary['error_count']} errors and {len(unused_hints)} unused hints")
    return records, audit


def skill_coverage(
    records: list[dict[str, object]],
) -> tuple[dict[str, dict[str, list[str]]], list[dict[str, str]]]:
    """Which trainers teach each MM6-MM8 skill at each mastery, and the skill masteries nobody teaches."""
    coverage: dict[str, dict[str, list[str]]] = {
        skill: {mastery: [] for mastery in MASTERIES} for skill in TRAINABLE_SKILLS
    }
    for record in records:
        mastery = str(record["TargetMastery"])
        teacher = f"{str(record['SourceDisplayNames']).split('|')[0]} ({record['RudeId']}, {record['ExpectedRegion']})"
        for skill in str(record["SharedSkills"]).split("|"):
            if skill not in coverage or mastery not in MASTERIES:
                raise GenerationError(f"{record['CanonicalId']}: unknown skill {skill!r} or mastery {mastery!r}")
            if teacher not in coverage[skill][mastery]:
                coverage[skill][mastery].append(teacher)
    untaught = [
        {"skill": skill, "mastery": mastery, "reason": UNTAUGHT_SKILLS.get(skill, "")}
        for skill, masteries in coverage.items()
        for mastery, teachers in masteries.items()
        if not teachers
    ]
    return coverage, untaught


def require_complete_coverage(audit: dict[str, object]) -> None:
    """Every trainable skill mastery has an MM9 trainer or a reviewed reason why it has none."""
    summary = audit["summary"]
    unexplained = [
        f"{entry['mastery']} {entry['skill']}"
        for entry in summary["untaught_skill_masteries"]
        if not entry["reason"]
    ]
    taught_exceptions = sorted(
        skill for skill in UNTAUGHT_SKILLS
        if any(audit["coverage"][skill][mastery] for mastery in MASTERIES)
    )
    if unexplained or taught_exceptions:
        raise GenerationError(
            f"no MM9 trainer teaches {', '.join(unexplained) or 'nothing missing'}; "
            f"taught but listed as untaught: {', '.join(taught_exceptions) or 'none'}")


def write_table(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, TABLE_COLUMNS, dialect="excel-tab", lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rude-dir", type=Path, default=Path("assets_dev/worlds/mm9/dialogue/rude"))
    parser.add_argument("--maps-dir", type=Path, default=Path("assets_editor_dev/worlds/mm9/maps"))
    parser.add_argument("--scripts-dir", type=Path, default=Path("mm9/extracted/SCRIPTS/SCRIPTS"))
    parser.add_argument("--output", type=Path, default=Path("assets_dev/worlds/mm9/data_tables/skill_trainers.txt"))
    parser.add_argument("--audit", type=Path, default=Path("assets_dev/worlds/mm9/import/skill_trainer_audit.yml"))
    args = parser.parse_args()
    try:
        records, audit = generate(args.rude_dir, args.maps_dir, args.scripts_dir)
        require_complete_coverage(audit)
        write_table(args.output, records)
        args.audit.parent.mkdir(parents=True, exist_ok=True)
        args.audit.write_text(yaml.safe_dump(audit, sort_keys=False, width=120), encoding="utf-8")
    except (GenerationError, OSError, ValueError, yaml.YAMLError) as exception:
        parser.error(str(exception))
    print(f"wrote {args.output} ({len(records)} trainer services)")
    print(f"wrote {args.audit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
