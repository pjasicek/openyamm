"""The Scour's BModel kit (THE_SCOUR.md section 12): MM-style buildings of a box or two and a roof, a strong 4x kit
texture per part (K5 grafted resin, K6 the Ancient foundry, K12 the Kept's salvage, K1/K11 the colony), the door one
fitted face in a frame. Built on Starport Reach's kit (hesper_out1/bmodels.py and houses.py: faces of world points,
OBJ in the editor's convention, the house frame). World units, z up; every builder takes the ground height it stands
on. `front` is the direction (radians, 0 east, counter-clockwise) a door or opening faces.

    pier, deck_span, hopper           the conveyor line: resin-wrapped Ancient piers, the belt deck, the two hoppers
    stack                             a Foundry smokestack (an octagonal tube and a ring)
    foundry                           the works hall and its annex against the north ridge, the Slag Gate (D8)
    depot_shed                        a works shed with an open front (the supply depot)
    wall_ring                         D3's outer wall on the mesa: a ring of straight segments, the Outer Gate
    pens_door_bay, cage_row           D4's sunken yard: the Pit Stairs door in its south wall, the resin cage rows
    kept_shanty, camp_gate            the work camps: a box with a lean roof; two spines and a lintel
    thrix_stall, tarro_lean_to        the counters of the two houses (9300, 9301)
    tunnel_portal                     the Ancient service tunnel's portal in the canyon wall (S2)
"""
import math

import numpy as np

from bmodels import Model
from houses import Frame, block, slab, wall_with_door

DECK_DEPTH = 160.0
DECK_WIDTH = 500.0


def pier(m, x, y, ground, deck_z, yaw=0.0):
    """An Ancient pier wrapped in resin: an octagonal column from the ground to under the deck, a cross head under the
    belt (its long side across the line), a resin collar where the column meets the ground."""
    top = deck_z - DECK_DEPTH
    m.prism((x, y, ground - 30), 141, top - 120 - ground + 30, 8, 'hompier', phase=math.pi / 8)
    m.prism((x, y, ground - 30), 175, 260, 8, 'hokspine', top='hokspine', phase=math.pi / 8)
    m.box((x, y, top - 120), (260, 700, 120), 'hmgantry', yaw=yaw, top='hmgantry', bottom=True)


def deck_span(m, a, b, za, zb):
    """The belt deck between two piers, its top at za over a and zb over b (it climbs over the spoil hills): a slab
    500 wide and 160 deep, the belt on top, the side plates and the gantry underside, the ends closed."""
    (ax, ay), (bx, by) = a, b
    length = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / length, (by - ay) / length
    px, py = -uy * DECK_WIDTH / 2, ux * DECK_WIDTH / 2
    top = [(ax - px, ay - py, za), (bx - px, by - py, zb), (bx + px, by + py, zb), (ax + px, ay + py, za)]
    low = [(x, y, z - DECK_DEPTH) for x, y, z in top]
    m.facing(top, 'hmbelt', (0, 0, 1))
    m.facing(low, 'hmgantry', (0, 0, -1))
    for i, side in enumerate(('hmbeltsd', 'hmgantry', 'hmbeltsd', 'hmgantry')):
        j = (i + 1) % 4
        m.facing([low[i], low[j], top[j], top[i]], side, (top[i][0] + top[j][0] - ax - bx,
                                                           top[i][1] + top[j][1] - ay - by, 0))


def hopper(m, x, y, ground, deck_z, yaw=0.0):
    """A hopper tower: a box 900 x 900 x 1 200 the deck runs into, its funnel below, on four legs to the ground."""
    box_top = deck_z + 300
    box_bottom = box_top - 1200
    m.box((x, y, box_bottom), (900, 900, 1200), 'hompier', yaw=yaw, top='hmgantry')
    c, s = math.cos(yaw), math.sin(yaw)

    def local(px, py, z):
        return (x + px * c - py * s, y + px * s + py * c, z)
    spout = box_bottom - 420
    for (ax, ay), (bx, by) in [((-450, -450), (450, -450)), ((450, -450), (450, 450)), ((450, 450), (-450, 450)),
                               ((-450, 450), (-450, -450))]:
        m.face([local(ax, ay, box_bottom), local(bx, by, box_bottom), local(bx * 0.33, by * 0.33, spout),
                local(ax * 0.33, ay * 0.33, spout)][::-1], 'hmwall')
    for px in (-380, 380):
        for py in (-380, 380):
            lx, ly, _ = local(px, py, 0)
            m.box((lx, ly, ground - 30), (150, 150, box_bottom - ground + 30), 'hompier', yaw=yaw)


