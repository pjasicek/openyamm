"""The MM9 AI settings of a placed actor (the scene actor's `mm9_ai` map), from its DAT object's properties and its
placement script (`ScriptName` / `ScriptParams`). Shared by the MM9 map converters: the BLV builds
(level_generation/projects/mm9r_common/dungeon/content.py `Content.actor`) and the ODM transcoder
(transcode_mm9_dat_to_odm.py). Field reference: devdocs/mm9_rework/monster_ai/PROFILE.md.

Distances are written in our units (LithTech units x 2.56); points in the map's native frame (the caller's `native`).
Sources: the placed-object properties (MM9_AI_DATA_AND_SCRIPTS.md section 1, MM9_AI_NATIVE_RE.md sections 5, 9, 11)
and the placement script patterns (MM9_AI_DATA_AND_SCRIPTS.md section 4.2).
"""

from __future__ import annotations

import re
import struct
from pathlib import Path
from typing import Callable

from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE as SCALE

REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPT_DIRECTORY = REPOSITORY / 'mm9' / 'extracted' / 'SCRIPTS' / 'SCRIPTS'
INCLUDE = re.compile(r'^\s*#include\s+(\S+)', re.IGNORECASE | re.MULTILINE)

# Placement scripts that start the monster dormant: (what wakes it, how it waits).
DORMANT_SCRIPTS = {
    'mummyawaken.scr': ('trigger', 'coffin'),        # loops "coffin" until the awaken trigger or damage; p1 chains
    'coffinmummy.scr': ('trigger', 'coffin'),        # a Rotter lying in a coffin, not solid, until awaken
    'autoresurrect.scr': ('trigger', 'underground'), # invisible underground, rises on the Resurrect trigger
    'kingkong.scr': ('trigger', 'caged'),            # ForceBreak / ForceFall / ForceAttack break it out (p0: the cage)
    'dp_cagemonster.scr': ('trigger', 'caged'),      # a Terror behind a door (p0) until go
    'klusossleeper.scr': ('trigger', 'sleep'),       # sleeps until damaged or Blackheart dies (no OnFoundTarget)
    'klusoshidden.scr': ('trigger', 'hidden'),       # invisible and not solid until triggered
    'yanmirhidden.scr': ('trigger', 'hidden'),       # Forest Giants that appear once Yanmir (p0) is gone
    'dooksleepgaurd.scr': ('trigger', 'sleep'),      # sleeps until the WakeUp trigger
    'jumper.scr': ('sighted', 'hidden'),             # JUMPER.inc: hidden on a cliff, leaps down at the party
    'll_flyingcreature.scr': ('trigger', 'hang'),    # hangs until Go, then flies its marker list
}
# Placement scripts that walk a marker list: how their params name the markers.
#   list: p0 = the markers' base name, p1 = first index, p2 = last index (ListTraverse.inc)
#   root: p0 = the base name, p1 = the count (markers base0 .. base<count - 1>)
#   names: every param is a marker name
PATH_SCRIPTS = {
    'll_flyingcreature.scr': 'list',
    '1000t_flyingcreature_.scr': 'list',
    'klusospatrol.scr': 'list',
    'honkfollower.scr': 'list',
    'is_fickyflock.scr': 'root',
    'is_ficky.scr': 'root',
    'dp_patrol.scr': 'root',
    'th_lobbyghouls.scr': 'names',
}
# Summoners: how their params name the summon points and which class they call (None: the spawn manager's).
#   list / root as above; class_point: p0 = the class, p1 = the point; point: p1 = the point
SUMMONER_SCRIPTS = {
    'summoner.scr': ('list', None),
    'chasm_ghostspawner.scr': ('list', None),
    'isle_summoner.scr': ('class_point', None),
    'wizardsummoner.scr': ('point', None),
    'wizardmaster.scr': ('point', 'WizardDemon'),
}
# Hostility gates: the *Hostility.inc a placement script includes (friendly until provoked; Dook's guards turn
# hostile once the party comes through the tunnel), and the guard scripts that only help or police.
HOSTILITY_INCLUDES = {
    'monkhostility.inc': ('friendly_until_provoked', 'monk'),
    'dookhostility.inc': ('hostile_after_event', 'dook'),
    'drangheimhostility.inc': ('friendly_until_provoked', 'drangheim'),
    'honkhostility.inc': ('friendly_until_provoked', 'honk'),
    'traininghostility.inc': ('friendly_until_provoked', 'training'),
}
HOSTILITY_SCRIPTS = {
    'guardrude.scr': ('friendly_until_provoked', 'guard'),
    'guardhelp.scr': ('friendly_until_provoked', 'guard'),
}
# Unique boss and set-piece placements (MM9_AI_DATA_AND_SCRIPTS.md section 4.2 "Unique boss fights").
BOSS_SCRIPTS = frozenset({
    'njamfreeze.scr', 'njamtaunt.scr', 'njamchase.scr', 'eborabath.scr', 'eboramines.scr', 'eboraconcubine.scr',
    'yanmirbase.scr', 'thronheimcity_badass.scr', 'ak_giantimp.scr', 'is_killinglich.scr', 'isle_seamon.scr',
})
# GREENPARTY.scr: "simply kill creatures at level launch".
DEAD_SCRIPTS = frozenset({'greenparty.scr'})

