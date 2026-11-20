"""The Crown's BModel kit (THE_CROWN.md section 12): every building a function returning a Model of faces with a
texture per part, built on Starport Reach's kit (level_generation/projects/hesper_out1/bmodels.py: OBJ in the
editor's convention, `facing` winds a face toward a direction, `both` makes a shell two sided 4 units apart).

Positions are world units (x east, y north, z up); `z` is the ground under the building. Faces that carry an event
(the node doors, the Spire Gate, the hatches, the lift, the collar node, the stalls' doors) are fitted once over
their face (`fit`), as Starport Reach's doors are.
"""
import math

import numpy as np

from bmodels import Model
import houses


def ring_points(cx, cy, radius, sides, phase=0.0):
    return [(cx + radius * math.cos(phase + 2 * math.pi * k / sides),
             cy + radius * math.sin(phase + 2 * math.pi * k / sides)) for k in range(sides)]


def frustum(m, cx, cy, z0, z1, r0, r1, sides, texture, top=None, phase=0.0, fit=False):
    """A tapering prism from radius r0 at z0 to r1 at z1, its sides facing out; `top` caps it."""
    low, high = ring_points(cx, cy, r0, sides, phase), ring_points(cx, cy, r1, sides, phase)
    for k in range(sides):
        j = (k + 1) % sides
        mid = ((low[k][0] + low[j][0]) / 2 - cx, (low[k][1] + low[j][1]) / 2 - cy, 0.0)
        m.facing([(*low[k], z0), (*low[j], z0), (*high[j], z1), (*high[k], z1)], texture, mid, fit=fit)
    if top:
        m.facing([(x, y, z1) for x, y in high], top, (0, 0, 1))
    return high


def box(m, centre, size, texture, yaw=0.0, top=None, z0=0.0, sides=None):
    """An upright box on centre's z + z0, turned by yaw, each side facing out (sides: {'south': texture, ...} in the
    box's own axes before the turn; None leaves a side out)."""
    cx, cy, cz = centre
    hx, hy, h = size[0] / 2, size[1] / 2, size[2]
    c, s = math.cos(yaw), math.sin(yaw)

    def at(x, y):
        return cx + x * c - y * s, cy + x * s + y * c
    corners = [at(-hx, -hy), at(hx, -hy), at(hx, hy), at(-hx, hy)]
    outs = [(s, -c), (c, s), (-s, c), (-c, -s)]
    for k, name in enumerate(['south', 'east', 'north', 'west']):
        texture_k = (sides or {}).get(name, texture)
        if texture_k is None:
            continue
        a, b = corners[k], corners[(k + 1) % 4]
        m.facing([(*a, cz + z0), (*b, cz + z0), (*b, cz + z0 + h), (*a, cz + z0 + h)], texture_k, (*outs[k], 0))
    if top:
        m.facing([(x, y, cz + z0 + h) for x, y in corners], top, (0, 0, 1))
    return corners


# --- The Crownspire -------------------------------------------------------------------------------------------------
# The enlarged Crownspire (the user, 2026-10-23: the capital's fortress must read much bigger): walls 3 200 high, the
# gatehouse and the Spire Gate scaled 1.5 with the square (THE_CROWN.md section 4).
WALL_H = 3200.0
GATE_SCALE = 1.5
GATEHOUSE_DEPTH = 320.0 * GATE_SCALE
GATE_COG = 9301                       # the Spire Gate's face: evt.SetTexture swaps hogate -> hogateof (QBit 100603)


