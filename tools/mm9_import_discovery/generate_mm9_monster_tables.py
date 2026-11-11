#!/usr/bin/env python3
"""Generate world-owned OpenYAMM monster rows from MM9 MONSTERS.txt."""

from __future__ import annotations

import argparse
import csv
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml

from mm9_monster_balance import balance_monster_rows
from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE


MM9_MONSTER_ID_BASE = 9000
FAMILY_TIER_LETTERS = "ABC"
OPENYAMM_TICKS_PER_SECOND = 128
# Runtime monster recovery applies the classic OE real-time factor after reading table ticks.
OPENYAMM_MONSTER_RECOVERY_SCALE = 2.133333333333333
# One MM9 game second in real seconds (the RPG clock's 33 ms step, object.lto 0x10055c10).
MM9_GAME_SECOND_SECONDS = 0.033
# Fly 0 in MONSTERS.txt, but Banshee.scr flies them through FlyRange.inc (FlyVelocity 250).
SCRIPT_FLYING_SOURCES = {162, 163, 164}
# MM9's AISwimFly swimmers (devdocs/mm9_rework/MM9_WATER_SWIMMING_RE.md section 6): the Jellyspore family, Sea Monster
# Male and Female, Fish. Their Fly cell takes "S" ("YS" for the flying spores): on a map with scene water volumes one
# that starts in the water swims in it, bound to it (game/tables/MonsterTable.h MonsterStatsEntry::swims).
SWIMMER_SOURCES = {168, 169, 170, 177, 178, 227}
# Horde rows list Axe and FireAr, but basemelee.scr with AttackRange 60 never throws, and the model has no throw clip.
# The Lobber Pods (84, 85) and the Ice Lobbercicle (105) list projectiles, but lobberpod.scr never sets
# g_bIsRangeAttacker, so its CanRangeAttack is false: they only melee (MM9_AI_NATIVE_RE.md section 7.2.3).
MELEE_ONLY_SOURCES = {84, 85, 105, 129, 130, 131}

# MONSTERS.txt contains duplicate Projectile2 and Att% headings. Keep positional
# ownership explicit so csv.DictReader cannot silently select the wrong column.
SOURCE_COLUMN = {
    "number": 0, "name": 1, "level": 7, "hp": 8, "ac": 9, "experience": 10,
    "treasure_type": 12, "fly": 14, "move": 15, "walk_velocity": 16, "run_velocity": 17,
    "fly_velocity": 18, "recovery": 22,
    "attack1_type": 27, "attack1_damage": 28, "attack1_projectile": 32,
    "attack2_chance": 33, "attack2_type": 34, "attack2_damage": 35, "attack2_dice": 36, "attack2_sides": 37,
    "attack2_bonus": 38, "attack2_projectile": 39,
    "spell1_chance": 40, "spell1": 41, "spell2_chance": 42, "spell2": 43,
    "elemental_resistance": 47, "spirit_resistance": 48, "dark_resistance": 49,
    "light_resistance": 50, "physical_resistance": 51, "script": 52, "is_monster": 61,
    "hostility_group": 63, "treasure_level": 64, "attack3_projectile": 66,
    "attack3_chance": 67, "attack3_type": 68, "attack3_damage": 69, "resurrect": 73,
}
SOURCE_COLUMN_COUNT = 79

PROJECTILE_TOKENS = {
    "": "0", "0": "0",
    "1": "0",  # evil mouse (300): a stray 1 under a second attack with Att% 0
    "Air": "Air", "Axe": "MM9Axe", "BlueLine": "Water",
    "BlueThingy": "Water", "BlueThingy2": "Cold", "DragonBreath2": "Fire",
    "DragonFireBolt": "Fire", "Earth": "Earth", "Egg": "MM9Egg", "Fire": "Fire",
    "FireAr": "FireAr", "FireBolt": "Fire", "Goo1": "Body", "Goo2": "Body",
    "Goo3": "Body", "GreenThingy": "Earth", "GreenYellowThingy": "Body",
    "IceBlast": "Cold", "Knife": "MM9Knife", "Lightning": "Elec",
    "LightningBolt": "Elec", "PurpleThingy": "Dark", "RedThingy": "Fire",
    "RedYellowThingy": "Light", "Redline": "Fire", "RingOfFire": "Fire",
    "Skull": "MM9Skull", "Spell": "0", "Stone": "Rock", "YellowThingy": "Elec",
}

# MM8 wander classes for MM9's Move column. MM9's AI never reads Move (devdocs/mm9_rework/monster_ai/
# MM9_AI_DATA_AND_SCRIPTS.md section 1): an MM9 monster moves as its script and velocities say, and the MM9 loops wander
# by the placement, not by this class. It only sizes the wander of the MM8 idle (allies, charmed actors). Move 0 (every
# named NPC, animal and turret) has no class: one that has a velocity wanders the shortest; Stationary is only a row
# whose velocities are all 0 (movement_type).
MOVEMENT_TYPES = {
    "0": "Short", "2": "Short", "3": "Short", "4": "Med",
    "5": "Med", "6": "Long", "7": "Long", "8": "Free",
}

DIRECT_DAMAGE_TYPES = {
    "": "0", "0": "0", "Dark": "Dark", "Light": "Light",
    "Phys": "Phys", "Spirit": "Spirit",
}

