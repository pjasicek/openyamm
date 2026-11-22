#!/usr/bin/env python3
"""XD-17 Shangri-La: writes the L4 playtests (A5, 2026-11-21) from places_l2.py and the town file.

    playtest.yml            the walk: out of the cave mouth, every house door clicked (its screen, then Escape), the
                            pyramid refused before m30, the well twice (the gift, then the water), the crystal
    playtest_exit_xd16.yml  the throat's back to XD-16's entrance:xd17_way
    playtest_exit_x7.yml    the back passage and the rockfall to X7's entrance:xd17_cleft, cleft_open set
    playtest_hostility.yml  Lacey and Stumpy peaceful, nothing hostile
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import places_l2 as L  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'devdocs/xeen/briefs/xd17/L4'
M = 'xeen_xd17.blv'
TOWN = yaml.safe_load(open(ROOT / 'assets_dev/worlds/xeen/source/towns/xd17.yml'))
HOUSES = {h['id']: h for h in TOWN['houses']}
_res = {}
for _l in open(_REPO_ROOT + '/assets_dev/worlds/xeen/data_tables/npc.txt', encoding='latin-1'):
    _c = _l.rstrip('\n').split('\t')
    if len(_c) > 6 and _c[0].isdigit() and _c[6].isdigit() and int(_c[6]) in HOUSES:
        _res.setdefault(int(_c[6]), []).append(int(_c[0]))
_kind = {}
for _l in open(_REPO_ROOT + '/assets_dev/worlds/xeen/data_tables/house_animations.txt', encoding='latin-1'):
    _c = _l.rstrip('\n').split('\t')
    if _c and _c[0].isdigit():
        _kind[int(_c[0])] = _c[-1]
RESIDENT = {h: r[0] for h, r in _res.items() if len(r) == 1 and _kind.get(h) == 'House'}
YAW = {'e': math.pi, 'w': 0.0, 'n': -math.pi / 2, 's': math.pi / 2}     # facing a door whose front looks that way
NORMAL = {'e': (1, 0), 'w': (-1, 0), 'n': (0, 1), 's': (0, -1)}


def head(tid, title):
    return {
        'id': tid, 'title': title, 'world': 'xeen', 'mode': 'faithful',
        'steps': [
            {'new_game_flow': {'start_map': M, 'party': {'gold': 0, 'food': 20, 'members': [
                {'name': 'Brokk', 'class': 'Knight', 'level': 48, 'skills': [], 'equipment': {}},
                {'name': 'Hild', 'class': 'Cleric', 'level': 48, 'skills': [], 'equipment': {}},
                {'name': 'Ivar', 'class': 'Archer', 'level': 48, 'skills': [], 'equipment': {}},
                {'name': 'Sefa', 'class': 'Sorcerer', 'level': 48, 'skills': [], 'equipment': {}}]}}},
            {'assert': {'map': M}},
            {'setup_shortcut': {'kind': 'immortal', 'value': True}},
            {'advance_runtime': {'seconds': 2.5, 'present_dialogs': True}},
        ]}


def floor_at(x, y):
    for t in L.TERRACES.values():
        x0, y0, x1, y1 = t['top']
        if x0 <= x <= x1 and y0 <= y <= y1:
            return t['h']
    return 0


class Walk:
    def __init__(self, steps):
        self.s = steps

    def note(self, text):
        self.s.append({'note': text})

    def to(self, *pts, timeout=90):
        for (x, y) in pts:
            self.s.append({'walk_to': {'x': x, 'y': y, 'z': floor_at(x, y), 'z_tolerance': 400, 'radius': 96,
                                       'timeout_seconds': timeout, 'close_dialogs': True}})

    def face(self, x, y, yaw, pitch=0.0):
        self.s.append({'set_pose': {'map': M, 'x': x, 'y': y, 'z': floor_at(x, y), 'yaw': round(yaw, 4),
                                    'pitch': pitch}})
        self.s.append({'advance_runtime': {'seconds': 0.5}})

    def click(self):
        self.s.append({'press_interact': {'expect': {'kind': 'event_target'}}})
        self.s.append({'advance_runtime': {'seconds': 0.6}})

    def close(self):
        self.s.append({'press_action': {'action': 'escape'}})
        self.s.append({'advance_runtime': {'seconds': 0.4}})
        self.s.append({'play_lua': {'source': 'close(); wait(0.2)'}})

    def door(self, aid, via=()):
        b = [b for b in L.BUILDINGS for d in b['doors'] if d[0] == aid][0]
        d = [d for d in b['doors'] if d[0] == aid][0]
        house, (dx, dy), face = d[1], d[3], d[4]
        nx, ny = NORMAL[face]
        sx, sy = dx + nx * 192, dy + ny * 192
        self.note(f"{b['name']} ({aid}, house {house}): walk to its door and open it")
        self.to(*via, (sx, sy))
        self.face(sx, sy, YAW[face])
        self.click()
        assert house in HOUSES, house
        # a house with one resident and no service opens on the resident (A4's npc.txt, 06:05: Martok and the others)
        self.s.append({'assert': {'dialog': {'active': True, 'source_id': RESIDENT.get(house, house)}}})
        self.close()


def walk():
    t = head('xeen.xd17.l4.walk', 'Shangri-La (XD-17 L4): the valley walked, every door opened, the well, the pyramid, '
                                  'the crystal')
    s = t['steps']
    s.append({'assert': {'dialog': {'active': True, 'text_contains': 'Green grass, still air and a clear sky'}}})
    s.append({'play_lua': {'source': 'close(); wait(0.3)'}})
    ax, ay = L.XD16_ARRIVAL
    s.append({'assert': {'party_position': {'x': ax, 'y': ay, 'radius': 96, 'z_min': -40, 'z_max': 60}}})
    w = Walk(s)
    w.to((-1280, -4100))
    w.door('door:tavern_xanadu')
    w.door('door:arm_and_hammer_arms', via=[(-640, -3200)])
    w.door('door:arm_and_hammer_armour')
    w.door('door:martok', via=[(-1280, -2480), (-3712, -2480)])
    w.door('door:benedict', via=[(-3712, -2480), (-1280, -2480), (-1280, -1920)])
    w.door('door:public_library', via=[(-1280, -1920), (-1280, -1280), (-2560, -1280), (-3264, -1280)])
    w.door('door:earth_temple', via=[(-3264, -1280), (-2560, -1280), (-1280, -1280), (-1280, 704), (-3456, 704),
                                     (-4288, 704)])
    w.door('door:an_education', via=[(-4288, 704), (-3456, 704), (-1280, 704), (-1280, 1344)])
    w.door('door:maurice', via=[(-1280, 1792), (-1664, 1792)])
    w.door('door:alexander', via=[(-1664, 1792), (1280, 1792)])
    # the pyramid: refused before m30.done
    w.note('The travel pyramid: refused before M30 (aaze0049:25)')
    w.to((1280, 1792), (0, 1792), (0, 2368), (0, 3072), (0, 3360))
    w.face(0, 3360, math.pi / 2)
    w.click()
    s.append({'assert': {'dialog': {'active': True, 'text_contains': 'The moons are not aligned'}}})
    w.close()
    s.append({'assert': {'map': M}})
    # with M30 done the pyramid carries the party to D6 outside Castle Alamar's gate, and D6's pyramid back
    w.note("M30 done: the pyramid to D6's entrance:xd17_pyramid, and D6's pyramid (its event 41) back here")
    s.append({'console': {'line': 'qbit set 111600'}})
    w.face(0, 3360, math.pi / 2)
    s.append({'press_interact': {'expect': {'kind': 'event_target'}}})
    s.append({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    s.append({'assert': {'map': 'xeen_d6.odm'}})
    s.append({'advance_runtime': {'seconds': 1.0, 'present_dialogs': True}})
    s.append({'play_lua': {'source': 'close(); wait(0.3)'}})
    s.append({'assert': {'party_position': {'x': -5120, 'y': 1024, 'radius': 192, 'z_min': 1700, 'z_max': 2000}}})
    s.append({'execute_event': {'id': 41}})
    s.append({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    s.append({'assert': {'map': M}})
    s.append({'advance_runtime': {'seconds': 1.0}})
    px, py, pz = L.PYRAMID_ARRIVAL
    s.append({'assert': {'party_position': {'x': px, 'y': py, 'radius': 160, 'z_min': pz - 40, 'z_max': pz + 60}}})
    w.door('door:murray', via=[(1792, 3360)])
    w.door('door:guild_light', via=[(1792, 3360), (0, 3360), (0, 3072), (0, 2368), (0, 1792), (1280, 1792),
                                    (1280, 1152), (3200, 1152)])
    w.door('door:pilar', via=[(3200, 1152), (3840, 1152), (3840, 3168)])
    w.door('door:sally', via=[(3840, 3168), (3840, 1152), (1280, 1152), (1280, -1280)])
    w.door('door:elona', via=[(1280, -1280), (1280, -1792), (2560, -1792)])
    # the well: the gift once per character, then the water
    w.note("The well (A3's xd17.well): 20,000 experience and the award Found Shangri-La, then the water")
    w.to((2560, -1792), (1280, -1792), (1280, 0), (320, 0))
    w.face(320, 0, math.pi, -0.25)
    w.click()
    # F13 / D-90 (A5 s29): the well's lines are status lines now (A3's hooks), or a window: either
    s.append({'play_lua': {'source': "local s = status(); local w = close(); if not w and not string.find(s, 'Congratulations, You', 1, true) "
                                     "then error('no line: ' .. s) end"}})
    s.append({'assert': {'award_acquired': [{'id': 421, 'member_index': 0}]}})
    w.face(320, 0, math.pi, -0.25)
    w.click()
    # F13 / D-90 (A5 s29): the well's lines are status lines now (A3's hooks), or a window: either
    s.append({'play_lua': {'source': "local s = status(); local w = close(); if not w and not string.find(s, 'The water is cool an', 1, true) "
                                     "then error('no line: ' .. s) end"}})
    # Lacey by the well and Stumpy in the orchard talk as their NPCs (A4's greetings; studio monsters[].npc)
    w.note('Lacey (actor 0, NPC 4719) by the well: her greeting')
    s.append({'interact_actor': {'actor_index': 0}})
    s.append({'advance_runtime': {'seconds': 0.6}})
    s.append({'assert': {'dialog': {'active': True, 'text_contains': 'The moons will align when you are able to visit '
                                                                     'the Darkside.'}}})
    w.close()
    w.note('Stumpy (actor 1, NPC 4718) in the orchard: his greeting')
    w.to((1280, 0), (1280, -1792), (2560, -1792), (2560, -2176), (3584, -2176), (4300, -2176))
    w.face(4300, -2176, -0.39)
    s.append({'interact_actor': {'actor_index': 1}})
    s.append({'advance_runtime': {'seconds': 0.6}})
    s.append({'assert': {'dialog': {'active': True, 'text_contains': 'the druids can help you'}}})
    w.close()
    w.to((3584, -2176), (2560, -2176), (2560, -1792), (1280, -1792), (1280, 0))
    # the crystal by the cave mouth
    w.note("The hidden crystal in the bluff by the cave mouth (A3's xd17.crystal)")
    w.to((1280, 0), (1280, -1792), (-1280, -1792), (-1280, -4736), (L.CRYSTAL_X, -5056))
    w.face(L.CRYSTAL_X, -5056, -math.pi / 2, 0.0)
    w.click()
    s.append({'assert': {'dialog': {'active': True, 'text_contains': 'broadcast to millions'}}})
    w.close()
    s.append({'assert': {'map': M}})
    return t


def exit_xd16():
    t = head('xeen.xd17.l4.exit_xd16', "Shangri-La (XD-17 L4): the cave throat's back to XD-16's cool passage")
    s = t['steps']
    s.append({'play_lua': {'source': 'close(); wait(0.3)'}})
    w = Walk(s)
    w.to((-1280, -5150), (-1280, -5560), (-1280, -5820))
    w.face(-1280, -5820, -math.pi / 2)
    s.append({'press_interact': {'expect': {'kind': 'event_target'}}})
    # F16 (merge point 40; A5 s29): a dungeon to a dungeon shows the standard entrance window; OK
    s.append({'advance_runtime': {'seconds': 0.3, 'present_dialogs': True}})
    s.append({'assert': {'dialog': {'active': True, 'action_label_present': 'OK'}}})
    s.append({'select_topic': {'match_label': 'OK'}})
    s.append({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    s.append({'assert': {'map': 'xeen_xd16.blv'}})
    s.append({'advance_runtime': {'seconds': 1.0}})
    s.append({'assert': {'party_position': {'x': 4864, 'y': -18176, 'radius': 160, 'z_min': -1340, 'z_max': -1200}}})
    return t


def exit_x7():
    t = head('xeen.xd17.l4.exit_x7', 'Shangri-La (XD-17 L4): the back passage and the rockfall out to X7, the cleft '
                                     'opened')
    s = t['steps']
    s.append({'play_lua': {'source': 'close(); wait(0.3)'}})
    s.append({'assert': {'qbit_clear': [116140]}})
    w = Walk(s)
    w.to((-1280, -1792), (-1280, 1792), (-1664, 1792), (-1664, 3456), (-5120, 3456), (-5440, 3540),
         (-5900, 3920), (-6200, 4140), (-7000, 4230), (-7400, 4230), timeout=120)
    w.face(-7400, 4230, math.pi)
    s.append({'press_interact': {'expect': {'kind': 'event_target'}}})
    s.append({'advance_runtime': {'seconds': 0.8, 'present_dialogs': True}})
    s.append({'select_topic': {'match_label': 'OK'}})
    s.append({'advance_runtime': {'seconds': 1.5, 'follow_map_move': True}})
    s.append({'assert': {'map': 'xeen_x7.odm'}})
    s.append({'advance_runtime': {'seconds': 1.0}})
    x, y, z = L.X7_CLEFT_POINT
    s.append({'assert': {'party_position': {'x': x, 'y': y, 'radius': 192, 'z_min': z - 160, 'z_max': z + 200}}})
    s.append({'assert': {'qbit_set': [116140]}})
    return t


def hostility():
    t = head('xeen.xd17.l4.hostility', 'Shangri-La (XD-17 L4): Lacey and Stumpy peaceful, nothing hostile')
    s = t['steps']
    s.append({'play_lua': {'source': 'close(); wait(0.3)'}})
    for mid in (L.LACEY_MONSTER, L.STUMPY_MONSTER):
        s.append({'assert': {'actor_count': {'monster_id': mid, 'hostile': False, 'min': 1, 'max': 1}}})
        s.append({'assert': {'actor_count': {'monster_id': mid, 'hostile': True, 'max': 0}}})
    s.append({'assert': {'actor_count': {'hostile': True, 'max': 0}}})
    s.append({'advance_runtime': {'seconds': 20}})
    s.append({'reload': {}})
    s.append({'advance_runtime': {'seconds': 2, 'present_dialogs': True}})
    s.append({'play_lua': {'source': 'close(); wait(0.3)'}})
    for mid in (L.LACEY_MONSTER, L.STUMPY_MONSTER):
        s.append({'assert': {'actor_count': {'monster_id': mid, 'hostile': False, 'min': 1, 'max': 1}}})
    s.append({'assert': {'actor_count': {'hostile': True, 'max': 0}}})
    s.append({'assert': {'map': M}})
    return t


def dump(name, t, comment):
    text = '\n'.join('# ' + line for line in comment.splitlines()) + '\n'
    text += yaml.safe_dump(t, sort_keys=False, width=118, allow_unicode=True)
    (OUT / name).write_text(text)


if __name__ == '__main__':
    gen = 'Written by output/studio_cal/xd17/tools/gen_playtests.py (A5, 2026-11-21); run with output/studio_cal/xd17/run.sh.'
    dump('playtest.yml', walk(), "XD-17 Shangri-La: the walk. Every house door is clicked from in front of it (A4's\n"
         "houses 4351-4365), its screen asserted and closed with Escape; the pyramid refuses before m30.done; the\n"
         "well gives its award once, then the water; the crystal speaks.\n" + gen)
    dump('playtest_exit_xd16.yml', exit_xd16(), "XD-17: the throat's back (the exit preset, the game's leave window) to\n"
         "XD-16's entrance:xd17_way. XD-16's own way back is A7's (sealed until XD-17 is installed).\n" + gen)
    dump('playtest_exit_x7.yml', exit_x7(), "XD-17: the back passage to the rockfall (the exit preset) and out to X7's\n"
         "entrance:xd17_cleft; A3's xd17.cleft_opened sets cleft_open 116140. X7's door back in is not open yet.\n" + gen)
    dump('playtest_hostility.yml', hostility(), "XD-17: Lacey (11915) and Stumpy (11916) peaceful, no hostile actor, also\n"
         "after a save and load.\n" + gen)
    print('written playtests')
