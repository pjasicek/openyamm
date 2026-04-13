#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


OPERATION_PATTERN = re.compile(r"\s*\d+:\s*([A-Za-z0-9_.]+)\s*\{")
VARIABLE_OPERATION_PATTERN = re.compile(
    r'\s*\d+:\s*(Cmp|Add|Set|Subtract|CanShowTopic\.Cmp|CanShowTopic\.Set)\s*\{"([A-Za-z][A-Za-z0-9]*)"'
)


@dataclass(frozen=True)
class CoverageEntry:
    evt_variable: str
    lua_surface: str
    notes: str = ""


COVERAGE = {
    "AirResistance": CoverageEntry("EvtVariable::AirResistance", "AirResistance", "Direct selector tag."),
    "AutonotesBits": CoverageEntry(
        "EvtVariable::AutoNotes",
        "AutonoteBit(id), IsAutonoteSet(id), SetAutonote(id), ClearAutonote(id)",
        "Authored API uses direct autonote helpers instead of magic packed selectors.",
    ),
    "Awards": CoverageEntry(
        "EvtVariable::Awards",
        "Award(id), HasAward(id), SetAward(id), ClearAward(id)",
        "Awards are authored as indexed ids, not raw packed numbers.",
    ),
    "BankGold": CoverageEntry("EvtVariable::GoldInBank", "BankGold", "Direct selector tag."),
    "BaseAccuracy": CoverageEntry("EvtVariable::BaseAccuracy", "BaseAccuracy", "Direct selector tag."),
    "BaseEndurance": CoverageEntry("EvtVariable::BaseEndurance", "BaseEndurance", "Direct selector tag."),
    "BaseIntellect": CoverageEntry("EvtVariable::BaseIntellect", "BaseIntellect", "Direct selector tag."),
    "BaseLuck": CoverageEntry("EvtVariable::BaseLuck", "BaseLuck", "Direct selector tag."),
    "BaseMight": CoverageEntry("EvtVariable::BaseMight", "BaseMight", "Direct selector tag."),
    "BasePersonality": CoverageEntry("EvtVariable::BasePersonality", "BasePersonality", "Direct selector tag."),
    "BaseSpeed": CoverageEntry("EvtVariable::BaseSpeed", "BaseSpeed", "Direct selector tag."),
    "ClassIs": CoverageEntry("EvtVariable::ClassId", "ClassIs", "Decompiled name kept for authored Lua."),
    "Counter": CoverageEntry(
        "EvtVariable::Counter1..Counter10",
        "Counter(index), AddToCounter(selector, value), SetCounter(selector, value)",
        "Indexed selector family.",
    ),
    "CurrentAccuracy": CoverageEntry("EvtVariable::ActualAccuracy", "CurrentAccuracy", "Direct selector tag."),
    "CurrentEndurance": CoverageEntry("EvtVariable::ActualEndurance", "CurrentEndurance", "Direct selector tag."),
    "CurrentIntellect": CoverageEntry("EvtVariable::ActualIntellect", "CurrentIntellect", "Direct selector tag."),
    "CurrentLuck": CoverageEntry("EvtVariable::ActualLuck", "CurrentLuck", "Direct selector tag."),
    "CurrentMight": CoverageEntry("EvtVariable::ActualMight", "CurrentMight", "Direct selector tag."),
    "CurrentPersonality": CoverageEntry(
        "EvtVariable::ActualPersonality",
        "CurrentPersonality",
        "Direct selector tag.",
    ),
    "CurrentSpeed": CoverageEntry("EvtVariable::ActualSpeed", "CurrentSpeed", "Direct selector tag."),
    "DayOfWeekIs": CoverageEntry("EvtVariable::DayOfWeek", "DayOfWeekIs", "Direct selector tag."),
    "Dead": CoverageEntry("EvtVariable::Dead", "Dead", "Direct selector tag."),
    "DiseasedGreen": CoverageEntry("EvtVariable::DiseasedGreen", "DiseasedGreen", "Direct selector tag."),
    "DiseasedYellow": CoverageEntry("EvtVariable::DiseasedYellow", "DiseasedYellow", "Direct selector tag."),
    "Drunk": CoverageEntry("EvtVariable::Drunk", "Drunk", "Direct selector tag."),
    "EarthResistance": CoverageEntry("EvtVariable::EarthResistance", "EarthResistance", "Direct selector tag."),
    "Experience": CoverageEntry("EvtVariable::Experience", "Experience", "Direct selector tag."),
    "FireResBonus": CoverageEntry("EvtVariable::FireResistanceBonus", "FireResBonus", "Direct selector tag."),
    "FireResistance": CoverageEntry("EvtVariable::FireResistance", "FireResistance", "Direct selector tag."),
    "Food": CoverageEntry("EvtVariable::Food", "Food", "Direct selector tag."),
    "Gold": CoverageEntry("EvtVariable::Gold", "Gold", "Direct selector tag."),
    "HasFullHP": CoverageEntry(
        "EvtVariable::MaxHealth",
        "HasFullHP",
        "Decompiled semantic name for the full-health compare selector.",
    ),
    "HasFullSP": CoverageEntry(
        "EvtVariable::MaxSpellPoints",
        "HasFullSP",
        "Decompiled semantic name for the full-spell-points compare selector.",
    ),
    "History": CoverageEntry(
        "EvtVariable::HistoryBegin..HistoryEnd",
        "History(index)",
        "Indexed selector family.",
    ),
    "HP": CoverageEntry("EvtVariable::CurrentHealth", "HP", "Decompiled semantic name kept for authored Lua."),
    "IntellectBonus": CoverageEntry("EvtVariable::IntellectBonus", "IntellectBonus", "Direct selector tag."),
    "Inventory": CoverageEntry(
        "EvtVariable::Inventory",
        "InventoryItem(id), HasItem(id), RemoveItem(id), GiveItem(id)",
        "Indexed inventory helper family.",
    ),
    "Invisible": CoverageEntry("EvtVariable::Invisible", "Invisible", "Direct selector tag."),
    "MapVar": CoverageEntry(
        "EvtVariable::MapPersistentVariableBegin..End",
        "MapVar(index)",
        "Indexed selector family.",
    ),
    "MightBonus": CoverageEntry("EvtVariable::MightBonus", "MightBonus", "Direct selector tag."),
    "PersonalityBonus": CoverageEntry("EvtVariable::PersonalityBonus", "PersonalityBonus", "Direct selector tag."),
    "PlayerBits": CoverageEntry(
        "EvtVariable::PlayerBits",
        "PlayerBit(index), IsPlayerBitSet(index), SetPlayerBit(index), ClearPlayerBit(index)",
        "Indexed authored helper family.",
    ),
    "Players": CoverageEntry(
        "EvtVariable::Players",
        "Player(index), HasPlayer(index)",
        "Roster-member indexed selector family.",
    ),
    "PoisonedGreen": CoverageEntry("EvtVariable::PoisonedGreen", "PoisonedGreen", "Direct selector tag."),
    "PoisonedYellow": CoverageEntry("EvtVariable::PoisonedYellow", "PoisonedYellow", "Direct selector tag."),
    "QBits": CoverageEntry(
        "EvtVariable::QBits",
        "QBit(id), IsQBitSet(id), SetQBit(id), ClearQBit(id)",
        "Indexed authored helper family.",
    ),
    "RepairSkill": CoverageEntry("EvtVariable::RepairSkill", "RepairSkill", "Direct selector tag."),
    "SkillPoints": CoverageEntry("EvtVariable::NumSkillPoints", "SkillPoints", "Direct selector tag."),
    "SP": CoverageEntry(
        "EvtVariable::CurrentSpellPoints",
        "SP",
        "Decompiled semantic name kept for authored Lua.",
    ),
    "WaterResistance": CoverageEntry("EvtVariable::WaterResistance", "WaterResistance", "Direct selector tag."),
}


