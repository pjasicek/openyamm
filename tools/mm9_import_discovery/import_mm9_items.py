#!/usr/bin/env python3
"""Generate the world-owned MM9 item contribution and its audit artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from mm9_item_balance import EngineReference, balance_effect, balance_rows, random_item_rows, round_price
from mm9_spellbooks import install_icons as install_spellbook_icons, spellbook_item_id, spellbook_rows


GLOBAL_ITEM_ID_BASE = 10000
GLOBAL_ITEM_ID_BEGIN = 10000
GLOBAL_ITEM_ID_END = 10999
CLOVER_RAW_ID = 590
WORLD_ITEM_OBJECT_ID_BASE = 20000
WORLD_ITEM_SPRITE_ID_BASE = 24000
EXCLUDED_CATEGORIES = {"magic", "magic scroll", "magic runestone", "potion", "wand"}
ENGINE_ITEM_MAPPINGS: dict[int, tuple[int, str]] = {
    253: (222, "MM9 Cure Wounds potion mapped to the shared Cure Wounds potion"),
    347: (spellbook_item_id(20), "MM9 Eye of the Storm spellbook mapped to MM9's Implosion spellbook (mm9_spellbooks.py)"),
    511: (317, "MM9 Chain Lightning scroll mapped to the shared Lightning Bolt scroll"),
    523: (311, "MM9 Eye of Leggib scroll mapped to the shared Wizard Eye scroll"),
    532: (306, "MM9 Magic Mine scroll mapped to the shared Fire Spike scroll"),
    547: (314, "MM9 Sparks scroll mapped to the shared Sparks scroll"),
    548: (379, "MM9 Spell Reaver scroll mapped to the shared Dispel Magic scroll"),
    555: (334, "MM9 Wrath of Bugs scroll mapped to the shared Slow scroll"),
}
ITEM_COLUMN_COUNT = 45
# MM9's icon package is x2 (engine/icon_packages.txt): inventory art goes to icons_x2, world-item sprites stay x1.
ICON_SCALE = 2
ICON_DIRECTORY = "icons_x2"
EQUIPMENT_VISUAL_EQUIP_STATS = {"Weapon", "Weapon2", "Missile", "Shield"}
EQUIPMENT_VISUAL_REVIEW_STATES = {"candidate", "reviewed"}
BODY_EQUIPMENT_COVERAGE_PROFILES = {"short_torso", "hip_length", "thigh_length", "full_harness"}

CONTENT_EFFECT_FIELDS = [
    "might", "intellect", "personality", "endurance", "speed", "accuracy", "luck", "max_health",
    "max_sp", "armor_class", "melee_attack", "ranged_attack", "melee_damage", "ranged_damage",
    "all_resistances", "fire_resistance", "air_resistance", "water_resistance", "earth_resistance",
    "mind_resistance", "body_resistance", "spirit_resistance", "skill_bonuses", "weapon_damage",
    "recovery_reduction_ticks", "health_regen_per_second", "spell_regen_per_second", "effect_flags",
]

ITEM_HEADERS = [
    "Item #", "Pic File", "Name", "Value", "Equip Stat", "Skill Group", "Mod1", "Mod2", "material",
    "ID/Rep/St", "Not identified name", "Sprite Index", "VarA", "VarB", "Equip X", "Equip Y", "Notes",
    "package_id", "canonical_id", "source_item_id", "content_flags", "normalized_tier", "use_action",
    "use_target", "set_id", "effect_profile", "allowed_class_roots", "required_might", "required_accuracy",
    "inventory_width", "inventory_height", "visual_status", "x_mm9_raw_item_id", "x_mm9_canonical_id",
    "x_mm9_source_equip_type", "x_mm9_source_skill", "x_mm9_source_icon_pcx", "x_mm9_source_name_type",
    "x_mm9_source_min", "x_mm9_source_max", "x_mm9_source_field_05", "x_mm9_source_flags",
    "x_mm9_source_restrictions", "x_mm9_import_status", "x_mm9_balance_profile",
]

EQUIP_STAT_BY_CATEGORY = {
    "weapon": "Weapon",
    "weapon2h": "Weapon2",
    "ranged weapon": "Missile",
    "armor": "Armor",
    "shield": "Shield",
    "helm": "Helm",
    "boots": "Boots",
    "gloves": "Gauntlets",
    "belt": "Belt",
    "items ring": "Ring",
    "items amulet": "Amulet",
}

OPENYAMM_VALUE_TARGETS = {
    "Weapon": [35, 100, 200, 350, 500, 850],
    "Weapon2": [200, 250, 425, 575, 900, 1200],
    "Missile": [100, 200, 250, 400, 550, 800],
    "Armor": [300, 350, 500, 875, 1175, 2100],
    "Shield": [175, 225, 325, 450, 625, 750],
    "Helm": [60, 150, 200, 250, 450, 960],
    "Boots": [65, 90, 175, 425, 450, 1000],
    "Gauntlets": [125, 200, 425, 425, 425, 900],
    "Belt": [10, 60, 225, 225, 250, 650],
    "Ring": [225, 225, 925, 950, 1175, 1900],
    "Amulet": [300, 550, 950, 950, 950, 1550],
}

DIRECT_SKILLS = {
    "bow": "Bow",
    "spear": "Spear",
    "shield": "Shield",
    "sheild": "Shield",
    "thrown": "Throwing",
    "armsmaster": "Armsmaster",
    "unarmed": "Unarmed",
    "dodge": "Dodging",
    "disarm trap": "DisarmTraps",
    "merchant": "Merchant",
    "perception": "Perception",
    "repair item": "RepairItem",
    "identify item": "IdentifyItem",
    "id item": "IdentifyItem",
    "identify monster": "IdentifyMonster",
    "id monster": "IdentifyMonster",
    "body building": "Bodybuilding",
    "learning": "Learning",
    "meditation": "Meditation",
    "light": "LightMagic",
    "dark": "DarkMagic",
    "spirit": "SpiritMagic",
}

SKILL_BOOK_TARGETS = {
    **DIRECT_SKILLS,
    "cudgel": "Mace",
    "armor": "LeatherArmor|ChainArmor|PlateArmor",
    "elemental": "FireMagic|AirMagic|WaterMagic|EarthMagic",
    "blade": "Sword|Dagger",
}

SET_BY_RAW_ITEM_ID = {
    **{item_id: "mm9:set/prize" for item_id in range(219, 224)},
    **{item_id: "mm9:set/broderick" for item_id in range(224, 229)},
    **{item_id: "mm9:set/death" for item_id in range(229, 234)},
    **{item_id: "mm9:set/fre" for item_id in range(234, 239)},
}

ALLOWED_CLASS_ROOTS_BY_RAW_ITEM_ID = {
    # MM9 Fighter -> Mercenary -> Gladiator/Assassin maps to the promoted OpenYAMM Knight branch.
    **{item_id: "Cavalier" for item_id in range(219, 224)},
    **{item_id: "Paladin" for item_id in range(224, 229)},
    # Scholar and Lich map most closely to OpenYAMM's Necromancer -> Lich branch, not Sorcerer.
    **{item_id: "Necromancer" for item_id in range(229, 234)},
    **{item_id: "Cleric" for item_id in range(234, 239)},
}

RELIC_RAW_ITEM_IDS = {
    176, 178, 179, 188, 190, 191, 194, 196, 199, 206, 209, 212, 216, 217, 218,
}

# ItemTable's Sprite Index is an ObjectId from the composed object table. Quest and miscellaneous MM9 items receive
# stable MM9-owned descriptors below; ordinary equipment continues to use the closest shared object family.
GROUND_OBJECT_ID_BY_ITEM_FAMILY = {
    "amulet": 33,
    "axe": 7,
    "bag of herbs": 349,
    "baslisk skin": 106,
    "basket of food": 394,
    "belt": 28,
    "black orb of knowledge": 137,
    "boat schedule": 77,
    "book": 78,
    "book key": 80,
    "book of rules": 78,
    "book of spells": 78,
    "bow": 12,
    "boots": 31,
    "broad sword": 3,
    "broken jar": 101,
    "capstone of order": 378,
    "chain armor": 21,
    "clover": 387,
    "cloth gloves": 30,
    "club": 16,
    "crona kiga": 27,
    "crossbow": 13,
    "dagger": 5,
    "dolly": 247,
    "elixir ingredients": 76,
    "elixir of defedation": 76,
    "farmer's plow": 375,
    "flail": 14,
    "fluid": 76,
    "fur cap": 26,
    "fuzzy slippers": 31,
    "gloves": 30,
    "green stone": 137,
    "halberd": 10,
    "hammer": 15,
    "hand cannon": 172,
    "helm": 25,
    "holy relic": 33,
    "holy symbol": 356,
    "invoice": 77,
    "jar": 101,
    "keg of strange brew": 383,
    "key": 80,
    "kira's shield": 23,
    "layered potion": 64,
    "leather armor": 20,
    "letter": 77,
    "light crossbow": 13,
    "lock of hair": 106,
    "long sword": 1,
    "longbow": 12,
    "ludwig's manuscript": 78,
    "machine part": 300,
    "maul": 15,
    "morning star": 14,
    "orb of linking": 137,
    "ore": 131,
    "pamphlet": 77,
    "parchment": 77,
    "plate armor": 22,
    "poem": 77,
    "post": 77,
    "prize": 362,
    "quilted armor": 20,
    "red stone": 137,
    "ring": 32,
    "saint's relic": 110,
    "scimitar": 4,
    "shield": 23,
    "short sword": 1,
    "skill book": 78,
    "skullcap": 25,
    "spear": 9,
    "staff": 17,
    "the golden honk": 353,
    "throwing axe": 7,
    "throwing dagger": 5,
    "ticket": 77,
    "training memo": 77,
    "two-handed sword": 2,
    "weapon": 1,
    "wooden shield": 24,
    "wooden sword": 1,
}


@dataclass(frozen=True)
class SourceItem:
    row_number: int
    cells: tuple[str, ...]
    source_override_id: str = ""
    source_provenance: str = "MASTERITEMLIST.csv"

    @property
    def raw_id(self) -> int:
        return int(self.cells[0])

    @property
    def name(self) -> str:
        return self.cells[1].strip()

    @property
    def category(self) -> str:
        return self.cells[2].strip()

    @property
    def category_key(self) -> str:
        return self.category.casefold()

    @property
    def source_marker(self) -> str:
        return self.cells[3].strip()

    @property
    def subtype(self) -> str:
        return self.cells[7].strip()

    @property
    def description(self) -> str:
        return self.cells[8].strip()

    @property
    def icon_stem(self) -> str:
        return self.cells[9].strip()

    @property
    def source_skill(self) -> str:
        return self.cells[11].strip()

    @property
    def quest_item(self) -> bool:
        return "quest" in self.category_key or self.source_marker.casefold() == "quest item"


def parse_int(value: str, default: int = 0) -> int:
    try:
        return int(float(value.strip()))
    except (TypeError, ValueError):
        return default


def read_source_item_overrides(path: Path) -> list[SourceItem]:
    with path.open("r", encoding="utf-8") as source_file:
        document = yaml.safe_load(source_file) or {}
    if document.get("format_version") != 1 or document.get("kind") != "mm9_item_source_overrides":
        raise ValueError(f"{path}: invalid MM9 item source override document")

    overrides: list[SourceItem] = []
    for override_id, definition in document.get("items", {}).items():
        if not isinstance(definition, dict) or definition.get("review_state") != "reviewed":
            raise ValueError(f"{path}: item override {override_id!r} is not reviewed")
        cells = definition.get("cells")
        if not isinstance(cells, list) or len(cells) != 15 or not all(isinstance(cell, str) for cell in cells):
            raise ValueError(f"{path}: item override {override_id!r} must provide 15 string cells")
        if not definition.get("reason") or not definition.get("source_provenance"):
            raise ValueError(f"{path}: item override {override_id!r} lacks reason or source provenance")
        overrides.append(SourceItem(
            row_number=0,
            cells=tuple(cells),
            source_override_id=str(override_id),
            source_provenance=str(definition["source_provenance"]),
        ))
    return overrides


def read_source_items(path: Path, overrides_path: Path | None = None) -> list[SourceItem]:
    with path.open("r", encoding="cp1252", newline="") as source_file:
        rows = list(csv.reader(source_file))

    items: list[SourceItem] = []
    seen_ids: set[int] = set()
    for row_number, row in enumerate(rows, start=1):
        if len(row) != 15:
            raise ValueError(f"{path}:{row_number}: expected 15 columns, found {len(row)}")
        raw_id = parse_int(row[0], -1)
        if raw_id <= 0:
            raise ValueError(f"{path}:{row_number}: invalid raw item id {row[0]!r}")
        if raw_id in seen_ids:
            raise ValueError(f"{path}:{row_number}: duplicate raw item id {raw_id}")
        if GLOBAL_ITEM_ID_BASE + raw_id > GLOBAL_ITEM_ID_END:
            raise ValueError(f"{path}:{row_number}: raw item id {raw_id} exceeds the declared range")
        seen_ids.add(raw_id)
        items.append(SourceItem(row_number, tuple(row)))

    if overrides_path is not None:
        for item in read_source_item_overrides(overrides_path):
            if item.raw_id in seen_ids:
                raise ValueError(
                    f"{overrides_path}: item override {item.source_override_id!r} duplicates source id {item.raw_id}")
            if item.raw_id <= 0 or GLOBAL_ITEM_ID_BASE + item.raw_id > GLOBAL_ITEM_ID_END:
                raise ValueError(f"{overrides_path}: override raw item id {item.raw_id} is outside the declared range")
            seen_ids.add(item.raw_id)
            items.append(item)

    return sorted(items, key=lambda item: item.raw_id)


def read_readable_texts(path: Path) -> dict[int, tuple[str, str]]:
    with path.open("r", encoding="cp1252", newline="") as source_file:
        rows = list(csv.reader(source_file))

    result: dict[int, tuple[str, str]] = {}
    for row_number, row in enumerate(rows, start=1):
        if len(row) < 3 or any(cell.strip() for cell in row[3:]):
            raise ValueError(f"{path}:{row_number}: expected 3 populated columns, found {len(row)}")
        row = row[:3]
        raw_id = parse_int(row[0], -1)
        if raw_id <= 0 or raw_id in result:
            raise ValueError(f"{path}:{row_number}: invalid or duplicate readable item id {row[0]!r}")
        result[raw_id] = (row[1], row[2])
    return result


def canonical_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return slug or "item"


def canonical_ids(items: list[SourceItem]) -> dict[int, str]:
    slugs = {item.raw_id: canonical_slug(item.name) for item in items}
    counts = Counter(slugs.values())
    return {
        item.raw_id: f"mm9:item/{slugs[item.raw_id]}"
        if counts[slugs[item.raw_id]] == 1
        else f"mm9:item/{slugs[item.raw_id]}_{item.raw_id}"
        for item in items
    }


def classify_item(item: SourceItem) -> tuple[str, str]:
    if item.raw_id == CLOVER_RAW_ID:
        return "imported", "source Potion category corrected to miscellaneous Clover"
    if item.category_key in EXCLUDED_CATEGORIES:
        mapping = ENGINE_ITEM_MAPPINGS.get(item.raw_id)
        if mapping is not None:
            return "mapped", mapping[1]
        return "excluded", f"excluded MM9 {item.category} family"
    return "imported", "supported item definition"


def normalized_skill(item: SourceItem) -> str:
    source_skill = item.source_skill.casefold()
    subtype = item.subtype.casefold()
    if item.category_key in {"helm", "boots", "gloves", "belt", "items ring", "items amulet"}:
        return "Misc"
    if source_skill == "blade":
        if "dagger" in subtype:
            return "Dagger"
        if "axe" in subtype:
            return "Axe"
        return "Sword"
    if source_skill == "cudgel":
        return "Staff" if "staff" in subtype else "Mace"
    if source_skill == "armor":
        if "leather" in subtype or "quilted" in subtype:
            return "Leather"
        if "chain" in subtype:
            return "Chain"
        if "plate" in subtype:
            return "Plate"
    mapped_skill = DIRECT_SKILLS.get(source_skill)
    if mapped_skill is None:
        raise ValueError(
            f"raw item {item.raw_id} has unmapped equippable skill {item.source_skill!r} "
            f"for {item.category!r}/{item.subtype!r}")
    return mapped_skill


def normalized_category(item: SourceItem) -> str:
    if item.raw_id == 197:
        return "weapon2h"
    return item.category_key


def normalized_tier(item: SourceItem) -> int:
    if 175 <= item.raw_id <= 238:
        return 7
    if item.quest_item or item.category_key == "items_skill" or item.category_key == "letter":
        return 0
    quality = parse_int(item.cells[3])
    return 7 if quality >= 6 else max(0, min(6, quality))


def normalized_material(item: SourceItem) -> str:
    if item.raw_id in SET_BY_RAW_ITEM_ID:
        return "Special"
    if item.raw_id in RELIC_RAW_ITEM_IDS:
        return "Relic"
    if 175 <= item.raw_id <= 218:
        return "Artifact"
    category = normalized_category(item)
    subtype = item.subtype.casefold()
    if category in {"weapon", "weapon2h"}:
        return "8"
    if category == "ranged weapon":
        return "8" if "throw" in subtype else "3"
    if category == "armor":
        if "plate" in subtype:
            return "9"
        if "chain" in subtype:
            return "6"
        return "3"
    return {
        "shield": "4", "helm": "6", "boots": "3", "gloves": "6", "belt": "3",
        "items ring": "7", "items amulet": "4",
    }.get(category, "0")


def normalized_modifiers(item: SourceItem) -> tuple[str, str]:
    category = normalized_category(item)
    first = max(0, parse_int(item.cells[4]))
    second = max(0, parse_int(item.cells[5]))
    if category in {"weapon", "weapon2h", "ranged weapon"}:
        return (f"{first}d{second}" if first > 0 and second > 0 else "0", "0")
    if category == "armor":
        subtype = item.subtype.casefold()
        recovery = 18 if "plate" in subtype else 6 if "chain" in subtype else 3
        return str(recovery), str(first)
    if category == "shield":
        subtype = item.subtype.casefold()
        shield_size = 2 if "small" in subtype or "buckler" in subtype else 4
        return str(shield_size), str(first)
    if category in {"helm", "boots", "gloves"}:
        return "1", str(first)
    return "0", str(first if category == "belt" else 0)


def normalized_equip_stat(item: SourceItem, readable_texts: dict[int, tuple[str, str]]) -> str:
    if item.category_key == "items_skill":
        return "LearnSkill"
    if item.raw_id in readable_texts:
        return "Mscroll"
    return EQUIP_STAT_BY_CATEGORY.get(normalized_category(item), "Misc")


def uses_dedicated_world_item_sprite(item: SourceItem) -> bool:
    return item.quest_item or item.category_key == "items"


def normalized_ground_object_id(item: SourceItem) -> int:
    if uses_dedicated_world_item_sprite(item):
        return WORLD_ITEM_OBJECT_ID_BASE + item.raw_id

    object_id = GROUND_OBJECT_ID_BY_ITEM_FAMILY.get(item.subtype.casefold())
    if object_id is None:
        raise ValueError(
            f"raw item {item.raw_id} has unmapped ground-object family "
            f"{item.category!r}/{item.subtype!r}")
    return object_id


def normalized_stat_requirements(item: SourceItem) -> tuple[int, int]:
    required_might = 0
    required_accuracy = 0
    for token in item.cells[14].split(","):
        match = re.fullmatch(r"\s*(\d+)\s+(Might|Strength|Accuracy)\s*", token, flags=re.IGNORECASE)
        if not match:
            continue
        amount = int(match.group(1))
        if match.group(2).casefold() in {"might", "strength"}:
            required_might = max(required_might, amount)
        else:
            required_accuracy = max(required_accuracy, amount)
    return required_might, required_accuracy


def inventory_slots_from_pixels(pixel_size: int) -> int:
    return max(1, 1 + (max(14, pixel_size) - 14) // 32)


def normalized_value(item: SourceItem, equip_stat: str, tier: int) -> tuple[int, str]:
    source_value = max(0, parse_int(item.cells[10]))
    if item.quest_item:
        return 0, "quest_value_zero"
    targets = OPENYAMM_VALUE_TARGETS.get(equip_stat)
    if targets is None or tier < 1 or tier > 6:
        return source_value, "source_value_preserved"
    target = targets[tier - 1]
    minimum = max(1, (target * 3 + 3) // 4)
    maximum = max(minimum, (target * 5) // 4)
    return round_price(max(minimum, min(maximum, source_value))), "openyamm_category_tier_value_envelope"


# Artifacts and relics with a fixed source: hand-placed in a black chest (Black's Heart, Everstrike, Gungnir,
# Spencer's Obedience) or a quest reward (The Green Man, Frosgard). They keep NoRandom; every other artifact and relic
# rolls from the black chests' level-7 slots (BALANCE_PLAN.md section 3.8), which pick only items without NoRandom.
# Every MM9 artifact and relic is World:mm9, so random loot rolls them only in MM9 and MM9 only them.
# mm9_balance_report.py checks this list against the scenes and event scripts.
FIXED_SOURCE_RARE_RAW_IDS = {180, 184, 189, 198, 213}

# Artifacts and relics end their description with an "(Effects: ...)" list. MM9's own lists name MM9's enchantments
# ("+10 to Magic", "of the Jajarb") and miss the balance changes, so the importer writes the list from the item's final
# effect (OY-588). Set pieces keep MM9's list: it also describes the set bonus.
EFFECT_TEXT_RAW_IDS = range(175, 219)
EFFECT_TEXT_STATS = ["might", "intellect", "personality", "endurance", "speed", "accuracy", "luck"]
EFFECT_TEXT_FIELDS = {
    "max_health": "HP", "max_sp": "SP", "armor_class": "AC", "melee_attack": "to hit", "melee_damage": "damage",
    "ranged_attack": "ranged to hit", "ranged_damage": "ranged damage", "all_resistances": "to all resistances",
    "fire_resistance": "Fire resistance", "air_resistance": "Air resistance", "water_resistance": "Water resistance",
    "earth_resistance": "Earth resistance", "mind_resistance": "Mind resistance", "body_resistance": "Body resistance",
    "spirit_resistance": "Spirit resistance",
}
MAGIC_SCHOOLS = ["FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "SpiritMagic", "MindMagic", "BodyMagic",
                 "LightMagic", "DarkMagic"]
ARMOR_SKILLS = ["LeatherArmor", "ChainArmor", "PlateArmor"]
EFFECT_FLAG_TEXT = {
    "BreakAfterFirstAttack": "breaks after its first attack",
    "PoisonOnHit40Grandmaster": "40% chance to poison the target at Grandmaster",
    "PerfectAccuracy": "always hits",
    "TripleProjectile": "three projectiles per throw",
    "HalveTargetArmor": "halves the target's AC",
    "BreakChance2SelfDamage": "2% chance per shot to break and hurt the wielder",
    "BypassArmorChance20": "20% chance to ignore the target's AC",
    "Vampiric": "Vampiric",
    "WeeklyInsanityChance10": "10% chance of insanity each week",
    "WeeklyHealthLossChance10": "10% chance each week to lose a tenth of HP",
    "EnrageOnHit5Grandmaster": "5% chance to enrage the target at Grandmaster",
    "StunOnHit5": "5% chance to stun the target",
    "SelfKnockoutOnFailedStun70": "70% chance to knock the wielder unconscious when a hit does not stun",
    "KillOnHit10": "10% chance to kill the target outright",
    "ReelOnHit": "stuns the target on every hit",
    "DisableDivineIntervention": "Divine Intervention always fails",
    "FearOnHit10": "10% chance to frighten the target on a hit",
    "MeleeArmor40": "+40 AC against melee attacks",
    "RangedArmorMinus10": "-10 AC against missiles",
    "MagicArmor20": "+20 AC against magic",
    "MissileArmor30": "+30 AC against missiles",
    "Amelioration": "immune to weakness and drunkenness",
    "Everlasting": "never breaks",
    "WeeklyGold1000": "1,000 gold each week",
    "PartyEnduranceMinus40": "-40 Endurance for the whole party",
    "PhysicalDamageReduction3Percent": "3% less physical damage taken",
    "EncounterChancePlus15Percent": "random encounters 15% more likely",
    "AllConditionImmunity": "immune to all conditions",
    "ExperienceGainMinus15Percent": "15% less experience",
}
WEAPON_DAMAGE_KIND = {"PoisonWeaponDamage": "poison ", "DiseaseWeaponDamage": "disease "}

# MM9's spelling slips in the artifact and set piece stories, corrected in the imported text. Each must still occur.
DESCRIPTION_CORRECTIONS: dict[int, list[tuple[str, str]]] = {
    175: [("weilder", "wielder")],
    179: [("comissioned", "commissioned"), ("Clans of Chedian ", "Clans of Chedian. ")],
    180: [("lead by", "led by"), ("it's contents", "its contents")],
    181: [("commited", "committed")],
    184: [("missle", "missile")],
    188: [("paticular invetion", "particular invention"), ("it's muzzle", "its muzzle")],
    189: [("forsaw", "foresaw"), ("surfaced in Chedian ", "surfaced in Chedian. ")],
    190: [("Desipte", "Despite")],
    191: [("It's first", "Its first"), ("carries is long", "carries are long")],
    194: [("extremly", "extremely")],
    197: [("suceeded", "succeeded")],
    198: [("intstead", "instead")],
    207: [("sheild", "shield"), ("possesed", "possessed")],
    209: [("suitor's became", "suitors became")],
    210: [("it's life", "its life"), ("it's new owner", "its new owner"), ("piece of them with when",
                                                                         "piece of them with it when")],
    216: [("preceeds", "precedes")],
    217: [("Beggers", "Beggars"), ("the begger", "the beggar"), ("One begger", "One beggar")],
    218: [("it's inhabitants", "its inhabitants"), ("exorborant", "exorbitant"), ("This ring", "This amulet")],
    **{raw_id: [("Hundred's", "Hundreds")] for raw_id in range(234, 239)},
    221: [("Regenereration", "Regeneration")],
    226: [("Regenereration", "Regeneration")],
    236: [("+ 10", "+10")],
}


def signed(value: int) -> str:
    return f"+{value}" if value > 0 else str(value)


def skill_label(name: str) -> str:
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)


def effect_text(effect: dict[str, Any]) -> str:
    """The "(Effects: ...)" list of an artifact or relic, written from its final effect."""
    parts: list[str] = []
    stats = [effect.get(name, 0) for name in EFFECT_TEXT_STATS]
    if stats[0] and len(set(stats)) == 1:
        parts.append(f"{signed(stats[0])} to all stats")
    else:
        parts += [f"{signed(value)} {name.capitalize()}" for name, value in zip(EFFECT_TEXT_STATS, stats) if value]
    parts += [f"{signed(effect[name])} {label}" for name, label in EFFECT_TEXT_FIELDS.items() if effect.get(name)]

    skills = dict(effect.get("skill_bonuses", {}))
    for group, label in ((MAGIC_SCHOOLS, "to all magic skills"), (ARMOR_SKILLS, "to the armor skills")):
        amounts = {skills.get(name) for name in group}
        if len(amounts) == 1 and None not in amounts:
            parts.append(f"{signed(amounts.pop())} {label}")
            for name in group:
                del skills[name]
    parts += [f"{signed(amount)} {skill_label(name)}" for name, amount in skills.items()]

    flags = list(effect.get("flags", []))
    if effect.get("weapon_damage"):
        kind = next((WEAPON_DAMAGE_KIND[flag] for flag in flags if flag in WEAPON_DAMAGE_KIND), "")
        parts.append(f"{signed(effect['weapon_damage'])} {kind}damage per hit")
    recovery = effect.get("recovery_reduction_ticks", 0)
    if recovery:
        parts.append("faster recovery" if recovery > 0 else "slower recovery")
    if effect.get("health_regen_per_second"):
        parts.append("regenerates HP")
    if effect.get("spell_regen_per_second"):
        parts.append("regenerates SP")
    for flag in flags:
        if flag in WEAPON_DAMAGE_KIND or flag == "CarriedPartyEffect":
            continue
        if flag not in EFFECT_FLAG_TEXT:
            raise ValueError(f"effect flag {flag!r} has no description text")
        parts.append(EFFECT_FLAG_TEXT[flag])

    if not parts:
        raise ValueError("an artifact effect without any description text")
    text = ", ".join(parts)
    if "CarriedPartyEffect" in flags:
        text = "while carried, for the whole party: " + text
    return f"(Effects: {text[0].upper()}{text[1:]})"


def item_description(item: SourceItem, effect: dict[str, Any] | None) -> str:
    """MM9's description with its spelling corrected and, on an artifact or relic, the effect list rewritten."""
    description = item.description
    for wrong, right in DESCRIPTION_CORRECTIONS.get(item.raw_id, []):
        if wrong not in description:
            raise ValueError(f"raw item {item.raw_id}: description correction {wrong!r} no longer matches")
        description = description.replace(wrong, right)
    if item.raw_id in EFFECT_TEXT_RAW_IDS and effect is not None:
        start = description.find("(Effects:")
        if start < 0:
            raise ValueError(f"raw item {item.raw_id}: description has no effect list")
        description = description[:start].rstrip() + " " + effect_text(effect)
    return description


