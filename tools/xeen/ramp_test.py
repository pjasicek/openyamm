#!/usr/bin/env python3
"""D-160 (2026-11-25, X4 p11 "i crawl under the ramp"): writes a headless scenario that checks an outdoor ramp is solid.

    python3 tools/xeen/ramp_test.py x4          # writes tests/scenarios/xeen/x4_castle_ramp.yml

A ramp here is a studio `stairs` thing with `ramp: true` (X4's castle lane, D1's Kalindra's ramp), in its own frame from
foot to top. The scenario plays, in party mode (four members) and in solo mode (one member, MAW's solo run with its
Blink talent):

(a) the real exit event of the dungeon whose door lands on the ramp (read from its generated Lua by the arrival's
    MoveToMap coordinates): the party stands within 300 of the arrival with its feet ARRIVAL_Z after 0.5 s and 3 s;
(b) stations along the ramp (on its centre line and near both cheeks), each set at the ramp's height plus 16 and
    settled for 0.5 s: the feet stay within 32 of the ramp's surface (a straight line from foot to top); then a walk
    from the arrival down to the foot and back up, which ends on the top (a party that slipped under the ramp on the
    way down could not walk back up to it);
(c) at ground level beside each cheek, where the ramp stands at least 250 over the land (nobody steps onto it there),
    pushing into the cheek for 2 s from four headings, with a jump, and in solo mode a Blink toward the ramp: the party
    stays outside the footprint (its centre at least CLEAR outside the cheek's face, sliding along it allowed); and
    from the foot, walking in from three headings for 4 s ends on the top, never under it.

Failing (a) is the engine's arrival floor pick, failing (b) or (c) its collision (A1, D-160).
"""
import math
import os
import re
import sys

import yaml

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..'))

# key: map; the ramp's foot and top (x, y, feet z: the middle of its low and high edges) and width; the arrival
# (x, y) with its z window and the dungeon whose exit lands there (left out: no exit lands on the ramp); `land_z` the
# land at the foot; `cheeks`: distances up the ramp from its foot where the cheek pushes are made (the ramp >= 250
# over the land there; empty where the cheeks stand lower than a step, as D1's); `end`: the distance up the ramp a walk
# from the foot passes (X4: the gate stops it short of the arrival) and the feet's z window there; `off_foot_z`: the
# feet's window after the walk down past the foot (left out: the land at the foot less 32 to plus 96).
RAMPS = {
    'x4': {'map': 'xeen_x4.odm', 'foot': (-1024, 5325, 1312), 'top': (-1024, 7194, 1888), 'width': 640,
           'arrival': (-1024, 6912), 'arrival_z': (1760, 1860), 'land_z': 1312,
           'exit_map': 'xeen_xd07.blv', 'cheeks': (1025, 1475), 'end': (1437, None),
           'note': "X4's castle lane (x4/places.py thing:castle_ramp): the village square up the rise's face to the "
                   "gate; XD-07's castle door lands on it."},
    'd1': {'map': 'xeen_d1.odm', 'foot': (-8397, -1741, 1542), 'top': (-8909, -2560, 1662), 'width': 512,
           'land_z': 1542, 'cheeks': (), 'end': (816, None), 'off_foot_z': (1000, 1638),
           'arrival_text': ('You step out of the pyramid',), 'slant_seconds': 0.8,
           'note': "D1's Kalindra's ramp (d1/gen.py thing:kalindra_ramp): up to the castle's forecourt; its cheeks "
                   "stand under a step over the land, so no cheek pushes, only stations, the walk and the foot."},
}
CLEAR = 8          # the party's centre outside a cheek's face by at least this (its own radius keeps it ~30 out)
BIG = 20000.0      # radius of the circles that stand for a half-plane (a cheek's face)
SLANT_SECONDS = 1.2   # the slant walks into the foot: short enough to stay on the top (a ramp's `slant_seconds`)
SLANT_V = 400.0       # where a slant walk ends up the ramp, about (the half-planes' middle)
SLANT_V_MIN = 250.0   # the least it climbs: its feet at least this far up the ramp's surface less 32


def exit_event(key):
    """The id of the exit event in the dungeon's generated Lua whose MoveToMap lands on the arrival."""
    r = RAMPS[key]
    stem = r['exit_map'].split('.')[0]
    src = open(os.path.join(REPO, 'assets_dev/worlds/xeen/events/maps', stem + '.lua')).read()
    current = None
    for line in src.splitlines():
        m = re.match(r'\s*RegisterEvent\((\d+),', line)
        if m:
            current = int(m.group(1))
        m = re.search(r'evt\.MoveToMap\((-?\d+), (-?\d+), (-?\d+),.*"%s"' % re.escape(r['map']), line)
        if m and current is not None and (int(m.group(1)), int(m.group(2))) == tuple(r['arrival']):
            return current
    raise SystemExit('%s: no event of %s moves to %s' % (key, stem, r['arrival']))