ELEMENTAL_PROJECTILE_DAMAGE_TYPES = {
    "BlueLine": "Water", "BlueThingy": "Water", "BlueThingy2": "Water",
    "DragonBreath2": "Fire", "DragonFireBolt": "Fire", "Fire": "Fire",
    "FireAr": "Fire", "FireBolt": "Fire", "GreenThingy": "Earth",
    "GreenYellowThingy": "Earth", "IceBlast": "Water", "Lightning": "Air",
    "LightningBolt": "Air", "RedThingy": "Fire", "RedYellowThingy": "Fire",
    "Redline": "Fire", "RingOfFire": "Fire", "Stone": "Earth", "YellowThingy": "Air",
}

# MM9 spell id -> the MM6-MM8 spell a monster casts instead (devdocs/mm9_rework/MM9_SPELL_MAPPING.md section 3).
SPELL_NAMES = {
    1: "Bless",
    2: "Lightning Bolt",       # Chain Lightning: same damage, no chain
    4: "Incinerate",           # Column-of-Fire
    5: "Dark Grasp",           # Curse: the Dark debuff projectile, leaving Cursed (MM9_SPELL_CONDITIONS)
    6: "Dark Grasp",           # leaving Weak
    7: "Spirit Lash",          # Death's Touch: single target (Lifedrain is not a monster spell yet)
    8: "Toxic Cloud",          # Disease
    12: None,                   # Elemental Bolt: selected from the actor's projectile family or cast effect
    19: "Fear",                # leaving Afraid; no damage
    23: "Heal",
    27: "Stone Skin",          # Natural Armor
    29: "Paralyze",            # leaving Paralyzed; no damage
    31: "Poison Spray",
    39: "Dragon Breath",       # Souldrinker is not a monster spell yet: the Dark area spell
    40: "Sparks",
    41: "Dispel Magic",        # SpellReaver
    47: "Harm",                # Wound
}

# The condition a monster's cast of the MM9 debuff leaves on a struck party member (the spell_conditions modifier,
# written by generate_mm9_monster_modifiers.py).
SPELL_CONDITIONS = {5: "cursed", 6: "weak", 19: "afraid", 29: "paralyzed"}

# Spells whose SPELL.txt SpellType is defense or healing (Bless, Heal, Natural Armor); the others SPELL_NAMES maps
# are offense. A row whose two spells are both of these never casts (object.lto 0x100b57a9).
NON_OFFENSIVE_SPELLS = frozenset({1, 23, 27})

# Rows whose scripts never call RangeAttack, so MM9 never casts their spells (MM9_AI_NATIVE_RE.md section 7.2.2): the
# Astral Icky (FlyingIcky.scr), the wolves and the Canopic and Embalmed Mummies (BaseCrawl.inc; the placed mummies run
# MummyAwaken.scr, also BaseCrawl), the Dagrells (Dagrell.scr).
NO_RANGE_ATTACK_SOURCES = frozenset({89, 114, 115, 116, 144, 145, 148, 149})

# Elemental Bolt rows whose element MM9 shows by the cast's hand effect rather than a coloured projectile: the Evil
# Apprentice and Evil Sorcerer cast with rAttack1 (EvilSorcerer.abc). This choice read its `DoFX 2 1` as FX1 `redyeldots`;
# DoFX is 0-based (object.lto 0x1001af90), so rAttack1 shows FX2 `greenyeldots` and redyeldots is the melee's (2026-11-10).
ELEMENTAL_BOLT_BY_CAST_FX = {156: "Fire Bolt", 157: "Fire Bolt"}

# A monster spell's damage in OpenYAMM (rollMonsterSpellDamage): DamageBase + skill x 1..DamageDiceSides from
# spells.txt, so its average is base + per_point x skill (Spirit Lash adds the skill once more).
MONSTER_SPELL_AVERAGE = {
    "Fire Bolt": (0.0, 2.0), "Lightning Bolt": (0.0, 4.5), "Ice Bolt": (0.0, 2.5), "Rock Blast": (10.0, 5.5),
    "Incinerate": (15.0, 8.0), "Poison Spray": (2.0, 1.5), "Harm": (8.0, 1.5), "Sparks": (2.0, 1.0),
    "Dragon Breath": (0.0, 13.0), "Toxic Cloud": (25.0, 5.5), "Spirit Lash": (10.0, 5.0),
}

MASTERY_INDEX = {"N": 0, "E": 1, "M": 2, "G": 3}

# A monster's Sparks fires 3/5/7/9 sparks at Normal/Expert/Master/Grandmaster (MM6-MM8, monsterSpellProjectileCount);
# MM9's volley is 5/7/9/12. The mastery whose count is nearest MM9's.
SPARKS_MASTERY = {"N": "E", "E": "M", "M": "G", "G": "G"}


def mm9_spell_average(spell_id: int, mastery: str, skill: int) -> float | None:
    """The average damage of one MM9 cast (SPELL.txt), None for spells without damage and for Sparks (each spark is
    2 + 1 per point in both games: the skill stays, the mastery sets the count, SPARKS_MASTERY)."""
    index = MASTERY_INDEX[mastery]
    if spell_id == 2:                                   # Chain Lightning: s x 1-8
        return skill * 4.5
    if spell_id == 4:                                   # Column-of-Fire: 30 + s x 1-6
        return 30 + skill * 3.5
    if spell_id == 7:                                   # Death's Touch: 7 + s x 1-7
        return 7 + skill * 4.0
    if spell_id in (12, 31):                            # Elemental Bolt, Poison: s x 1-4/6/8/10
        return skill * (1 + (4, 6, 8, 10)[index]) / 2
    if spell_id == 39:                                  # Souldrinker: 25 + s x 1-8
        return 25 + skill * 4.5
    if spell_id == 47:                                  # Wound: 10 + s x 2-6/8/10 (Expert up)
        return 10 + skill * (2 + (6, 6, 8, 10)[index]) / 2
    return None