# MM9's defaults (the AIBase constructor and BaseWander.inc) for a placement without the property.
DEFAULT_SIGHT = 1320.0
DEFAULT_HEARING = 360.0
DEFAULT_RUNAWAY = 0.25


def script_path(name: str, directory: Path = SCRIPT_DIRECTORY) -> Path | None:
    """The file of a script or include by its case-insensitive name; None when SCRIPTS.REZ has none."""
    key = name.lower().strip('"')
    path = directory / key
    if path.is_file():
        return path
    matches = [p for p in directory.iterdir() if p.name.lower() == key] if directory.is_dir() else []
    return matches[0] if matches else None


def script_chain(name: str, memo: dict[str, frozenset] | None = None, seen: tuple = (),
                 directory: Path = SCRIPT_DIRECTORY) -> frozenset:
    """The script and every file it includes, lower case."""
    memo = {} if memo is None else memo
    key = name.lower().strip('"')
    if key in memo:
        return memo[key]
    result = {key}
    path = script_path(key, directory)
    if path is not None and key not in seen:
        for include in INCLUDE.findall(path.read_text(encoding='latin-1')):
            result |= script_chain(include, memo, seen + (key,), directory)
    memo[key] = frozenset(result)
    return memo[key]


def script_stem(script_name: str) -> str:
    """'scripts\\MummyAwaken.scr' -> 'mummyawaken.scr'."""
    return script_name.replace('\\', '/').rsplit('/', 1)[-1].strip().lower()


def float_property(value) -> float:
    """A DAT property as a float; some float properties are stored as their bit pattern in an int (RangeAttackType
    1.0 = 1065353216)."""
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int) and abs(value) > 1_000_000:
        return struct.unpack('<f', struct.pack('<I', value & 0xFFFFFFFF))[0]
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def units(value: float) -> int:
    return int(round(value * SCALE))


def _marker_names(kind: str, params: list[str]) -> list[str]:
    try:
        if kind == 'list' and len(params) >= 3:
            first, last = sorted((int(params[1]), int(params[2])))
            return [f'{params[0]}{index}' for index in range(first, last + 1)]
        if kind == 'root' and len(params) >= 2:
            return [f'{params[0]}{index}' for index in range(int(params[1]))]
    except ValueError:
        return []
    if kind == 'names':
        return list(params)
    if kind == 'point' and len(params) >= 2:
        return [params[1]]
    if kind == 'class_point' and len(params) >= 2:
        return [params[1]]
    return []


def _points(names: list[str], markers: dict[str, list[float]], native: Callable) -> list[list[int]]:
    return [[int(round(float(v))) for v in native(markers[name.lower()])]
            for name in names if name.lower() in markers]


_ROW_PROFILES: dict[int, dict] = {}


