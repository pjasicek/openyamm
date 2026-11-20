#!/usr/bin/env python3
"""Writes assets_dev/worlds/mm9/modifiers.yml: an `mm9_ai` profile for every MM9 monster row of the runtime tables,
and the `skirmisher` modifier for every one whose MONSTERS.txt script builds on BaseMelee.inc.

mm9_ai (devdocs/mm9_rework/monster_ai/PROFILE.md): the row's MM9 AI archetype, from its native class and its default
script's include chain (devdocs/mm9_rework/monster_ai/MM9_AI_DATA_AND_SCRIPTS.md, MM9_AI_NATIVE_RE.md), its ranged
add-on, its reach, sweep, alert radius and speeds in our units (LithTech units x 2.56), its wince rule, whether it
resurrects, and the per-family hooks of its script (read by the MM9 loops, MM9_MONSTER_AI_PLAN.md phases 2-4).

relations.yml (phase 4b): MM9's one default-script faction, the town guards (PoliceMan.inc) against every AIBase row.

skirmisher: MM9's BaseMelee AI keeps a monster moving while it attacks, runs strafe attacks and evades after a strike
(devdocs/mm9_rework/MM9_ACTOR_ANIMATION_BLENDING_RE.md), with its Strafe Attack Pct and Evade Chance, and the length of
its model's Taunt clip when its actors.yml binding plays a `taunt` script clip.

spell_conditions (devdocs/MONSTER_MODIFIERS.md): the condition each cast MM9 debuff leaves on a struck party member
(devdocs/mm9_rework/MM9_SPELL_MAPPING.md).

reposition (devdocs/MONSTER_MODIFIERS.md; an OpenYAMM addition, not MM9): the Evil Sorcerer rows (REPOSITION_ROWS) walk
to see a target they lost and back off from a rush.

Our runtime monster id is 9000 + the MM9 row number.

Usage: generate_mm9_monster_modifiers.py [--mm9-root mm9/extracted] [--output assets_dev/worlds/mm9/modifiers.yml]
"""

import argparse
import csv
import math
import os
import re
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import convert_abc_model  # noqa: E402
from mm9_ai_placement import SCRIPT_DIRECTORY, script_chain, script_path  # noqa: E402
from mm9_monster_bodies import Mm9MonsterBodies  # noqa: E402
from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE as SCALE  # noqa: E402
import generate_mm9_monster_tables as tables  # noqa: E402

REPOSITORY = Path(__file__).resolve().parents[2]
RUNTIME_ID_BASE = 9000
# The catalogue defaults (game/tables/MonsterModifiers.cpp); parameters at their default are left out.
DEFAULT_STRAFE = 0.8
DEFAULT_EVADE = 0.4

# The rows whose native class is not AIBase (object.lto's ClassDefs: the C++ constructor each class id calls,
# re_mm8/work/mm9_ai/class_ids.txt and devdocs/mm9_rework/monster_ai/MM9_AI_NATIVE_RE.md section 2; the class id is
# the MONSTERS.txt row). AISwimFly flies or swims whatever the Fly column says; Lobber derives from it; NOEFly walks.
AISWIMFLY_ROWS = frozenset({75, 76, 77, 87, 88, 89, 93, 94, 95, 138, 139, 140, 159, 160, 161, 162, 163, 164,
                            168, 169, 170, 177, 178, 227, 228, 229, 230})
LOBBER_ROWS = frozenset({86, 106})
# The pod each Lobber launches (LOBBER.scr LaunchPod: a pod every 5-10 s, MIN/MAX_LOBBER_LAUNCH_WAIT; the pod is the
# family's own pod row: Lobber -> Lobber Pod, Ice Lobber -> Ice Lobbercicle).
LOBBER_PODS = {86: 84, 106: 105}
LOBBER_POD_COOLDOWN = (5.0, 10.0)
# Scripts whose rows are a boss (devdocs/mm9_rework/MM9_MONSTER_AI.md "What is genuinely per-monster").
BOSS_SCRIPTS = frozenset({'dragon.scr', 'yanmirbase.scr'})
# Scripts with no base loop that never move (the Magic Mine's script is missing from SCRIPTS.REZ; its velocities are 0).
TURRET_SCRIPTS = frozenset({'lobber.scr', 'dragon.scr', 'magicmine.scr'})
# Per-family hooks of the default scripts (MM9_AI_DATA_AND_SCRIPTS.md section 4.1).
NO_THROTTLE_SCRIPTS = frozenset({'dagrell.scr'})            # DAGRELL.scr:16-22: BaseMelee without SpeedThrottle
ALWAYS_EVADE_SCRIPTS = frozenset({'lobberpod.scr'})         # LOBBERPOD.scr: evades after every attack, never shoots
RANGE_DISABLED_SCRIPTS = frozenset({'lobberpod.scr'})       # LOBBERPOD.scr:150-158: its range attack switched off
MELEE_WINDOW_SCRIPTS = {'banshee.scr': 5.0}                 # BANSHEE.scr:19-84: stat Undead up to 5 s per melee pass
SPAWN_IN_SCRIPTS = frozenset({'greaterdemon.scr'})          # GREATERDEMON.scr:14-77 (p0 = 1: a spawner's demons)
DEATH_SPAWN_SCRIPTS = {'lesserdemon.scr': 242}              # LESSERDEMON.scr:18-53: a Greater Demon (p0 = 1)
# FLYINGICKY.scr:18-247: hangs upside down until damaged, alerted, helped, shot at or it sees a target, then
# launches into BaseFly; the Airborne Icky (row 87) starts in the air.
HANGING_SCRIPTS = frozenset({'flyingicky.scr'})
AIRBORNE_ROWS = frozenset({87})
# The guards' friends (PoliceMan.inc PoliceManInit: AddFriend Player, Cat, NPC, Animal, GuardBase; AddEnemy AIBase):
# the rows whose native class derives from NPC, Animal or Cat (re_mm8/work/mm9_ai/class_ids.txt, actor_classes.txt);
# the mice (299, 300) have no ClassDef and count as animals. GuardBase: the four Town Guard rows. Every other row's
# class is an AIBase: a guard's enemy, and (IsFriend asks both sides) the guard is its enemy.
GUARD_FRIEND_ROWS = frozenset(list(range(1, 75)) + [246, 247, 248, 249, 250, 251, 252, 254, 255, 256, 257, 258, 259,
                                                   260, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 292,
                                                   294, 295, 297, 299, 300])