def mapped_skill(spell_id: int, mastery: str, skill: int, spell_name: str) -> int:
    """The skill that gives one cast of the mapped spell MM9's average damage (MM9_SPELL_MAPPING.md section 3.1).
    Debuffs, buffs, heals, dispels and Sparks keep MM9's
    skill; Natural Armor's AC (+s at Master, +2s at Grandmaster) becomes Stone Skin's skill + 5; Disease's damage over
    time becomes Toxic Cloud at skill 1 (its base 25 alone), at Grandmaster (Njam) the skill as it is."""
    if spell_id == 27:
        return max(1, (2 * skill if mastery == "G" else skill) - 5)
    if spell_id == 8:
        return skill if mastery == "G" else 1
    average = mm9_spell_average(spell_id, mastery, skill)
    if average is None:
        return skill
    base, per_point = MONSTER_SPELL_AVERAGE[spell_name]
    return max(1, int((average - base) / per_point + 0.5))


# The monster table writes Grandmaster as G (parseSkillMasteryToken; "GM" would read as no mastery).
MASTERY_NAMES = {"N": "N", "E": "E", "M": "M", "G": "G"}


def numeric_rows(path: Path) -> tuple[list[list[str]], dict[int, list[str]]]:
    with path.open(newline="", encoding="utf-8") as input_file:
        rows = list(csv.reader(input_file, delimiter="\t"))
    return rows, {
        int(row[0]): row for row in rows if row and re.fullmatch(r"\d+", row[0].strip())
    }


def source_monsters(path: Path, npc_numbers: frozenset[int] = frozenset()) -> dict[int, list[str]]:
    """IsMonster rows, plus the listed NPC rows (IsMonster 0) that are placed as actors."""
    with path.open(newline="", encoding="cp1252") as input_file:
        rows = list(csv.reader(input_file, delimiter="\t"))
    if not rows or len(rows[0]) != SOURCE_COLUMN_COUNT:
        raise ValueError(f"Unexpected MM9 MONSTERS.txt schema in {path}")

    monsters: dict[int, list[str]] = {}
    for row in rows[1:]:
        if len(row) != SOURCE_COLUMN_COUNT or not row[SOURCE_COLUMN["number"]].strip().isdigit():
            continue
        number = int(row[SOURCE_COLUMN["number"]])
        if row[SOURCE_COLUMN["is_monster"]].strip() != "1" and number not in npc_numbers:
            continue
        monsters[number] = [cell.strip() for cell in row]
    return monsters


def npc_actor_ids(path: Path | None) -> dict[int, int]:
    """NPC rows (IsMonster 0) placed as actors with their own 3D model: source number -> legacy visual actor."""
    if path is None:
        return {}
    with path.open(newline="", encoding="utf-8") as input_file:
        return {
            int(row["mm9_source_number"]): int(row["legacy_actor_id"])
            for row in csv.DictReader(input_file, delimiter="\t")
        }


def replacement_ids(path: Path) -> dict[int, int]:
    with path.open(newline="", encoding="utf-8") as input_file:
        return {
            int(row["mm9_source_number"]): int(row["legacy_actor_id"])
            for row in csv.DictReader(input_file, delimiter="\t")
        }


def internal_name(source_number: int, display_name: str) -> str:
    return f"MM9 {source_number} {display_name}"


@dataclass(frozen=True)
class MonsterFamily:
    family_id: str
    name: str
    tiers: tuple[int, ...]

    @property
    def picture_base(self) -> str:
        return f"MM9 {self.name}"


@dataclass(frozen=True)
class MonsterFamilies:
    families: tuple[MonsterFamily, ...]
    mapstats_aliases: dict[str, int]

    def family_of(self, source_number: int) -> MonsterFamily | None:
        for family in self.families:
            if source_number in family.tiers:
                return family
        return None


def load_families(path: Path, sources: dict[int, list[str]]) -> MonsterFamilies:
    with path.open(encoding="utf-8") as input_file:
        document = yaml.safe_load(input_file)

    families: list[MonsterFamily] = []
    family_ids: set[str] = set()
    family_names: set[str] = set()
    owner_by_source: dict[int, str] = {}
    for entry in document["families"]:
        family = MonsterFamily(str(entry["id"]), str(entry["name"]), tuple(int(n) for n in entry["tiers"]))
        if family.family_id in family_ids or family.name.lower() in family_names:
            raise ValueError(f"Duplicate MM9 monster family {family.family_id!r} / {family.name!r}")
        if not 2 <= len(family.tiers) <= len(FAMILY_TIER_LETTERS):
            raise ValueError(f"MM9 monster family {family.family_id!r} needs two or three tiers")
        for source_number in family.tiers:
            if source_number not in sources:
                raise ValueError(
                    f"MM9 monster family {family.family_id!r} names {source_number}, which is not an IsMonster row"
                )
            if source_number in owner_by_source:
                raise ValueError(
                    f"MM9 monster {source_number} is in families {owner_by_source[source_number]!r} "
                    f"and {family.family_id!r}"
                )
            owner_by_source[source_number] = family.family_id
        family_ids.add(family.family_id)
        family_names.add(family.name.lower())
        families.append(family)

    aliases = {str(name): int(number) for name, number in (document.get("mapstats_aliases") or {}).items()}
    for name, source_number in aliases.items():
        if source_number not in sources:
            raise ValueError(f"MM9 MAPSTATS alias {name!r} names {source_number}, which is not an IsMonster row")
    return MonsterFamilies(tuple(families), aliases)