def row_profiles() -> dict[int, dict]:
    """The runtime MM9 rows' mm9_ai profiles from assets_dev/worlds/mm9/modifiers.yml (the generator's output), by id."""
    if not _ROW_PROFILES:
        import yaml
        document = yaml.safe_load((REPOSITORY / 'assets_dev/worlds/mm9/modifiers.yml').read_text())
        for key, items in (document.get('monsters') or {}).items():
            first, _, last = str(key).partition('-')
            for item in items:
                if isinstance(item, dict) and 'mm9_ai' in item:
                    for monster_id in range(int(first), int(last or first) + 1):
                        _ROW_PROFILES[monster_id] = item['mm9_ai']
    return _ROW_PROFILES


def starts_dormant(placement: dict, monster_id: int, properties: dict) -> bool:
    """Whether a placed actor starts dormant in a way the AI wakes by itself (the scene's `dormant`): a placement
    disturbed start (KlusosSleeper.scr), or a row whose own script hangs it (FlyingIcky.scr's Sleep) when the placement
    runs that script and its p0 is not 2 (BeAwake). Trigger starts are wired by each map's converter."""
    if (placement.get('dormant') or {}).get('until') == 'disturbed':
        return True
    row = row_profiles().get(monster_id, {})
    params = str(properties.get('ScriptParams') or '').split()
    return (row.get('dormant_until') == 'disturbed' and not str(properties.get('ScriptName') or '').strip()
            and (not params or params[0] != '2'))


def townsperson_walks(placement: dict) -> bool:
    """Whether a converted townsperson walks (the scene actor's `immobile: false`): one on MM9's own wander
    (NPCBase.inc BaseWanderStartup: an aimless walk, meeting and chatting with other townsfolk, or its marker path)
    with no script of its own. A scripted one waits for its script (Sturmford City's Hatlati walks only on
    NPC48.scr's Wander message; Frosgard City's NPC181-199.scr walkers) and one MM9 gives no wander stands
    (devdocs/mm9_rework/monster_ai/MM9_AMBIENT_ANIMATION.md sections 2.2-2.3). placement: the actor's mm9_ai."""
    return placement.get('wander') in ('aimless', 'path') and not placement.get('script')


# A path marker's clip (AnimationName) as the bindings' role: Fidget1 is the binding's own fidget, the other numbered
# fidgets keep their names, hAttack<n> is attack<n> (the converted models' AttackMelee<n>); anything else lower case.
def marker_clip_role(name: str) -> str:
    key = name.strip().lower()
    if key in ('fidget', 'fidget1'):
        return 'fidget'
    match = re.fullmatch(r'hattack(\d+)', key)
    if match:
        return 'attack_melee' if match.group(1) == '1' else f'attack{match.group(1)}'
    return key


def _path_stops(names: list[str], marker_properties: dict[str, dict], facing: Callable) -> list[dict]:
    """BaseWander.inc OnWanderAtMarkerNext: at each marker of a wander path, the marker's own facing
    (UseMarkerRotation: its Rotation, as the caller's `facing` gives a placement's yaw, degrees), its own wait
    (UseMarkerWaitTime: WanderWaitMin/Max, a 0 read as 0.01) and its clip (AnimationName, looped with LoopAnim)."""
    stops = []
    for index, name in enumerate(names):
        p = marker_properties.get(name.lower())
        if not p:
            continue
        stop: dict = {}
        if float_property(p.get('UseMarkerRotation', 0)) and p.get('Rotation') is not None:
            stop['face'] = round(float(facing(p['Rotation'])) % 360.0, 1)
        if float_property(p.get('UseMarkerWaitTime', 0)):
            low = float_property(p.get('WanderWaitMin', 0)) or 0.01
            high = float_property(p.get('WanderWaitMax', 0)) or 0.01
            stop['wait'] = sorted((round(low, 2), round(high, 2)))
        clip = str(p.get('AnimationName') or '').strip()
        if clip:
            stop['clip'] = marker_clip_role(clip)
            if float_property(p.get('LoopAnim', 0)):
                stop['loop'] = True
        if stop:
            stops.append(dict({'point': index}, **stop))
    return stops