def stack(m, x, y, ground, top_z):
    """A smokestack: an octagonal tube 900 across from the ground to top_z, a ring round its lip, open at the top."""
    m.prism((x, y, ground - 40), 450, top_z - ground + 40, 8, 'homstack', phase=math.pi / 8)
    m.prism((x, y, top_z - 160), 520, 160, 8, 'hokwall', top=None, phase=math.pi / 8)
    m.prism((x, y, top_z - 1400), 490, 120, 8, 'hokwall', phase=math.pi / 8)
    ring = [(x + 400 * math.cos(math.pi / 8 + k * math.pi / 4), y + 400 * math.sin(math.pi / 8 + k * math.pi / 4))
            for k in range(8)]
    for k in range(8):                                   # the dark inside of the lip
        (ax, ay), (bx, by) = ring[k], ring[(k + 1) % 8]
        m.face([(bx, by, top_z - 300), (ax, ay, top_z - 300), (ax, ay, top_z + 2), (bx, by, top_z + 2)], 'hmgantry')
    outer = [(x + 520 * math.cos(math.pi / 8 + k * math.pi / 4), y + 520 * math.sin(math.pi / 8 + k * math.pi / 4))
             for k in range(8)]
    for k in range(8):                                   # the lip's top, from the ring to the tube's inside
        (ax, ay), (bx, by) = outer[k], outer[(k + 1) % 8]
        (cx, cy), (dx, dy) = ring[(k + 1) % 8], ring[k]
        m.face([(ax, ay, top_z + 2), (bx, by, top_z + 2), (cx, cy, top_z + 2), (dx, dy, top_z + 2)], 'hokwall')