def picture_names(sources: dict[int, list[str]], families: MonsterFamilies) -> dict[int, str]:
    """Family rows get "MM9 <family> A|B|C"; every other row keeps its unique "MM9 <n> <name>"."""
    pictures = {
        source_number: internal_name(source_number, source_value(row, "name"))
        for source_number, row in sources.items()
    }
    for family in families.families:
        for letter, source_number in zip(FAMILY_TIER_LETTERS, family.tiers):
            pictures[source_number] = f"{family.picture_base} {letter}"

    seen: dict[str, int] = {}
    for source_number, picture in sorted(pictures.items()):
        if picture.lower() in seen:
            raise ValueError(f"MM9 monsters {seen[picture.lower()]} and {source_number} share picture {picture!r}")
        seen[picture.lower()] = source_number
    return pictures


def normalized_monster_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def mapstats_family(
    name: str, sources: dict[int, list[str]], families: MonsterFamilies
) -> MonsterFamily | None:
    """Resolve a MAPSTATS.txt monster name to its family; None when the named row has no family."""
    key = normalized_monster_name(name)
    for alias, source_number in families.mapstats_aliases.items():
        if normalized_monster_name(alias) == key:
            return families.family_of(source_number)

    for source_number in sorted(sources):
        if normalized_monster_name(source_value(sources[source_number], "name")) == key:
            return families.family_of(source_number)

    for family in families.families:
        if normalized_monster_name(family.name) == key:
            return family

    raise ValueError(f"MM9 MAPSTATS monster {name!r} matches no MONSTERS.txt row or family")


def source_value(row: list[str], name: str) -> str:
    return row[SOURCE_COLUMN[name]]


def required_mapping(mapping: dict[str, str], value: str, field: str, source_number: int) -> str:
    if value not in mapping:
        raise ValueError(f"MM9 monster {source_number} has unsupported {field} token {value!r}")
    return mapping[value]


def projectile_token(value: str, source_number: int) -> str:
    return required_mapping(PROJECTILE_TOKENS, value, "projectile", source_number)


def elemental_damage_type(row: list[str], projectile: str) -> str:
    if projectile in ELEMENTAL_PROJECTILE_DAMAGE_TYPES:
        return ELEMENTAL_PROJECTILE_DAMAGE_TYPES[projectile]

    attack1_projectile = source_value(row, "attack1_projectile")
    if attack1_projectile in ELEMENTAL_PROJECTILE_DAMAGE_TYPES:
        return ELEMENTAL_PROJECTILE_DAMAGE_TYPES[attack1_projectile]

    # MM9's combined elemental family has no classic equivalent. Air is the
    # least theme-specific fallback for source spell/melee rows.
    return "Air"


def damage_type(row: list[str], type_token: str, projectile: str, source_number: int) -> str:
    if type_token == "Elem":
        return elemental_damage_type(row, projectile)
    return required_mapping(DIRECT_DAMAGE_TYPES, type_token, "damage type", source_number)


# MM9 farm and house animals: MONSTERS.txt Hostility 2 with is_monster 0, scripted wanderers that flee when hit
# (cow.scr, goat.scr, hen.scr, rooster.scr, pig.scr, basecrawl.scr, duck.scr, cat.scr, dog.scr). They roam like the
# MM6-MM8 villagers: wander (Med), AI Wimp, table Hst 0 so the placed actors export friendly (no aggressor bit,
# hostility_type 0). The evil mouse (300) shares the group but is hostile by design; Ratatosk (259) and The Great
# Honk (262) are Hostility 1 scripted bosses; the Fish (227) stays put until swimming exists.
HARMLESS_ANIMAL_SOURCES = frozenset({267, 268, 269, 270, 271, 272, 273, 293, 294, 295, 297, 299})


def is_harmless_animal(source_number: int, row: list[str]) -> bool:
    return (
        source_number in HARMLESS_ANIMAL_SOURCES
        and source_value(row, "is_monster") == "0"
        and source_value(row, "hostility_group") == "2"
    )


def movement_type(row: list[str], source_number: int) -> str:
    # Only a monster that cannot move is Stationary (the Lobbers, the Magic Mine): Move 0 with a velocity (the Magreebs,
    # Forad Darre, Njam, Ebora) moves in MM9.
    if max(source_movement_velocities(row)) == 0:
        return "Stationary"
    if is_harmless_animal(source_number, row):
        return "Med"
    return required_mapping(MOVEMENT_TYPES, source_value(row, "move"), "movement", source_number)


