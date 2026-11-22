#!/usr/bin/env python3
"""P4's L4 playtests (A6, seventeenth session, 2026-11-21; after P2's), from the build's scene (the guardians'
indices): the walk, hostility, the test (and a save and reload), the P-2 proof (straight into the Veil, and from the
sea against the Veil's colonnade and the Grotto's rim), and the water (D-58 P4 Q1): swimming at the surface costs no
breath over 20 s, an edge band's current carries the party inward, a flight of steps takes a swimmer out onto a walk.
Run with output/studio_cal/p4/run.sh.

    python3 level_generation/projects/xeen/p4/gen_playtests.py
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math
import os
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen  # noqa: E402
sys.path.insert(0, str(pathlib.Path(_REPO_ROOT, 'level_generation/projects/xeen/common/planes')))
import pieces as PC  # noqa: E402

L4 = gen.BRIEF / 'L4'
BUILD = pathlib.Path(_REPO_ROOT, 'output/studio_cal/p4') / 'build'
MAP = 'xeen_p4.blv'
SCENE = yaml.safe_load(open(BUILD / 'xeen_p4.scene.yml'))
ACTORS = SCENE['initial_state']['actors']
GUARDS = [i for i, a in enumerate(ACTORS) if a.get('group') == gen.GUARD_GROUP]
ARRIVAL = gen.PLACE['entrance:d7_fall']['at']
COURT = gen.ARENA_FL
GX, GY = gen.GATE_X, gen.GATE_Y
FRONT = (GX, GY + 420)                      # on the court, facing the Veil
LEVEL = 60
PROBE = os.environ.get('P4_PROBE') == '1'
# measured end points (P4_PROBE=1 runs print them; then fixed here)
CURRENT_END = None
SURF_Z = int(os.environ.get('P4_SURF_Z', '-197'))     # the feet of a party held at the surface (probed)


def party():
    names = [('Brokk', 'Knight'), ('Hild', 'Cleric'), ('Ivar', 'Archer'), ('Sefa', 'Sorcerer')]
    return {'gold': 0, 'food': 20, 'members': [{'name': n, 'class': c, 'level': LEVEL, 'skills': [], 'equipment': {}}
                                               for n, c in names]}


def head(immortal=True):
    s = [{'new_game_flow': {'start_map': MAP, 'party': party()}}]
    if immortal:
        s.append({'setup_shortcut': {'kind': 'immortal', 'value': True}})
    s += [{'play_lua': {'source': 'wait(2); close()'}}, {'assert': {'map': MAP}}]
    return s


def walk(x, y, z, radius=128, timeout=60, clear=1500, ztol=160):
    return {'walk_to': {'x': int(x), 'y': int(y), 'z': int(z), 'z_tolerance': ztol, 'radius': radius,
                        'timeout_seconds': timeout, 'clear_hostiles': clear, 'close_dialogs': True}}


def lua(src):
    return {'play_lua': {'source': src}}


def pose(x, y, z, yaw=0):
    return {'set_pose': {'map': MAP, 'x': int(x), 'y': int(y), 'z': int(z), 'yaw_degrees': yaw, 'pitch': 0}}


def at(x, y, r, zmin, zmax):
    return {'assert': {'party_position': {'x': int(x), 'y': int(y), 'radius': int(r), 'z_min': int(zmin),
                                          'z_max': int(zmax)}}}


def seg(x, y, z, yaw, seconds, inp='forward', **kw):
    e = {'input': inp, 'seconds': seconds, 'actor_collision': True, 'actor_ai': False,
         'start': {'map': MAP, 'x': int(x), 'y': int(y), 'z': int(z), 'yaw_degrees': yaw, 'pitch': 0},
         'expect_stop': {'map': MAP, 'x': int(x), 'y': int(y), 'z': int(z), 'yaw_degrees': yaw, 'pitch': 0},
         'loose_tolerance': True, 'tolerance_xy': 40000, 'tolerance_z': 8000}
    e.update(kw)
    return {'movement_segment': e}


def surface(x, y, yaw=0):
    """Into the sea under (x, y) and up to its surface (Fly Up held, Verhoffin's route)."""
    return [seg(x, y, -420, yaw, 2.5, inp='none', fly_up=True, actor_collision=False),
            {'assert': {'water': {'state': 'surface', 'eye_under': False, 'breath_min': 0.99}}}]


def water(state=None, **kw):
    w = dict(kw)
    if state:
        w['state'] = state
    return {'assert': {'water': w}}


def write(name, title, comment, steps):
    doc = {'id': f'xeen.p4.l4.{name}', 'title': f'Plane of Water (P4): {title}', 'world': 'xeen', 'mode': 'faithful',
           'steps': steps}
    path = L4 / (f'playtest_{name}.yml' if name != 'walk' else 'playtest.yml')
    with open(path, 'w') as f:
        f.write(f'# {comment}\n# Written by output/studio_cal/p4/tools/gen_playtests.py; run with --world xeen --map '
                f'{MAP}.\n')
        yaml.safe_dump(doc, f, sort_keys=False, width=120, allow_unicode=True)


def veil_holds():
    """Straight south into the Veil from the court: the party stops north of it."""
    return [seg(FRONT[0], FRONT[1], COURT, -90, 3.0),
            at(GX, GY + 110, 120, COURT - 8, COURT + 16)]


def through_veil():
    """Through the stilled Veil, along its colonnade into the Grotto."""
    cy = gen.CHAMBER['at'][1]
    return [walk(FRONT[0], FRONT[1], COURT, clear=0), walk(GX, GY - 700, COURT + 20, clear=0),
            walk(GX, gen.GATE_Q[1] + 400, gen.CHAMBER_FL, clear=0, timeout=90),
            walk(GX + 300, cy + 500, gen.CHAMBER_FL, clear=0),
            at(GX + 300, cy + 500, 200, gen.CHAMBER_FL - 8, gen.CHAMBER_FL + 24)]


def pt(link_id, t):
    l = next(x for x in gen.D['links'] if x['id'] == link_id)
    p, q = gen.PL.link_ends(l)
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t), gen.slab_z(l, (p[0] + (q[0] - p[0]) * t,
                                                                                  p[1] + (q[1] - p[1]) * t))