def crownspire(half, z, gate_event):
    """The citadel's square of polished black resin walls (hocrown) with gold-trimmed buttresses every 1 200 and a
    cornice, the flat parapet roof the dome stands on (hpfloor), and the Spire Gate: a gatehouse standing out of the
    south wall, its leaves (hogate, the event face; 900 x 1 400 at GATE_SCALE) recessed in a gold frame (1 200 x
    1 700 at GATE_SCALE)."""
    m = Model('crownspire')
    corners = [(-half, -half), (half, -half), (half, half), (-half, half)]
    gate_w, gate_h, frame_w, frame_h = (v * GATE_SCALE for v in (900.0, 1400.0, 1200.0, 1700.0))
    for k in range(4):
        (ax, ay), (bx, by) = corners[k], corners[(k + 1) % 4]
        out = ((by - ay) / (2 * half), -(bx - ax) / (2 * half), 0.0)
        m.facing([(ax, ay, z), (bx, by, z), (bx, by, z + WALL_H), (ax, ay, z + WALL_H)], 'hocrown', out)
        # Buttresses every 1 200 (the corners are inside the bastions), 160 out and 220 wide.
        length = 2 * half
        for d in np.arange(-half + 1200, half - 600, 1200):
            if k == 0 and abs(d) < frame_w:              # the gatehouse takes the south wall's middle
                continue
            t = (d + half) / length
            px, py = ax + (bx - ax) * t + out[0] * 80, ay + (by - ay) * t + out[1] * 80
            box(m, (px, py, z), (220, 160, WALL_H + 60), 'hocrown', yaw=math.atan2(by - ay, bx - ax), top='hptrim')
    # The cornice: a gold band round the wall tops, standing 30 out.
    for k in range(4):
        (ax, ay), (bx, by) = corners[k], corners[(k + 1) % 4]
        out = np.array([(by - ay) / (2 * half), -(bx - ax) / (2 * half)])
        a, b = np.array([ax, ay]) + out * 30, np.array([bx, by]) + out * 30
        m.facing([(*a, z + WALL_H - 120), (*b, z + WALL_H - 120), (*b, z + WALL_H), (*a, z + WALL_H)], 'hptrim',
                 (*out, 0))
        m.facing([(*a, z + WALL_H), (*b, z + WALL_H), (bx, by, z + WALL_H), (ax, ay, z + WALL_H)], 'hptrim',
                 (0, 0, 1))
    m.facing([(x, y, z + WALL_H) for x, y in corners], 'hpfloor', (0, 0, 1))
    # The gatehouse: a block 1 700 wide and 2 000 high standing 320 out of the south wall.
    gy = -half - GATEHOUSE_DEPTH
    gx0, gx1, gh = -850.0 * GATE_SCALE, 850.0 * GATE_SCALE, WALL_H + 400.0
    for (x0, x1, z0, z1) in [(gx0, -frame_w / 2, 0, gh), (frame_w / 2, gx1, 0, gh), (-frame_w / 2, frame_w / 2,
                                                                                        frame_h, gh)]:
        m.facing([(x0, gy, z + z0), (x1, gy, z + z0), (x1, gy, z + z1), (x0, gy, z + z1)], 'hocrown', (0, -1, 0))
    for x in (gx0, gx1):
        m.facing([(x, gy, z), (x, -half, z), (x, -half, z + gh), (x, gy, z + gh)], 'hocrown', (math.copysign(1, x), 0, 0))
    m.facing([(gx0, gy, z + gh), (gx1, gy, z + gh), (gx1, -half, z + gh), (gx0, -half, z + gh)], 'hpfloor', (0, 0, 1))
    m.facing([(gx0 - 20, gy - 20, z + gh - 100), (gx1 + 20, gy - 20, z + gh - 100), (gx1 + 20, gy - 20, z + gh),
              (gx0 - 20, gy - 20, z + gh)], 'hptrim', (0, -1, 0))
    # The frame: a gold reveal 150 deep from the gatehouse's face to the leaves.
    fx0, fx1, depth = -frame_w / 2, frame_w / 2, 150.0 * GATE_SCALE
    for x, n in ((fx0, 1), (fx1, -1)):
        m.facing([(x, gy, z), (x, gy + depth, z), (x, gy + depth, z + frame_h), (x, gy, z + frame_h)], 'hptrim',
                 (n, 0, 0))
    m.facing([(fx0, gy, z + frame_h), (fx1, gy, z + frame_h), (fx1, gy + depth, z + frame_h),
              (fx0, gy + depth, z + frame_h)], 'hptrim', (0, 0, -1))
    # The leaves' surround inside the frame (resin), then the leaves, fitted once (CR-P3-04: native 512).
    ly = gy + depth
    for (x0, x1, z0, z1) in [(fx0, -gate_w / 2, 0, frame_h), (gate_w / 2, fx1, 0, frame_h),
                             (-gate_w / 2, gate_w / 2, gate_h, frame_h)]:
        m.facing([(x0, ly, z + z0), (x1, ly, z + z0), (x1, ly, z + z1), (x0, ly, z + z1)], 'hocrown', (0, -1, 0))
    m.facing([(-gate_w / 2, ly - 2, z), (gate_w / 2, ly - 2, z), (gate_w / 2, ly - 2, z + gate_h),
              (-gate_w / 2, ly - 2, z + gate_h)], 'hogate', (0, -1, 0), event=gate_event, fit=True)
    gate_face = len(m.faces) - 1
    # Steps down from the gate to the gate road.
    for k in range(2):
        box(m, (0, gy - 110 - 110 * k, z - 40), (frame_w + 200 * (k + 1), 110, 70 - 30 * k), 'hpfloor', top='hpfloor')
    return m, gate_face