def ai_type(row: list[str], source_number: int) -> str:
    if is_harmless_animal(source_number, row):
        return "Wimp"
    if max(source_movement_velocities(row)) == 0:
        return "Normal"

    script = source_value(row, "script").lower()
    if script in {
        "basemelee.scr", "dagrell.scr", "dragon.scr", "greaterdemon.scr",
        "lesserdemon.scr", "titan.scr", "yanmirbase.scr",
    }:
        return "Suicidal"
    if script in {"guardbase.scr", "monkbase.scr"}:
        return "Normal"
    return "Aggress"


def fly_cell(row: list[str], source_number: int) -> str:
    flies = source_value(row, "fly") == "1" or source_number in SCRIPT_FLYING_SOURCES
    if source_number in SWIMMER_SOURCES:
        return "YS" if flies else "S"
    return "Y" if flies else "N"


def movement_speed(row: list[str]) -> str:
    # The table speed is the monster's walking speed; the shared AI doubles it while pursuing or fleeing (MM8). Half of
    # MM9's fastest velocity (its RunVel, or FlyVel for flyers) makes the pursuit run at MM9's speed; the walk is then
    # half the run (MM9 walks at about a third of it).
    source_speed = max(source_movement_velocities(row))
    return str(min(1000, round(source_speed * MM9_TO_OPENYAMM_COORDINATE_SCALE * 0.5)))


def source_movement_velocities(row: list[str]) -> tuple[int, int, int]:
    return (
        int(source_value(row, "walk_velocity") or "0"),
        int(source_value(row, "run_velocity") or "0"),
        int(source_value(row, "fly_velocity") or "0"),
    )


def recovery_ticks(row: list[str]) -> str:
    # MONSTERS.txt Recovery counts MM9 game seconds, and MM9's game clock advances one second every 33 ms of real time
    # (object.lto 0x10055c10; devdocs/mm9_rework/monster_ai/MM9_AI_NATIVE_RE.md section 7.2.1): 30 is 0.99 s. The
    # scripts' RecoveryTime stat reads it x 0.1 (3.0 s), 3 times the real length. Rows that never attack may leave it
    # empty (mouse, evil mouse).
    seconds = float(source_value(row, "recovery") or "0") * MM9_GAME_SECOND_SECONDS
    ticks = seconds * OPENYAMM_TICKS_PER_SECOND / OPENYAMM_MONSTER_RECOVERY_SCALE
    return str(round(ticks))


def treasure_definition(row: list[str], source_number: int) -> str:
    treasure_type = source_value(row, "treasure_type").lower()
    level = int(source_value(row, "treasure_level") or "0")
    if treasure_type in {"", "0", "none"} or level <= 0:
        return "0"

    kind = {"armor": "Armor", "item": "", "random": "", "weapon": "Weapon"}.get(treasure_type)
    if kind is None:
        raise ValueError(f"MM9 monster {source_number} has unsupported treasure type {treasure_type!r}")

    # MM9 stores no per-actor drop chance. Preserve level/category with a
    # conservative world-specific chance rather than guaranteeing an item.
    return f"25%L{level}{kind}"


def resistance(value: str) -> str:
    numeric = int(value or "0")
    return "Imm" if numeric >= 1000 else str(numeric)


def elemental_bolt_spell(row: list[str], source_number: int) -> str:
    if source_number in ELEMENTAL_BOLT_BY_CAST_FX:
        return ELEMENTAL_BOLT_BY_CAST_FX[source_number]
    # The row's coloured projectile gives the element; without one (Spell) Lightning Bolt.
    damage_family = elemental_damage_type(row, source_value(row, "attack1_projectile"))
    return {
        "Fire": "Fire Bolt", "Air": "Lightning Bolt",
        "Water": "Ice Bolt", "Earth": "Rock Blast",
    }[damage_family]


def parse_source_spell(descriptor: str, row: list[str], source_number: int) -> tuple[str, int, int] | None:
    """(the mapped `Spell,Mastery,Skill` cell, the MM9 spell id, MM9's own skill), None for an empty cell."""
    if descriptor in {"", "0"}:
        return None

    match = re.match(r"^\s*(\d+)\s*,\s*([NEMG])\s*,\s*(\d+)", descriptor, re.IGNORECASE)
    if match is None:
        raise ValueError(f"MM9 monster {source_number} has unsupported spell descriptor {descriptor!r}")

    spell_id = int(match.group(1))
    mastery_token = match.group(2).upper()
    skill = int(match.group(3))
    if spell_id not in SPELL_NAMES or mastery_token not in MASTERY_NAMES:
        raise ValueError(f"MM9 monster {source_number} has unsupported spell {descriptor!r}")

    spell_name = SPELL_NAMES[spell_id]
    if spell_id == 12:
        spell_name = elemental_bolt_spell(row, source_number)
    assert spell_name is not None
    mapped = mapped_skill(spell_id, mastery_token, skill, spell_name)
    mastery = SPARKS_MASTERY[mastery_token] if spell_id == 40 else MASTERY_NAMES[mastery_token]
    return f"{spell_name},{mastery},{mapped}", spell_id, skill


def numeric_chance(value: str, source_number: int, field: str) -> int:
    # The word "concat" parses as 0 in MM9 (atoi); an empty cell (the Ewe, row 272) means no spell
    if value.lower() == "concat" or value == "":
        return 0
    if not value.isdigit():
        raise ValueError(f"MM9 monster {source_number} has unsupported {field} chance {value!r}")
    return int(value)