def item_flags(item: SourceItem, readable_texts: dict[int, tuple[str, str]]) -> list[str]:
    flags: list[str] = []
    if item.quest_item:
        flags.extend(["Quest", "NoRandom", "NoShop"])
    if item.raw_id in readable_texts:
        flags.append("Readable")
    if item.category_key == "items_skill":
        flags.extend(["SkillLearning", "NoRandom"])
    if normalized_tier(item) == 7:
        flags.append("Unique")
        if normalized_material(item) not in {"Artifact", "Relic"} or item.raw_id in FIXED_SOURCE_RARE_RAW_IDS:
            flags.append("NoRandom")
        if normalized_material(item) in {"Artifact", "Relic"}:
            flags.append("World:mm9")   # a world's artifacts and relics drop only in it (devdocs/LOOT_POOL.md)
    if item.source_skill.casefold() == "thrown" and "dagger" in item.subtype.casefold():
        flags.append("ExtraProjectileAtGrandmaster")
    return list(dict.fromkeys(flags))


def normalized_item_row(
    item: SourceItem,
    canonical_id: str,
    readable_texts: dict[int, tuple[str, str]],
    icon_dimensions: tuple[int, int],
    equipment_visual: dict[str, Any] | None,
    body_equipment_visual: dict[str, Any] | None,
) -> list[str]:
    row = [""] * ITEM_COLUMN_COUNT
    global_id = GLOBAL_ITEM_ID_BASE + item.raw_id
    tier = normalized_tier(item)
    mod1, mod2 = normalized_modifiers(item)
    equip_stat = normalized_equip_stat(item, readable_texts)
    source_skill_key = item.source_skill.casefold()
    use_target = SKILL_BOOK_TARGETS.get(source_skill_key, "") if item.category_key == "items_skill" else ""
    required_might, required_accuracy = normalized_stat_requirements(item)
    inventory_width, inventory_height = (inventory_slots_from_pixels(size) for size in icon_dimensions)
    item_value, value_rule = normalized_value(item, equip_stat, tier)
    if item.category_key == "items_skill" and not use_target:
        raise ValueError(f"raw item {item.raw_id} has unmapped learning skill {item.source_skill!r}")

    row[0] = str(global_id)
    row[1] = f"mm9_item_{global_id}"
    row[2] = item.name
    row[3] = str(item_value)
    row[4] = equip_stat
    row[5] = normalized_skill(item) if equip_stat in EQUIP_STAT_BY_CATEGORY.values() else "Misc"
    row[6] = mod1
    row[7] = mod2
    row[8] = normalized_material(item)
    row[9] = str(max(0, parse_int(item.cells[13])))
    row[10] = item.subtype or item.name
    row[11] = str(normalized_ground_object_id(item))
    # MM9's Clover gives the character who uses it one skill point (cshell.dll 0x100249c4, item 590).
    row[12] = "1" if item.raw_id == CLOVER_RAW_ID else "0"
    row[13] = "0"
    row[14] = str(equipment_visual["equip_anchor"][0]) if equipment_visual is not None else "0"
    row[15] = str(equipment_visual["equip_anchor"][1]) if equipment_visual is not None else "0"
    row[16] = item.description
    row[17] = "mm9"
    row[18] = canonical_id
    row[19] = str(item.raw_id)
    row[20] = "|".join(item_flags(item, readable_texts))
    row[21] = str(tier)
    row[22] = (
        "LearnSkill" if item.category_key == "items_skill"
        else "ReadText" if item.raw_id in readable_texts
        else "GrantSkillPoints" if item.raw_id == CLOVER_RAW_ID
        else ""
    )
    row[23] = use_target
    row[24] = SET_BY_RAW_ITEM_ID.get(item.raw_id, "")
    row[25] = f"mm9:item_effect/{item.raw_id}" if tier == 7 else ""
    row[26] = ALLOWED_CLASS_ROOTS_BY_RAW_ITEM_ID.get(item.raw_id, "")
    row[27] = str(required_might) if required_might else ""
    row[28] = str(required_accuracy) if required_accuracy else ""
    row[29] = str(inventory_width)
    row[30] = str(inventory_height)
    if equipment_visual is not None:
        row[31] = "generated_equipped_anchor_" + str(equipment_visual["review_status"])
    elif body_equipment_visual is not None:
        row[31] = "generated_body_variants_" + str(body_equipment_visual["review_status"])
    else:
        row[31] = "generated_inventory_icon"
    row[32] = str(item.raw_id)
    row[33] = canonical_id
    row[34] = item.category
    row[35] = item.source_skill
    row[36] = f"ART/INVENTORYICONS/{item.icon_stem}.pcx"
    row[37] = item.subtype
    row[38] = item.cells[4]
    row[39] = item.cells[5]
    row[40] = item.cells[3]
    row[41] = item.cells[6]
    row[42] = item.cells[14]
    row[43] = "reviewed_source_override" if item.source_override_id else "imported"
    row[44] = f"mm9_balance_v1_l{tier}:{value_rule}:source_combat_layout"
    if item.source_override_id:
        row[44] += f":{item.source_override_id}"
    return row