# The animals' own wander rules (the plan's "Animals"). cat.scr and dog.scr (and NjamCameo.scr, the Njam that Dark
# Passageway's SpawnNjamCameo.scr spawns) start BaseWander with BaseWanderForceStartUp whatever WanderON says; wander.inc (pig.scr, hen.scr, rooster.scr) runs its own loop with no
# WanderON check: within MAX_DIST_FROM_STARTPOINT (ScriptParams p0, else 350 LT) of its start, a 5 s tick re-heads it
# 15-90 degrees or pauses it (written as an aimless wander: an approximation); FarmAnimalInit (cow.scr, goat.scr)
# sets WanderWaitMin/Max to 10 and 20 before its BaseWander starts.
FORCED_WANDER_SCRIPTS = frozenset({'cat.scr', 'dog.scr', 'njamcameo.scr'})
TICK_WANDER_LEASH = 350.0
TICK_WANDER_WAIT = [5.0, 5.0]
TICK_WANDER_TIME = [5.0, 10.0]
FARM_ANIMAL_WAIT = [10.0, 20.0]


# A script that starts BaseWander itself (BaseWander.inc's entry labels, or its own copy of one: Shopkeeper.scr).
WANDER_START = re.compile(r'^[^;]*\b(?:gosub|goto)\s+(?:basewanderinit|basewanderstartup|basewanderforcestartup)\b',
                          re.IGNORECASE | re.MULTILINE)
WANDER_FIELDS = ('wander', 'path', 'path_random', 'path_stops', 'wander_leash', 'wander_wait', 'wander_time')


def starts_wander(script: str) -> bool:
    path = script_path(script)
    return path is not None and WANDER_START.search(path.read_text(encoding='latin-1')) is not None


def _wander_path(base: str, markers: dict[str, list[float]]) -> list[str]:
    """BaseWander.inc's path markers: <WanderPathName>0, 1, ... as long as they exist."""
    names = []
    while f'{base}{len(names)}'.lower() in markers:
        names.append(f'{base}{len(names)}')
    return names