def has_attack2_damage(row: list[str]) -> bool:
    """MM9's attack 2 exists when its dice x sides + bonus is above 0 (object.lto 0x10053f00)."""
    dice, sides, bonus = (int(source_value(row, name) or "0") for name in ("attack2_dice", "attack2_sides",
                                                                          "attack2_bonus"))
    return dice * sides + bonus > 0


def total_spell_chance(row: list[str], spell1: tuple[str, int, int] | None,
                       spell2: tuple[str, int, int] | None) -> int:
    """MM9's chance in percent that a RangeAttack casts rather than shoots (object.lto 0x100b5690): 100 - Att% when the
    row has attack 2, else 100; none when it has no spell, or two spells that are both defense or healing."""
    if spell1 is None and spell2 is None:
        return 0
    if spell1 is not None and spell2 is not None and {spell1[1], spell2[1]} <= NON_OFFENSIVE_SPELLS:
        return 0
    if not has_attack2_damage(row):
        return 100
    return 100 - min(100, max(0, int(source_value(row, "attack2_chance") or "0")))


def sequential_spell_chances(total: int, spell1_share: int, has_spell1: bool, has_spell2: bool) -> tuple[int, int]:
    """The table's spell 1 and spell 2 chances for MM9's two rolls. MM9 casts by `total` and picks spell 1 by
    `spell1_share` (SpellUse%1) when it has both; a lone spell takes the whole total (ChooseSpell, 0x10053210). The engine
    rolls spell 1 by its chance, then spell 2 by its own: spell1 = T x S1, spell2 = T x (1 - S1) / (1 - T x S1)."""
    if not has_spell1:
        return 0, total if has_spell2 else 0
    if not has_spell2:
        return total, 0
    spell1 = int(total * spell1_share / 100 + 0.5)
    if spell1 >= 100:
        return spell1, 0
    return spell1, int(100 * (total - spell1) / (100 - spell1) + 0.5)


def cast_spells(
    row: list[str], source_number: int
) -> tuple[int, tuple[str, int, int] | None, int, tuple[str, int, int] | None]:
    """(chance, spell) of the row's two casting slots, as MM9 casts them (MM9_AI_NATIVE_RE.md section 7.2.2): none for a
    row whose scripts never call RangeAttack, and a slot whose chance comes out 0 is left empty. SpellUse%2 is not read,
    and a `concat` row's spell is an ordinary spell with SpellUse%1 0."""
    if source_number in NO_RANGE_ATTACK_SOURCES:
        return 0, None, 0, None
    spell1 = parse_source_spell(source_value(row, "spell1"), row, source_number)
    spell2 = parse_source_spell(source_value(row, "spell2"), row, source_number)
    spell1_share = min(100, numeric_chance(source_value(row, "spell1_chance"), source_number, "spell 1"))
    spell1_chance, spell2_chance = sequential_spell_chances(
        total_spell_chance(row, spell1, spell2), spell1_share, spell1 is not None, spell2 is not None)
    return (spell1_chance, spell1 if spell1_chance > 0 else None,
            spell2_chance, spell2 if spell2_chance > 0 else None)


def spell_conditions(row: list[str], source_number: int) -> dict[str, str]:
    """The spell_conditions modifier's slots: the condition each cast MM9 debuff leaves ({"spell1": "afraid"})."""
    _, spell1, _, spell2 = cast_spells(row, source_number)
    return {
        slot: SPELL_CONDITIONS[spell[1]]
        for slot, spell in (("spell1", spell1), ("spell2", spell2))
        if spell is not None and spell[1] in SPELL_CONDITIONS
    }


def spell_columns(row: list[str], source_number: int) -> tuple[str, str, str, str]:
    spell1_chance, spell1, spell2_chance, spell2 = cast_spells(row, source_number)
    return (
        str(spell1_chance),
        spell1[0] if spell1 is not None else "0",
        str(spell2_chance),
        spell2[0] if spell2 is not None else "0",
    )


def build_data_row(
    source_number: int, row: list[str], base_data: list[str], picture: str | None = None
) -> list[str]:
    display_name = source_value(row, "name")
    if picture is None:
        picture = internal_name(source_number, display_name)
    attack1_projectile = source_value(row, "attack1_projectile")
    attack2_projectile = source_value(row, "attack2_projectile")
    attack2_type = source_value(row, "attack2_type")
    attack2_damage = source_value(row, "attack2_damage")
    if source_value(row, "attack3_projectile") not in {"", "0"}:
        attack2_projectile = source_value(row, "attack3_projectile")
        attack2_type = source_value(row, "attack3_type")
        attack2_damage = source_value(row, "attack3_damage")
    if source_number in MELEE_ONLY_SOURCES:
        attack1_projectile = attack2_projectile = "0"
    spell1_chance, spell1, spell2_chance, spell2 = spell_columns(row, source_number)
    elemental_resistance = resistance(source_value(row, "elemental_resistance"))
    spirit_resistance = resistance(source_value(row, "spirit_resistance"))

    return [
        str(MM9_MONSTER_ID_BASE + source_number), display_name, picture,
        source_value(row, "level"), source_value(row, "hp"), source_value(row, "ac"),
        source_value(row, "experience"), treasure_definition(row, source_number), base_data[8],
        fly_cell(row, source_number),
        movement_type(row, source_number),
        ai_type(row, source_number), "0" if is_harmless_animal(source_number, row) else "4",
        # No on-hit special attack: MM9 loads the Bonus column and never reads it, ConcatAttk is never read, and no
        # spell rides on a hit (MM9_AI_NATIVE_RE.md section 7.2.2). A blow is always physical.
        movement_speed(row), recovery_ticks(row), "0", "0",
        damage_type(row, source_value(row, "attack1_type"), attack1_projectile, source_number),
        source_value(row, "attack1_damage"), projectile_token(attack1_projectile, source_number),
        source_value(row, "attack2_chance"),
        damage_type(row, attack2_type, attack2_projectile, source_number),
        attack2_damage, projectile_token(attack2_projectile, source_number),
        spell1_chance, spell1, spell2_chance, spell2,
        elemental_resistance, elemental_resistance, elemental_resistance, elemental_resistance,
        spirit_resistance, spirit_resistance, spirit_resistance,
        resistance(source_value(row, "light_resistance")),
        resistance(source_value(row, "dark_resistance")),
        resistance(source_value(row, "physical_resistance")), "0",
    ]


