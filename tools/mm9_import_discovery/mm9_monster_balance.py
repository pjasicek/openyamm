#!/usr/bin/env python3
"""MM9 monster balance (devdocs/mm9_rework/BALANCE_PLAN.md sections 3.2 and 3.3): MM9's monster rows on our rules.

generate_mm9_monster_tables.py builds each row from MONSTERS.txt as MM9 has it; balance_monster_rows then applies:

- HP: MM9's, x0.95 at levels 41-60 and x0.90 above 60.
- Attack speed: 75 ticks at levels 1-20 (MM9's 59 above), so low-level monsters attack every 1.25 s, not every second.
- Damage: x0.75 at levels 1-5.
- Spells: use x0.4, at most 40% (25% for condition spells); skill at most MM6-MM8's highest for the ten levels.
- Resistances: MM6-MM8-style family profiles (one immunity or strong school and one weakness by theme) on the
  band's base value, instead of MM9's one value for the four elements and one for the self schools.
- Treasure: gold dice and item chance by the monster's XP at MM7's gold and items per XP (x2.2 gold, x1.6 items, item
  chance at most 75%), treasure level by MM9's level placed on MM7's stages (treasure_level); MM9's treasure kind stays the item
  category. Bosses (BOSSES) always drop an item of level 6.

Rows the profiles do not name (townsfolk, animals, named story characters) keep MM9's resistances; harmless rows
(hostility 0 in the table) and rows without XP get no treasure.
"""
from __future__ import annotations

import re

# Output columns of monster_data.txt.
LEVEL, HP, XP, TREASURE, HOSTILITY, RECOVERY = 3, 4, 6, 7, 12, 14
ATTACK1_DAMAGE, ATTACK2_DAMAGE = 18, 22
SPELL1_USE, SPELL1, SPELL2_USE, SPELL2 = 24, 25, 26, 27
SCHOOLS = {"fire": 28, "air": 29, "water": 30, "earth": 31, "mind": 32, "spirit": 33, "body": 34}

LOW_LEVEL_RECOVERY_TICKS = 75
SPELL_USE_SCALE, SPELL_USE_CAP, CONDITION_SPELL_USE_CAP = 0.4, 40, 25
CONDITION_SPELLS = {"fear", "paralyze", "slow", "charm", "turn undead", "mass fear", "stun"}

# Base resistance by level, MM6-MM8 medians (balance_prototypes, 2026-11-06).
def base_resistance(level: int) -> int:
    return 0 if level <= 10 else 5 if level <= 20 else 15 if level <= 35 else 18 if level <= 55 else 30