GUARD_BASE_ROWS = frozenset({107, 108, 109, 110})
# DRAGON.scr:1158 "Dragons hate everyone": AddEnemy AIBase, every AI class (the guards' friends too: NPC, Animal and Cat
# derive from AIBase). The Dragon King's row (212).
HATE_ALL_ROWS = frozenset({212})
# The reposition modifier (an OpenYAMM addition, not MM9; devdocs/MONSTER_MODIFIERS.md, MM9_MONSTER_AI_PLAN.md
# "Repositioning casters"): the Evil Apprentice, Evil Sorcerer and Evil Grand Sorcerer (EvilSorcerer.scr, the ranged
# holder rows) walk to see a target they lost and back off from a rush, with the modifier's defaults. Placements that
# are holders by their own RangeAttackType 2 keep MM9's holder.
REPOSITION_ROWS = frozenset({156, 157, 158})
HANGING_CLIPS = ('wake_seconds', 'dormant_fidget_seconds')
# A cast sets the spell's own recovery for the caster's mastery (Spell::Cast 0x1008a306: SPELL.txt's Recovery columns,
# Normal, Expert, Master, Grandmaster), not the monster's Recovery, in MM9 game seconds of 33 ms of real time
# (MM9_AI_NATIVE_RE.md section 7.2.1).
SPELL_RECOVERY_COLUMNS = ('RecoveryNorm (sec)', 'RecoveryExp (sec)', 'RecoveryMas (sec)', 'RecoveryGM')
# SPELL.txt's four `Duration (min)` columns, one per mastery (normal, expert, master, grandmaster).
SPELL_DURATION_COLUMN = 'Duration (min)'
# A duration cell: "10 minutes per point in e1", "1 per point in e2", "5 minutes per point of e1", or a plain number.
DURATION_PATTERN = re.compile(r'^\s*(\d+(?:\.\d+)?)\s*(?:minutes?\s*)?(?:per\s+point\s+(?:in|of)\s+(e[12]))?', re.I)
SPELL_MASTERIES = {'n': 0, 'e': 1, 'm': 2, 'g': 3}
GAME_SECOND_SECONDS = 0.033
MONSTER_SPELLS = (('spell1_recovery', 'Spl,Mas,Skil1'), ('spell2_recovery', 'Spl,Mas,Skil2'))
SPAWN_IN_CLIPS = ('spawn_seconds', 'aware_seconds')
ARCHETYPES = ('crawler', 'skirmisher', 'ranged_holder', 'flier', 'swimmer', 'turret', 'civilian', 'guard')
# LOBBERPOD.scr DoEvade: GetRandomFloat 1.8, 2.2 for the wait that ends its evade.
EVADE_SECONDS = {'lobberpod.scr': (1.8, 2.2)}
# WEAPON.txt weapon types a monster's prop shoots with: Attack becomes RangeAttack for a monster holding one
# (MM9_AI_NATIVE_RE.md sections 7.2.3 and 7.3).
RANGED_WEAPON_TYPES = frozenset({'bow', 'crossbow', 'throw', 'wand', 'staff', 'scroll'})
ATTACH_PROP = re.compile(r'^\s*AttachProp\s+"?([^",\s]+)', re.IGNORECASE | re.MULTILINE)

# Whether a script runs an AI loop (devdocs/mm9_rework/monster_ai/PROFILE.md "Placement scripts"). A base include only
# brings the labels: the loop runs once a file of the script's own (the script or a hostility include, not the base
# library that defines the init) calls its init (gosub or goto). A fight loop: BaseInit (BaseMelee.inc, the walkers'
# BaseCrawl), BaseCrawlInit, BaseFlyInit, BaseSwimInit; a loop that only moves (townsfolk, animals, set pieces that
# wander): NPCBaseInit, BaseWanderInit, BaseRunInit, FarmAnimalInit, FarmInitWander, WanderInit.
FIGHT_INITS = ('baseinit', 'basecrawlinit', 'baseflyinit', 'baseswiminit')
MOVE_INITS = ('npcbaseinit', 'basewanderinit', 'baseruninit', 'farmanimalinit', 'farminitwander', 'wanderinit')
FIGHT_INCLUDES = frozenset({'basecrawl.inc', 'basemelee.inc', 'basefly.inc', 'baseswim.inc', 'base.inc',
                            'policeman.inc'})
LABEL = re.compile(r'^:\s*(\w+)', re.MULTILINE)
GOSUB = re.compile(r'\b(?:gosub|goto)\s+(\w+)', re.IGNORECASE)
# RunScript hands the object over to another script: a literal name, or the row's own (GetStatStr <object>,
# ScriptName, <variable>; AutoResurrect.scr, Jumper.inc, IsleOfAshesActor.scr).
RUN_SCRIPT = re.compile(r'^\s*RunScript\s+"?([^"\s]+)"?', re.IGNORECASE | re.MULTILINE)
SCRIPT_NAME_STAT = re.compile(r'GetStatStr\s+\w+\s*,\s*ScriptName\s*,\s*(\w+)', re.IGNORECASE)


# Range.inc's stand-and-shoot mode, assigned by the script itself (`g_rangeAttackType = RANGE_TYPE2` before
# SetupRangeAttackType: EvilSorcerer.scr Main, WizardSummoner.scr LinkToBaseRange; `SetStat ..., RangeAttackType,
# RANGE_TYPE2`: the unused SpellCaster.scr): it never runs after a target (RANGE.inc:291-316), a ranged holder.
RANGE_TYPE2_ASSIGNMENT = re.compile(
    r'g_rangeattacktype\s*(?<![=!<>])=(?!=)\s*range_type2\b|rangeattacktype\s*,\s*range_type2\b')