# MM9's own monster bodies (mm9_monster_bodies.py, devdocs/mm9_rework/MM9_MONSTER_COLLISION_RE.md): the listed rows'
# Height, Radius and ToHitRadius replace the values copied from the legacy descriptor row.
BODY_OVERRIDE_COLUMNS = {"Height": 2, "Radius": 3, "ToHitRadius": 5}


def read_body_overrides(path: Path) -> dict[int, dict[int, str]]:
    """Descriptor row id -> {descriptor column: value} from mm9_monster_body_overrides.tsv (empty cells keep)."""
    with path.open(newline="", encoding="utf-8") as input_file:
        lines = [line for line in input_file if not line.startswith("#")]
    overrides = {}
    for row in csv.DictReader(lines, delimiter="\t"):
        values = {column: row[name].strip() for name, column in BODY_OVERRIDE_COLUMNS.items() if row[name].strip()}
        for value in values.values():
            if not value.isdigit():
                raise ValueError(f"MM9 body override {row['row']} has a non-numeric value {value!r}")
        overrides[int(row["row"])] = values
    return overrides


def apply_body_overrides(descriptor_rows: list[list[str]], overrides: dict[int, dict[int, str]]) -> None:
    by_id = {int(row[0]): row for row in descriptor_rows if row and re.fullmatch(r"\d+", row[0].strip())}
    unknown = sorted(set(overrides) - set(by_id))
    if unknown:
        raise ValueError(f"MM9 body overrides name rows the generator does not write: {unknown}")
    for row_id, values in overrides.items():
        for column, value in values.items():
            by_id[row_id][column] = value


# MM9's own sounds (generate_mm9_monster_sounds.py, devdocs/mm9_rework/MM9_MONSTER_SOUNDS.md): AttackSoundId,
# DeathSoundId, WinceSoundId and AwareSoundId of every MM9 row, ids of the world's sounds table (0: MM9 has none there),
# in place of the legacy descriptor's MM6-MM8 sounds.
SOUND_SLOT_COLUMNS = {"attack_sound_id": 7, "death_sound_id": 8, "wince_sound_id": 9, "fidget_sound_id": 10}


def read_sound_slots(path: Path) -> dict[int, dict[int, str]]:
    """MM9 source number -> {descriptor column: sound id} from mm9_monster_sound_slots.tsv."""
    with path.open(newline="", encoding="utf-8") as input_file:
        slots = {}
        for row in csv.DictReader(input_file, delimiter="\t"):
            values = {column: row[name].strip() for name, column in SOUND_SLOT_COLUMNS.items()}
            if not all(value.isdigit() for value in values.values()):
                raise ValueError(f"MM9 sound slots for {row['mm9_source_number']} are not numeric: {values}")
            slots[int(row["mm9_source_number"])] = values
    return slots


def apply_sound_slots(descriptor_rows: list[list[str]], slots: dict[int, dict[int, str]],
                      source_numbers: list[int]) -> None:
    missing = sorted(set(source_numbers) - set(slots))
    unknown = sorted(set(slots) - set(source_numbers))
    if missing or unknown:
        raise ValueError(f"MM9 sound slots do not cover the generated rows: missing={missing}, unknown={unknown}")
    by_id = {int(row[0]): row for row in descriptor_rows if row and re.fullmatch(r"\d+", row[0].strip())}
    for source_number, values in slots.items():
        for column, value in values.items():
            by_id[MM9_MONSTER_ID_BASE + source_number][column] = value


def write_rows(path: Path, rows: list[list[str]]) -> None:
    # Replace the file instead of rewriting it in place: hard-linked staging copies of the world keep their version.
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", newline="", encoding="utf-8") as output_file:
            csv.writer(output_file, delimiter="\t", lineterminator="\n").writerows(rows)
        os.chmod(temporary_name, 0o664)
        os.replace(temporary_name, path)
    except BaseException:
        os.unlink(temporary_name)
        raise