class Frame:
    """The ramp's own frame: v up the ramp from its foot, u across it to the right (the studio's `side`)."""

    def __init__(self, r):
        (fx, fy, fz), (tx, ty, tz) = r['foot'], r['top']
        self.length = math.hypot(tx - fx, ty - fy)
        self.ax, self.ay = (tx - fx) / self.length, (ty - fy) / self.length
        self.fx, self.fy, self.fz, self.tz = fx, fy, fz, tz
        self.half = r['width'] / 2.0
        self.yaw = math.degrees(math.atan2(self.ay, self.ax))   # up the ramp

    def at(self, u, v):
        return self.fx + self.ax * v + self.ay * u, self.fy + self.ay * v - self.ax * u

    def v_of(self, x, y):
        return (x - self.fx) * self.ax + (y - self.fy) * self.ay

    def z(self, v):
        t = max(0.0, min(1.0, v / self.length))
        return self.fz + (self.tz - self.fz) * t


def scenario(key):
    r = RAMPS[key]
    m = r['map']
    f = Frame(r)
    up_yaw, down_yaw = f.yaw, f.yaw + 180.0
    steps = []
    add = steps.append

    def pose(x, y, z, yaw_deg):
        add({'set_pose': {'map': m, 'x': round(x), 'y': round(y), 'z': round(z), 'yaw': round(math.radians(yaw_deg), 4),
                          'pitch': 0.0}})

    def at(x, y, radius, z_min=None, z_max=None):
        a = {'x': round(x), 'y': round(y), 'radius': round(radius)}
        if z_min is not None:
            a['z_min'] = round(z_min)
        if z_max is not None:
            a['z_max'] = round(z_max)
        add({'assert': {'party_position': a}})

    def walk(x, y, z, yaw_deg, seconds, stop, jump=False):
        seg = {'input': 'forward', 'seconds': seconds, 'actor_collision': True, 'actor_ai': False,
               'start': {'map': m, 'x': round(x), 'y': round(y), 'z': round(z), 'yaw_degrees': round(yaw_deg, 2),
                         'pitch': 0},
               'expect_stop': {'map': m, 'x': round(stop[0]), 'y': round(stop[1]), 'z': round(stop[2]),
                               'yaw_degrees': round(yaw_deg, 2), 'pitch': 0},
               'loose_tolerance': True, 'tolerance_xy': 40000, 'tolerance_z': 8000}
        if jump:
            seg['jump'] = True
        add({'movement_segment': seg})

    def push(x, y, yaw_deg, seconds, jump=False):
        walk(x, y, r['land_z'], yaw_deg, seconds, (x, y, r['land_z']), jump)
        add({'advance_runtime': {'seconds': 0.5}})

    def outside(side, v):
        """The party's centre beyond the right cheek (side +1) or the left (-1), by CLEAR."""
        x, y = f.at(side * (f.half + CLEAR + BIG), v)
        at(x, y, BIG)

    end_v, end_z = r['end']
    end_z = end_z or (f.z(end_v) - 32, f.tz + 96)
    end_x, end_y = f.at(0, end_v + BIG)

    for mode in ('party', 'solo'):
        add({'note': '---- %s mode ----' % mode})
        flow = {'start_map': r.get('exit_map', m)}
        if mode == 'solo':
            flow.update({'member_count': 1, 'ruleset': 'maw:solo'})
        add({'new_game_flow': flow})
        add({'setup_shortcut': {'kind': 'immortal', 'value': True}})
        if mode == 'solo':
            add({'console': {'line': 'talent blink 1', 'expect_contains': 'blink'}})
        if 'exit_map' in r:
            ax, ay = r['arrival']
            event = exit_event(key)
            add({'note': '(a) the real exit: %s event %d lands on the ramp at %s' % (r['exit_map'], event, r['arrival'])})
            add({'play_lua': {'source': 'wait(3) close()'}})     # the map's entry text, as the dungeon's own playtest
            add({'execute_event': {'id': event}})
            add({'select_topic': {'match_label': 'OK'}})        # the leave window
            add({'advance_runtime': {'seconds': 0.5, 'follow_map_move': True}})
            add({'assert': {'map': m}})
            at(ax, ay, 300, *r['arrival_z'])
            add({'advance_runtime': {'seconds': 2.5}})
            at(ax, ay, 300, *r['arrival_z'])
            start_v = f.v_of(ax, ay)
        else:
            add({'note': 'no dungeon exit lands on this ramp: (a) does not apply'})
            for text in r.get('arrival_text', ()):          # the map's own first-arrival text (a timer)
                add({'advance_runtime': {'seconds': 4}})
                add({'assert': {'dialog': {'active': True, 'text_contains': text}}})
                add({'press_action': {'action': 'cancel_dialog'}})
                add({'advance_runtime': {'seconds': 0.3}})
            start_v = f.length - 120
        add({'clear_hostiles': {'radius': 6000}})
        add({'note': '(b) stations along the ramp: the feet within 32 of its surface'})
        n = 8
        for i in range(n + 1):
            v = 120 + (f.length - 240) * i / float(n)
            for u in (0.0, -(f.half - 96), f.half - 96):
                x, y = f.at(u, v)
                z = f.z(v)
                pose(x, y, z + 16, down_yaw)
                add({'advance_runtime': {'seconds': 0.5}})
                at(x, y, 48, z - 32, z + 32)
        add({'note': '(b) the walk from %s down to the foot and back up to the top'
                     % ('the arrival' if 'exit_map' in r else 'the top')})
        sx, sy = f.at(0, start_v)
        add({'clear_hostiles': {'radius': 8000}})   # what closed in during the stations (a melee stops a walk)
        pose(sx, sy, f.z(start_v) + 8, down_yaw)
        add({'advance_runtime': {'seconds': 0.3}})
        walk(sx, sy, f.z(start_v), down_yaw, 6.0, f.at(0, -1500) + (r['land_z'],))
        add({'advance_runtime': {'seconds': 0.3}})
        add({'note': 'off the foot, on the land beyond it'})
        x, y = f.at(0, -50 - BIG)
        at(x, y, BIG, *r.get('off_foot_z', (r['land_z'] - 32, r['land_z'] + 96)))
        fx, fy = f.at(0, -400)
        walk(fx, fy, r['land_z'], up_yaw, 4.0, f.at(0, f.length) + (f.tz,))
        add({'advance_runtime': {'seconds': 0.3}})
        add({'note': 'back up past %d along the ramp: a party under the ramp could not stand this high' % end_v})
        at(end_x, end_y, BIG, *end_z)
        if r['cheeks']:
            add({'note': '(c) beside the cheeks at ground level: pushes from four headings, a jump%s'
                         % (' and a Blink' if mode == 'solo' else '')})
        for side in (-1, 1):
            for v in r['cheeks']:
                px, py = f.at(side * (f.half + 200), v)
                base = f.yaw + (90.0 if side > 0 else -90.0)     # facing the ramp from its right or left
                for turn in (0, 35, -35, 70):
                    push(px, py, base - turn * side, 2.0)
                    outside(side, v)
                push(px, py, base, 2.0, jump=True)
                outside(side, v)
                if mode == 'solo':
                    pose(px, py, r['land_z'], base)
                    add({'advance_runtime': {'seconds': 0.3}})
                    add({'console': {'line': 'talent use blink', 'expect_contains': 'using'}})
                    add({'advance_runtime': {'seconds': 1.0}})
                    outside(side, v)
        add({'note': '(c) into the foot from three headings: straight on up to its top; at 20 degrees for %.1f s, '
                     'on its top inside its footprint (a longer slant walk steps off its side onto the land, which '
                     'is not under it), never under it' % r.get('slant_seconds', SLANT_SECONDS)})
        for turn in (0, -20, 20):
            ox, oy = fx + f.ax * 200, fy + f.ay * 200
            if not turn:
                walk(ox, oy, r['land_z'], up_yaw, 4.0, f.at(0, f.length) + (f.tz,))
                add({'advance_runtime': {'seconds': 0.3}})
                at(end_x, end_y, BIG, *end_z)
                continue
            walk(ox, oy, r['land_z'], up_yaw + turn, r.get('slant_seconds', SLANT_SECONDS),
                 f.at(0, SLANT_V) + (f.z(SLANT_V),))
            add({'advance_runtime': {'seconds': 0.3}})
            for side in (-1, 1):     # inside both cheeks' faces, its feet over the land (on the top, not under it)
                x, y = f.at(side * (f.half - BIG), SLANT_V)
                at(x, y, BIG, f.z(SLANT_V_MIN) - 32 if side > 0 else None)
    return {'id': 'xeen.%s.ramp_solid' % key,
            'title': '%s: the ramp is solid (D-160): %swalking keeps to its top, pushing, jumping and Blinking at it '
                     'never gets under it' % (key.upper(), 'the dungeon exit lands on it, ' if 'exit_map' in r else ''),
            'world': 'xeen', 'mode': 'faithful', 'steps': steps}


def main():
    keys = sys.argv[1:] or sorted(RAMPS)
    for key in keys:
        r = RAMPS[key]
        out = os.path.join(REPO, 'tests/scenarios/xeen/%s_castle_ramp.yml' % key if key == 'x4'
                           else 'tests/scenarios/xeen/%s_ramp.yml' % key)
        doc = scenario(key)
        with open(out, 'w') as f:
            f.write('# Written by tools/xeen/ramp_test.py %s (D-160): edit the script, not this file.\n' % key)
            f.write('# %s\n' % r['note'])
            f.write('#   build-xeen/game/openyamm --world xeen --map %s --headless-run-scenario %s --scenario-no-color\n'
                    % (r['map'], os.path.relpath(out, REPO)))
            yaml.safe_dump(doc, f, sort_keys=False, width=120)
        print(out, len(doc['steps']), 'steps')


if __name__ == '__main__':
    main()