def assigns_range_type2(script: str, directory: Path = SCRIPT_DIRECTORY) -> bool:
    """Whether the script's own file (not an include: Range.inc only compares with it) sets Range type 2."""
    return bool(RANGE_TYPE2_ASSIGNMENT.search(script_source(script, directory)))


def classify(row_number: int, script: str, chain: frozenset,
             directory: Path = SCRIPT_DIRECTORY) -> tuple[str, str, str]:
    """(archetype, movement, ranged) of a row from its native class and its default script's include chain."""
    swim_fly = row_number in AISWIMFLY_ROWS
    if script in TURRET_SCRIPTS or row_number in LOBBER_ROWS:
        archetype = 'turret'
    elif 'policeman.inc' in chain:
        archetype = 'guard'
    elif 'basefly.inc' in chain:
        archetype = 'flier'
    elif 'baseswim.inc' in chain:
        archetype = 'swimmer'
    elif 'range.inc' in chain and assigns_range_type2(script, directory):
        archetype = 'ranged_holder'
    elif 'basemelee.inc' in chain:
        archetype = 'skirmisher'
    elif 'basecrawl.inc' in chain or 'base.inc' in chain and 'wander.inc' not in chain:
        archetype = 'crawler'
    else:
        # NPCBase.inc townsfolk, the animals (FarmAnimal.inc, wander.inc, cat, dog), the Fish and RailTest
        archetype = 'civilian'

    if archetype == 'swimmer' or swim_fly and archetype == 'civilian':
        movement = 'swim'                   # Jellyspores, Sea Monsters; the Fish in its water volume
    elif swim_fly and archetype != 'turret':
        movement = 'fly'                    # BaseFly fliers; beholders and ghosts hover on the walker loops
    else:
        movement = 'walk'

    ranged = 'none'
    if 'flyrange.inc' in chain:
        ranged = 'flier'
    elif 'range.inc' in chain and script not in RANGE_DISABLED_SCRIPTS:
        ranged = 'walker'
    return archetype, movement, ranged


def number(row: list[str], header: dict[str, int], column: str) -> float:
    try:
        return float(row[header[column]].strip() or 0.0)
    except (ValueError, IndexError):
        return 0.0


def units(value: float) -> int:
    """A LithTech distance or speed in our units."""
    return int(round(value * SCALE))


def attack_reach(row: list[str], header: dict[str, int], bodies: Mm9MonsterBodies, scale: float) -> int:
    """MM9's AI attack range (the AttackRange stat, MM9_AI_NATIVE_RE.md section 7.1): the AttackReach column plus
    1.25 x (the horizontal radius sqrt(x^2 + z^2) - the half depth z) of the object's dims (the model's half extents x
    its scale), in our units."""
    reach = number(row, header, 'AttackReach')
    extents = bodies.model_extents(row[header['ModelName']].strip())
    if extents is not None:
        half_x, _, half_z = (value * scale for value in extents[1])
        reach += 1.25 * (math.hypot(half_x, half_z) - half_z)
    return units(reach)


def layer_clips(model_directory: Path, model_name: str, cache: dict[str, dict]) -> dict:
    """The MM9 model's clips the AI layers need (MM9_MONSTER_AI_PLAN.md phase 4a): Cower (BaseRun.inc's CanCower),
    Resurrect (AICommon.inc's CanBeResurrected) and ResurrectSpell with its DoResurrection key, by the script's
    case-insensitive GetAnimNbr."""
    key = model_name.lower()
    if key not in cache:
        models = {path.name.lower(): path for path in model_directory.glob('*.abc')}
        clips = {}
        if key in models:
            for animation in convert_abc_model.read_abc(models[key]).animations:
                name = animation.name.lower()
                if name in ('cower', 'resurrect', 'resurrectspell', 'launch', 'hangfidget', 'spawn', 'aware',
                            'taunt', 'wakeup') and animation.keyframes:
                    clips.setdefault(name, animation)
        result = {}
        if 'cower' in clips:
            result['cower'] = True
        if 'resurrect' in clips:
            result['raise_seconds'] = round(clips['resurrect'].keyframes[-1].time_ms / 1000.0, 3)
        if 'resurrectspell' in clips:
            spell = clips['resurrectspell']
            keys = [frame.time_ms for frame in spell.keyframes if frame.event.strip().lower() == 'doresurrection']
            if keys:
                result['resurrect_spell_seconds'] = round(spell.keyframes[-1].time_ms / 1000.0, 3)
                result['resurrect_key_seconds'] = round(keys[0] / 1000.0, 3)
        # Phase 4b: a hanging start's Launch and HangFidget (FlyingIcky.scr), a spawn-in's Spawn and Aware (the
        # Aware state plays Taunt on a model without Aware: assumed). mm9_ai_profile keeps those its row uses. A lying
        # start's Wakeup (a coffin's mummy getting up; MummyAwaken.scr plays none, OpenYAMM does: the placement, not
        # the row, says it lies, so every row whose model has one keeps it).
        for field, name in (('wake_seconds', 'launch'), ('dormant_fidget_seconds', 'hangfidget'),
                            ('spawn_seconds', 'spawn'), ('aware_seconds', 'aware' if 'aware' in clips else 'taunt'),
                            ('wakeup_seconds', 'wakeup')):
            if name in clips:
                result[field] = round(clips[name].keyframes[-1].time_ms / 1000.0, 3)
        cache[key] = result
    return cache[key]