def dome(z, radius, crown):
    """The ribbed dome on the wall tops (hodomrib: its gold ribs and violet bands), 16 ribs by 5 rings."""
    m = Model('dome')
    m.dome((0.0, 0.0, z), radius, crown - WALL_H, 16, 5, 'hodomrib', z0=WALL_H)
    return m


def cannon_tower(z, height, radius=1000.0):
    """The great cannon's tower on the dome's crown: a short drum (hocannon, gold bands, hnfloor top) lifting the yoke
    over the dome's curve, so the cannon shows from the killing ground (the dome otherwise hides its crown)."""
    m = Model('cannon_tower')
    frustum(m, 0, 0, z - 200, z + height, radius * 1.15, radius, 16, 'hocannon', top='hnfloor')
    frustum(m, 0, 0, z + height - 120, z + height, radius * 1.04, radius * 1.04, 16, 'hntrim')
    return m


def bastion(name, cx, cy, z, radius=720.0, height=2000.0):
    """A round corner bastion (12 sides, hocannon) with its top (hnfloor) and a parapet ring (hntrim)."""
    m = Model(name)
    frustum(m, cx, cy, z, z + height, radius, radius, 12, 'hocannon', top='hnfloor', phase=math.pi / 12)
    outer = ring_points(cx, cy, radius + 10, 12, math.pi / 12)
    inner = ring_points(cx, cy, radius - 70, 12, math.pi / 12)
    top = z + height + 60                              # low, so the Crown Sentinel on the top shows over it
    for k in range(12):
        j = (k + 1) % 12
        mx, my = (outer[k][0] + outer[j][0]) / 2 - cx, (outer[k][1] + outer[j][1]) / 2 - cy
        m.facing([(*outer[k], z + height - 10), (*outer[j], z + height - 10), (*outer[j], top), (*outer[k], top)],
                 'hntrim', (mx, my, 0))
        m.facing([(*inner[k], z + height), (*inner[j], z + height), (*inner[j], top), (*inner[k], top)], 'hntrim',
                 (-mx, -my, 0))
        m.facing([(*inner[k], top), (*inner[j], top), (*outer[j], top), (*outer[k], top)], 'hntrim', (0, 0, 1))
    return m


# --- The Lattice nodes ----------------------------------------------------------------------------------------------
def blockhouse(name, door, outward, back, radius, z, event):
    """A node blockhouse: a low 12-sided drum under a dome (honode, crown 450), the blast door (hnblast, 320 x 260,
    the event face) at the end of a sloped vestibule on the outer flank, in a gold frame (hntrim). Returns the model
    and the dome's crown (for the node mast)."""
    m = Model(name)
    ox, oy = outward
    cx, cy = door[0] - ox * back, door[1] - oy * back
    drum = 140.0
    frustum(m, cx, cy, z - 20, z + drum, radius, radius, 12, 'honode', phase=math.atan2(oy, ox) + math.pi / 12)
    m.dome((cx, cy, z), radius, 450 - drum, 12, 4, 'honode', z0=drum)
    # The vestibule: from inside the drum out to the door, its roof sloping down to the door.
    ex, ey = -oy, ox                                   # across the door
    near, far = back - 420.0, back                     # from the centre, along outward
    half_w, h_back, h_front = 300.0, 420.0, 330.0

    def at(along, across, up):
        return (cx + ox * along + ex * across, cy + oy * along + ey * across, z + up)
    for side in (-1, 1):
        m.facing([at(near, side * half_w, 0), at(far, side * half_w, 0), at(far, side * half_w, h_front),
                  at(near, side * half_w, h_back)], 'honode', (ex * side, ey * side, 0))
    m.facing([at(near, -half_w, h_back), at(near, half_w, h_back), at(far, half_w, h_front),
              at(far, -half_w, h_front)], 'hnresin', (ox * 0.3, oy * 0.3, 1))
    # The front: the wall round the door, the door recessed 40 in a gold frame.
    dw, dh, inset = 320.0, 260.0, 40.0
    for (a0, a1, z0, z1) in [(-half_w, -dw / 2, 0, h_front), (dw / 2, half_w, 0, h_front), (-dw / 2, dw / 2, dh,
                                                                                             h_front)]:
        m.facing([at(far, a0, z0), at(far, a1, z0), at(far, a1, z1), at(far, a0, z1)], 'hntrim', (ox, oy, 0))
    m.facing([at(far - inset, -dw / 2, 0), at(far - inset, dw / 2, 0), at(far - inset, dw / 2, dh),
              at(far - inset, -dw / 2, dh)], 'hnblast', (ox, oy, 0), event=event, fit=True)
    for side in (-1, 1):
        m.facing([at(far, side * dw / 2, 0), at(far - inset, side * dw / 2, 0), at(far - inset, side * dw / 2, dh),
                  at(far, side * dw / 2, dh)], 'hntrim', (-ex * side, -ey * side, 0))
    m.facing([at(far, -dw / 2, dh), at(far, dw / 2, dh), at(far - inset, dw / 2, dh), at(far - inset, -dw / 2, dh)],
             'hntrim', (0, 0, -1))
    return m, (cx, cy, z + 450)