def build_case_insensitive_icon_index(icon_root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in sorted(icon_root.iterdir(), key=lambda candidate: candidate.name.casefold()):
        if not path.is_file() or path.suffix.casefold() != ".pcx":
            continue
        key = path.stem.casefold()
        if key in result:
            raise ValueError(f"case-insensitive duplicate MM9 icon stem: {path.stem}")
        result[key] = path
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for block in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_generated_art_manifest(path: Path) -> dict[int, dict[str, Any]]:
    """The inventory art per raw item id (install_mm9_item_art_x2.py): x2 PNGs installed into icons_x2."""
    with path.open("r", encoding="utf-8") as source_file:
        document = yaml.safe_load(source_file) or {}
    if document.get("format_version") != 2 or document.get("scale") != ICON_SCALE:
        raise ValueError(f"unsupported generated item art manifest in {path}: expected format 2 at x{ICON_SCALE}")
    definitions: dict[int, dict[str, Any]] = {}
    for raw_id_text, definition in document.get("items", {}).items():
        raw_id = int(raw_id_text)
        if raw_id in definitions or not isinstance(definition, dict) or not definition.get("asset"):
            raise ValueError(f"invalid generated art definition for raw item {raw_id}")
        definitions[raw_id] = definition
    return definitions


def load_equipment_visual_overlay(path: Path | None) -> dict[int, dict[str, Any]]:
    if path is None or not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as source_file:
        document = yaml.safe_load(source_file) or {}

    if document.get("format_version") != 1:
        raise ValueError(f"unsupported MM9 equipment visual overlay version in {path}")
    if document.get("kind") != "mm9_item_equipment_visual_overlay":
        raise ValueError(f"invalid MM9 equipment visual overlay kind in {path}")

    definitions: dict[int, dict[str, Any]] = {}

    for raw_id_text, definition in document.get("items", {}).items():
        raw_id = int(raw_id_text)

        if raw_id in definitions or not isinstance(definition, dict):
            raise ValueError(f"invalid duplicate equipment visual definition for raw item {raw_id}")

        allowed_fields = {
            "equip_anchor", "reference_item_id", "method", "review_status", "notes",
        }
        unknown_fields = set(definition) - allowed_fields

        if unknown_fields:
            raise ValueError(
                f"raw item {raw_id} equipment visual has unknown fields: {sorted(unknown_fields)}")

        anchor = definition.get("equip_anchor")

        if (not isinstance(anchor, list) or len(anchor) != 2
                or any(isinstance(value, bool) or not isinstance(value, int) for value in anchor)):
            raise ValueError(f"raw item {raw_id} has invalid equipment anchor: {anchor!r}")

        reference_item_id = definition.get("reference_item_id")

        if (isinstance(reference_item_id, bool) or not isinstance(reference_item_id, int)
                or reference_item_id <= 0):
            raise ValueError(f"raw item {raw_id} has invalid reference item id: {reference_item_id!r}")

        method = definition.get("method")
        review_status = definition.get("review_status")

        if not isinstance(method, str) or not method:
            raise ValueError(f"raw item {raw_id} has no equipment visual derivation method")
        if review_status not in EQUIPMENT_VISUAL_REVIEW_STATES:
            raise ValueError(f"raw item {raw_id} has invalid equipment visual review state: {review_status!r}")

        definitions[raw_id] = definition

    return definitions


def load_body_equipment_visual_overlay(path: Path | None) -> dict[int, dict[str, Any]]:
    if path is None or not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as source_file:
        document = yaml.safe_load(source_file) or {}

    if document.get("format_version") != 1:
        raise ValueError(f"unsupported MM9 body-equipment visual overlay version in {path}")
    if document.get("kind") != "mm9_item_body_equipment_visual_overlay":
        raise ValueError(f"invalid MM9 body-equipment visual overlay kind in {path}")

    definitions: dict[int, dict[str, Any]] = {}

    for raw_id_text, definition in document.get("items", {}).items():
        raw_id = int(raw_id_text)

        if raw_id in definitions or not isinstance(definition, dict):
            raise ValueError(f"invalid duplicate body-equipment visual definition for raw item {raw_id}")

        allowed_fields = {"reference_item_id", "coverage_profile", "method", "review_status"}
        unknown_fields = set(definition) - allowed_fields

        if unknown_fields:
            raise ValueError(
                f"raw item {raw_id} body-equipment visual has unknown fields: {sorted(unknown_fields)}")

        reference_item_id = definition.get("reference_item_id")
        coverage_profile = definition.get("coverage_profile")
        method = definition.get("method")
        review_status = definition.get("review_status")

        if (isinstance(reference_item_id, bool) or not isinstance(reference_item_id, int)
                or reference_item_id <= 0):
            raise ValueError(f"raw item {raw_id} has invalid body-equipment reference: {reference_item_id!r}")
        if coverage_profile not in BODY_EQUIPMENT_COVERAGE_PROFILES:
            raise ValueError(f"raw item {raw_id} has invalid body-equipment coverage: {coverage_profile!r}")
        if method != "fitted_mask_design_transfer":
            raise ValueError(f"raw item {raw_id} has invalid body-equipment method: {method!r}")
        if review_status not in EQUIPMENT_VISUAL_REVIEW_STATES:
            raise ValueError(f"raw item {raw_id} has invalid body-equipment review state: {review_status!r}")

        definitions[raw_id] = definition

    return definitions


def read_equipment_visual_reference_ids(path: Path) -> set[int]:
    with path.open("r", encoding="cp1252", newline="") as source_file:
        rows = list(csv.reader(source_file, delimiter="\t"))

    header_index = next(
        index for index, row in enumerate(rows)
        if row and row[0] == "Item #"
    )
    headers = rows[header_index]
    item_id_column = headers.index("Item #")
    equip_x_column = headers.index("Equip X")
    equip_y_column = headers.index("Equip Y")
    return {
        parse_int(row[item_id_column])
        for row in rows[header_index + 1:]
        if len(row) > equip_y_column
        and parse_int(row[item_id_column]) > 0
        and (parse_int(row[equip_x_column]) != 0 or parse_int(row[equip_y_column]) != 0)
    }


def generated_asset_path(manifest_path: Path, definition: dict[str, Any]) -> Path:
    asset_path = manifest_path.parent / str(definition["asset"])
    if not asset_path.is_file():
        raise ValueError(f"generated item art asset does not exist: {asset_path}")
    if definition.get("asset_sha256") and sha256_file(asset_path) != definition["asset_sha256"]:
        raise ValueError(f"generated item art changed after its manifest was written: {asset_path}")
    return asset_path


def logical_icon_dimensions(manifest_path: Path, definition: dict[str, Any]) -> tuple[int, int]:
    """The icon's size in logical (x1) pixels, rounded up as the engine rounds a scaled tier."""
    with Image.open(generated_asset_path(manifest_path, definition)) as image:
        return tuple(-(-size // ICON_SCALE) for size in image.size)


def copy_generated_icon(manifest_path: Path, definition: dict[str, Any], output_path: Path) -> Path:
    asset_path = generated_asset_path(manifest_path, definition)
    with Image.open(asset_path) as source_image:
        if "A" not in source_image.getbands() or source_image.getchannel("A").getextrema()[0] == 255:
            raise ValueError(f"generated item art has no transparent alpha pixels: {asset_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(asset_path, output_path)
    return asset_path


def read_plain_tsv(path: Path) -> list[list[str]]:
    with path.open("r", encoding="cp1252", newline="") as source_file:
        return [line.rstrip("\r\n").split("\t") for line in source_file]


def write_tsv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        writer.writerows(rows)


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as output_file:
        yaml.safe_dump(data, output_file, sort_keys=False, allow_unicode=True, width=120)


def write_world_item_sprite_artifacts(
    args: argparse.Namespace,
    items: list[SourceItem],
    icon_records: list[dict[str, Any]],
) -> None:
    icon_records_by_raw_id = {int(record["raw_mm9_id"]): record for record in icon_records}
    world_items = [
        item
        for item in items
        if classify_item(item)[0] == "imported" and uses_dedicated_world_item_sprite(item)
    ]
    object_rows: list[list[str]] = [[
        "// Name", "SpriteName", "ObjectId", "Radius", "Height", "LifetimeTicks", "Speed", "SpriteId",
        "ParticleTrailColor", "ParticleTrailRed", "ParticleTrailGreen", "ParticleTrailBlue", "Flags",
    ]]
    sprite_groups: list[dict[str, Any]] = []
    manifest_items: list[dict[str, Any]] = []

    for item in world_items:
        icon_record = icon_records_by_raw_id.get(item.raw_id)

        if icon_record is None:
            raise ValueError(f"raw item {item.raw_id} has no generated icon record for its WorldItem sprite")

        icon_path = args.output_root / str(icon_record["output"])
        texture_name = f"mm9wi{item.raw_id:04d}"
        sprite_path = args.output_root / "sprites" / f"{texture_name}.png"
        object_id = WORLD_ITEM_OBJECT_ID_BASE + item.raw_id
        sprite_id = WORLD_ITEM_SPRITE_ID_BASE + item.raw_id

        with Image.open(icon_path) as icon_image:
            if "A" not in icon_image.getbands() or icon_image.getchannel("A").getextrema()[0] == 255:
                raise ValueError(f"raw item {item.raw_id} WorldItem art has no transparent alpha pixels")
            # The sprite keeps the native x1 scale of world sprites: the x2 icon halved (premultiplied alpha).
            width, height = (-(-size // ICON_SCALE) for size in icon_image.size)
            sprite = icon_image.convert("RGBa").resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")

        sprite_path.parent.mkdir(parents=True, exist_ok=True)
        sprite.save(sprite_path, format="PNG", optimize=False, compress_level=9)
        object_rows.append([
            f"MM9 World Item {item.raw_id} {item.name}",
            texture_name,
            str(object_id),
            "64",
            "64",
            "0",
            "0",
            str(sprite_id),
            "0x00000000",
            "0",
            "0",
            "0",
            "Bounce",
        ])
        sprite_groups.append({
            "sprite_id": sprite_id,
            "sprite_name": texture_name,
            "animation_length_raw": 2,
            "frames": [{
                "texture_name": texture_name,
                "frame_length_raw": 2,
                "flags": ["Image1"],
            }],
        })
        manifest_entry: dict[str, Any] = {
            "raw_mm9_id": item.raw_id,
            "item_id": GLOBAL_ITEM_ID_BASE + item.raw_id,
            "name": item.name,
            "source_category": item.category,
            "source_marker": item.source_marker,
            "source_icon_stem": item.icon_stem,
            "source_visual_family": item.icon_stem.casefold(),
            "inventory_icon": str(icon_record["output"]),
            "world_sprite": sprite_path.relative_to(args.output_root).as_posix(),
            "object_id": object_id,
            "sprite_id": sprite_id,
            "width": width,
            "height": height,
            "art_method": "inventory_sprite_reuse",
            "visual_source": icon_record["visual_source"],
        }
        if "generation_tool" in icon_record:
            manifest_entry["generation_tool"] = icon_record["generation_tool"]
        manifest_items.append(manifest_entry)

    visual_families = sorted({entry["source_visual_family"] for entry in manifest_items})
    write_tsv(args.output_root / "data_tables" / "object_descriptors.txt", object_rows)
    write_yaml(
        args.output_root / "rendering" / "sprite_frame_data_world_items.yml",
        {
            "format_version": 1,
            "kind": "world_item_sprite_frames",
            "package_id": "mm9",
            "sprites": sprite_groups,
        },
    )
    write_yaml(args.output_root / "state" / "world_item_sprite_manifest.yml", {
        "format_version": 1,
        "kind": "mm9_world_item_sprite_manifest",
        "selection": "imported items whose source category or source marker classifies them as quest/miscellaneous",
        "item_count": len(manifest_items),
        "visual_family_count": len(visual_families),
        "visual_families": visual_families,
        "items": manifest_items,
    })


def discover_literal_script_item_references(script_root: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    pattern = re.compile(r"\b(giveitem|takeitem|hasitem)\s+(\d+)\b", re.IGNORECASE)
    for path in sorted(script_root.rglob("*.scr"), key=lambda candidate: candidate.as_posix().casefold()):
        text = path.read_text(encoding="cp1252")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in pattern.finditer(line):
                result.append({
                    "source": path.relative_to(script_root).as_posix(),
                    "source_line": line_number,
                    "operation": match.group(1).casefold(),
                    "raw_mm9_id": int(match.group(2)),
                })
    return result


def effect_row(prefix: list[str], definition: dict[str, Any]) -> list[str]:
    allowed_keys = set(CONTENT_EFFECT_FIELDS) | {"flags"}
    unknown_keys = set(definition) - allowed_keys
    if unknown_keys:
        raise ValueError(f"unknown content effect fields: {sorted(unknown_keys)}")

    row = list(prefix)
    for field_name in CONTENT_EFFECT_FIELDS:
        source_name = "flags" if field_name == "effect_flags" else field_name
        value = definition.get(source_name, "")
        if field_name == "skill_bonuses":
            if value and not isinstance(value, dict):
                raise ValueError("skill_bonuses must be a mapping")
            value = "|".join(f"{name}:{amount}" for name, amount in (value or {}).items())
        elif field_name == "effect_flags":
            if value and not isinstance(value, list):
                raise ValueError("flags must be a sequence")
            value = "|".join(value or [])
        row.append(str(value))
    return row


def import_items(args: argparse.Namespace) -> dict[str, int]:
    item_source_overrides = getattr(args, "item_source_overrides", None)
    if item_source_overrides is None:
        item_source_overrides = Path(__file__).resolve().with_name("mm9_item_source_overrides.yml")
    items = read_source_items(args.master_items, item_source_overrides)
    readable_texts = read_readable_texts(args.readable_text)
    ids = canonical_ids(items)
    icon_index = build_case_insensitive_icon_index(args.icon_root)
    generated_art_manifest_path = getattr(args, "generated_art_manifest", None)
    if generated_art_manifest_path is None:
        generated_art_manifest_path = Path(__file__).resolve().with_name("mm9_item_generated_art.yml")
    generated_art = load_generated_art_manifest(generated_art_manifest_path)
    equipment_visual_overlay_path = getattr(args, "equipment_visual_overlay", None)
    if equipment_visual_overlay_path is None:
        equipment_visual_overlay_path = Path(__file__).resolve().with_name("mm9_item_equipment_visuals.yml")
    equipment_visuals = load_equipment_visual_overlay(equipment_visual_overlay_path)
    body_equipment_visual_overlay_path = getattr(args, "body_equipment_visual_overlay", None)
    if body_equipment_visual_overlay_path is None:
        body_equipment_visual_overlay_path = Path(__file__).resolve().with_name(
            "mm9_item_body_equipment_visuals.yml")
    body_equipment_visuals = load_body_equipment_visual_overlay(body_equipment_visual_overlay_path)
    equipment_visual_reference_items_path = getattr(args, "equipment_visual_reference_items", None)
    if equipment_visual_reference_items_path is None:
        equipment_visual_reference_items_path = Path("assets_dev/engine/data_tables/items.txt")
    equipment_visual_reference_ids = read_equipment_visual_reference_ids(equipment_visual_reference_items_path)
    unknown_equipment_visual_reference_ids = {
        definition["reference_item_id"]
        for definition in equipment_visuals.values()
        if definition["reference_item_id"] not in equipment_visual_reference_ids
    }

    if unknown_equipment_visual_reference_ids:
        raise ValueError(
            "MM9 equipment visual overlay has unusable reference item ids: "
            f"{sorted(unknown_equipment_visual_reference_ids)}")
    imported_raw_ids = {item.raw_id for item in items if classify_item(item)[0] == "imported"}
    unknown_generated_ids = set(generated_art) - imported_raw_ids
    missing_generated_ids = imported_raw_ids - set(generated_art)
    if unknown_generated_ids or missing_generated_ids:
        raise ValueError(
            "generated art manifest must cover exactly the imported items; "
            f"missing={sorted(missing_generated_ids)}, extra={sorted(unknown_generated_ids)}")
    expected_equipment_visual_ids = {
        item.raw_id
        for item in items
        if classify_item(item)[0] == "imported"
        and normalized_equip_stat(item, readable_texts) in EQUIPMENT_VISUAL_EQUIP_STATS
    }
    missing_equipment_visual_ids = expected_equipment_visual_ids - set(equipment_visuals)
    unexpected_equipment_visual_ids = set(equipment_visuals) - expected_equipment_visual_ids

    if missing_equipment_visual_ids or unexpected_equipment_visual_ids:
        raise ValueError(
            "MM9 equipment visual overlay coverage mismatch; "
            f"missing={sorted(missing_equipment_visual_ids)}, extra={sorted(unexpected_equipment_visual_ids)}")

    expected_body_equipment_visual_ids = {
        item.raw_id
        for item in items
        if classify_item(item)[0] == "imported"
        and normalized_equip_stat(item, readable_texts) == "Armor"
    }
    missing_body_visual_ids = expected_body_equipment_visual_ids - set(body_equipment_visuals)
    unexpected_body_visual_ids = set(body_equipment_visuals) - expected_body_equipment_visual_ids

    if missing_body_visual_ids or unexpected_body_visual_ids:
        raise ValueError(
            "MM9 body-equipment visual overlay coverage mismatch; "
            f"missing={sorted(missing_body_visual_ids)}, extra={sorted(unexpected_body_visual_ids)}")

    with args.object_table.open("r", encoding="cp1252", newline="") as object_file:
        object_rows = csv.DictReader(object_file, delimiter="\t")
        renderable_object_ids = {
            parse_int(row["ObjectId"])
            for row in object_rows
            if parse_int(row["ObjectId"]) > 0
            and parse_int(row["SpriteId"]) > 0
            and "nosprite" not in row["Flags"].casefold()
        }
    renderable_object_ids.update(
        WORLD_ITEM_OBJECT_ID_BASE + item.raw_id
        for item in items
        if classify_item(item)[0] == "imported" and uses_dedicated_world_item_sprite(item)
    )
    imported_rows: list[list[str]] = []
    readable_rows: list[list[str]] = []
    report_rows: list[dict[str, Any]] = []
    id_mappings: list[dict[str, Any]] = []
    icon_records: list[dict[str, Any]] = []

    with args.item_effects.open("r", encoding="utf-8") as effect_file:
        authored_effects = yaml.safe_load(effect_file) or {}
    effect_definitions = authored_effects.get("effects", {})
    set_definitions = authored_effects.get("sets", [])

    for item in items:
        status, reason = classify_item(item)
        global_id = GLOBAL_ITEM_ID_BASE + item.raw_id
        report_entry: dict[str, Any] = {
            "raw_mm9_id": item.raw_id,
            "source_row": item.row_number,
            "name": item.name,
            "source_category": item.category,
            "status": status,
            "reason": reason,
            "source_provenance": item.source_provenance,
        }
        if item.source_override_id:
            report_entry["source_override_id"] = item.source_override_id

        if status == "mapped":
            mapped_item_id = ENGINE_ITEM_MAPPINGS[item.raw_id][0]
            report_entry["mapped_item_id"] = mapped_item_id
            own_item = GLOBAL_ITEM_ID_BASE <= mapped_item_id <= GLOBAL_ITEM_ID_END
            id_mappings.append({
                "raw_mm9_id": item.raw_id,
                "item_id": mapped_item_id,
                "kind": "mm9_mapping" if own_item else "engine_mapping",
                "canonical_id": f"{'mm9' if own_item else 'engine'}:item/{mapped_item_id}",
            })
        elif status == "imported":
            canonical_id = ids[item.raw_id]
            equipment_visual = equipment_visuals.get(item.raw_id)
            body_equipment_visual = body_equipment_visuals.get(item.raw_id)
            generated_definition = generated_art[item.raw_id]
            icon_width, icon_height = logical_icon_dimensions(generated_art_manifest_path, generated_definition)
            normalized_row = normalized_item_row(
                item,
                canonical_id,
                readable_texts,
                (icon_width, icon_height),
                equipment_visual,
                body_equipment_visual,
            )
            authored_effect = effect_definitions.get(str(item.raw_id))
            normalized_row[16] = item_description(
                item, balance_effect(item.raw_id, authored_effect) if authored_effect is not None else None)
            if equipment_visual is not None:
                equip_x, equip_y = equipment_visual["equip_anchor"]

                if not 0 <= equip_x < icon_width or not 0 <= equip_y < icon_height:
                    raise ValueError(
                        f"raw item {item.raw_id} equipment anchor {(equip_x, equip_y)} is outside "
                        f"its {icon_width}x{icon_height} equipped image")
            ground_object_id = int(normalized_row[11])
            if ground_object_id not in renderable_object_ids:
                raise ValueError(
                    f"raw item {item.raw_id} maps to non-renderable ground object {ground_object_id}")
            imported_rows.append(normalized_row)
            report_entry["source_values"] = {
                "quality": item.cells[3],
                "minimum_or_dice": item.cells[4],
                "maximum_or_sides": item.cells[5],
                "flags": item.cells[6],
                "value": item.cells[10],
                "identify_repair": item.cells[13],
                "restrictions": item.cells[14],
            }
            report_entry["normalized_values"] = {
                "item_id": global_id,
                "equip_stat": normalized_row[4],
                "skill": normalized_row[5],
                "mod1": normalized_row[6],
                "mod2": normalized_row[7],
                "rarity_or_material": normalized_row[8],
                "value": int(normalized_row[3]),
                "identify_repair": int(normalized_row[9]),
                "ground_object_id": ground_object_id,
                "tier": int(normalized_row[21]),
                "allowed_class_roots": normalized_row[26],
                "required_might": int(normalized_row[27] or 0),
                "required_accuracy": int(normalized_row[28] or 0),
                "inventory_width": int(normalized_row[29]),
                "inventory_height": int(normalized_row[30]),
                "visual_status": normalized_row[31],
                "equip_x": int(normalized_row[14]),
                "equip_y": int(normalized_row[15]),
                "effect_profile": normalized_row[25],
            }
            if equipment_visual is not None:
                report_entry["equipment_visual"] = {
                    "reference_item_id": equipment_visual["reference_item_id"],
                    "method": equipment_visual["method"],
                    "review_status": equipment_visual["review_status"],
                }
            if body_equipment_visual is not None:
                report_entry["body_equipment_visual"] = {
                    "reference_item_id": body_equipment_visual["reference_item_id"],
                    "method": body_equipment_visual["method"],
                    "review_status": body_equipment_visual["review_status"],
                }
            report_entry["balance_rule"] = normalized_row[44]
            id_mappings.append({
                "raw_mm9_id": item.raw_id,
                "item_id": global_id,
                "kind": "world_definition",
                "canonical_id": canonical_id,
            })

            source_icon = icon_index.get(item.icon_stem.casefold())
            if source_icon is None:
                raise ValueError(f"raw item {item.raw_id} references missing icon {item.icon_stem!r}")
            output_icon = args.output_root / ICON_DIRECTORY / f"mm9_item_{global_id}.png"
            generated_asset = copy_generated_icon(generated_art_manifest_path, generated_definition, output_icon)
            icon_record = {
                "item_id": global_id,
                "raw_mm9_id": item.raw_id,
                "source": source_icon.relative_to(args.source_root).as_posix(),
                "source_sha256": sha256_file(source_icon),
                "output": output_icon.relative_to(args.output_root).as_posix(),
                "output_sha256": sha256_file(output_icon),
                "width": icon_width,
                "height": icon_height,
                "scale": ICON_SCALE,
                "transparency": "rgba_alpha",
                "visual_source": "generated_inventory_art",
                "generated_asset": generated_asset.relative_to(generated_art_manifest_path.parent).as_posix(),
                "design_id": generated_definition.get("design_id"),
            }
            if equipment_visual is not None:
                icon_record["equip_anchor"] = list(equipment_visual["equip_anchor"])
                icon_record["anchor_reference_item_id"] = equipment_visual["reference_item_id"]
                icon_record["anchor_method"] = equipment_visual["method"]
                icon_record["anchor_review_status"] = equipment_visual["review_status"]
            icon_records.append(icon_record)

            if item.raw_id in readable_texts:
                title, body = readable_texts[item.raw_id]
                readable_rows.append([str(global_id), body, title, item.name])

        report_rows.append(report_entry)

    write_world_item_sprite_artifacts(args, items, icon_records)
    # Balance profile v2: MM9 equipment on MM6-MM8 scales, weighed and priced like MM6-MM8's items of its family and
    # tier (mm9_item_balance.py, BALANCE_PLAN.md sections 3.4-3.5).
    engine_tables = Path(__file__).resolve().parents[2] / "assets_dev" / "engine" / "data_tables"
    engine_item_rows = read_plain_tsv(getattr(args, "engine_items", None) or engine_tables / "items.txt")
    engine_random_rows = read_plain_tsv(getattr(args, "engine_random_items", None) or engine_tables / "random_items.txt")
    reference = EngineReference.from_tables(engine_item_rows, engine_random_rows)
    item_columns = {name: index for index, name in enumerate(ITEM_HEADERS)}
    balance_rows(imported_rows, item_columns, reference)
    # MM9's own spellbooks, one per spell, drawn by the spell's mastery (mm9_spellbooks.py).
    book_rows, book_random_rows = spellbook_rows(
        ITEM_HEADERS,
        engine_item_rows,
        engine_random_rows,
        read_plain_tsv(engine_tables / "spells.txt"),
        install_spellbook_icons(args.output_root, Path(__file__).resolve().parents[2]),
    )
    write_tsv(args.output_root / "data_tables" / "items.txt", [ITEM_HEADERS, *imported_rows, *book_rows])
    write_tsv(
        args.output_root / "data_tables" / "random_items.txt",
        [["Item #", "Pic File", "1", "2", "3", "4", "5", "6", "Name"],
         *random_item_rows(imported_rows, item_columns, reference), *book_random_rows],
    )
    write_tsv(
        args.output_root / "data_tables" / "readable_items.txt",
        [["Item#", "message text", "Location", "Item Name"], *readable_rows],
    )

    required_effect_ids = {
        item.raw_id for item in items
        if classify_item(item)[0] == "imported" and normalized_tier(item) == 7
    }
    authored_effect_ids = {int(raw_id) for raw_id in effect_definitions}
    if authored_effect_ids != required_effect_ids:
        missing = sorted(required_effect_ids - authored_effect_ids)
        extra = sorted(authored_effect_ids - required_effect_ids)
        raise ValueError(f"authored item effects do not cover tier-7 items; missing={missing}, extra={extra}")

    effect_rows = [
        effect_row(
            [str(GLOBAL_ITEM_ID_BASE + raw_id), f"mm9:item_effect/{raw_id}"],
            balance_effect(raw_id, effect_definitions[str(raw_id)]),
        )
        for raw_id in sorted(required_effect_ids)
    ]
    write_tsv(
        args.output_root / "data_tables" / "item_effects.txt",
        [["item_id", "effect_profile", *CONTENT_EFFECT_FIELDS], *effect_rows],
    )

    set_rows: list[list[str]] = []
    seen_set_thresholds: set[tuple[str, int]] = set()
    for definition in set_definitions:
        set_id = str(definition.get("set_id", ""))
        required_pieces = int(definition.get("required_pieces", 0))
        profile = str(definition.get("effect_profile", ""))
        threshold_key = (set_id, required_pieces)
        if not set_id or required_pieces <= 0 or not profile or threshold_key in seen_set_thresholds:
            raise ValueError(f"invalid or duplicate authored set definition: {definition}")
        seen_set_thresholds.add(threshold_key)
        set_rows.append(effect_row([set_id, str(required_pieces), profile],
                                   balance_effect(0, definition.get("effect", {}))))
    write_tsv(
        args.output_root / "data_tables" / "item_sets.txt",
        [["set_id", "required_piece_count", "effect_profile", *CONTENT_EFFECT_FIELDS], *set_rows],
    )
    alias_rows = [
        ["mm9", str(mapping["raw_mm9_id"]), str(mapping["item_id"]), mapping["kind"]]
        for mapping in id_mappings
    ]
    write_tsv(
        args.output_root / "data_tables" / "item_aliases.txt",
        [["package_id", "source_item_id", "item_id", "resolution"], *alias_rows],
    )
    write_yaml(args.output_root / "state" / "item_ids.yml", {
        "format_version": 1,
        "kind": "mm9_item_id_map",
        "global_id_formula": "10000 + raw_mm9_id",
        "mappings": id_mappings,
    })
    counts = Counter(entry["status"] for entry in report_rows)
    write_yaml(args.output_root / "state" / "item_import_report.yml", {
        "format_version": 1,
        "source": args.master_items.relative_to(args.source_root).as_posix(),
        "source_sha256": sha256_file(args.master_items),
        "source_table_row_count": sum(1 for item in items if not item.source_override_id),
        "source_override_count": sum(1 for item in items if item.source_override_id),
        "effective_row_count": len(items),
        "counts": dict(sorted(counts.items())),
        "items": report_rows,
    })
    write_yaml(args.output_root / "state" / "item_icon_manifest.yml", {
        "format_version": 1,
        "conversion": "generated RGBA art when authored; otherwise Pillow source-icon RGB black-key conversion",
        "icons": icon_records,
    })

    report_by_raw_id = {entry["raw_mm9_id"]: entry for entry in report_rows}
    script_references = discover_literal_script_item_references(args.script_root)
    for reference in script_references:
        source_item = report_by_raw_id.get(reference["raw_mm9_id"])
        if source_item is None:
            reference["resolution"] = "missing_source_definition"
        elif source_item["status"] == "imported":
            reference["resolution"] = "world_definition"
            reference["item_id"] = GLOBAL_ITEM_ID_BASE + reference["raw_mm9_id"]
        elif source_item["status"] == "mapped":
            own_item = GLOBAL_ITEM_ID_BASE <= source_item["mapped_item_id"] <= GLOBAL_ITEM_ID_END
            reference["resolution"] = "mm9_mapping" if own_item else "engine_mapping"
            reference["item_id"] = source_item["mapped_item_id"]
        else:
            reference["resolution"] = "excluded_requires_explicit_mapping"
    reference_counts = Counter(reference["resolution"] for reference in script_references)
    write_yaml(args.output_root / "state" / "item_script_reference_report.yml", {
        "format_version": 1,
        "source": args.script_root.relative_to(args.source_root).as_posix(),
        "literal_reference_count": len(script_references),
        "counts": dict(sorted(reference_counts.items())),
        "references": script_references,
    })

    if len(report_rows) != 530 or sum(counts.values()) != 530:
        raise ValueError(f"expected 529 source rows plus one reviewed override, got {len(report_rows)}")

    return dict(counts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path("mm9/extracted"))
    parser.add_argument("--output-root", type=Path, default=Path("assets_dev/worlds/mm9"))
    parser.add_argument(
        "--object-table",
        type=Path,
        default=Path("assets_dev/engine/data_tables/object_list.txt"),
    )
    args = parser.parse_args()
    args.master_items = args.source_root / "DATA" / "DATA" / "MASTERITEMLIST.csv"
    args.readable_text = args.source_root / "DATA" / "DATA" / "BOOK AND SCROLL TEXT.csv"
    args.icon_root = args.source_root / "ART" / "ART" / "INVENTORYICONS"
    args.script_root = args.source_root / "SCRIPTS" / "SCRIPTS"
    args.item_effects = Path(__file__).resolve().with_name("mm9_item_effects.yml")
    args.generated_art_manifest = Path(__file__).resolve().with_name("mm9_item_generated_art.yml")
    args.equipment_visual_overlay = Path(__file__).resolve().with_name("mm9_item_equipment_visuals.yml")
    args.body_equipment_visual_overlay = Path(__file__).resolve().with_name(
        "mm9_item_body_equipment_visuals.yml")
    args.item_source_overrides = Path(__file__).resolve().with_name("mm9_item_source_overrides.yml")
    args.equipment_visual_reference_items = Path("assets_dev/engine/data_tables/items.txt")
    return args


def main() -> int:
    args = parse_args()
    counts = import_items(args)
    print("MM9 item import complete: " + ", ".join(f"{key}={counts[key]}" for key in sorted(counts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
