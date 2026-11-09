#!/usr/bin/env python3
"""Generate the MM9 world's hireling table (worlds/mm9/data_tables/hirelings.txt).

One row per MM9 hireling: the thirteen paid retainers and the two story companions (devdocs/mm9/MM9_HIRELINGS.md,
the research, and MM9_HIRELINGS_PLAN.md, the implementation). Identity, prices, services and passives are MM9's
hard-coded values (the research's sections 1, 4 and 5, from cshell.dll and object.lto); the combat values come from
each one's MONSTERS.txt row through the monster importer's own conversions (generate_mm9_monster_tables.py: damage
types, projectiles, resistances on the MM6-MM8 schools, the mapped monster spells), so a hireling's numbers read as an
imported MM9 monster's. The MM9 balance work (devdocs/mm9_rework/BALANCE_PLAN.md) may revise them later.

    python3 tools/mm9_import_discovery/generate_mm9_hirelings.py [--output PATH]
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_mm9_monster_tables as monsters  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MONSTERS_TXT = ROOT / "mm9/extracted/DATA/DATA/MONSTERS.txt"
OUTPUT = ROOT / "assets_dev/worlds/mm9/data_tables/hirelings.txt"
MM9_QUEST_KEY_QBIT_BASE = 90000          # MM9 raw quest key k is QBit 90000 + k (mm9QBitForRawQuestKey)


@dataclass(frozen=True)
class Hireling:
    rude_id: int
    monster_row: int           # MONSTERS.txt Number
    kind: str                  # paid (at most two) or story (Forad, Tamur: the third slot)
    hire_key: int              # MM9 raw key held while hired
    fee: int = 0               # gold once, at hire
    wage: int = 0              # gold every 28 days
    gold_share: int = 0        # the dialogue's share of found gold; MM9 never deducts it (integer bug, research s. 5)
    service: str = "none"      # the -15 service: town_portal, heal, heal_cure
    passive: str = ""          # gold_percent:N, experience_percent:N, identify_always, repair_always, skill:Name+N


# Research section 1.1 (fees, wages, shares, keys), 4.1 (services) and 4.2 (passives). Portrait folder: MONSTERS row
# - 278, Forad 15 (section 7.2); portraits are the 9npcNN- families of the MM9 PC portrait pipeline.
HIRELINGS = (
    Hireling(42, 279, "paid", 450, 300, 300, 2),
    Hireling(43, 280, "paid", 451, 500, 500, 3),
    Hireling(44, 281, "paid", 452, 500, 500, 5),
    Hireling(85, 282, "paid", 453, 700, 700, 10),
    Hireling(86, 283, "paid", 454, 1000, 1000, 0),
    Hireling(125, 284, "paid", 455, 1000, 1000, 5, passive="skill:DisarmTraps+4|skill:Perception+4"),
    Hireling(126, 285, "paid", 456, 700, 700, 10, passive="gold_percent:20"),
    Hireling(177, 286, "paid", 457, 500, 500, 2, passive="skill:Merchant+6"),
    Hireling(178, 287, "paid", 458, 600, 600, 0, passive="repair_always"),
    Hireling(179, 288, "paid", 459, 1000, 1000, 15, service="town_portal"),
    Hireling(238, 289, "paid", 460, 1000, 1000, 10, service="heal"),
    Hireling(281, 290, "paid", 461, 1000, 1000, 20, passive="experience_percent:10|identify_always"),
    Hireling(308, 291, "paid", 462, 2000, 1000, 20, service="heal_cure"),
    Hireling(2, 252, "story", 29),
    Hireling(309, 292, "story", 190),
)
SERVICE_COOLDOWN_HOURS = 24          # 86400 game seconds after use (research 4.1)
# Florie (research 4.1: MM9 conditions 1, 3, 10, 13: cursed, diseased, insane, poisoned), as the engine's condition
# names (CharacterConditionNames): MM9's one disease and one poison are every stage of the MM6-MM8 ones.
HEAL_CURE_CONDITIONS = "Cursed|DiseaseWeak|DiseaseMedium|DiseaseSevere|Insane|PoisonWeak|PoisonMedium|PoisonSevere"
# Arienh's spells, which no MM9 monster casts (the monster importer has no mapping): MM9_SPELL_MAPPING.md keeps their
# formulas on the MM6-MM8 spells, the skill as MM9's.
HIRELING_SPELL_NAMES = {11: "Fireball", 32: "Toxic Cloud"}

COLUMNS = (
    "rude_id", "name", "kind", "portrait", "monster_row", "hire_qbit", "hire_fee", "wage", "gold_share_percent",
    "service", "service_cooldown_hours", "cured_conditions", "passive",
    "level", "hp", "ac", "recovery_seconds",
    "attack1_type", "attack1_damage", "attack2_type", "attack2_damage", "attack2_missile",
    "spell1", "spell1_share_percent", "spell2",
    "res_fire", "res_air", "res_water", "res_earth", "res_spirit", "res_mind", "res_body", "res_light", "res_dark",
    "res_physical",
)


def portrait(entry: Hireling) -> str:
    folder = 15 if entry.monster_row == 252 else entry.monster_row - 278
    return f"9npc{folder:02d}-01"


def hireling_spell(descriptor: str, row: list[str], number: int) -> str:
    """The mapped `Spell,Mastery,Skill` cell of a hireling spell, or empty."""
    if descriptor in {"", "0"}:
        return ""
    spell_id = int(descriptor.split(",")[0])
    if spell_id in HIRELING_SPELL_NAMES:
        _, mastery, skill = (part.strip() for part in descriptor.split("(")[0].split(",")[:3])
        return f"{HIRELING_SPELL_NAMES[spell_id]},{mastery.upper()},{int(skill)}"
    parsed = monsters.parse_source_spell(descriptor, row, number)
    return parsed[0] if parsed is not None else ""


def build_row(entry: Hireling, row: list[str]) -> list[str]:
    number = entry.monster_row
    value = lambda name: monsters.source_value(row, name)  # noqa: E731
    spell1 = hireling_spell(value("spell1"), row, number)
    spell2 = hireling_spell(value("spell2"), row, number)
    # The casters (Arienh, Ake) attack only by spell (Projectile1 Spell, research section 9): SpellUse%1 picks spell 1,
    # the rest spell 2.
    share = monsters.numeric_chance(value("spell1_chance"), number, "spell 1") if spell1 else 0
    if spell1 and not spell2:
        share = 100
    attack2 = monsters.has_attack2_damage(row)
    attack2_projectile = value("attack2_projectile").capitalize() if attack2 else "0"
    elemental = monsters.resistance(value("elemental_resistance"))
    spirit = monsters.resistance(value("spirit_resistance"))
    recovery = float(value("recovery") or "0") * monsters.MM9_GAME_SECOND_SECONDS
    return [
        str(entry.rude_id), value("name"), entry.kind, portrait(entry), str(number),
        str(MM9_QUEST_KEY_QBIT_BASE + entry.hire_key), str(entry.fee), str(entry.wage), str(entry.gold_share),
        entry.service, str(SERVICE_COOLDOWN_HOURS if entry.service != "none" else 0),
        HEAL_CURE_CONDITIONS if entry.service == "heal_cure" else "", entry.passive,
        value("level"), value("hp"), value("ac"), f"{recovery:.3f}",
        monsters.damage_type(row, value("attack1_type"), value("attack1_projectile"), number),
        value("attack1_damage").lower(),
        monsters.damage_type(row, value("attack2_type"), value("attack2_projectile"), number) if attack2 else "0",
        value("attack2_damage").lower() if attack2 else "0",
        # Hrolf, Tesar and Randver shoot arrows out of reach, which no MM9 monster does: the engine's Arrow missile
        "Arrow" if attack2_projectile == "Arrow" else monsters.projectile_token(attack2_projectile, number)
        if attack2 else "0",
        spell1, str(share), spell2,
        elemental, elemental, elemental, elemental, spirit, spirit, spirit,
        monsters.resistance(value("light_resistance")), monsters.resistance(value("dark_resistance")),
        monsters.resistance(value("physical_resistance")),
    ]


def generate(monsters_path: Path) -> list[list[str]]:
    sources = monsters.source_monsters(monsters_path, frozenset(entry.monster_row for entry in HIRELINGS))
    rows = [list(COLUMNS)]
    for entry in HIRELINGS:
        if entry.monster_row not in sources:
            raise ValueError(f"MONSTERS.txt has no row {entry.monster_row} for hireling {entry.rude_id}")
        rows.append(build_row(entry, sources[entry.monster_row]))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--monsters", type=Path, default=MONSTERS_TXT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    rows = generate(args.monsters)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as output:
        csv.writer(output, delimiter="\t", lineterminator="\n").writerows(rows)
    temporary.replace(args.output)
    print(f"wrote {args.output} ({len(rows) - 1} hirelings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