def placement_ai(properties: dict, markers: dict[str, list[float]], native: Callable,
                 memo: dict[str, frozenset] | None = None, row: int | None = None,
                 marker_properties: dict[str, dict] | None = None, facing: Callable | None = None) -> dict:
    """The scene actor's `mm9_ai` map for a placed MM9 AI object. properties: its DAT properties (cased names);
    markers: every DAT object's lower-case name -> its LT position; native: LT position -> the map's native
    [x, y, z]; row: its MONSTERS.txt row, whose default script the placement's own script is compared with (the
    `profile` overrides; none without a row); marker_properties: lower-case name -> the DAT properties of each
    object (cased names) and facing: an object's Rotation -> the map's yaw in degrees, for a wander path's stops
    (`path_stops`; none without them)."""
    p = properties
    out: dict = {
        'sight': units(float_property(p.get('SightDistance', DEFAULT_SIGHT))),
        'hearing': units(float_property(p.get('HearingDistance', DEFAULT_HEARING))),
        'runaway_chance': round(float_property(p.get('RunawayChance', DEFAULT_RUNAWAY)), 3),
    }
    if round(float_property(p.get('RangeAttackType', 1.0))) == 2:
        out['ranged_type'] = 2
    if float_property(p.get('CanBeResurrected', 0)):
        out['can_be_resurrected'] = True
    # Named hiding places (HidingPlace0-2): MM9's ShouldRunAway lets only a runner with one flee by morale.
    hiding_names = [str(p.get(f'HidingPlace{index}') or '').strip() for index in range(3)]
    hiding_places = _points([name for name in hiding_names if name], markers, native)
    if hiding_places:
        out['hiding_places'] = hiding_places

    script = script_stem(str(p.get('ScriptName') or ''))
    params = str(p.get('ScriptParams') or '').split()
    path: list[list[int]] = []
    if script in PATH_SCRIPTS:
        path = _points(_marker_names(PATH_SCRIPTS[script], params), markers, native)
    wander_on = bool(float_property(p.get('WanderON', 0)))
    # The script the placement runs: its own, else its row's (an animal's cat.scr, cow.scr, pig.scr).
    effective = script
    if not effective and row is not None:
        from generate_mm9_monster_modifiers import row_script
        effective = row_script(row)
    effective_chain = script_chain(effective, memo) if effective else frozenset()
    tick_wander = 'wander.inc' in effective_chain
    wander_on = wander_on or effective in FORCED_WANDER_SCRIPTS
    stops: list[dict] = []
    if not tick_wander and not path and wander_on and str(p.get('WanderPathName') or '').strip():
        names = [name for name in _wander_path(str(p['WanderPathName']).strip(), markers) if name.lower() in markers]
        path = _points(names, markers, native)
        if path and float_property(p.get('WanderPathRandom', 0)):
            out['path_random'] = True
        if marker_properties is not None and facing is not None:
            stops = _path_stops(names, marker_properties, facing)
    if tick_wander:
        try:
            distance = float(params[0]) if params else 0.0
        except ValueError:
            distance = 0.0
        out['wander'] = 'aimless'
        out['wander_leash'] = units(distance if distance > 0.0 else TICK_WANDER_LEASH)
        out['wander_wait'] = list(TICK_WANDER_WAIT)
        out['wander_time'] = list(TICK_WANDER_TIME)
    elif len(path) >= 2:
        out['wander'] = 'path'
        out['path'] = path
        if stops:
            out['path_stops'] = stops
    elif wander_on:
        out['wander'] = 'aimless'
        leash = float_property(p.get('WanderLeash', 0.0))
        if leash > 0.0:
            out['wander_leash'] = units(leash)
    if 'wander' in out and not tick_wander:
        # BaseWanderStartup reads a 0 as 0.01 s.
        for key, low, high in (('wander_wait', 'WanderWaitMin', 'WanderWaitMax'),
                               ('wander_time', 'WanderTimeMin', 'WanderTimeMax')):
            if low in p and high in p:
                pair = sorted((round(max(float_property(p[low]), 0.01), 2),
                               round(max(float_property(p[high]), 0.01), 2)))
                out[key] = pair
        if 'farmanimal.inc' in effective_chain:
            out['wander_wait'] = list(FARM_ANIMAL_WAIT)

    if not script:
        return out
    chain = script_chain(script, memo)
    if script in DORMANT_SCRIPTS:
        until, pose = DORMANT_SCRIPTS[script]
        out['dormant'] = {'until': until, 'pose': pose}
    hostility = HOSTILITY_SCRIPTS.get(script)
    for include, gate in HOSTILITY_INCLUDES.items():
        if hostility is None and include in chain:
            hostility = gate
    if hostility is not None:
        out['hostility'], out['faction'] = hostility
    if script in SUMMONER_SCRIPTS:
        kind, summon_class = SUMMONER_SCRIPTS[script]
        if kind == 'class_point' and params:
            summon_class = params[0]
        summon: dict = {}
        if summon_class:
            summon['class'] = summon_class
        summon['points'] = _points(_marker_names(kind, params), markers, native)
        out['summon'] = summon
    if script in DEAD_SCRIPTS:
        out['starts_dead'] = True
    if script in BOSS_SCRIPTS:
        out['boss'] = True
    # The placement's script wins over its row's (MM9 runs the placed ScriptName): where it runs a different loop, the
    # profile fields it decides (MM9_MONSTER_AI_PLAN.md "Which ScriptName wins").
    if row is not None:
        from generate_mm9_monster_modifiers import placement_profile
        profile = placement_profile(row, script, script in BOSS_SCRIPTS)
        if profile:
            out['profile'] = profile
        # WanderON only says how BaseWander walks once a script starts it: a placement script that runs no AI loop and
        # never starts it stands (Thjorgard's ScholarPromo.scr Magreeb until it runs off). A patrol script's markers
        # (PATH_SCRIPTS) stay.
        if profile.get('passive') and script not in PATH_SCRIPTS and not tick_wander and not starts_wander(script):
            for key in WANDER_FIELDS:
                out.pop(key, None)
    out['script'] = script
    if params:
        out['script_params'] = ' '.join(params)
    return out