def normalize_variable_family(raw_name: str) -> str:
    for prefix in ("MapVar", "Counter", "History"):
        if raw_name.startswith(prefix) and raw_name[len(prefix) :].isdigit():
            return prefix

    return raw_name


def collect_semantics(input_dir: Path) -> tuple[Counter[str], Counter[str]]:
    operation_counts: Counter[str] = Counter()
    variable_counts: Counter[str] = Counter()

    for path in sorted(input_dir.glob("*.txt")):
        for line in path.read_text(errors="ignore").splitlines():
            operation_match = OPERATION_PATTERN.match(line)

            if operation_match is None:
                continue

            operation = operation_match.group(1)
            operation_counts[operation] += 1

            variable_match = VARIABLE_OPERATION_PATTERN.match(line)

            if variable_match is None:
                continue

            variable_counts[normalize_variable_family(variable_match.group(2))] += 1

    return operation_counts, variable_counts


def render_markdown(operation_counts: Counter[str], variable_counts: Counter[str]) -> str:
    lines = []
    lines.append("# Decompiled Event Semantic Catalog")
    lines.append("")
    lines.append("Generated from `OpenMM8_Data/DecompiledScripts/*`.")
    lines.append("")
    lines.append("## Operations")
    lines.append("")
    lines.append("| Operation | Count |")
    lines.append("| --- | ---: |")

    for operation, count in sorted(operation_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{operation}` | {count} |")

    lines.append("")
    lines.append("## Variable Kinds")
    lines.append("")
    lines.append("| Decompiled Kind | Count | Internal Tag | Authored Lua Surface | Notes |")
    lines.append("| --- | ---: | --- | --- | --- |")

    for variable_name, count in sorted(variable_counts.items(), key=lambda item: (-item[1], item[0])):
        coverage = COVERAGE[variable_name]
        lines.append(
            f"| `{variable_name}` | {count} | `{coverage.evt_variable}` | `{coverage.lua_surface}` | {coverage.notes} |"
        )

    lines.append("")
    lines.append("## Coverage Check")
    lines.append("")
    lines.append(
        "Every normalized variable kind referenced by the decompiled corpus must exist in the coverage table used by"
    )
    lines.append("this tool. The tool exits with a failure if any kind is missing.")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    operation_counts, variable_counts = collect_semantics(args.input_dir)
    missing = sorted(set(variable_counts) - set(COVERAGE))

    if missing:
        print("Missing semantic coverage entries:", file=sys.stderr)

        for variable_name in missing:
            print(f"  - {variable_name}", file=sys.stderr)

        return 1

    args.output.write_text(render_markdown(operation_counts, variable_counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