def foundry(name, gate, ground, event, intake_y=None, intake_z=None):
    """The Foundry's works hall against the north ridge (5 200 x 2 400, 2 400 to the roof ridge): resin-banded shed
    walls, a gable roof, buttress bands of resin, an annex at its east end; the Slag Gate (D8) in the south wall at
    `gate` (x, y of the gate's face), facing south, in a resin frame; the conveyor's intake on the west wall."""
    m = Model(name)
    gx, gy = gate
    w, d, h = 5200.0, 2400.0, 1800.0
    x0, x1, y0, y1 = gx - w / 2, gx + w / 2, gy, gy + d
    z = ground
    gate_w, gate_h = 960.0, 1100.0
    # The south wall with the gate's opening; the other three walls whole.
    for (a, b, lo, hi) in [(x0, gx - gate_w / 2, 0, h), (gx + gate_w / 2, x1, 0, h), (gx - gate_w / 2, gx + gate_w / 2,
                                                                                    gate_h, h)]:
        m.facing([(a, y0, z + lo), (b, y0, z + lo), (b, y0, z + hi), (a, y0, z + hi)], 'homshed', (0, -1, 0))
    m.facing([(x1, y0, z - 60), (x1, y1, z - 60), (x1, y1, z + h), (x1, y0, z + h)], 'homshed', (1, 0, 0))
    m.facing([(x0, y1, z - 60), (x1, y1, z - 60), (x1, y1, z + h), (x0, y1, z + h)], 'homshed', (0, 1, 0))
    intake_y = gy + d * 0.75 if intake_y is None else intake_y
    iw, ih_lo, ih_hi = 700.0, h - 520, h - 60                  # the intake opening, where the belt deck comes in
    if intake_z is not None:
        ih_lo = min(max(intake_z - DECK_DEPTH - 120 - z, 200.0), h - 400)
        ih_hi = min(ih_lo + 460, h - 40)
    for (a, b, lo, hi) in [(y0, intake_y - iw / 2, -60, h), (intake_y + iw / 2, y1, -60, h),
                           (intake_y - iw / 2, intake_y + iw / 2, -60, ih_lo)]:
        m.facing([(x0, a, z + lo), (x0, b, z + lo), (x0, b, z + hi), (x0, a, z + hi)], 'homshed', (-1, 0, 0))
    m.facing([(x0 + 60, intake_y - iw / 2, z + ih_lo), (x0 + 60, intake_y + iw / 2, z + ih_lo),
              (x0 + 60, intake_y + iw / 2, z + ih_hi), (x0 + 60, intake_y - iw / 2, z + ih_hi)], 'hmgantry', (-1, 0, 0))
    m.facing([(x0, intake_y + iw / 2, z + ih_hi), (x0, intake_y - iw / 2, z + ih_hi),
              (x0, intake_y - iw / 2, z + h), (x0, intake_y + iw / 2, z + h)], 'homshed', (-1, 0, 0))
    # The gate: the hmgate face recessed 60 in a resin frame standing out of the wall.
    m.facing([(gx - gate_w / 2, y0 + 60, z), (gx + gate_w / 2, y0 + 60, z), (gx + gate_w / 2, y0 + 60, z + gate_h),
              (gx - gate_w / 2, y0 + 60, z + gate_h)], 'hmgate', (0, -1, 0), event=event, fit=True)
    for side in (-1, 1):
        px = gx + side * (gate_w / 2 + 70)
        m.box((px, y0 - 50, z - 40), (140, 220, gate_h + 220), 'hokspine', top='hokspine')
        m.facing([(gx + side * gate_w / 2, y0, z), (gx + side * gate_w / 2, y0 + 60, z),
                  (gx + side * gate_w / 2, y0 + 60, z + gate_h), (gx + side * gate_w / 2, y0, z + gate_h)],
                 'hokwall', (-side, 0, 0))
    m.box((gx, y0 - 50, z + gate_h), (gate_w + 280, 220, 200), 'hokwall', top='hokwall')
    m.facing([(gx - gate_w / 2, y0, z + gate_h), (gx + gate_w / 2, y0, z + gate_h), (gx + gate_w / 2, y0 + 60, z + gate_h),
              (gx - gate_w / 2, y0 + 60, z + gate_h)], 'hokwall', (0, 0, -1))
    # The gable roof (ridge along x) and its gable ends.
    ridge = z + 2400
    for (ya, yb, za, zb) in ((y0 - 80, (y0 + y1) / 2, z + h - 40, ridge), ((y0 + y1) / 2, y1 + 80, ridge, z + h - 40)):
        corners = [(x0 - 80, ya, za), (x1 + 80, ya, za), (x1 + 80, yb, zb), (x0 - 80, yb, zb)]
        m.both(corners, 'homroof')
    for xs, out in ((x0, -1), (x1, 1)):
        m.facing([(xs, y0, z + h), (xs, y1, z + h), (xs, (y0 + y1) / 2, ridge)], 'homshed', (out, 0, 0))
    # Buttress bands of resin up the long walls.
    for k in range(1, 7):
        bx = x0 + w * k / 7
        if abs(bx - gx) < gate_w / 2 + 300:
            continue
        m.box((bx, y0 - 70, z - 40), (180, 140, h + 40), 'hokwall', top='hokwall')
        m.box((bx, y1 + 70, z - 40), (180, 140, h + 40), 'hokwall', top='hokwall')
    # The annex at the east end, lower, with its own flat roof.
    m.box((x1 + 900, gy + d * 0.45, z - 60), (1800, 1600, 1500), 'homshed', top='homroof')
    return m


def depot_shed(name, centre, ground, front):
    """A works shed of the supply depot: 1 400 x 900 x 700, its front open (the crate stands inside), a lean roof
    over it, a closed store door (homdoor, no event) in the back wall."""
    m = Model(name)
    f = Frame(*centre, ground, front)
    w, d, h = 700.0, 900.0, 700.0
    y0, y1 = -d / 2, d / 2
    block(m, f, -w, y0, w, y1, -40, 30, 'hoplate', top='hoplate')
    for xs, out in ((-w, -1), (w, 1)):
        m.facing([f(xs, y0, 30), f(xs, y1, 30), f(xs, y1, h + 120), f(xs, y0, h)], 'homshed', f.direction(out, 0))
    m.facing([f(-w, y1, 30), f(w, y1, 30), f(w, y1, h + 120), f(-w, y1, h + 120)], 'homshed', f.direction(0, 1))
    m.facing([f(-w, y1 - 4, 30), f(w, y1 - 4, 30), f(w, y1 - 4, h + 120), f(-w, y1 - 4, h + 120)], 'homshed',
             f.direction(0, -1))
    m.facing([f(-160, y1 - 8, 30), f(160, y1 - 8, 30), f(160, y1 - 8, 430), f(-160, y1 - 8, 430)], 'homdoor',
             f.direction(0, -1), fit=True)
    slab(m, f, [(-w - 60, y0 - 120, h - 10), (w + 60, y0 - 120, h - 10), (w + 60, y1 + 60, h + 130),
                (-w - 60, y1 + 60, h + 130)], 16, 'homroof', 'hokwall')
    for px in (-w + 40, w - 40):                         # the posts of the open front
        block(m, f, px - 40, y0 - 40, px + 40, y0 + 40, 30, h - 20, 'hokwall', top='hokwall')
    return m