def spell_recoveries(path: Path) -> dict[int, list[float]]:
    """SPELL.txt: each spell id's recovery per mastery (game seconds; 0 where the mastery has none)."""
    with open(path, encoding='latin-1', newline='') as file:
        rows = list(csv.reader(file, delimiter='\t'))
    columns = [rows[0].index(name) for name in SPELL_RECOVERY_COLUMNS]
    result = {}
    for row in rows[1:]:
        if row and row[0].strip().isdigit():
            result[int(row[0])] = [float(row[index] or 0) if len(row) > index else 0.0 for index in columns]
    return result


def projectile_blasts(path: Path) -> dict[str, float]:
    """PROJECTILE.txt: each projectile's burst radius (damageRadius, feet: 12 LT each, x 2.56 to our units; the loader
    0x100418a0 scales it by 12), by lower-case name; only those with one."""
    with open(path, encoding='latin-1', newline='') as file:
        rows = list(csv.reader(file, delimiter='\t'))
    column = rows[0].index('damageRadius (ft)')
    result = {}
    for row in rows[1:]:
        if row and row[0].strip() and len(row) > column:
            feet = float_or_zero(row[column])
            if feet > 0.0:
                result[row[0].strip().lower()] = round(feet * 12.0 * 2.56, 1)
    return result