def conduit(name, a, b, z_at, width=300.0, height=180.0):
    """A Lattice conduit run: a duct (hocondt sides, hnresin top) from a to b, in 1 200 lengths on the ground."""
    m = Model(name)
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    pieces = max(1, int(round(length / 1200)))
    yaw = math.atan2(b[1] - a[1], b[0] - a[0])
    for k in range(pieces):
        t0, t1 = k / pieces, (k + 1) / pieces
        x = a[0] + (b[0] - a[0]) * (t0 + t1) / 2
        y = a[1] + (b[1] - a[1]) * (t0 + t1) / 2
        box(m, (x, y, z_at(x, y) - 30), (length / pieces + 2, width, height + 30), 'hocondt', yaw=yaw, top='hnresin')
    return m


# --- The killing ground's cover -------------------------------------------------------------------------------------
def cover_slab(m, centre, length, degrees, z, tilt=10.0, thick=120.0, height=700.0):
    """A tilted slab of black-violet resin with violet joints (hnfloor faces, hogold edges; the integrator's sheet
    review: hoplate read as Earth brickwork): 1 200 x 120 x 700, leaning tilt degrees, sunk 40."""
    yaw = math.radians(degrees)
    ax, ay = math.cos(yaw), math.sin(yaw)              # along the slab
    nx, ny = -ay, ax                                   # through it
    lean = height * math.tan(math.radians(tilt))
    cx, cy = centre
    pts = {}
    for i, along in enumerate((-length / 2, length / 2)):
        for j, through in enumerate((-thick / 2, thick / 2)):
            for k, up in enumerate((-40.0, height)):
                off = through + lean * (up / height)
                pts[i, j, k] = (cx + ax * along + nx * off, cy + ay * along + ny * off, z + up)
    quad = lambda keys: [pts[key] for key in keys]   # noqa: E731
    m.facing(quad([(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]), 'hnfloor', (-nx, -ny, 0))
    m.facing(quad([(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)]), 'hnfloor', (nx, ny, 0))
    m.facing(quad([(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]), 'hogold', (0, 0, 1))
    m.facing(quad([(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)]), 'hogold', (-ax, -ay, 0))
    m.facing(quad([(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]), 'hogold', (ax, ay, 0))


# --- The landing plaza ----------------------------------------------------------------------------------------------
def plaza(cx, cy, z, radius):
    """The colony's round landing pad: a disc 60 high under one fitted hoplaza face (the rings and the gold inlay,
    CR-P3-04), gold sides, and two steps down to the ground. 20 sides, not the design's 32: an ODM face has at most
    20 vertices, and the pad's top is one face so the texture's rings stay whole."""
    m = Model('plaza')
    SIDES = 20
    top = z + 60
    edge = ring_points(cx, cy, radius, SIDES)
    m.facing([(x, y, top) for x, y in edge], 'hoplaza', (0, 0, 1), fit=True)
    frustum(m, cx, cy, z + 30, top, radius, radius, SIDES, 'hogold')
    step = ring_points(cx, cy, radius + 120, SIDES)
    for k in range(SIDES):
        j = (k + 1) % SIDES
        m.facing([(*edge[k], z + 30), (*edge[j], z + 30), (*step[j], z + 30), (*step[k], z + 30)], 'hoplate',
                 (0, 0, 1))
    frustum(m, cx, cy, z - 30, z + 30, radius + 120, radius + 120, SIDES, 'hogold')
    return m, top


def lift_kiosk(x, y, z, front, event):
    """The colony's pad lift: as Starport Reach's Lift Head, smaller (520 across, 900 high): a 12-sided white
    tower (holift), gold bands, a dome (hoterm), the cage in a bay at the front (its fitted face the event)."""
    m = Model('pad_lift')
    f = houses.Frame(x, y, z, front)
    sides, radius, height = 12, 260.0, 900.0
    cy_ = radius
    ring = [(radius * math.cos(2 * math.pi * k / sides + math.pi / sides),
             cy_ + radius * math.sin(2 * math.pi * k / sides + math.pi / sides)) for k in range(sides)]
    for k in range(sides):
        (x0, y0), (x1, y1) = ring[k], ring[(k + 1) % sides]
        m.facing([f(x0, y0, 0), f(x1, y1, 0), f(x1, y1, height), f(x0, y0, height)], 'holift',
                 f.direction((x0 + x1) / 2, (y0 + y1) / 2 - cy_))
    for z0, z1 in ((0, 50), (height - 40, height)):
        band = [(1.06 * px, cy_ + 1.06 * (py - cy_)) for px, py in ring]
        for k in range(sides):
            (x0, y0), (x1, y1) = band[k], band[(k + 1) % sides]
            m.facing([f(x0, y0, z0), f(x1, y1, z0), f(x1, y1, z1), f(x0, y0, z1)], 'hogold',
                     f.direction((x0 + x1) / 2, (y0 + y1) / 2 - cy_))
        m.facing([f(px, py, z1) for px, py in band], 'hogold', f.direction(0, 0, 1))
    m.dome(f(0, cy_, height), radius + 16, 220, 12, 4, 'hoterm')
    bw, bd, bh = 260.0, 120.0, 380.0
    houses.block(m, f, -bw / 2, -bd, bw / 2, 40, 0, bh, {'front': None, 'all': 'hoterm'}, top='hogold')
    m.facing([f(-bw / 2 + 20, -bd, 0), f(bw / 2 - 20, -bd, 0), f(bw / 2 - 20, -bd, bh - 30),
              f(-bw / 2 + 20, -bd, bh - 30)], 'holift', f.direction(0, -1), event=event, fit=True)
    for px in (-bw / 2, bw / 2 - 20):
        houses.block(m, f, px, -bd - 6, px + 20, -bd + 4, 0, bh, 'hogold', top='hogold')
    houses.block(m, f, -bw / 2, -bd - 6, bw / 2, -bd + 4, bh - 30, bh, 'hogold', top='hogold')
    return m


# --- The districts --------------------------------------------------------------------------------------------------
def spine(m, x, y, z, radius=300.0, height=1600.0):
    """A Kreegan watch spine: an eight-sided resin spike (hokspine) 1 600 high on a short collar."""
    frustum(m, x, y, z - 30, z + 120, radius * 1.15, radius, 8, 'hokspine', phase=math.pi / 8)
    frustum(m, x, y, z + 120, z + height, radius, 30, 8, 'hokspine', phase=math.pi / 8)


def roost(m, x, y, z, radius, height):
    """A noble roost: an octagonal tower (horoost) to its perch platform at 80 % (hpfloor, gold-trimmed edge), a
    narrower crown storey to a flat top, and membrane banners (hpbanner) hanging under the platform on four sides."""
    perch = height * 0.8
    phase = math.pi / 8
    frustum(m, x, y, z - 30, z + perch - 60, radius, radius * 0.92, 8, 'horoost', phase=phase)
    platform = ring_points(x, y, radius * 1.55, 8, phase)
    frustum(m, x, y, z + perch - 60, z + perch, radius * 1.55, radius * 1.55, 8, 'hptrim', top='hpfloor',
            phase=phase)
    m.facing([(px, py, z + perch - 60) for px, py in platform], 'hptrim', (0, 0, -1))
    frustum(m, x, y, z + perch, z + height, radius * 0.7, radius * 0.62, 8, 'horoost', top='hpfloor', phase=phase)
    for k in range(0, 8, 2):                         # banners on four sides, under the platform's edge
        (ax, ay), (bx, by) = platform[k], platform[(k + 1) % 8]
        mx, my = (ax + bx) / 2, (ay + by) / 2
        out = np.array([mx - x, my - y])
        out /= np.linalg.norm(out)
        along = np.array([bx - ax, by - ay]) / math.hypot(bx - ax, by - ay)
        c = np.array([mx, my]) - out * 12
        w = min(220.0, radius * 0.5)
        top_z, low_z = z + perch - 70, z + perch - 70 - 900
        quad = [(*(c - along * w), low_z), (*(c + along * w), low_z), (*(c + along * w), top_z),
                (*(c - along * w), top_z)]
        m.facing(quad, 'hpbanner', (*out, 0), fit=True)
        m.facing([tuple(np.array(p) - np.array([*out, 0]) * 4) for p in reversed(quad)], 'hpbanner', (*-out, 0),
                 fit=True)
    return z + height


def shed(m, x, y, z, sx, sy, open_dir, height=700.0):
    """A grafting shed: resin walls (hokwall) on three sides, open toward open_dir (degrees), under a ribbed resin
    vault (hoaresin) along its long axis."""
    yaw = math.radians(open_dir) + math.pi / 2          # the box's south side faces open_dir
    c, s = math.cos(yaw), math.sin(yaw)
    w, d = (sx, sy) if abs(math.cos(math.radians(open_dir))) < 0.5 else (sy, sx)
    box(m, (x, y, z - 20), (w, d, height + 20), 'hokwall', yaw=yaw, sides={'south': None})
    # Inner faces of the three walls, 4 inside the outer ones (the shed is seen from its open front).
    hx, hy = w / 2 - 4, d / 2 - 4

    def at(px, py, pz):
        return (x + px * c - py * s, y + px * s + py * c, z + pz)
    for (a, b, n) in [((-hx, hy), (hx, hy), (0, -1)), ((hx, hy), (hx, -d / 2), (-1, 0)), ((-hx, -d / 2), (-hx, hy),
                                                                                       (1, 0))]:
        nx, ny = n[0] * c - n[1] * s, n[0] * s + n[1] * c
        m.facing([at(*a, -20), at(*b, -20), at(*b, height), at(*a, height)], 'hokwall', (nx, ny, 0))
    # The vault: six segments across the shed's width, from wall top to wall top, along its depth.
    rise = w * 0.32
    segments = 6
    for k in range(segments):
        a0, a1 = math.pi * k / segments, math.pi * (k + 1) / segments
        p0 = (-w / 2 * math.cos(a0), height + rise * math.sin(a0))
        p1 = (-w / 2 * math.cos(a1), height + rise * math.sin(a1))
        quad = [at(p0[0], -d / 2 - 60, p0[1]), at(p1[0], -d / 2 - 60, p1[1]), at(p1[0], d / 2, p1[1]),
                at(p0[0], d / 2, p0[1])]
        mid = (a0 + a1) / 2
        out = (-math.cos(mid) * c, -math.cos(mid) * s, math.sin(mid))
        m.facing(quad, 'hoaresin', out)
        m.facing([tuple(np.array(p) - np.array(out) * 4) for p in reversed(quad)], 'hoaresin',
                 tuple(-v for v in out))
    # The vault's back end is closed; its front stays open over the open side.
    pts = [at(-w / 2 * math.cos(math.pi * k / segments), d / 2, height + rise * math.sin(math.pi * k / segments))
           for k in range(segments + 1)]
    m.facing(pts, 'hokwall', (-s, c, 0))


def pen(m, x, y, z, sx, sy, degrees, open_side='south', height=500.0):
    """A cage pen of the Kept market: walls of bars (homarket) on three sides, two sided, open on its auction side
    so the Kept inside are seen from the plinth."""
    yaw = math.radians(degrees)
    c, s = math.cos(yaw), math.sin(yaw)
    hx, hy = sx / 2, sy / 2

    def at(px, py, pz):
        return (x + px * c - py * s, y + px * s + py * c, z + pz)
    walls = {'south': ((-hx, -hy), (hx, -hy)), 'east': ((hx, -hy), (hx, hy)), 'north': ((hx, hy), (-hx, hy)),
             'west': ((-hx, hy), (-hx, -hy))}
    for name, (a, b) in walls.items():
        if name == open_side:
            continue
        m.both([at(*a, -10), at(*b, -10), at(*b, height), at(*a, height)], 'homarket')
    for px, py in [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]:   # corner posts
        cx, cy, _ = at(px, py, 0)
        box(m, (cx, cy, z), (50, 50, height + 60), 'hptrim', yaw=yaw, top='hptrim', z0=-20)


def auction_plinth(m, x, y, z, radius, collar_event, collar_front):
    """The auction plinth: an octagon in two steps (hpfloor tops, hptrim sides) and the collar node on it, a short
    pedestal whose front (hkcollar, the event face; dark hkcollof once freed) faces collar_front (degrees)."""
    frustum(m, x, y, z - 20, z + 60, radius, radius, 8, 'hptrim', top='hpfloor', phase=math.pi / 8)
    frustum(m, x, y, z + 60, z + 120, radius * 0.78, radius * 0.78, 8, 'hptrim', top='hpfloor', phase=math.pi / 8)
    yaw = math.radians(collar_front) + math.pi / 2     # the pedestal's open south side faces the collar face
    box(m, (x, y, z + 120), (240, 140, 300), 'hptrim', yaw=yaw, top='hptrim', sides={'south': None})
    ox, oy = math.cos(math.radians(collar_front)), math.sin(math.radians(collar_front))
    ex, ey = -oy, ox
    fx, fy = x + ox * 72, y + oy * 72
    m.facing([(fx - ex * 120, fy - ey * 120, z + 120), (fx + ex * 120, fy + ey * 120, z + 120),
              (fx + ex * 120, fy + ey * 120, z + 420), (fx - ex * 120, fy - ey * 120, z + 420)], 'hkcollar',
             (ox, oy, 0), event=collar_event, fit=True)
    return len(m.faces) - 1


def pavilion(m, x, y, z, sx, sy, height=620.0):
    """The slavers' open pavilion: four resin posts (horoost) under a peaked membrane roof (hpbanner, two sided)."""
    hx, hy = sx / 2, sy / 2
    for px, py in [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]:
        box(m, (x + px, y + py, z), (70, 70, height), 'horoost', top='hptrim', z0=-20)
    apex = (x, y, z + height + 220)
    corners = [(x - hx - 60, y - hy - 60, z + height), (x + hx + 60, y - hy - 60, z + height),
               (x + hx + 60, y + hy + 60, z + height), (x - hx - 60, y + hy + 60, z + height)]
    for k in range(4):
        tri = [corners[k], corners[(k + 1) % 4], apex]
        out = np.cross(np.subtract(tri[1], tri[0]), np.subtract(tri[2], tri[0]))
        m.facing(tri, 'hpbanner', tuple(out))
        m.facing([tuple(np.array(p) - out / np.linalg.norm(out) * 4) for p in reversed(tri)], 'hpbanner',
                 tuple(-out))


def stall(name, x, y, z, front, event):
    """A K12 salvage booth (600 x 500): Starport Reach's salvage house with a lean-to roof and its door the event
    face (hhdoorsl)."""
    return houses.salvage_house(name, x, y, z, front, event, 600.0, 500.0, 'lean', windows=0, pipe=False,
                                awning=True, wall_top=380.0)


def ruin_dome(m, x, y, z, radius, open_from, seed):
    """A broken Ancient half-dome (hodome, two sided): the half facing away from open_from (degrees) stands, a few
    of its panels fallen, with a broken wall stub (hoterm) along the cut."""
    rng = np.random.default_rng(seed)
    sides, rings = 16, 5
    rise = radius * 0.8
    base = math.radians(open_from) + math.pi / 2       # the standing half runs from base to base + pi

    def point(k, r):
        a = base + math.pi * k / (sides // 2)
        angle = math.pi / 2 * r / rings
        rr = radius * math.cos(angle)
        return (x + rr * math.cos(a), y + rr * math.sin(a), z - 30 + rise * math.sin(angle) + (40 if r else 0))
    for r in range(rings - 1):
        for k in range(sides // 2):
            if r >= 2 and rng.random() < 0.3:          # fallen panels high up
                continue
            quad = [point(k, r), point(k + 1, r), point(k + 1, r + 1), point(k, r + 1)]
            centre = np.mean(np.array(quad), 0) - np.array([x, y, z])
            m.facing(quad, 'hodome', tuple(centre))
            m.facing([tuple(np.array(p) - centre / np.linalg.norm(centre) * 4) for p in reversed(quad)], 'hodome',
                     tuple(-centre))
    yaw = base
    for k, t in enumerate((-0.6, 0.0, 0.55)):
        px, py = x + math.cos(base + math.pi / 2) * radius * t, y + math.sin(base + math.pi / 2) * radius * t
        box(m, (px, py, z), (radius * 0.45, 90, 180 + 160 * rng.random()), 'hoterm', yaw=yaw, top='hoterm', z0=-30)


def hatch(name, x, y, z, front, event):
    """A service tunnel hatch: a ceramic surround (hoterm) set into a black-glass outcrop at the rim's foot, the
    round hatch (hohatch) in a gold rim on its front, facing front (degrees)."""
    m = Model(name)
    ox, oy = math.cos(math.radians(front)), math.sin(math.radians(front))
    yaw = math.radians(front) - math.pi / 2
    box(m, (x - ox * 450, y - oy * 450, z), (900, 940, 650), 'hoterm', yaw=yaw, top='hoterm', z0=-40)   # into the rock
    m.disc((x + ox * 22, y + oy * 22, z + 300), 230, (ox, oy), 'hohatch', event=event, rim=50, rim_depth=40,
           rim_texture='hogold')
    box(m, (x + ox * 120, y + oy * 120, z - 30), (520, 240, 50), 'hoplate', yaw=yaw, top='hoplate')
    return m


def test_plinth(m, x, y, z, radius=300.0, height=220.0):
    frustum(m, x, y, z - 30, z + height, radius, radius * 0.9, 12, 'hocannon', top='hnfloor')
    return z + height


def blast_wall(m, a, b, z_at, height=600.0, thick=150.0):
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    box(m, (cx, cy, min(z_at(*a), z_at(*b)) - 30), (length, thick, height + 30), 'hocannon',
        yaw=math.atan2(b[1] - a[1], b[0] - a[0]), top='hntrim')


# --- The Blooding Ring (HARROWERS.md, THE_CROWN.md section 7) ---------------------------------------------------------
RING_SIDES = 32


def blooding_ring(cx, cy, z, radius, gate_degrees, gate_sides=2, height=400.0, thick=150.0, cheek=250.0,
                  blind=800.0, blind_half=800.0, dais_radius=380.0, dais_height=90.0):
    """The Harrowers' proving pit: a ring wall of black resin (hoaresin, an hnresin coping) round a floor of
    `radius`, open in one gate of `gate_sides` of its 32 sides centred on gate_degrees. Cheek walls line the gate to
    `cheek` past the wall's outer face, a gate post (horoost) at each one's mouth, and a blind wall `blind` beyond the
    outer face (2 x blind_half long) screens the gate: no line from the ring road reaches the floor. The low bone dais
    (hokspine sides, an ivory hptrim top) stands in the middle. Returns the model and the dais's top."""
    m = Model('blooding_ring')
    step = 2 * math.pi / RING_SIDES
    gate = math.radians(gate_degrees)
    inner = ring_points(cx, cy, radius, RING_SIDES, gate)       # vertex 0 on the gate's centre line
    outer = ring_points(cx, cy, radius + thick, RING_SIDES, gate)
    half_gate = gate_sides // 2
    gate_segments = {(k % RING_SIDES) for k in range(-half_gate, half_gate)}
    low, top = z - 40, z + height
    for k in range(RING_SIDES):
        if k in gate_segments:
            continue
        j = (k + 1) % RING_SIDES
        mid = gate + step * (k + 0.5)
        out = (math.cos(mid), math.sin(mid), 0.0)
        m.facing([(*inner[k], low), (*inner[j], low), (*inner[j], top), (*inner[k], top)], 'hoaresin',
                 (-out[0], -out[1], 0.0))
        m.facing([(*outer[k], low), (*outer[j], low), (*outer[j], top), (*outer[k], top)], 'hoaresin', out)
        m.facing([(*inner[k], top), (*inner[j], top), (*outer[j], top), (*outer[k], top)], 'hnresin', (0, 0, 1))
    ox, oy = math.cos(gate), math.sin(gate)                     # out along the gate's axis
    px, py = -oy, ox
    opening = radius * math.sin(step * half_gate)               # the gate's half width at the wall's inner face
    inner_face = radius * math.cos(step * half_gate)
    mouth = radius + thick + cheek
    for side in (-1, 1):
        off = side * (opening + thick / 2)
        along = (inner_face + mouth) / 2
        box(m, (cx + ox * along + px * off, cy + oy * along + py * off, z), (mouth - inner_face, thick, height + 40),
            'hoaresin', yaw=gate, top='hnresin', z0=-40)
        box(m, (cx + ox * mouth + px * off, cy + oy * mouth + py * off, z), (thick + 90, thick + 90, height + 300),
            'horoost', yaw=gate, top='hptrim', z0=-40)
    far = radius + thick + blind + thick / 2
    box(m, (cx + ox * far, cy + oy * far, z), (thick, 2 * blind_half + thick, height + 40), 'hoaresin', yaw=gate,
        top='hnresin', z0=-40)
    frustum(m, cx, cy, z - 20, z + dais_height, dais_radius, dais_radius * 0.88, 8, 'hokspine', top='hptrim',
            phase=math.pi / 8)
    return m, z + dais_height