def wall_ring(name, centre, radius, ground, gate_angle, event, segments=12, height=700.0, thickness=160.0):
    """D3's outer wall on the mesa top: `segments` straight resin segments on a ring, one of them centred on
    gate_angle (radians) holding the Outer Gate (hkblast, fitted, recessed in an hkrib frame), two watch spines."""
    m = Model(name)
    cx, cy = centre
    z = ground
    gate_w, gate_h = 512.0, 640.0
    for k in range(segments):
        mid = gate_angle + 2 * math.pi * k / segments     # segment 0 is centred on the gate
        chord = 2 * radius * math.sin(math.pi / segments) + 40
        px, py = cx + radius * math.cos(mid) * math.cos(math.pi / segments), \
            cy + radius * math.sin(mid) * math.cos(math.pi / segments)
        yaw = mid + math.pi / 2
        if k:
            m.box((px, py, z - 60), (chord, thickness, height + 60), 'hokwall', yaw=yaw, top='hkrib')
            continue
        # The gate segment: two wall pieces and a lintel round the opening, the door face recessed into it.
        f = Frame(px, py, z, mid)                         # the frame's front faces out of the ring
        half = chord / 2
        t = thickness / 2
        for xa, xb in ((-half, -gate_w / 2), (gate_w / 2, half)):
            block(m, f, xa, -t, xb, t, -60, height, 'hokwall', top='hkrib')
        block(m, f, -gate_w / 2, -t, gate_w / 2, t, gate_h, height, 'hokwall', top='hkrib')
        m.facing([f(-gate_w / 2, -t + 40, 0), f(gate_w / 2, -t + 40, 0), f(gate_w / 2, -t + 40, gate_h),
                  f(-gate_w / 2, -t + 40, gate_h)], 'hkblast', f.direction(0, -1), event=event, fit=True)
        for xs, out in ((-gate_w / 2, 1), (gate_w / 2, -1)):
            m.facing([f(xs, -t, 0), f(xs, -t + 40, 0), f(xs, -t + 40, gate_h), f(xs, -t, gate_h)], 'hkrib',
                     f.direction(out, 0))
        m.facing([f(-gate_w / 2, -t, gate_h), f(gate_w / 2, -t, gate_h), f(gate_w / 2, -t + 40, gate_h),
                  f(-gate_w / 2, -t + 40, gate_h)], 'hkrib', f.direction(0, 0, -1))
        for xs in (-gate_w / 2 - 70, gate_w / 2 + 70):     # the rib frame standing out round the opening
            block(m, f, xs - 70, -t - 70, xs + 70, -t, -40, gate_h + 140, 'hkrib', top='hkrib')
        block(m, f, -gate_w / 2 - 140, -t - 70, gate_w / 2 + 140, -t, gate_h, gate_h + 140, 'hkrib', top='hkrib')
    for a in (gate_angle + math.pi * 0.62, gate_angle - math.pi * 0.62):      # two watch spines on the ring
        m.prism((cx + radius * math.cos(a), cy + radius * math.sin(a), z - 60), 190, height + 900, 6, 'hokspine',
                top='hkrib')
    return m