def float_or_zero(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


def missile_blast_items(row: list[str], blasts: dict[str, float]) -> list[str]:
    """missile_blast (devdocs/MONSTER_MODIFIERS.md): the burst radius of the row's attack missiles, as the table
    generator fills its Attack1 and Attack2 missiles (MM9_PROJECTILES_RE.md: every victim in the radius takes the
    attack whole; no falloff)."""
    if len(row) != tables.SOURCE_COLUMN_COUNT:
        return []
    cells = [cell.strip() for cell in row]
    source = int(cells[0])
    if source in tables.MELEE_ONLY_SOURCES:
        return []
    attack1 = tables.source_value(cells, 'attack1_projectile')
    attack2 = tables.source_value(cells, 'attack2_projectile')
    if tables.source_value(cells, 'attack3_projectile') not in {'', '0'}:
        attack2 = tables.source_value(cells, 'attack3_projectile')
    radii = {slot: blasts.get(name.lower(), 0.0) for slot, name in (('attack1', attack1), ('attack2', attack2))}
    radii = {slot: radius for slot, radius in radii.items() if radius > 0.0}
    return [f'{{missile_blast: {flow(radii)}}}'] if radii else []


def spell_durations(path: Path) -> dict[int, list[str]]:
    """SPELL.txt: each spell id's duration cell per mastery (game minutes, as text: "1 minute per point in e1")."""
    with open(path, encoding='latin-1', newline='') as file:
        rows = list(csv.reader(file, delimiter='\t'))
    columns = [index for index, name in enumerate(rows[0]) if name.strip() == SPELL_DURATION_COLUMN]
    if len(columns) != 4:
        raise ValueError(f'{path}: expected four {SPELL_DURATION_COLUMN!r} columns, found {len(columns)}')
    result = {}
    for row in rows[1:]:
        if row and row[0].strip().isdigit():
            result[int(row[0])] = [row[index].strip() if len(row) > index else '' for index in columns]
    return result


def duration_minutes(cell: str, e1: int, e2: int) -> float:
    """A SPELL.txt duration cell in game minutes for the caster's skills (Spell::Duration: [+0xdc] x 60 game seconds,
    plain or times e1 or e2); 0 for none."""
    match = DURATION_PATTERN.match(cell)
    if match is None:
        return 0.0
    minutes = float(match.group(1))
    if match.group(2):
        minutes *= e1 if match.group(2).lower() == 'e1' else e2
    return minutes


def cast_recoveries(row: list[str], header: dict[str, int], recoveries: dict[int, list[float]]) -> dict:
    """The recovery (real seconds) of each spell the row casts (its slot in the generated table: not a spell MM9 never
    casts), when SPELL.txt gives its mastery one."""
    if len(row) != tables.SOURCE_COLUMN_COUNT:
        return {}
    cells = [cell.strip() for cell in row]
    _, spell1, _, spell2 = tables.cast_spells(cells, int(cells[0]))
    result = {}
    for (field, spell_column), cast in zip(MONSTER_SPELLS, (spell1, spell2)):
        if cast is None:
            continue
        parts = [part.strip().lower() for part in row[header[spell_column]].split(',')]
        if len(parts) < 2 or not parts[0].isdigit() or parts[1][:1] not in SPELL_MASTERIES:
            continue
        seconds = recoveries.get(int(parts[0]), [0.0] * 4)[SPELL_MASTERIES[parts[1][:1]]] * GAME_SECOND_SECONDS
        if seconds > 0.0:
            result[field] = round(seconds, 3)
    return result


def script_source(name: str, directory: Path) -> str:
    """A script's text without its comments (';' to the end of the line), lower case; empty when it is missing."""
    path = script_path(name, directory)
    if path is None:
        return ''
    return '\n'.join(line.split(';', 1)[0] for line in path.read_text(encoding='latin-1').splitlines()).lower()


def starts_loop(chain: frozenset, inits: tuple, directory: Path) -> bool:
    """Whether a file of the chain that does not define a base init calls one of `inits`."""
    for name in chain:
        text = script_source(name, directory)
        defined = set(LABEL.findall(text)) & set(FIGHT_INITS + MOVE_INITS)
        if not defined and set(GOSUB.findall(text)) & set(inits):
            return True
    return False


def holds_ranged_weapon(chain: frozenset, directory: Path, weapons: dict[str, str]) -> bool:
    """Whether the chain attaches a prop that WEAPON.txt lists as a ranged weapon (by its model)."""
    for name in chain:
        for model in ATTACH_PROP.findall(script_source(name, directory)):
            model = model.replace('\\', '/').rsplit('/', 1)[-1]
            if weapons.get(model) in RANGED_WEAPON_TYPES:
                return True
    return False


def weapon_types(path: Path) -> dict[str, str]:
    """WEAPON.txt: each weapon model (lower case) -> its Weapon Type (lower case)."""
    if not path.is_file():
        return {}
    with open(path, encoding='latin-1', newline='') as file:
        rows = list(csv.reader(file, delimiter='\t'))
    model, kind = rows[0].index('Model Name'), rows[0].index('Weapon Type')
    return {row[model].strip().lower(): row[kind].strip().lower() for row in rows[1:] if len(row) > kind}


def script_traits(row_number: int, script: str, chain: frozenset, directory: Path, weapons: dict[str, str],
                  moves_only: bool = False) -> dict:
    """The profile fields a script decides (archetype, ranged add-on, family hooks), every one with its value; the
    skirmisher footwork is `footwork` (BaseMelee.inc's strafe attacks and evades). moves_only: the script starts a
    loop that only moves (effective_script), a civilian whatever base includes it brings."""
    archetype, _, ranged = classify(row_number, script, chain, directory)
    fights = not moves_only
    evade = EVADE_SECONDS.get(script, (0.0, 0.0)) if fights else (0.0, 0.0)
    return {
        'archetype': archetype if fights else 'civilian',
        'ranged': ranged if fights else 'none',
        'ranged_weapon': holds_ranged_weapon(chain, directory, weapons),
        'guard_refuge': 'npcbase.inc' in chain,
        'throttle': script not in NO_THROTTLE_SCRIPTS,
        'always_evade': fights and script in ALWAYS_EVADE_SCRIPTS,
        'evade_min_seconds': evade[0],
        'evade_max_seconds': evade[1],
        'melee_window_seconds': MELEE_WINDOW_SCRIPTS.get(script, 0.0) if fights else 0.0,
        'spawn_in': fights and script in SPAWN_IN_SCRIPTS,
        'death_spawn': RUNTIME_ID_BASE + DEATH_SPAWN_SCRIPTS[script] if fights and script in DEATH_SPAWN_SCRIPTS else 0,
        'footwork': fights and 'basemelee.inc' in chain,
    }


def effective_script(script: str, row_script: str, memo: dict, directory: Path,
                     seen: tuple = ()) -> tuple[str, bool] | None:
    """(the script whose loop a placement runs, whether that loop only moves): its own when it starts a fight loop
    (or is a turret script); else the one it hands over to (RunScript: the row's own script when it reads the
    ScriptName stat, else the first literal name); else its own when it starts a loop that only moves (a civilian);
    None when it runs no AI at all (a dialogue or set-piece script, such as Sturmguard.scr)."""
    chain = script_chain(script, memo, directory=directory)
    if script in TURRET_SCRIPTS or (chain & FIGHT_INCLUDES and starts_loop(chain, FIGHT_INITS, directory)):
        return script, False
    handoffs = []
    for name in sorted(chain):
        text = script_source(name, directory)
        stat_variables = set(SCRIPT_NAME_STAT.findall(text))
        handoffs.extend(row_script if target in stat_variables else target
                        for target in RUN_SCRIPT.findall(text))
    handoffs = [name.lower() for name in handoffs if name.lower().endswith('.scr')]
    if row_script in handoffs:
        return row_script, False
    for target in handoffs:
        if target not in seen and target != script and script_path(target, directory) is not None:
            return effective_script(target, row_script, memo, directory, seen + (script,))
    if starts_loop(chain, MOVE_INITS, directory):
        return script, True
    return None


def mm9_ai_profile(row: list[str], header: dict[str, int], chain: frozenset, bodies: Mm9MonsterBodies,
                   clips: dict, recoveries: dict[int, list[float]], traits: dict,
                   directory: Path = SCRIPT_DIRECTORY) -> dict:
    row_number = int(row[0])
    script = row[header['ScriptName']].strip().lower()
    archetype, movement, ranged = classify(row_number, script, chain, directory)
    scale = number(row, header, 'Scale') or 1.0
    profile = {'archetype': archetype}
    if movement != 'walk':
        profile['movement'] = movement
    if ranged != 'none':
        profile['ranged'] = ranged
    profile['attack_reach'] = attack_reach(row, header, bodies, scale)
    # The melee hit sweep: about the attacker's radius + scale x the AttackRange column + the target's radius (7.3)
    profile['melee_sweep'] = units(number(row, header, 'AttackRange') * scale)
    profile['alert_radius'] = units(number(row, header, 'AlertRadius') * scale)
    for key, column in (('walk_speed', 'WalkVelocity'), ('run_speed', 'RunVelocity'), ('fly_speed', 'FlyVelocity'),
                        ('lunge_velocity', 'LungeVelocity')):
        value = units(number(row, header, column))
        if value:
            profile[key] = value
    # `Always Wince? = 1` turns the wince roll off (0x10019e00; the column reads as its opposite): MM9 as it plays
    if row[header['Always Wince?']].strip() == '1':
        profile['wince'] = 'never'
    if number(row, header, 'Resurrect') == 1:
        profile['resurrecter'] = True
    # HeadTurn (the CanHeadTurn stat, 0x10016c20; MM9_AMBIENT_ANIMATION.md 2.4): 0 turns the head toward nothing.
    if row[header['HeadTurn']].strip() != '1':
        profile['head_turn'] = False
    hanging = script in HANGING_SCRIPTS and row_number not in AIRBORNE_ROWS
    profile.update({key: value for key, value in clips.items()
                    if key not in HANGING_CLIPS + SPAWN_IN_CLIPS
                    or key in HANGING_CLIPS and hanging or key in SPAWN_IN_CLIPS and script in SPAWN_IN_SCRIPTS})
    # NPCBase.inc's BaseRunFindHidingPlace: a fleeing townsperson runs to a town guard.
    if traits['guard_refuge']:
        profile['guard_refuge'] = True
    if script in BOSS_SCRIPTS:
        profile['boss'] = True
    if not traits['throttle']:
        profile['throttle'] = False
    if traits['always_evade']:
        profile['always_evade'] = True
    if traits['evade_max_seconds']:
        profile['evade_min_seconds'] = traits['evade_min_seconds']
        profile['evade_max_seconds'] = traits['evade_max_seconds']
    if traits['ranged_weapon']:
        profile['ranged_weapon'] = True
    if row_number in LOBBER_PODS:
        profile['pod_launch'] = RUNTIME_ID_BASE + LOBBER_PODS[row_number]
        profile['pod_cooldown_min'], profile['pod_cooldown_max'] = LOBBER_POD_COOLDOWN
    if traits['melee_window_seconds']:
        profile['melee_window_seconds'] = traits['melee_window_seconds']
    if traits['spawn_in']:
        profile['spawn_in'] = True
    if traits['death_spawn']:
        profile['death_spawn'] = traits['death_spawn']
    if script in HANGING_SCRIPTS and row_number not in AIRBORNE_ROWS:
        profile['dormant_until'], profile['dormant_pose'] = 'disturbed', 'hang'
    profile.update(cast_recoveries(row, header, recoveries))
    return profile


def hit_condition_items(row: list[str], header: dict[str, int], durations: dict[int, list[str]]) -> list[str]:
    """spell_conditions (devdocs/MONSTER_MODIFIERS.md): the condition each cast MM9 debuff leaves (Curse: cursed, Dark
    Grasp: weak, Fear: afraid, Paralyze: paralyzed; MM9_SPELL_MAPPING.md), and how long it lasts: SPELL.txt's duration
    for the cast's mastery and skills (the cell's `Spell,Mastery,e1,e2`), in game minutes."""
    if len(row) != tables.SOURCE_COLUMN_COUNT:
        return []
    cells = [cell.strip() for cell in row]
    conditions = tables.spell_conditions(cells, int(cells[0]))
    if not conditions:
        return []
    for slot, (_, spell_column) in zip(('spell1', 'spell2'), MONSTER_SPELLS):
        if slot not in conditions:
            continue
        parts = [part.strip().lower() for part in re.split(r'[,(]', row[header[spell_column]])]
        if len(parts) < 4 or not parts[0].isdigit() or parts[1][:1] not in SPELL_MASTERIES:
            continue
        e1 = int(parts[2]) if parts[2].isdigit() else 0
        e2 = int(parts[3]) if parts[3].isdigit() else 0
        cell = durations.get(int(parts[0]), [''] * 4)[SPELL_MASTERIES[parts[1][:1]]]
        minutes = duration_minutes(cell, e1, e2)
        if minutes > 0.0:
            conditions[f'{slot}_minutes'] = round(minutes, 3)
    return [f'{{spell_conditions: {flow(conditions)}}}']


def runtime_monster_descriptors(path: Path) -> dict[int, str]:
    descriptors = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        columns = line.split('\t')
        if columns[0].isdigit() and len(columns) > 2:
            descriptors[int(columns[0])] = columns[2].strip()
    return descriptors


def descriptors_with_taunt(path: Path) -> set[str]:
    document = yaml.safe_load(path.read_text(encoding='utf-8'))
    return {entry['descriptor'] for entry in document.get('actors', [])
            if 'taunt' in (entry.get('script_clips') or {})}


def taunt_seconds(model_directory: Path, model_name: str, cache: dict[str, float]) -> float:
    """The length of the model's Taunt clip (taunt, tauntAir, else the first taunt*), 0 without one."""
    key = model_name.lower()
    if key not in cache:
        models = {path.name.lower(): path for path in model_directory.glob('*.abc')}
        cache[key] = 0.0
        if key in models:
            animations = convert_abc_model.read_abc(models[key]).animations
            taunts = [animation for animation in animations if animation.name.lower() in ('taunt', 'tauntair')]
            taunts = taunts or [animation for animation in animations if animation.name.lower().startswith('taunt')]
            if taunts and taunts[0].keyframes:
                cache[key] = taunts[0].keyframes[-1].time_ms / 1000.0
    return cache[key]


def percent(value: str) -> float:
    value = value.strip()
    return round(float(value) / 100.0, 2) if value else 0.0


def flow(values: dict) -> str:
    def scalar(value):
        if isinstance(value, bool):
            return 'true' if value else 'false'
        if isinstance(value, float):
            return f'{value:g}'
        return str(value)
    return '{' + ', '.join(f'{key}: {scalar(value)}' for key, value in values.items()) + '}'


def skirmisher_item(strafe: float, evade: float, taunt: float) -> str:
    parameters = {}
    if strafe != DEFAULT_STRAFE:
        parameters['strafe_attack_chance'] = strafe
    if evade != DEFAULT_EVADE:
        parameters['evade_chance'] = evade
    if taunt > 0.0:
        parameters['taunt_seconds'] = taunt
    return f'{{skirmisher: {flow(parameters)}}}' if parameters else 'skirmisher'


class Mm9Rows:
    """MONSTERS.txt and what the profiles need beside it: the scripts, the models, SPELL.txt, WEAPON.txt and the
    runtime tables of the world."""

    def __init__(self, mm9_root: Path, world: Path):
        self.script_directory = mm9_root / 'SCRIPTS' / 'SCRIPTS'
        self.model_directory = mm9_root / 'MODELS' / 'MODELS'
        self.descriptors = runtime_monster_descriptors(world / 'data_tables' / 'monster_data.txt')
        self.taunting_descriptors = descriptors_with_taunt(world / 'models' / 'actors.yml')
        self.bodies = Mm9MonsterBodies(mm9_root / 'DATA' / 'DATA' / 'MONSTERS.txt', self.model_directory)
        self.recoveries = spell_recoveries(mm9_root / 'DATA' / 'DATA' / 'SPELL.txt')
        self.durations = spell_durations(mm9_root / 'DATA' / 'DATA' / 'SPELL.txt')
        self.blasts = projectile_blasts(mm9_root / 'DATA' / 'DATA' / 'PROJECTILE.txt')
        self.weapons = weapon_types(mm9_root / 'DATA' / 'DATA' / 'WEAPON.txt')
        self.taunt_cache: dict[str, float] = {}
        self.clip_cache: dict[str, dict] = {}
        self.memo: dict[str, frozenset] = {}
        with open(mm9_root / 'DATA' / 'DATA' / 'MONSTERS.txt', encoding='latin-1', newline='') as file:
            rows = list(csv.reader(file, delimiter='\t'))
        self.header = {}
        for index, name in enumerate(rows[0]):
            self.header.setdefault(name, index)     # the first of the doubled names (Projectile2, Att%)
        self.rows = {int(row[0]): row for row in rows[1:]
                     if len(row) > self.header['Strafe Attack Pct'] and row[0].strip().isdigit()}

    def script(self, row: list[str]) -> str:
        return row[self.header['ScriptName']].strip().lower()

    def chain(self, script: str) -> frozenset:
        return script_chain(script, self.memo, directory=self.script_directory)

    def traits(self, row_number: int, script: str, moves_only: bool = False) -> dict:
        return script_traits(row_number, script, self.chain(script), self.script_directory, self.weapons, moves_only)

    def footwork(self, row: list[str]) -> tuple[float, float, float]:
        """(strafe attack chance, evade chance, taunt seconds) of BaseMelee.inc's footwork for this row."""
        taunt = 0.0
        if self.descriptors.get(RUNTIME_ID_BASE + int(row[0])) in self.taunting_descriptors:
            taunt = taunt_seconds(self.model_directory, row[self.header['ModelName']].strip(), self.taunt_cache)
        return (percent(row[self.header['Strafe Attack Pct']]), percent(row[self.header['Evade Chance']]), taunt)


def build_entries(mm9_root: Path, world: Path) -> list[tuple[int, list[str], str]]:
    """(runtime id, its modifier items as YAML flow text, its name) for every MM9 row of the runtime tables."""
    data = Mm9Rows(mm9_root, world)
    entries = []
    for row_number, row in data.rows.items():
        runtime_id = RUNTIME_ID_BASE + row_number
        script = data.script(row)
        if runtime_id not in data.descriptors or not script:
            continue
        chain = data.chain(script)
        traits = data.traits(row_number, script)
        items = []
        if traits['footwork']:
            items.append(skirmisher_item(*data.footwork(row)))
        items.extend(hit_condition_items(row, data.header, data.durations))
        items.extend(missile_blast_items(row, data.blasts))
        if row_number in REPOSITION_ROWS:
            items.append('reposition')
        clips = layer_clips(data.model_directory, row[data.header['ModelName']].strip(), data.clip_cache)
        profile = mm9_ai_profile(row, data.header, chain, data.bodies, clips, data.recoveries, traits,
                                 data.script_directory)
        items.append(f'{{mm9_ai: {flow(profile)}}}')
        entries.append((runtime_id, items, row[data.header['Monster Name']].strip()))
    return entries


_ROWS: Mm9Rows | None = None


def row_script(row_number: int) -> str:
    """A MONSTERS.txt row's own script (lower case, its file name only); empty for an unknown row."""
    global _ROWS
    if _ROWS is None:
        _ROWS = Mm9Rows(REPOSITORY / 'mm9' / 'extracted', REPOSITORY / 'assets_dev' / 'worlds' / 'mm9')
    row = _ROWS.rows.get(row_number)
    return _ROWS.script(row).replace('\\', '/').rsplit('/', 1)[-1] if row is not None else ''


def placement_profile(row_number: int, placement_script: str, boss: bool = False) -> dict:
    """The profile fields a placement's own script decides where they differ from its row's default script
    (MM9_MONSTER_AI_PLAN.md "Which ScriptName wins": the placement's): the scene actor's `mm9_ai` `profile` map, empty
    when the placement runs its row's loop. `passive: true` for a script that runs no AI (never targets, answers no hit
    or call, never attacks), but not for a boss placement, whose Lua behaviour stands in for its script. `skirmisher`:
    false drops the row's footwork, a map gives the row's footwork to a script that adds it. row_number: the placed
    object's MONSTERS.txt row (an NPC's own row also when the converter places it on a stand-in engine row)."""
    global _ROWS
    if _ROWS is None:
        _ROWS = Mm9Rows(REPOSITORY / 'mm9' / 'extracted', REPOSITORY / 'assets_dev' / 'worlds' / 'mm9')
    data = _ROWS
    row = data.rows.get(row_number)
    if row is None or not placement_script:
        return {}
    row_script = data.script(row)
    effective = effective_script(placement_script.lower(), row_script, data.memo, data.script_directory)
    if effective is None:
        return {} if boss else {'passive': True}
    script, moves_only = effective
    if script == row_script:
        return {}
    placed = data.traits(row_number, script, moves_only)
    default = data.traits(row_number, row_script)
    out = {key: value for key, value in placed.items() if key != 'footwork' and value != default[key]}
    if placed['footwork'] != default['footwork']:
        if placed['footwork']:
            strafe, evade, taunt = data.footwork(row)
            out['skirmisher'] = {'strafe_attack_chance': strafe, 'evade_chance': evade, 'taunt_seconds': taunt}
        else:
            out['skirmisher'] = False
    return out


def render(entries: list[tuple[int, list[str], str]]) -> str:
    # Consecutive ids with the same modifiers share one range.
    groups = []
    for entry in entries:
        if groups and groups[-1][-1][0] == entry[0] - 1 and groups[-1][-1][1] == entry[1]:
            groups[-1].append(entry)
        else:
            groups.append([entry])

    lines = [
        '# Generated by tools/mm9_import_discovery/generate_mm9_monster_modifiers.py from MM9 MONSTERS.txt; do not edit.',
        "# mm9_ai: the row's MM9 AI profile (devdocs/mm9_rework/monster_ai/PROFILE.md): archetype from its native",
        '# class and default script, ranged add-on, reach, sweep, alert radius and speeds in our units (LithTech',
        '# x 2.56), wince rule, resurrecter, family hooks and the MM9 model clips the AI layers need (cower, raise_seconds,',
        '# resurrect_spell_seconds and its DoResurrection key).',
        "# skirmisher: MM9's BaseMelee footwork (devdocs/mm9_rework/MM9_ACTOR_ANIMATION_BLENDING_RE.md) for every",
        '# monster whose MM9 script builds on BaseMelee.inc; chances from its Strafe Attack Pct and Evade Chance, the',
        "# taunt from its MM9 model's Taunt clip when its actors.yml binding plays a `taunt` script clip.",
        "# spell_conditions: the condition its cast MM9 debuff leaves (Curse cursed, Dark Grasp weak, Fear afraid,",
        "# Paralyze paralyzed; devdocs/mm9_rework/MM9_SPELL_MAPPING.md).",
        "# reposition: an OpenYAMM addition (not MM9) for the Evil Sorcerer rows: they walk to see a target they lost",
        "# and back off from a rush (devdocs/MONSTER_MODIFIERS.md).",
        'schema: openyamm.monsterModifiers.v1',
        'monsters:',
    ]
    for group in groups:
        first, last = group[0][0], group[-1][0]
        key = str(first) if first == last else f'{first}-{last}'
        names = sorted({entry[2] for entry in group})
        lines.append(f'  {key}:  # {", ".join(names)}')
        lines.extend(f'    - {item}' for item in group[0][1])
    return '\n'.join(lines) + '\n'


def id_ranges(ids: list[int]) -> str:
    """Monster ids as relations.yml writes them: consecutive runs as first-last."""
    parts, start = [], None
    for index, value in enumerate(ids):
        if start is None:
            start = value
        if index + 1 == len(ids) or ids[index + 1] != value + 1:
            parts.append(str(start) if start == value else f'{start}-{value}')
            start = None
    return '[' + ', '.join(parts) + ']'


def render_relations(entries: list[tuple[int, list[str], str]]) -> str:
    """worlds/mm9/relations.yml (devdocs/ENERGY_SHIELDS_AND_RELATIONS.md): MM9's default relation makes every monster
    a friend of every other (IsFriend 0x10018130: friendly unless one is the Player), which the engine table already
    gives rows outside it; the one faction a default script sets is the town guards' (PoliceMan.inc AddEnemy AIBase),
    so the guards and the AIBase rows are at war both ways. The Dragon King (Dragon.scr AddEnemy AIBase) hates the
    monsters and the guards, and the guards him (he is an AIBase); his hatred of the townsfolk and animals is not
    written (a faction of theirs would also change who shares their native alerts)."""
    ids = [runtime_id for runtime_id, _, _ in entries]
    guards = [i for i in ids if i - RUNTIME_ID_BASE in GUARD_BASE_ROWS]
    haters = [i for i in ids if i - RUNTIME_ID_BASE in HATE_ALL_ROWS]
    monsters = [i for i in ids if i - RUNTIME_ID_BASE not in GUARD_BASE_ROWS | GUARD_FRIEND_ROWS | HATE_ALL_ROWS]
    return '\n'.join([
        '# Generated by tools/mm9_import_discovery/generate_mm9_monster_modifiers.py from MM9 MONSTERS.txt and the',
        "# native class table; do not edit. MM9's factions (devdocs/mm9_rework/MM9_MONSTER_AI_PLAN.md phase 4b): monsters",
        '# are friends of each other unless a script sets hate; the town guards (PoliceMan.inc) hate every AIBase class but',
        '# their friends (townsfolk, animals, cats, guards). Map scripts set the rest (evt.SetMonsterRelation).',
        'schema: openyamm.monsterRelations.v1',
        'factions:',
        f'  mm9_guards: {{monsters: {id_ranges(guards)}}}',
        f'  mm9_monsters: {{monsters: {id_ranges(monsters)}}}',
        f'  mm9_dragon: {{monsters: {id_ranges(haters)}}}',
        'relations:',
        '  - {from: mm9_guards, to: mm9_monsters, relation: long}',
        '  - {from: mm9_monsters, to: mm9_guards, relation: long}',
        '  - {from: mm9_guards, to: mm9_dragon, relation: long}',
        '  - {from: mm9_dragon, to: mm9_monsters, relation: long}',
        '  - {from: mm9_dragon, to: mm9_guards, relation: long}',
    ]) + '\n'


def write_replacing(path: Path, text: str) -> None:
    """Replace the file instead of rewriting it in place: hard-linked mirrors of assets_dev keep their version."""
    descriptor, temporary = tempfile.mkstemp(prefix=f'.{path.name}.', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as file:
            file.write(text)
        os.chmod(temporary, 0o664)
        os.replace(temporary, path)
    except BaseException:
        os.unlink(temporary)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--mm9-root', type=Path, default=REPOSITORY / 'mm9' / 'extracted')
    parser.add_argument('--output', type=Path, default=REPOSITORY / 'assets_dev' / 'worlds' / 'mm9' / 'modifiers.yml')
    arguments = parser.parse_args()

    entries = build_entries(arguments.mm9_root, REPOSITORY / 'assets_dev' / 'worlds' / 'mm9')
    write_replacing(arguments.output, render(entries))
    write_replacing(arguments.output.parent / 'relations.yml', render_relations(entries))
    counts: dict[str, int] = {}
    for _, items, _ in entries:
        archetype = re.search(r'archetype: (\w+)', items[-1]).group(1)
        counts[archetype] = counts.get(archetype, 0) + 1
    skirmishers = sum(1 for _, items, _ in entries if items[0].startswith(('skirmisher', '{skirmisher')))
    spell_conditions = sum(1 for _, items, _ in entries if any('spell_conditions' in item for item in items))
    print(f'{arguments.output}: {len(entries)} monsters, {skirmishers} skirmisher footwork, {spell_conditions} '
          f'spell_conditions; archetypes: '
          + ', '.join(f'{name} {counts.get(name, 0)}' for name in ARCHETYPES))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