def clear_band_y():
    """A y in the east band where the run inward from the wall meets no stack or terrace."""
    solid = [gen.foot(p) for p in gen.ROOMS['rooms'][0]['platforms'] if p.get('solid') is not False
             and p['id'] != 'platform:sea']
    for y in sorted(range(-3000, 3001, 128), key=abs):
        pts = [(x, y) for x in range(4200, 6500, 64)]
        if all(not gen.PG.point_in(q, f) and gen.poly_dist_outline(q, f) > 260 for q in pts for f in solid):
            return y
    raise SystemExit('no clear run in the east band')


def main():
    # the walk: arrival, the north-east colonnade, round the fountain, the west colonnade, the court, the Veil shut
    s = head()
    s.append(at(ARRIVAL[0], ARRIVAL[1], 96, -8, 40))
    s.append({'note': 'Along the north-east colonnade to the Sea Statue (S: the statue, blocked; its plinth stands).'})
    for t in (0.0, 0.35, 0.7, 1.0):
        (x, y), z = pt('link:walk_ne', t)
        s.append(walk(x, y, z))
    sx, sy = gen.STATUE
    s.append({'note': 'Round the fountain on its north side, then the west colonnade to the Whirlpool Court.'})
    s += [walk(sx + 500, sy + 760, 32), walk(sx - 500, sy + 760, 32)]
    for t in (0.0, 0.4, 0.8, 1.0):
        (x, y), z = pt('link:walk_w', t)
        s.append(walk(x, y, z))
    s += [walk(-3300, 1000, COURT), walk(*FRONT, COURT)]
    s.append({'note': 'The Veil holds before the test.'})
    s += veil_holds()
    write('walk', "arrival, the colonnades, the statue's forecourt, the Whirlpool Court; the Veil holds before the test",
          'The walk (D-58): arrival, the statue, the court, the Veil shut before the test.', s)

    # hostility
    s = head()
    s.append({'advance_runtime': {'seconds': 2}})
    s.append({'assert': {'actor_count': {'hostile': True, 'min': 27}}})
    for i in GUARDS:
        s.append({'assert': {'actor_visible': {'actor_index': i, 'hidden': True}}})
    s.append({'advance_runtime': {'seconds': 6}})
    s.append(at(ARRIVAL[0], ARRIVAL[1], 96, -8, 40))
    write('hostility', "27 hostiles placed, the test's three hidden, a quiet arrival",
          'Hostility: the field groups hostile, the guardians hidden until the test.', s)

    # the test
    plate = gen.TEST_PLATE
    s = head()
    s += [pose(plate[0] + 360, plate[1], COURT + 8, 180), {'clear_hostiles': {'radius': 3000}},
          {'advance_runtime': {'seconds': 1}}]
    for i in GUARDS:
        s.append({'assert': {'actor_visible': {'actor_index': i, 'hidden': True}}})
    s.append({'note': "Onto the test's floor: 'Accept the test of Water?' Yes."})
    s += [{'walk_to': {'x': plate[0], 'y': plate[1], 'z': COURT + 4, 'z_tolerance': 60, 'radius': 48,
                       'timeout_seconds': 20, 'expect': 'dialog'}},
          {'answer_input': {'text': 'Yes'}}, {'advance_runtime': {'seconds': 1.5}},
          lua("close(); wait(0.5); close()")]
    for i in GUARDS:
        s.append({'assert': {'actor_visible': {'actor_index': i, 'hidden': False}}})
    s.append(lua(f"if qbit({gen.TEST_QBIT}) then error('the test qbit is set before the guardians die') end"))
    s.append({'note': 'Before the kill the Veil still holds.'})
    s += veil_holds()
    s.append({'note': 'The three guardians die (the scenario strikes them): Xeen.planeTestCheck sets 111767.'})
    for i in GUARDS:
        s.append({'damage_actor': {'actor_index': i, 'amount': 1000000}})
    s += [{'advance_runtime': {'seconds': 3}}, lua('close(); wait(0.5); close()'),
          lua(f"if not qbit({gen.TEST_QBIT}) then error('qbit {gen.TEST_QBIT} not set after the kill') end"),
          {'advance_runtime': {'seconds': 2}}, lua('close(); wait(0.5); close()')]
    s.append({'note': "The Veil stilled: along its colonnade into the Sleeper's Grotto."})
    s += through_veil()
    s.append({'note': 'A save and a reload: the qbit kept, the guardians dead; the Veil passable again.'})
    s += [{'reload': {}}, {'advance_runtime': {'seconds': 2}},
          lua(f"if not qbit({gen.TEST_QBIT}) then error('qbit lost') end"), pose(*FRONT, COURT + 8, -90),
          {'advance_runtime': {'seconds': 1}}]
    for i in GUARDS:
        s.append({'assert': {'actor_visible': {'actor_index': i, 'dead': True}}})
    s += through_veil()
    write('test', 'the test raises the guardians, their deaths set 111767 and still the Veil, kept over a reload',
          'The test (D-58 C3, C4, P-1).', s)

    # P-2: straight into the Veil; off the court beside each flank into the sea, then against the Veil's colonnade;
    # from the sea against the Grotto's rim: the party stays in the water (z under 40), never on the walk (132+)
    s = head()
    s += [{'clear_hostiles': {'radius': 40000}}]
    s.append({'note': 'Straight into the Veil: the party stays on the court.'})
    s += veil_holds()
    for k, sgn in enumerate((-1, 1)):
        x0 = GX + sgn * 900
        s.append({'note': f"Off the court {'west' if sgn < 0 else 'east'} of the flank, into the sea, then swimming "
                          "at the Veil's colonnade: it stands 196 and more over the water."})
        s += [seg(x0, GY + 300, COURT, -90, 4.0), {'advance_runtime': {'seconds': 2.0}},
              at(x0, GY - 900, 900, -1100, 40)]
        s += [seg(x0, GY - 1300, -420, 0 if sgn < 0 else 180, 1.0, inp='none', fly_up=True, actor_collision=False),
              seg(x0, GY - 1300, SURF_Z, 0 if sgn < 0 else 180, 5.0, inp='forward', actor_collision=False),
              {'advance_runtime': {'seconds': 1.0}},
              at(GX + sgn * 420, GY - 1300, 300, -1100, 40)]
    cx, cy = gen.CHAMBER['at']
    for k, (dx, dy, yaw) in enumerate(((-1700, 0, 0), (1700, 0, 180), (0, -1600, 90))):
        sx, sy = cx + dx, cy + dy
        s.append({'note': "From the sea against the Grotto's rim (256 over the water): the party stays in the water."})
        s += [seg(sx, sy, -420, yaw, 1.0, inp='none', fly_up=True, actor_collision=False),
              seg(sx, sy, SURF_Z, yaw, 6.0, inp='forward', actor_collision=False),
              {'advance_runtime': {'seconds': 1.0}},
              at(sx + (cx - sx) * 0.5, sy + (cy - sy) * 0.5, 1300, -1100, 40)]
    write('bypass', 'before the test nobody reaches the Grotto: the Veil holds; from the court or the sea the '
          "colonnade and the Grotto's rim stand out of reach (P-2)", 'P-2: no way to the Grotto but through the Veil.', s)

    # the water: surface swimming, 20 s, no breath lost
    s = head()
    s += [{'clear_hostiles': {'radius': 40000}}]
    s.append({'note': 'Into the open sea and up to its surface (D-58 P4 Q1).'})
    s += surface(-1800, -1800, 0)
    s.append({'advance_runtime': {'seconds': 20}})
    s.append({'note': 'After 20 s at the surface: still at the surface, breath full, no drowning tick.'})
    s.append(water('surface', eye_under=False, breath_min=0.99, drowning_ticks_max=0,
                   foot_z_min=SURF_Z - (400 if PROBE else 4), foot_z_max=SURF_Z + (400 if PROBE else 4)))
    s.append(at(-1800, -1800, 300, -260, -60))
    write('swim', 'swimming at the surface costs no breath over 20 s (D-58 P4 Q1)',
          'The water: surface swimming free.', s)

    # the current: from the east band's outer edge the party is carried inward (west) with no input
    y = clear_band_y()
    x0 = gen.HALF - 300
    s = head()
    s += [{'clear_hostiles': {'radius': 40000}}]
    s.append({'note': f"At the surface in the east band (x {x0}): its constant current of {gen.CURRENT} pushes west."})
    s += surface(x0, y, 180)
    s += [{'advance_runtime': {'seconds': 5.0}}]
    s.append({'note': "Carried inward to the band's inner edge (x 5,632), where the current ends; held at the surface."})
    s.append(at(gen.HALF - gen.BAND - 2, y, 40, SURF_Z - 4, SURF_Z + 4))
    s.append(water('surface', eye_under=False, breath_min=0.99))
    write('current', 'an edge band carries a swimmer inward (D-58: constant current 256)',
          'The water: the outer sea pushes swimmers back.', s)

    # step out: swim to the Spray Terrace's flight and walk up out of the water
    p, n = gen.FLIGHTS['room:landing']
    steps = len([q for q in gen.ROOMS['rooms'][0]['platforms'] if q['id'].startswith('platform:landing_steps_')])
    off = 64 * steps + 360
    sx, sy = p[0] + n[0] * off, p[1] + n[1] * off
    yaw = math.degrees(math.atan2(-n[1], -n[0]))
    s = head()
    s += [{'clear_hostiles': {'radius': 40000}}]
    s.append({'note': "At the surface off the Spray Terrace's flight of steps, swimming at it."})
    s += surface(sx, sy, yaw)
    s += [seg(sx, sy, SURF_Z, yaw, 3.2, inp='forward', actor_collision=False), {'advance_runtime': {'seconds': 1}}]
    s.append({'note': 'Up the steps and out: dry, on the terrace (floor 0).'})
    s.append(water('dry', eye_under=False))
    s.append(at(p[0] - n[0] * 500, p[1] - n[1] * 500, 700, -8, 40))
    write('stepout', 'a swimmer climbs a flight of steps out of the sea onto the Spray Terrace (D-58 P4 Q1)',
          'The water: steps out at every walk.', s)
    # session 20: S's pieces: the sleeper's three answers and the dais
    ids = yaml.safe_load(open(L4 / 'ids.lock.yml'))
    if 'evt:sleeper' in ids['events']:
        px, py = gen.PLACE['poi:sleeper']['at']
        f = math.radians(90)
        near = (px + 420 * math.cos(f), py + 420 * math.sin(f), gen.CHAMBER_FL + 8)
        write('sleeper', "the Water Sleeper's three answers, the dais rising when he wakes, kept over a reload, to D7",
              "The sleeper (A3's m38.sleeper_water) and the return dais (D-58 C5, C7).",
              PC.sleeper_steps('water', MAP, head, ids, near, 270))
    print('playtests written; guardians', GUARDS, 'band y', y, 'stepout from', (int(sx), int(sy)), 'yaw', int(yaw))


if __name__ == '__main__':
    main()