def pens_door_bay(name, door, ground, event):
    """D4's Pit Stairs door: a resin bay 1 000 wide built into the sunken yard's south wall, the door one fitted face
    (hkdoor, closed, 320 x 640 like its 1:2 texture) recessed in its north face at `door` (x, y), facing north across
    the yard; two resin spines either side and one fitted trim band (hktrim, 4:1) over the opening."""
    m = Model(name)
    dx, dy = door
    f = Frame(dx, dy, ground, math.pi / 2)               # front (local -y) faces north
    block(m, f, -500, 0, 500, 700, -60, 720, 'hokwall', top='hokwall', skip=('front',))
    door_w, door_h, inset = 320.0, 640.0, 40.0
    a, b = -door_w / 2, door_w / 2
    north = f.direction(0, -1)
    for p0, p1, q0, q1 in ((-500, a, -60, 720), (b, 500, -60, 720), (a, b, door_h, 720), (a, b, -60, 0)):
        m.facing([f(p0, 0, q0), f(p1, 0, q0), f(p1, 0, q1), f(p0, 0, q1)], 'hokwall', north)
    m.facing([f(a, inset, 0), f(b, inset, 0), f(b, inset, door_h), f(a, inset, door_h)], 'hkdoor', north,
             event=event, fit=True)
    m.facing([f(a, 0, 0), f(a, inset, 0), f(a, inset, door_h), f(a, 0, door_h)], 'hokwall', f.direction(1, 0))
    m.facing([f(b, inset, 0), f(b, 0, 0), f(b, 0, door_h), f(b, inset, door_h)], 'hokwall', f.direction(-1, 0))
    m.facing([f(a, 0, door_h), f(b, 0, door_h), f(b, inset, door_h), f(a, inset, door_h)], 'hokwall',
             f.direction(0, 0, -1))
    for xs in (a - 75, b + 75):                          # the spines standing either side of the opening
        x, y, _ = f(xs, -45, 0)
        m.prism((x, y, ground - 40), 70, door_h + 230, 6, 'hokspine', top='hkrib')
    band_w, band_h = 640.0, 160.0                        # hktrim is 512 x 128: one band, fitted, over the door
    z0 = door_h + 10
    block(m, f, -band_w / 2, -60, band_w / 2, 0, z0, z0 + band_h, {'front': None, 'all': 'hkrib'}, top='hkrib',
          bottom='hkrib')
    m.facing([f(-band_w / 2, -60, z0), f(band_w / 2, -60, z0), f(band_w / 2, -60, z0 + band_h),
              f(-band_w / 2, -60, z0 + band_h)], 'hktrim', north, fit=True)
    return m


def cage_row(m, centre, ground, yaw, length=1600.0):
    """A row of resin cages against the yard's side: a long low box of cage bars (hkcage) under a rib top."""
    m.box((centre[0], centre[1], ground - 30), (length, 300, 530), 'hkcage', yaw=yaw, top='hkrib')
    c, s = math.cos(yaw), math.sin(yaw)
    for k in range(5):
        t = -length / 2 + length * k / 4
        m.box((centre[0] + c * t, centre[1] + s * t, ground - 30), (60, 320, 600), 'hkrib', yaw=yaw, top='hkrib')


def kept_shanty(m, x, y, ground, front, width=440.0, depth=520.0, height=320.0):
    """A Kept shanty: a salvage box under a lean roof (low at the front), the door (no event) in its front wall.
    (x, y) is the shanty's centre."""
    fx, fy = x + math.cos(front) * depth / 2, y + math.sin(front) * depth / 2
    f = Frame(fx, fy, ground, front)
    w = width / 2
    block(m, f, -w - 10, -10, w + 10, depth + 10, -60, 30, 'hhkeptw', top='hoplate')
    wall_with_door(m, f, -w, w, 0.0, 30, height, 'hhkeptw', 'hhkeptw', 'hhkeptdr', None, door_x=-w * 0.2,
                   door_w=110, door_h=230)
    high = height + 130
    block(m, f, -w, 0, w, depth, 30, height, 'hhkeptw', skip=('front',))
    m.facing([f(-w, depth, height), f(w, depth, height), f(w, depth, high), f(-w, depth, high)], 'hhkeptw',
             f.direction(0, 1))
    for xs in (-w, w):
        m.facing([f(xs, 0, height), f(xs, depth, height), f(xs, depth, high)], 'hhkeptw', f.direction(xs, 0))
    rise = (high - height) / depth
    slab(m, f, [(-w - 40, -60, height - 60 * rise + 10), (w + 40, -60, height - 60 * rise + 10),
                (w + 40, depth + 40, high + 40 * rise + 10), (-w - 40, depth + 40, high + 40 * rise + 10)], 10,
         'hhkeptrf', 'hhkeptw')


def camp_gate(m, corners, ground):
    """A camp gate: two resin spines either side of the road and a rib lintel across it (the plan's `post` part:
    900 across the road, 160 deep, 800 high)."""
    p = np.array(corners, dtype=np.float64)
    edges = [(p[i], p[(i + 1) % 4]) for i in range(4)]
    a, b = max(edges, key=lambda e: np.linalg.norm(e[1] - e[0]))
    across = (b - a) / np.linalg.norm(b - a)
    centre = p.mean(0)
    yaw = math.atan2(across[1], across[0])
    for side in (-1, 1):
        sx, sy = centre + across * side * 450
        m.prism((sx, sy, ground - 40), 90, 840, 6, 'hokspine', top='hkrib')
    m.box((centre[0], centre[1], ground + 700), (1000, 160, 130), 'hkrib', yaw=yaw, top='hkrib', bottom=True)


