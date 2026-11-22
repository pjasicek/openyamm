#!/usr/bin/env python3
"""A5 (2026-11-21, 17th session, D-58): D3's playtest_d7_fall.yml, the landing of D7's E3-F4 fall zone.

A new game on X9 (D7 is not built; START_MAP) with a level-55 party (not immortal) runs A3's Xeen.skyFallTo("d7_ef34") as a map event: the party
is set Xeen.SkyFallHeight (850) over the table's ground z at entrance:d7_fall, (-15360, 11776), falls and takes the
engine's fall damage. The test asserts the landing (xeen_d3.odm, within 256 of the point), every member's HP just after
it (FALL_HP, measured once and hard-coded as X9's), and the same HP after 20 s on D3 (D-54: no ranged hostile within
5,888 of a fall landing). D7 is not built yet: once it is, the start moves to D7's E3-F4 sky and the fall comes from
D7's own fall event (Xeen.skyFallD7)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
import yaml

R = _REPO_ROOT
OUT = f'{R}/devdocs/xeen/briefs/d3/L4/playtest_d7_fall.yml'
LANDING = (-15360, 11776)
LEVEL = 55
# The fall starts on another map: a move onto the map the party is on is a same-map teleport, which drops keepHeight
# (GameApplication's isSameMapTeleport branch: teleportTo without it), so a skyFallTo run on D3 lands with no fall and
# no damage. X9, the Clouds of Xeen, is a sky BLV as D7 will be.
START_MAP = 'xeen_x9.blv'
# Each member's HP just after the fall (Knight, Cleric, Archer, Sorcerer at level 55): measured from the 2026-11-21 runs
# with the table's ground z 1440 (the land there is 1,312, so the fall is 978: 978 x (max HP / 10) / 256 each, from
# 315/142/198/132). A change of the classes' HP, the party's level, the table's z or Xeen.SkyFallHeight changes these.
# 18th session (merge point 26's game, 05:26; A3's table now z 1312): measured again, the same four values.
# [None]: a measuring run (prints `hp show` instead of asserting).
FALL_HP = [197, 89, 126, 83]


def party():
    return {'gold': 0, 'food': 20, 'members': [
        {'name': 'Brokk', 'class': 'Knight', 'level': LEVEL, 'skills': [], 'equipment': {}},
        {'name': 'Hild', 'class': 'Cleric', 'level': LEVEL, 'skills': [], 'equipment': {}},
        {'name': 'Ivar', 'class': 'Archer', 'level': LEVEL, 'skills': [], 'equipment': {}},
        {'name': 'Sefa', 'class': 'Sorcerer', 'level': LEVEL, 'skills': [], 'equipment': {}}]}


def hp_check(label):
    if FALL_HP == [None]:
        return [{'note': label}, {'console': {'line': 'hp show'}}]
    return [{'note': label}] + [{'assert': {'member_points': {'member_index': k, 'health_min': hp, 'health_max': hp}}}
                                for k, hp in enumerate(FALL_HP)]


def fall_lua():
    """A3's fall code, copied from the installed xeen_common.lua when this runs: a scenario's lua_event (and the console's
    `lua`) loads only scripts/common/event_support.lua, not the world's events/common scripts, so `Xeen` is nil there.
    The lines from `Xeen.SkyFallHeight` to the end of `Xeen.skyFallTo` (the SkyFalls table, skyFall, skyFallD7,
    skyFallTo) run as written, then the call. Run this again after A3 changes them."""
    src = open(f'{R}/assets_dev/worlds/xeen/events/common/xeen_common.lua').read()
    start = src.index('Xeen.SkyFallHeight = ')
    body = src.index('function Xeen.skyFallTo(key)', start)
    end = src.index('\nend\n', body) + len('\nend\n')
    code = src[start:end]
    assert 'd7_ef34 = {-15360, 11776,' in code, 'the d7_ef34 row moved: check entrance:d7_fall'
    return ('-- A3\'s Xeen.skyFallTo and its table, from assets_dev/worlds/xeen/events/common/xeen_common.lua\n'
            'local Xeen = {}\n' + code + 'Xeen.skyFallTo("d7_ef34")\n')


def scenario():
    s = [{'note': "D7 is not built yet: the start is a new game on X9 (a sky BLV, as D7) and the fall is A3's skyFallTo "
                  "run as a map event there. Once D7 is built, start on D7 in its E3-F4 sky and walk off its edge "
                  "(Xeen.skyFallD7)."},
         {'new_game_flow': {'start_map': START_MAP, 'party': party()}},
         {'play_lua': {'source': 'wait(3); close()'}},
         {'clear_hostiles': {'radius': 40000}},
         {'console': {'line': 'hp show'}},
         {'note': 'Xeen.skyFallTo("d7_ef34"): A3\'s code, copied in by the generator (lua_event has no world scripts).'},
         {'lua_event': {'source': fall_lua()}},
         # the fall ends within about 3 s, as X9's onto X2
         {'advance_runtime': {'seconds': 3.0, 'follow_map_move': True}},
         {'advance_runtime': {'seconds': 0.5}},
         {'assert': {'map': 'xeen_d3.odm'}},
         {'assert': {'party_position': {'x': LANDING[0], 'y': LANDING[1], 'radius': 256}}}]
    s += hp_check('Just after the fall: everyone alive, the fall\'s damage only')
    s += [{'advance_runtime': {'seconds': 20.0}}, {'assert': {'map': 'xeen_d3.odm'}}]
    s += hp_check('After 20 s on D3 (D-54): nobody has lost a point more')
    return {'id': 'xeen.d3.l4.d7_fall', 'title': "D3 Sandcaster: D7's E3-F4 fall lands outside the south gate, costs "
            'only the fall\'s hit points, and nothing hurts the party for 20 s (D-58, D-54)',
            'world': 'xeen', 'mode': 'faithful', 'steps': s}


def _block(dumper, text):
    style = '|' if '\n' in text else None
    return dumper.represent_scalar('tag:yaml.org,2002:str', text, style=style)


def main():
    yaml.SafeDumper.add_representer(str, _block)
    head = ('# D7\'s E3-F4 fall onto D3 (D-58), written by output/studio_cal/d3/tools/gen_fall.py; do not edit.\n'
            '# A new game on X9 (a sky BLV, as D7) runs Xeen.skyFallTo("d7_ef34"); the party lands at entrance:d7_fall (-15360, 11776),\n'
            '# takes the fall\'s damage (not immortal), and keeps its HP for 20 s (D-54: no ranged hostile within 5,888).\n'
            '# D7 is not built yet: once it is, the start moves to D7\'s E3-F4 sky (Xeen.skyFallD7).\n')
    with open(OUT, 'w') as f:
        f.write(head)
        yaml.safe_dump(scenario(), f, sort_keys=False, allow_unicode=True, width=120)
    print('wrote', OUT, 'FALL_HP', FALL_HP)


if __name__ == '__main__':
    main()