# (name pattern, immune schools, strong schools, weak schools)
FAMILIES: list[tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = [
    (r"Skeleton|Skeletoid|Bone Thrasher|Skull Thrower|Mummy|Ghast|Ghoul|Revenant|Rotter|Dripper|Zombie|Lich|Dagrell"
     r"|Shadow|Apparition|Specter|Fright|Dread|^Terror$|Phantom", ("mind",), ("body",), ("spirit",)),
    (r"Vampir|^Baron$|Viscount|^Count$|Bloodsucker", ("mind",), ("body",), ("spirit",)),
    (r"Fire Dragonfly|^Imp|Demon|Dragon King|Concubine|Ebora", ("fire",), (), ("water",)),
    (r"Ice Lob|Yeti|Yanmir", ("water",), (), ("fire",)),
    (r"Lobber|Spore", (), ("earth",), ("fire",)),
    (r"Colloidal", ("mind",), ("earth",), ("air",)),
    (r"Icky|Winged|Dragonfly|^Bird$", (), ("air",), ("earth",)),
    (r"^Eye$|Orbus|Oculus", ("mind",), (), ("body",)),
    (r"Basilisk", (), ("earth",), ("air",)),
    (r"Nagate|Amphibious|Sea Monster", (), ("water",), ("air",)),
    (r"Desert Terror", (), ("fire",), ("water",)),
    (r"Reptilian|Lizard-Orc", (), ("earth",), ("water",)),
    (r"Annelid|Gezzampt|Magreeb", (), ("earth",), ("fire",)),
    (r"Wolf|Bigfoot|Sasquatch", (), ("body",), ("mind",)),
    (r"Giant", (), ("earth",), ("mind",)),
    (r"Trellborg", (), ("body",), ("fire",)),
    (r"Honk", (), ("mind",), ("spirit",)),
    (r"Sorcerer|Apprentice|Scholar", (), ("fire",), ("body",)),
    (r"Initiate|Monk", (), ("mind",), ("body",)),
    # Fighting people: no immunity, the band's base everywhere.
    (r"Cutpurse|Burglar|Bandit|Half Orc|Troglodyte|Thrall|Guard|Dwarven|Horde|Clan|Old Hag", (), (), ()),
]

# Gold per 1,000 XP and items per 1M XP by level band (MM7's, economy.py), with the plan's factors. MM7's 41-55 items
# rate (116) is one monster's, the Fire Hydra (level 45, an L3 item every kill, 76 kills); the band takes its
# neighbours' rate instead (BALANCE_PLAN.md section 3.3).
LOOT_BANDS = [  # (top level, gold per 1000 XP, items per 1M XP)
    (5, 109, 180), (10, 107, 253), (15, 80, 163), (20, 88, 156), (30, 82, 84), (40, 79, 53),
    (55, 76, 55), (80, 124, 52), (10**9, 142, 62),
]
# The factors match MM7's totals as parties play (balance_prototypes/fit_check.py CLEAR: MM7 parties kill half of an
# outdoor map's monsters and 90% of a dungeon's, MM9's 85% and all; 2026-11-07), not a full clear of MM7. Gold is
# 2.2x that (the user, 2026-11-08: a level-55 Specter paying about 400 felt like nothing; it pays about 900 now), and
# items twice that, at most 75% (the user, 2026-11-08: kills gave gold and almost no items; at MM6-MM8's chances per
# level, MM9's fewer and level-compressed kills give far fewer items).
GOLD_FACTOR, ITEM_FACTOR, ITEM_CHANCE_CAP = 2.2, 1.6, 75

# Treasure level by MM9 monster level: (top level, treasure level). MM9's levels are compressed against MM7's (its last
# chapter fights levels 30-79, MM7's last stage 65-100), so the levels are set where each chapter's drops take MM7's
# stage mix of treasure levels, not at MM7's level for level (BALANCE_PLAN.md section 3.3).
TREASURE_LEVELS = [(7, 1), (15, 2), (30, 3), (44, 4), (64, 5), (10**9, 6)]

# Story bosses the party fights: an item of level 6 on every kill, as MM6-MM8's dragons and lords. The Dragon King
# (Dragon Stadium), Njam (hostile in Arslegard), Forad Darre (Retribution, Afterworld) and Tamur Leng (the Battle of
# Frosgard). The six Jarls are friendly characters and Ebora cannot be hurt, so they are not here.
BOSSES = {"Dragon King", "Njam the Meddler", "Forad Darre", "Tamur Leng"}
BOSS_TREASURE_LEVEL = 6


def scale_dice(text: str, factor: float) -> str:
    """NdS+B with its average scaled: the bonus first, then the die size."""
    match = re.fullmatch(r"\s*(\d+)[dD](\d+)\s*(?:\+\s*(\d+))?\s*", text)
    if not match:
        return text
    count, sides, bonus = int(match.group(1)), int(match.group(2)), int(match.group(3) or 0)
    target = (count * (sides + 1) / 2 + bonus) * factor
    bonus = int(bonus * factor)
    sides = max(1, round(2 * max(0.0, target - bonus) / count - 1))
    return f"{count}D{sides}" + (f"+{bonus}" if bonus else "")


def capped_spell(cell: str, cap: int) -> str:
    """'Spell,Mastery,Skill' with the skill at most `cap`."""
    parts = cell.split(",")
    if len(parts) != 3 or not parts[2].strip().isdigit():
        return cell
    return f"{parts[0]},{parts[1]},{min(int(parts[2]), cap)}"


def spell_use(use: str, cell: str) -> str:
    if not use.isdigit() or cell in {"", "0"}:
        return use
    name = cell.split(",")[0].strip().casefold()
    cap = CONDITION_SPELL_USE_CAP if name in CONDITION_SPELLS else SPELL_USE_CAP
    return str(min(cap, round(int(use) * SPELL_USE_SCALE)))


def mm7_spell_skill_caps(base_rows: list[list[str]]) -> dict[int, int]:
    """The highest monster spell skill MM6-MM8 give per ten levels."""
    caps: dict[int, int] = {}
    for row in base_rows:
        if len(row) <= SPELL2 or not row[0].strip().isdigit() or not row[LEVEL].strip().isdigit():
            continue
        band = min(int(row[LEVEL]) // 10, 12)
        for cell in (row[SPELL1], row[SPELL2]):
            parts = cell.split(",")
            if len(parts) == 3 and parts[2].strip().isdigit():
                caps[band] = max(caps.get(band, 0), int(parts[2]))
    # A band without casters takes the next lower band's cap.
    for band in range(13):
        caps[band] = max(caps.get(band, 0), caps.get(band - 1, 0))
    return caps


def treasure_level(level: int) -> int:
    return next(treasure for top, treasure in TREASURE_LEVELS if level <= top)


def treasure(level: int, xp: int, previous: str, boss: bool = False) -> str:
    _, gold_rate, item_rate = next(band for band in LOOT_BANDS if level <= band[0])
    gold = xp * gold_rate / 1000 * GOLD_FACTOR
    chance = 100 if boss else min(ITEM_CHANCE_CAP, round(xp * item_rate / 1e6 * 100 * ITEM_FACTOR))
    level_of_item = BOSS_TREASURE_LEVEL if boss else treasure_level(level)
    sides = 6 if gold < 40 else 10 if gold < 150 else 20 if gold < 600 else 50
    count = max(1, round(gold / ((sides + 1) / 2)))
    kind = ""
    match = re.search(r"L\d(\w*)", previous or "")
    if match:
        kind = match.group(1)
    if chance <= 0:
        return f"{count}d{sides}"
    return f"{chance}%{count}d{sides}+L{level_of_item}{kind}"


def family_of(name: str):
    for pattern, immune, strong, weak in FAMILIES:
        if re.search(pattern, name, re.IGNORECASE):
            return immune, strong, weak
    return None


def balance_monster_rows(rows: list[list[str]], base_rows: list[list[str]]) -> None:
    """Apply the balance to the generated MM9 rows in place."""
    caps = mm7_spell_skill_caps(base_rows)
    for row in rows:
        if len(row) <= SCHOOLS["body"] or not row[0].strip().isdigit():
            continue
        level = int(row[LEVEL] or 0)
        family = family_of(row[1])
        harmless = row[HOSTILITY].strip() == "0"
        xp = int(row[XP] or 0)
        boss = row[1].strip() in BOSSES
        if family is None:
            # Townsfolk, animals and named story characters keep MM9's numbers; story bosses take boss treasure.
            if boss and not harmless and xp > 0:
                row[TREASURE] = treasure(level, xp, row[TREASURE], boss=True)
            continue
        hp = int(row[HP] or 0)
        row[HP] = str(round(hp * (0.90 if level > 60 else 0.95 if level >= 41 else 1.0)))
        if level <= 20 and row[RECOVERY].isdigit() and int(row[RECOVERY]) > 0:
            row[RECOVERY] = str(max(int(row[RECOVERY]), LOW_LEVEL_RECOVERY_TICKS))
        if level <= 5:
            row[ATTACK1_DAMAGE] = scale_dice(row[ATTACK1_DAMAGE], 0.75)
            row[ATTACK2_DAMAGE] = scale_dice(row[ATTACK2_DAMAGE], 0.75)
        cap = caps.get(min(level // 10, 12), 0)
        for use, spell in ((SPELL1_USE, SPELL1), (SPELL2_USE, SPELL2)):
            row[use] = spell_use(row[use], row[spell])
            row[spell] = capped_spell(row[spell], max(cap, 1))
        immune, strong, weak = family
        base = base_resistance(level)
        for school, column in SCHOOLS.items():
            row[column] = ("Imm" if school in immune else str(2 * base + 20) if school in strong
                           else "0" if school in weak else str(base))
        row[TREASURE] = "0" if harmless or xp <= 0 else treasure(level, xp, row[TREASURE], boss=boss)
