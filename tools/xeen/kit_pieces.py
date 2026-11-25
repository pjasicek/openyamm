"""Generic outdoor kit pieces the Xeen map generators share (sketch structures in cells and map units).

water_end (D-94, the user 2026-11-22 on Vertigo's creek wall: "maybe make some 'end water piece'"): a town wall or
tower that must end in water ends in a low battered stone pier, a cutwater, not a curtain wall run out into the
water. It leaves the tower or wall foot level at about 1.5 party heights, runs on so until it is out of the party's
reach from the bank, slopes down over the water and ends in a rounded nose. No crenellations. It stays impassable:
over CLIMB above the land everywhere the party can reach it from the bank, and its nose stands in water the party
cannot walk in. `tools/xeen/wall_check.py` checks both (`walls.water_end`) for every thing named `thing:water_end*`.

sunken_entrance (D-95, the user 2026-11-22 on Vertigo's culvert: "sloped down terrain a bit and there the
entrance"): a culvert, sewer, drain or cellar entrance is set into the ground. The generator cuts a short ditch on
its approach side (`cut_height`), about one party height deep, whose sides are lined by low revetments of the
headwall's stone; the mouth opens in the ditch's end face, its crown about at ground level, and a stone cap behind
the end face is the ground's level up to the far side (a quay on a creek). No water lies on dry land: a culvert's
outflow is a trickle on the ditch's floor. An optional `outfall` (a creek behind the end face) is a low grated arched
mouth at the waterline in the quay's face, so the creek side reads as a drain, not a second door.

Both pieces are axis-aligned here (their sites run north-south or face south); `turn` is left to a later site.
"""
from __future__ import annotations

import math

CELL = 512
PARTY_H = 192            # the party's height
CLIMB = 224              # what the party can get onto: a step of 128 over a jump of about 90 (480^2 / 2 / 1280)
LEVEL_ON = 64            # the pier stays level this far past the bank before it slopes


# -------------------------------------------------------------------------------------------------- water end

def water_end(tid, root, tip, bank, ground, width=320, high=None, low=CLIMB, texture='cwb', batter=48,
              title='Pier', notes=''):
    """A pier from `root` (cells, inside the tower or the wall's end) south or north to `tip` (cells, its nose's
    point in the water). `bank` is the row (cells) where the water starts along it, `ground` the land's height there.
    Its top is `high` (1.5 party heights when left out) over the land until LEVEL_ON past the bank, then slopes down
    to `low` (CLIMB) over the water and ends in a round nose under a low cone. Returns one building structure."""
    high = high if high is not None else round(PARTY_H * 1.5)
    x, y0 = root
    y1 = tip[1]
    south = y1 > y0
    length = abs(y1 - y0) * CELL
    flat = abs(bank - y0) * CELL + LEVEL_ON         # level a little past the bank
    radius = width / 2.0
    slope = length - flat - radius                   # then down to the nose's middle
    if low < CLIMB or slope < 96:
        raise ValueError(f'{tid}: the pier needs {flat + radius + 96:.0f} from its root to its tip (has {length:.0f}) '
                         f'and a low end of at least {CLIMB} (has {low})')
    w_cells = width / CELL
    at = [round(x - w_cells / 2, 4), round(min(y0, y1), 4)]
    size = [round(w_cells, 4), round(length / CELL, 4)]
    tex = {'wall': texture, 'roof': texture}
    # local map units from the plot's north-west corner (y grows south); a pier running north is mirrored
    def span(a, b):
        return (a, b) if south else (length - b, length - a)
    f0, f1 = span(0, flat)
    s0, s1 = span(flat, flat + slope)
    nose_y = (flat + slope) if south else (length - flat - slope)
    parts = [
        {'id': 'pier', 'at': [0, round(f0)], 'size': [width, round(f1 - f0)], 'wall_height': high, 'roof': 'flat',
         'windows': 'none', 'batter': batter, 'batter_height': low, 'batter_walls': ['e', 'w'], 'textures': tex},
        {'id': 'cutwater', 'at': [0, round(s0)], 'size': [width, round(s1 - s0)], 'wall_height': low,
         'roof': 'lean_to', 'roof_low': 's' if south else 'n', 'roof_height': high - low, 'windows': 'none',
         'batter': batter, 'batter_height': low, 'batter_walls': ['e', 'w'], 'textures': tex},
        {'id': 'nose', 'shape': 'round', 'at': [round(radius), round(nose_y)], 'radius': round(radius - batter / 2),
         'sides': 8, 'wall_height': low, 'roof': 'cone', 'roof_pitch': 30, 'windows': 'none', 'textures': tex},
    ]
    return {'id': tid, 'kind': 'building', 'at': at, 'size': size, 'kit': 'castle', 'door': 'none',
            'title': title, 'parts': parts,
            'notes': notes or ('D-94 water end: a low battered pier from the wall into the water, level %d over the '
                               'land (%d) to %d past the bank, sloping to %d over the water, a round nose.'
                               % (high, ground, LEVEL_ON, low))}