def write_audit(path: Path, sources: dict[int, list[str]], replacements: dict[int, int]) -> None:
    rows = [[
        "mm9_source_number", "runtime_id", "name", "legacy_visual_id", "source_projectile1",
        "mapped_projectile1", "source_spell1", "mapped_spell1", "source_spell2", "mapped_spell2",
        "source_elemental_resistance", "source_spirit_resistance", "source_recovery",
        "mapped_recovery_ticks", "source_resurrect", "source_attack3",
    ]]
    for source_number, legacy_actor_id in sorted(replacements.items()):
        row = sources[source_number]
        _, spell1, _, spell2 = spell_columns(row, source_number)
        rows.append([
            str(source_number), str(MM9_MONSTER_ID_BASE + source_number), source_value(row, "name"),
            str(legacy_actor_id), source_value(row, "attack1_projectile"),
            projectile_token(source_value(row, "attack1_projectile"), source_number),
            source_value(row, "spell1"), spell1, source_value(row, "spell2"), spell2,
            source_value(row, "elemental_resistance"), source_value(row, "spirit_resistance"),
            source_value(row, "recovery"), recovery_ticks(row), source_value(row, "resurrect"),
            source_value(row, "attack3_projectile") or source_value(row, "attack3_damage"),
        ])
    write_rows(path, rows)


def generate_tables(
    source_monsters_path: Path,
    replacements_path: Path,
    families_path: Path,
    base_monster_data_path: Path,
    base_descriptors_path: Path,
    output_dir: Path,
    npc_actors_path: Path | None = None,
    body_overrides_path: Path | None = None,
    sound_slots_path: Path | None = None,
) -> tuple[int, int]:
    npc_actors = npc_actor_ids(npc_actors_path)
    sources = source_monsters(source_monsters_path, frozenset(npc_actors))
    replacements = replacement_ids(replacements_path)
    overlap = sorted(set(npc_actors) & set(replacements))
    if overlap:
        raise ValueError(f"MM9 NPC actor rows are also monster replacement rows: {overlap}")
    replacements.update(npc_actors)
    pictures = picture_names(sources, load_families(families_path, sources))
    data_rows, data_by_id = numeric_rows(base_monster_data_path)
    descriptor_rows, descriptors_by_id = numeric_rows(base_descriptors_path)

    generated_data = [row for row in data_rows if not row or not re.fullmatch(r"\d+", row[0].strip())]
    generated_descriptors = [
        row for row in descriptor_rows if not row or not re.fullmatch(r"\d+", row[0].strip())
    ]

    missing_sources = sorted(set(replacements) - set(sources))
    unclassified_sources = sorted(set(sources) - set(replacements))
    if missing_sources or unclassified_sources:
        raise ValueError(
            f"MM9 monster replacement coverage mismatch: missing={missing_sources}, "
            f"unclassified={unclassified_sources}"
        )

    for source_number, legacy_actor_id in sorted(replacements.items()):
        source_row = sources[source_number]
        base_data = data_by_id.get(legacy_actor_id)
        base_descriptor = descriptors_by_id.get(legacy_actor_id)
        if base_data is None or base_descriptor is None:
            raise ValueError(
                f"Cannot generate MM9 monster {source_number}: missing legacy visual actor "
                f"{legacy_actor_id} tables"
            )

        generated_data.append(build_data_row(source_number, source_row, base_data, pictures[source_number]))

        descriptor_row = list(base_descriptor)
        descriptor_row[0] = str(MM9_MONSTER_ID_BASE + source_number)
        descriptor_row[1] = pictures[source_number]
        generated_descriptors.append(descriptor_row)

    # MM9's rows on our rules (mm9_monster_balance.py, devdocs/mm9_rework/BALANCE_PLAN.md sections 3.2-3.3).
    balance_monster_rows(generated_data, data_rows)

    if body_overrides_path is not None:
        apply_body_overrides(generated_descriptors, read_body_overrides(body_overrides_path))
    if sound_slots_path is not None:
        apply_sound_slots(generated_descriptors, read_sound_slots(sound_slots_path), sorted(replacements))

    write_rows(output_dir / "monster_data.txt", generated_data)
    write_rows(output_dir / "monster_descriptors.txt", generated_descriptors)
    write_audit(output_dir / "monster_conversion_audit.tsv", sources, replacements)
    return len(generated_data), len(replacements)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-monsters", type=Path, default=Path("mm9/extracted/DATA/DATA/MONSTERS.txt"))
    parser.add_argument(
        "--replacements", type=Path,
        default=Path("tools/mm9_import_discovery/mm9_monster_legacy_replacements.tsv"),
    )
    parser.add_argument(
        "--families", type=Path, default=Path("tools/mm9_import_discovery/mm9_monster_families.yml"),
    )
    parser.add_argument(
        "--npc-actors", type=Path, default=Path("tools/mm9_import_discovery/mm9_npc_actor_rows.tsv"),
    )
    parser.add_argument(
        "--body-overrides", type=Path,
        default=Path("tools/mm9_import_discovery/mm9_monster_body_overrides.tsv"),
    )
    parser.add_argument(
        "--sound-slots", type=Path, default=Path("tools/mm9_import_discovery/mm9_monster_sound_slots.tsv"),
    )
    parser.add_argument(
        "--base-monster-data", type=Path,
        default=Path("assets_dev/engine/data_tables/monster_data.txt"),
    )
    parser.add_argument(
        "--base-descriptors", type=Path,
        default=Path("assets_dev/engine/data_tables/monster_descriptors.txt"),
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("assets_dev/worlds/mm9/data_tables"),
    )
    args = parser.parse_args()

    _, monster_count = generate_tables(
        args.source_monsters, args.replacements, args.families, args.base_monster_data,
        args.base_descriptors, args.output_dir, args.npc_actors, args.body_overrides, args.sound_slots,
    )
    print(f"Generated {monster_count} MM9 monster rows in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