def thrix_stall(name, x, y, ground, front, event):
    """Thrix's stall at his cave mouth: a counter of salvaged plate (its front face clicks: house 9300) under a resin
    canopy on plate posts (Hesper has no wood: the integrator's review of build01)."""
    m = Model(name)
    f = Frame(x, y, ground, front)
    block(m, f, -450, 0, 450, 300, -40, 110, {'front': None, 'all': 'hosalvage'}, top='hmplate')
    m.facing([f(-450, 0, -40), f(450, 0, -40), f(450, 0, 110), f(-450, 0, 110)], 'hosalvage', f.direction(0, -1),
             event=event)
    for xs in (-560, 560):
        block(m, f, xs - 30, 380, xs + 30, 440, -20, 470, 'hmplate', top='hmplate')
        block(m, f, xs - 30, -330, xs + 30, -270, -20, 330, 'hmplate', top='hmplate')
    slab(m, f, [(-620, -350, 330), (620, -350, 330), (620, 450, 470), (-620, 450, 470)], 24, 'hoaresin', 'hkrib')
    return m


def tarro_lean_to(name, x, y, ground, front, event):
    """Tarro's lean-to shop: a colony prefab back wall and sides under a lean roof, open at the front, a counter under
    the opening (its front face clicks: house 9301)."""
    m = Model(name)
    f = Frame(x, y, ground, front)
    w, d = 350.0, 500.0
    block(m, f, -w, 0, w, d, -40, 30, 'hoplate', top='hoplate')
    m.facing([f(-w, d, 30), f(w, d, 30), f(w, d, 430), f(-w, d, 430)], 'hhprefab', f.direction(0, 1))
    m.facing([f(w, d - 4, 30), f(-w, d - 4, 30), f(-w, d - 4, 430), f(w, d - 4, 430)], 'hhprefab', f.direction(0, -1))
    for xs in (-w, w):
        m.facing([f(xs, 0, 30), f(xs, d, 30), f(xs, d, 430), f(xs, 0, 330)], 'hhprefab', f.direction(xs, 0))
    slab(m, f, [(-w - 50, -120, 320), (w + 50, -120, 320), (w + 50, d + 40, 440), (-w - 50, d + 40, 440)], 10,
         'hhprefrf', 'hhprefdk')
    block(m, f, -w + 40, 10, w - 40, 130, 30, 140, {'front': None, 'all': 'hhprefdk'}, top='hhprefdk')
    m.facing([f(-w + 40, 10, 30), f(w - 40, 10, 30), f(w - 40, 10, 140), f(-w + 40, 10, 140)], 'hhprefdk',
             f.direction(0, -1), event=event)
    return m


def tunnel_portal(name, x, y, ground, front, event):
    """The Ancient service tunnel's portal: a white frame 900 wide and 800 high set into the rock, gold trim round
    the heavy shutter (hcshutter, fitted, the door face), a light strip over it (dark until S2: the strip stays
    hcstripw; the map's event tells the state)."""
    m = Model(name)
    f = Frame(x, y, ground, front)
    block(m, f, -450, 0, 450, 600, -60, 800, {'front': None, 'all': 'hoterm'}, top='hoterm')
    for (xa, xb, za, zb) in ((-450, -300, -60, 800), (300, 450, -60, 800), (-300, 300, 560, 800)):
        m.facing([f(xa, 0, za), f(xb, 0, za), f(xb, 0, zb), f(xa, 0, zb)], 'hoterm', f.direction(0, -1))
    m.facing([f(-300, 40, 0), f(300, 40, 0), f(300, 40, 560), f(-300, 40, 560)], 'hcshutter', f.direction(0, -1),
             event=event, fit=True)
    for xs, out in ((-300, 1), (300, -1)):
        m.facing([f(xs, 0, 0), f(xs, 40, 0), f(xs, 40, 560), f(xs, 0, 560)], 'hctrim', f.direction(out, 0))
    m.facing([f(-300, 0, 560), f(300, 0, 560), f(300, 40, 560), f(-300, 40, 560)], 'hctrim', f.direction(0, 0, -1))
    block(m, f, -340, -24, 340, 0, 600, 650, 'hcstripw', top='hctrim')
    for xs in (-390, 390):
        block(m, f, xs - 30, -30, xs + 30, 0, -40, 760, 'hctrim', top='hctrim')
    block(m, f, -420, -30, 420, 0, 740, 800, 'hctrim', top='hctrim')
    return m