# -------------------------------------------------------------------------------------------------- sunken entrance

class SunkenEntrance:
    """A culvert or cellar mouth set into the ground (D-95), looking south (the sites so far; `turn` is for a later
    one). The ditch's floor nodes are columns `x0`..`x1` and rows `face_y` (a whole row: the mouth stands on it) to
    `floor_to`, `depth` under the land `ground`; south of `floor_to` the ramp rises to the land's node row `ramp_to`.
    The mouth (a `culvert` structure: its headwall is the ditch's end face, `top` its top) stands at `face_y` with its
    crown about at the land's level; revetments line the cell beside the floor on each side from the end face to
    `revet_to`, their tops 16 under `top`; a stone cap at `top` reaches from the end face's back to row `back_to` over
    the cut's slope behind it, with a lintel over the tunnel's last part so the dark face stays in sight. `outfall`
    (a creek behind) is the creek side's own low barred mouth at the waterline on the bank's edge (`outfall_y`), in a
    small block of the same stone: a drain, not a second door.

    P2 feedback F25 (pins p3, p18, 2026-11-23; tools/xeen/town_fit_check.py `culverts.*`, `walls.hollow`): `under`
    rows behind the end face are cut to the floor too, so the land under the mouth's tunnel is the floor's (it climbed
    into the arch as a grass slope under the dark face); the mouth sits DRY_SINK under the floor so its tunnel water
    lies under the land (a dry ditch shows no flat strip of water); the revetments reach down to the floor (they hung
    over it); the outfall's block has cheeks over its tunnel's sides between the headwall and the cap (seen from the
    creek its side showed the tunnel cut through).

    D-170 (2026-11-25, `faces.on_land`): with `bank` the land nodes beside the ditch (columns x0 - 1 and x1 + 1 on its
    floor rows) stand at that height, so the revetments' tops (16 under `top`), the end face and the cap stand over the
    land they retain (X1's bank at 640 lay over the revetments' tops and round the end face's corners: their top faces
    crossed the land and flickered with it). Pick `bank` and `revet_to` so the land under each revetment stays 4 or
    more under its top. Left out, the land is the land words' (X4)."""

    THICK = 112           # the mouth's headwall
    DEPTH = 16            # the dark face behind it
    DRY_SINK = 16         # a dry mouth's floor under the ditch's floor: its tunnel water stays under the land

    def __init__(self, name, x0, x1, face_y, floor_to, ramp_to, ground, top, depth=PARTY_H + 32, back_to=None,
                 revet_to=None, texture='cwb', land=None, revet_thick=CELL, under=0, bank=None):
        self.name, self.x0, self.x1 = name, x0, x1
        self.face_y, self.floor_to, self.ramp_to = face_y, floor_to, ramp_to
        self.ground, self.floor, self.top = ground, ground - depth, top
        self.back_to, self.texture = back_to, texture
        self.revet_to = revet_to if revet_to is not None else ramp_to
        self.revet_thick = revet_thick     # thinner where a house stands at the slope's top (X4's undercroft stair)
        self.land = land or (lambda i, j: ground)        # the land's node heights round the ditch, before the cut
        self.rows = range(int(face_y) - under, floor_to + 1)
        assert face_y == int(face_y), 'the end face stands on a whole row of floor nodes'
        assert under * CELL >= self.THICK + self.DEPTH or under == 0, 'the cut rows behind reach past the dark face'
        assert bank is None or bank % 32 == 0, "the bank is a whole number of the nodes block's units (32)"
        self.bank = bank

    def node(self, i, j):
        """A node's height after the cut (the floor's, the bank's beside it, else the land's)."""
        if j in self.rows and self.x0 <= i <= self.x1:
            return self.floor
        if j in self.rows and self.bank is not None and i in (self.x0 - 1, self.x1 + 1):
            return self.bank
        return self.land(i, j)

    def stored(self, x, y):
        return bilinear(self.node, x, y)

    def nodes(self):
        """The heights.nodes block: the floor's nodes (applied after the land words; keep roads and water off)."""
        unit = 32
        row = [round(self.floor / unit)] * (self.x1 - self.x0 + 1)
        notes = 'D-95: the %s\'s sunken approach, %d under the land; its ramp rises south to row %s.' % (
            self.name, self.ground - self.floor, self.ramp_to)
        if self.bank is not None:
            # D-170: the bank's nodes either side, under the revetments' tops
            row = [self.bank // unit] + row + [self.bank // unit]
            notes += " D-170: the bank beside it at %d, under the revetments' tops (%d)." % (self.bank, self.top - 16)
        return {'at': [self.x0 - (1 if self.bank is not None else 0), self.rows[0]], 'unit': unit,
                'rows': [list(row) for _ in self.rows], 'notes': notes}

    def backing(self, tag, xm, width, front, facing, thick, depth, top, to_y, sink=0):
        """The cap and lintel behind a mouth whose front is at row `front` looking `facing` (+1 south, -1 north):
        the lintel over the tunnel's last part (its foot 80 under `top`, over the crown), the cap from 4 behind the
        dark face to row `to_y`, both topped at `top`. With `sink` the cap reaches into the block in front of it (a
        negative `depth`) and stands `sink` lower and 4 narrower each side, so its front lies inside that block and no
        two faces share a plane (P3 2026-11-24: the culvert's cap and its frame's back were drawn back to back)."""
        back = front - facing * thick / CELL
        dark = back - facing * depth / CELL
        end = dark - facing * 4.0 / CELL
        tex = {'wall': self.texture}
        out = []
        for part, a, b in (('lintel', back, end), ('cap', end, to_y)):
            mid = (a + b) / 2
            size = [width - (8 if sink and part == 'cap' else 0), round(abs(b - a) * CELL)]
            if part == 'lintel':
                st = {'height': 16, 'raise': round(top - 16 - self.stored(xm, mid))}
            else:
                st = {'height': round(top - sink - self.stored(xm, mid))}
            out.append(dict({'id': 'thing:%s_%s' % (tag, part), 'kind': 'platform', 'at': [xm, round(mid, 4)],
                             'size': size, 'textures': tex, 'title': 'Quay',
                             'notes': 'D-95: the stone behind the %s mouth (%s).' % (tag.replace('_', ' '), part)},
                            **st))
        return out

    def structures(self, mouth, outfall_y=None, outfall=None, quay=False):
        """The mouth (a culvert structure: `at`, `thickness`, `depth` and `wall` are set here), the revetments, the
        cap and lintel behind it, and with `outfall_y` the creek side's mouth with its block (words over the
        defaults in `outfall`)."""
        tex = {'wall': self.texture}
        xm = (self.x0 + self.x1) / 2.0
        # the ditch's width over the revetments' outer faces ((x1 - x0 + 2) cells with CELL-thick revetments)
        width = (self.x1 - self.x0) * CELL + 2 * self.revet_thick
        # the end face 16 inside the revetments' outer faces at either end (no faces in one plane)
        # F25 (pin p3): the mouth is a dark arched door in the end face (a `doorway`: its frame the end face, `THICK`
        # deep, its sill on the floor), not a culvert's tunnel: the tunnel ran back under the bank, whose land (held
        # at the creek's level) climbed into it as a grass slope under the dark face, and its water lay on the dry
        # floor as a flat strip. A dark door in a stone face is the MM6-MM8 way into a dungeon from a wall.
        keep = {k: v for k, v in mouth.items() if k not in ('kind', 'outflow', 'water_level', 'hint', 'thickness',
                                                              'depth', 'wall', 'grating')}
        m = dict(keep, kind='doorway', at=[xm, round(self.face_y - 32.0 / CELL, 4)], floor=self.floor,
                 width=mouth.get('width', 288), height=mouth.get('height', 384), arch=mouth.get('arch', 'round'),
                 sides=mouth.get('sides', 8), depth=self.THICK, frame_width=width - 32,
                 frame_height=self.top - self.floor)
        tx = dict(tex, **(mouth.get('textures') or {}))
        tx.setdefault('door', '7solid01')
        m['textures'] = tx
        crown = self.floor + m['height']
        assert crown <= self.top - 80, 'the mouth\'s crown must stay 80 under the top (the lintel over the tunnel)'
        out = [m]
        back = self.face_y - self.THICK / CELL
        half = self.revet_thick / 2.0 / CELL
        for side, cx in (('w', self.x0 - half), ('e', self.x1 + half)):
            steps = [self.face_y + (self.revet_to - self.face_y) * k / 8 for k in range(9)]
            high = max(self.stored(cx, y) for y in steps)
            low = min(self.stored(cx, y) for y in steps)
            # F25: the foot down to the floor (a wall's foot is its line's lowest land less 64: it hung over the floor)
            sink = min(0, round(self.floor - 32 - (low - 64)))
            rv = {'id': 'thing:%s_revetment_%s' % (self.name, side), 'kind': 'wall',
                  'line': [[cx, round(back + 0.02, 4)], [cx, self.revet_to]],
                  'height': max(32, round(self.top - 16 - high - sink)), 'thickness': self.revet_thick, 'textures': tex,
                  'title': 'Revetment', 'notes': "D-95: lines the sunken approach's side, 16 under the end face."}
            if sink:
                rv['raise'] = sink
            out.append(rv)
        if self.back_to is not None:
            # the cap 4 into the end face's block (depth -8), 2 under its top and 4 inside its sides
            out += [st for st in self.backing(self.name, xm, width - 32, self.face_y, 1, self.THICK, -8, self.top,
                                              self.back_to, sink=2) if not st['id'].endswith('_lintel')]
        if outfall_y is not None:
            water = self.land(round(xm), math.ceil(outfall_y))
            o = {'id': 'thing:%s_outfall' % self.name, 'kind': 'culvert', 'turn': 180, 'at': [xm, outfall_y],
                 'width': 224, 'height': 112, 'thickness': 16, 'depth': 16, 'water_level': 4, 'outflow': 0,
                 'grating': {'bars': [3, 1], 'width': 12, 'back': 0},
                 'textures': {'wall': self.texture, 'grating': '7t1butts'}, 'title': 'Outfall',
                 'notes': "D-95: the creek side, a low barred arch at the waterline: a drain, not a second door."}
            o.update(outfall or {})
            o_top = water + o['height'] + 80
            o['wall'] = [o['width'] + 96, o_top - water]
            out.append(o)
            out += self.backing(self.name + '_outfall', xm, o['width'] + 96, outfall_y, -1, o['thickness'],
                                o['depth'], o_top, outfall_y + 0.4)
            if quay:
                # F25: with the cut reaching under the bank (`under`), the cap runs on to the outfall's block and two
                # wings either side of it close the quay's front along the water: nothing of the cut bank shows
                ow = (o['width'] + 96) / 2.0 / CELL
                cw = (width - 32) / 2.0 / CELL
                a0 = outfall_y + o['thickness'] / CELL
                b0 = outfall_y + 0.4
                for side, sx in (('w', -1), ('e', 1)):
                    mx = xm + sx * (ow + cw) / 2.0
                    my = (a0 + b0) / 2.0
                    out.append({'id': 'thing:%s_quay_%s' % (self.name, side), 'kind': 'platform',
                                'at': [round(mx, 4), round(my, 4)],
                                'size': [round((cw - ow) * CELL), round((b0 - a0) * CELL)],
                                'height': round(self.top - self.stored(mx, my)), 'textures': tex, 'title': 'Quay',
                                'notes': "F25: the quay's front beside the outfall, over the cut bank."})
            # F25 (p18): cheeks over the tunnel's sides between the headwall's back and the cap, 4 inside the block's
            # sides (no faces in one plane), from the creek's bed to the lintel's foot
            a = outfall_y + o['thickness'] / CELL - 0.01
            b = outfall_y + (o['thickness'] + o['depth'] + 4) / CELL + 0.01
            half = (o['width'] + 96) / 2.0 - 4 - 16      # 32 thick (a wall's least), 4 inside the block's side
            for side, sx in (('w', -1), ('e', 1)):
                cx = round(xm + sx * half / CELL, 4)
                g = min(self.stored(cx, a), self.stored(cx, b))
                out.append({'id': 'thing:%s_outfall_cheek_%s' % (self.name, side), 'kind': 'wall',
                            'line': [[cx, round(a, 4)], [cx, round(b, 4)]], 'thickness': 32,
                            'height': round(o_top - 16 - g), 'textures': tex, 'title': 'Outfall',
                            'notes': "F25: closes the side of the outfall's tunnel between its headwall and cap."})
        return out


def bilinear(nodes, x, y):
    """The stored heights' bilinear value at (x, y) cells (as the studio's storedHeightAt); `nodes(ix, iy)` a node's
    height."""
    ix, iy = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - ix, y - iy
    return (nodes(ix, iy) * (1 - fx) * (1 - fy) + nodes(ix + 1, iy) * fx * (1 - fy)
            + nodes(ix, iy + 1) * (1 - fx) * fy + nodes(ix + 1, iy + 1) * fx * fy)
