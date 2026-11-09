"""Starport Reach's house kit: simple houses as BModels in the manner of MM6-8 (a box or two, a roof, a door and
windows as faces of their own), the look carried by the house textures of design/kreegan_world/art/textures_out1
(round 3). Every house is built in its own frame: x along its front, y from the front (y = 0) to the back, z up
from its floor; the front faces `front` (radians). The door is one fitted face, recessed into the wall with trimmed
jambs, so it reads as the way in; windows are fitted faces on shallow boxes standing out of the wall.

    salvage_house  scrap-clad walls on a slab plinth, a gable or lean-to roof of corrugated sheet, an awning, a stove
                   pipe (the Hesperian village, the Ashrunner camp)
    hull_house     a gutted crawler hull lying on its treads, the door in its front end, a stove pipe
    hab_house      an Ancient habitat module of white ceramic under a curved roof (the Hesperian village)
    shop_house     a shop: the salvage house with a sign over the door and a hanging sign beside it
    lift_head      the round tower of the lift to the Undervault, the gold cage at the front as its door
    prefab_wall    the Hesperian village's ring wall of prefab panels, with gate towers
    town_wall      Landfall's polygon wall with its wall-walk, gates and towers
Houses take a skin: `salvage` (scrap, rust) or `prefab` (the Hesperians' colony stock).
"""
import math

import numpy as np

from bmodels import Model

DOOR_W, DOOR_H, DOOR_INSET = 128.0, 256.0, 16.0


class Frame:
    def __init__(self, x, y, z, front):
        self.origin = np.array([x, y, z], dtype=np.float64)
        yaw = front + math.pi / 2                       # local -y (out of the front) points along `front`
        c, s = math.cos(yaw), math.sin(yaw)
        self.ex = np.array([c, s, 0.0])
        self.ey = np.array([-s, c, 0.0])

    def __call__(self, x, y, z):
        return tuple(self.origin + self.ex * x + self.ey * y + np.array([0.0, 0.0, z]))

    def direction(self, x, y, z=0.0):
        return self.ex * x + self.ey * y + np.array([0.0, 0.0, z])


def block(m, f, x0, y0, x1, y1, z0, z1, side, top=None, bottom=False, skip=()):
    """An axis box in the house frame: sides `side` (or {'front': ..., ...}), top `top`."""
    sides = side if isinstance(side, dict) else {}
    texture = (lambda name: sides.get(name, sides.get('all'))) if sides else (lambda name: side)
    quads = {'front': ([(x0, y0), (x1, y0)], (0, -1)), 'right': ([(x1, y0), (x1, y1)], (1, 0)),
             'back': ([(x1, y1), (x0, y1)], (0, 1)), 'left': ([(x0, y1), (x0, y0)], (-1, 0))}
    for name, ((a, b), out) in quads.items():
        if name in skip or texture(name) is None:
            continue
        m.facing([f(*a, z0), f(*b, z0), f(*b, z1), f(*a, z1)], texture(name), f.direction(*out))
    if top:
        m.facing([f(x0, y0, z1), f(x1, y0, z1), f(x1, y1, z1), f(x0, y1, z1)], top, f.direction(0, 0, 1))
    if bottom:
        m.facing([f(x0, y0, z0), f(x1, y0, z0), f(x1, y1, z0), f(x0, y1, z0)], side if isinstance(side, str)
                 else bottom, f.direction(0, 0, -1))


def door_frame(m, f, a, b, y, z0, top, texture, out=(0, -1), width=26.0, depth=14.0):
    """A frame standing out of the wall round a door opening from a to b: two jambs and a lintel, so the door reads
    against a wall of its own colour."""
    oy = out[1]
    y1 = y + oy * depth
    for x0, x1 in ((a - width, a), (b, b + width)):
        block(m, f, x0, min(y, y1), x1, max(y, y1), z0, top + width, {'back' if oy < 0 else 'front': None,
                                                                    'all': texture}, top=texture)
    block(m, f, a, min(y, y1), b, max(y, y1), top, top + width, {'back' if oy < 0 else 'front': None,
                                                                'all': texture}, top=texture)


def wall_with_door(m, f, x0, x1, y, z0, z1, wall, trim, door, event, door_x=0.0, out=(0, -1), door_w=DOOR_W,
                   door_h=DOOR_H, inset=DOOR_INSET, frame=None):
    """A wall in the plane y from x0 to x1 (facing `out`), a door opening of door_w x door_h at door_x, the door
    face recessed by `inset` with trim jambs and lintel, and a `frame` standing out round it when given."""
    o = f.direction(*out)
    a, b = door_x - door_w / 2, door_x + door_w / 2
    top = min(z0 + door_h, z1)
    pieces = [(x0, a, z0, z1), (b, x1, z0, z1), (a, b, top, z1)]
    for p0, p1, q0, q1 in pieces:
        if p1 - p0 > 1 and q1 - q0 > 1:
            m.facing([f(p0, y, q0), f(p1, y, q0), f(p1, y, q1), f(p0, y, q1)], wall, o)
    d = -inset * out[1]                                 # into the wall
    m.facing([f(a, y + d, z0), f(b, y + d, z0), f(b, y + d, top), f(a, y + d, top)], door, o, event=event, fit=True)
    m.facing([f(a, y, z0), f(a, y + d, z0), f(a, y + d, top), f(a, y, top)], trim, f.direction(1, 0))
    m.facing([f(b, y + d, z0), f(b, y, z0), f(b, y, top), f(b, y + d, top)], trim, f.direction(-1, 0))
    m.facing([f(a, y, top), f(b, y, top), f(b, y + d, top), f(a, y + d, top)], trim, f.direction(0, 0, -1))
    if frame:
        door_frame(m, f, a, b, y, z0, top, frame, out)


def window(m, f, x, y, z, out, frame, glass, size=96.0, depth=10.0):
    """A window box standing `depth` out of the wall plane y (its glass the fitted `glass` face)."""
    ox, oy = out
    h = size / 2
    if ox == 0:                                         # on a front or back wall
        y1 = y + oy * depth
        block(m, f, x - h, min(y, y1), x + h, max(y, y1), z, z + size,
              {'front' if oy < 0 else 'back': None, 'all': frame}, top=frame)
        m.facing([f(x - h, y1, z), f(x + h, y1, z), f(x + h, y1, z + size), f(x - h, y1, z + size)], glass,
                 f.direction(0, oy), fit=True)
    else:                                               # on a side wall: x is the wall plane, y along it
        x1 = x + ox * depth
        block(m, f, min(x, x1), y - h, max(x, x1), y + h, z, z + size,
              {'right' if ox > 0 else 'left': None, 'all': frame}, top=frame)
        m.facing([f(x1, y - h, z), f(x1, y + h, z), f(x1, y + h, z + size), f(x1, y - h, z + size)], glass,
                 f.direction(ox, 0), fit=True)


def slab(m, f, corners, thickness, top, edge):
    """A thin roof or awning plate: corners (four (x, y, z) in the house frame, counter-clockwise from above),
    extruded down by thickness."""
    up = [f(*c) for c in corners]
    down = [f(c[0], c[1], c[2] - thickness) for c in corners]
    m.facing(up, top, f.direction(0, 0, 1))
    m.facing(down, top, f.direction(0, 0, -1))
    centre = np.mean(np.array(up), 0)
    for i in range(4):
        j = (i + 1) % 4
        quad = [down[i], down[j], up[j], up[i]]
        mid = (np.array(up[i]) + np.array(up[j])) / 2
        m.facing(quad, edge, mid - centre)


SKINS = {
    # The Ashrunners' and the outskirts' scrap; the Hesperian village's colony prefab stock.
    'salvage': {'wall': 'hhscrapw', 'plinth': 'hhplinth', 'roof': 'hhcorrug', 'trim': 'hhtrimrs', 'door': 'hhdoorsl',
                'frame': 'hoterm', 'window': 'hhwinsl', 'awning': 'hotarp'},
    # The prefab walls are the plain panels: hhprefab's and hhprefdk's vents, repeated on every tile, read as rows of
    # vents on a house or a tower.
    'prefab': {'wall': 'hhwallpf', 'plinth': 'hoplate', 'roof': 'hhprefrf', 'trim': 'hhpost', 'door': 'hhdoorpf',
               'frame': 'hhpost', 'window': 'hhwinpf', 'awning': 'hotarp'},
    # Landfall's second finish: the same stock, slate grey-green with ochre markings.
    'prefab_dark': {'wall': 'hhwalldk', 'plinth': 'hoplate', 'roof': 'hhprefrd', 'trim': 'hhpostdk', 'door': 'hhdoordk',
                    'frame': 'hhpostdk', 'window': 'hhwindk', 'awning': 'hfcloth'},
}


def door_steps(m, f, door_x, floor, plinth, steps=2):
    """Steps from the ground (z 0) up to a door on a plinth `floor` high whose front is at y = -plinth: `steps` treads
    of equal rise, 100 deep, a little wider than the door."""
    half = DOOR_W / 2 + 50
    for k in range(steps):
        rise = floor * (k + 1) / (steps + 1)
        y0 = -plinth - 100 * (steps - k)
        block(m, f, door_x - half, y0, door_x + half, -plinth, -40, rise, 'hoplate', top='hoplate')


def salvage_house(name, x, y, z, front, event, width=520.0, depth=420.0, roof='gable', windows=2, pipe=True,
                  awning=True, wall_top=400.0, door_x=None, skin='salvage'):
    """A box house with a gable or lean-to roof, in the salvage or the prefab skin (SKINS)."""
    t = SKINS[skin]
    m = Model(name)
    f = Frame(x, y, z, front)
    w, d, base = width / 2, depth, 60.0
    door_x = (-w * 0.25 if windows else 0.0) if door_x is None else door_x
    block(m, f, -w - 12, -12, w + 12, d + 12, -40, base, t['plinth'], top='hoplate')
    wall_with_door(m, f, -w, w, 0.0, base, wall_top, t['wall'], t['trim'], t['door'], event,
                   door_x=door_x, frame=t['frame'])
    door_steps(m, f, door_x, base, 12)
    if roof == 'gable':
        ridge = wall_top + 170
        block(m, f, -w, 0, w, d, base, wall_top, t['wall'], skip=('front',))
        for xs in (-w, w):                                         # gable ends
            out = (1 if xs > 0 else -1, 0)
            m.facing([f(xs, 0, wall_top), f(xs, d, wall_top), f(xs, d / 2, ridge)], t['wall'], f.direction(*out))
        over = 50.0
        for (y0, y1) in ((-over, d / 2), (d / 2, d + over)):       # the two roof slopes, eaves overhanging
            low = wall_top - over * 170 / (d / 2)
            if y0 < d / 2:
                corners = [(-w - over, y0, low), (w + over, y0, low), (w + over, y1, ridge), (-w - over, y1, ridge)]
            else:
                corners = [(-w - over, y0, ridge), (w + over, y0, ridge), (w + over, y1, low), (-w - over, y1, low)]
            slab(m, f, corners, 10, t['roof'], t['trim'])
    else:                                                          # lean-to: low at the front, high at the back
        high, low = wall_top + 150, wall_top
        block(m, f, -w, 0, w, d, base, low, t['wall'], skip=('front',))
        m.facing([f(-w, d, low), f(w, d, low), f(w, d, high), f(-w, d, high)], t['wall'], f.direction(0, 1))
        for xs in (-w, w):
            m.facing([f(xs, 0, low), f(xs, d, low), f(xs, d, high)], t['wall'], f.direction(1 if xs > 0 else -1, 0))
        rise = (high - low) / d
        slab(m, f, [(-w - 40, -60, low - 60 * rise + 10), (w + 40, -60, low - 60 * rise + 10),
                    (w + 40, d + 40, high + 40 * rise + 10), (-w - 40, d + 40, high + 40 * rise + 10)], 10,
             t['roof'], t['trim'])
    left, right = door_x + DOOR_W / 2 + 60, w - 30               # front windows in the wall beside the door
    count = min(windows, int((right - left) // 130))
    for k in range(count):
        window(m, f, left + (right - left) * (k + 0.5) / count, 0.0, base + 130, (0, -1), t['frame'], t['window'])
    window(m, f, w, d * 0.5, base + 130, (1, 0), t['frame'], t['window'])
    for cx in (-w, w):                                             # corner trims
        for cy in (0, d):
            block(m, f, cx - 10, cy - 10, cx + 10, cy + 10, base, wall_top, t['trim'], top=t['trim'])
    if awning:
        dx = door_x
        slab(m, f, [(dx - 130, -170, base + 280), (dx + 130, -170, base + 280), (dx + 130, 2, base + 330),
                    (dx - 130, 2, base + 330)], 6, t['awning'], t['awning'])
        for px in (dx - 120, dx + 120):                          # its posts, on the ground beside the steps
            block(m, f, px - 6, -166, px + 6, -154, -20, base + 282, t['trim'])
    if pipe:
        m.tube(f(w - 90, d - 90, wall_top - 40), f(w - 90, d - 90, wall_top + 300), 18, 'hoscrap')
    return m


def hull_house(name, x, y, z, front, event, length=860.0, radius=210.0, skin='salvage'):
    """A crawler hull lying front to back (its front end, with the door, toward `front`) on its two treads."""
    hull, trim, wall, door = (('hhhull', 'hhtrimrs', 'hhscrapw', 'hhdoorsl') if skin == 'salvage' else
                              ('hhwallpf', 'hhpost', 'hhwallpf', 'hhdoorpf'))
    m = Model(name)
    f = Frame(x, y, z, front)
    tread, sides, sill = 70.0, 8, 40.0
    zc = tread + 30                                    # the hull's axis height
    ring = [(radius * math.cos(math.pi * k / sides), zc + radius * 1.25 * math.sin(math.pi * k / sides))
            for k in range(sides + 1)]                 # from the right side (k = 0) over the top to the left
    for k in range(sides):                                         # the hull shell
        (x0, z0), (x1, z1) = ring[k], ring[k + 1]
        mid = math.pi * (k + 0.5) / sides
        m.facing([f(x0, 0, z0), f(x1, 0, z1), f(x1, length, z1), f(x0, length, z0)], hull,
                 f.direction(math.cos(mid), 0, math.sin(mid)))
    for side in (-1, 1):                                           # the treads under the hull's sides
        block(m, f, side * radius - 60, -20, side * radius + 50, length + 20, 0, tread,
              {'front': trim, 'back': trim, 'left': 'hhtread', 'right': 'hhtread'}, top=trim)
    block(m, f, -radius + 70, 0, radius - 70, length, 0, zc, wall, skip=('front', 'back'))

    def arc_z(px):                                                 # the shell's height above px
        for (x0, z0), (x1, z1) in zip(ring, ring[1:]):
            if min(x0, x1) <= px <= max(x0, x1) and x0 != x1:
                return z0 + (z1 - z0) * (px - x0) / (x1 - x0)
        return zc
    outline_left = [(px, pz) for px, pz in ring if px < 0]          # the left half of the arc, top down
    outline_right = [(px, pz) for px, pz in ring if px > 0]
    a, b, top = -DOOR_W / 2, DOOR_W / 2, sill + DOOR_H
    front = f.direction(0, -1)
    # The front end: a left and a right piece beside the door and a cap above it, each convex.
    m.facing([f(-radius, 0, sill), f(a, 0, sill), f(a, 0, arc_z(a))] +
             [f(px, 0, pz) for px, pz in outline_left if px < a], wall, front)
    m.facing([f(b, 0, sill), f(radius, 0, sill)] + [f(px, 0, pz) for px, pz in outline_right if px > b] +
             [f(b, 0, arc_z(b))], wall, front)
    m.facing([f(a, 0, top), f(b, 0, top), f(b, 0, arc_z(b))] + [f(px, 0, pz) for px, pz in ring if a < px < b] +
             [f(a, 0, arc_z(a))], wall, front)
    d = DOOR_INSET
    m.facing([f(a, d, sill), f(b, d, sill), f(b, d, top), f(a, d, top)], door, front, event=event, fit=True)
    for px, dirx in ((a, 1), (b, -1)):
        m.facing([f(px, 0, sill), f(px, d, sill), f(px, d, top), f(px, 0, top)], trim, f.direction(dirx, 0))
    m.facing([f(a, 0, top), f(b, 0, top), f(b, d, top), f(a, d, top)], trim, f.direction(0, 0, -1))
    door_frame(m, f, a, b, 0.0, sill, top, 'hoterm')
    block(m, f, a - 60, -110, b + 60, 0, sill - 40, sill, trim, top='hoplate')           # the step
    block(m, f, -radius, -2, radius, 0, 0, sill, trim, skip=('back',), top=None)       # the sill below
    # The back end: whole.
    m.facing([f(-radius, length, sill), f(radius, length, sill)] + [f(px, length, pz) for px, pz in ring],
             wall, f.direction(0, 1))
    for k in (0.3, 0.7):                                           # windows along the sides
        for side in (-1, 1):
            window(m, f, side * radius * 0.93, length * k, zc + 40, (side, 0), 'hoterm', 'hhwinsl', size=80)
    crest = zc + radius * 1.25
    m.tube(f(radius * 0.4, length * 0.2, crest - 40), f(radius * 0.4, length * 0.2, crest + 240), 18, 'hoscrap')
    return m


def hab_house(name, x, y, z, front, event, width=600.0, depth=380.0, sign=None):
    """An Ancient habitat module: a white ceramic box on a low plinth under a curved roof, the door in the front; a
    shop's square corner sign (sign) sticking out from its front corner."""
    m = Model(name)
    f = Frame(x, y, z, front)
    w, d, base, top = width / 2, depth, 40.0, 360.0
    block(m, f, -w - 16, -16, w + 16, d + 16, -40, base, 'hoplate', top='hoplate')
    wall_with_door(m, f, -w, w, 0.0, base, top, 'hhmodule', 'hogold', 'hhmoddr', event)
    door_steps(m, f, 0.0, base, 16, steps=1)
    block(m, f, -w, 0, w, d, base, top, 'hhmodule', skip=('front',))
    rise, steps = 110.0, 6
    arc = [(d * k / steps, top + rise * math.sin(math.pi * k / steps)) for k in range(steps + 1)]
    for k in range(steps):                                         # the curved roof, front to back
        (y0, z0), (y1, z1) = arc[k], arc[k + 1]
        mid = math.pi * (k + 0.5) / steps
        m.facing([f(-w - 20, y0, z0), f(w + 20, y0, z0), f(w + 20, y1, z1), f(-w - 20, y1, z1)], 'hhmodrf',
                 f.direction(0, -math.cos(mid), math.sin(mid) + 0.2))
    for xs in (-w - 20, w + 20):                                   # the roof's end caps
        m.facing([f(xs, py, pz) for py, pz in arc], 'hhmodule', f.direction(1 if xs > 0 else -1, 0))
    block(m, f, -w - 6, -6, w + 6, d + 6, top - 24, top, 'hogold')
    if sign:
        blade_sign(m, f, w + 6, top - 34, sign, 'hogold', start=0.0)      # against the side wall
    return m


def blade_sign(m, f, x, top, sign, trim, size=120.0, thickness=12.0, start=-10.0):
    """MM6-8's shop sign: a square framed board fixed to a house's front corner and sticking straight out from the
    front (y < 0) from `start` (against the front or its corner trim), in the plane x of the side wall, its top at
    `top`; the trade's icon (hhsq<name>, the square half of the hfsign<name> board) on both faces, so it reads from
    down the street either way."""
    y0, y1, z0 = start - size, start, top - size
    block(m, f, x - thickness / 2, y0, x + thickness / 2, y1, z0, top, trim, top=trim, bottom=True,
          skip=('left', 'right'))                            # the faces are the icon itself (its own gold frame)
    square = 'hhsq' + sign[len('hfsign'):]
    for side in (-1, 1):
        px = x + side * thickness / 2
        m.facing([f(px, y0, z0), f(px, y1, z0), f(px, y1, top), f(px, y0, top)], square, f.direction(side, 0),
                 fit=True)


def shop_house(name, x, y, z, front, event, sign='hhsignmk', width=600.0, depth=440.0, skin='salvage'):
    """A shop as MM6-8 have them: a house (the salvage house, its front wall taller) with its sign board over the
    door and the square corner sign sticking out from its front corner, so the shop reads from down the street."""
    door_x = -width * 0.18
    m = salvage_house(name, x, y, z, front, event, width, depth, 'gable', windows=1, pipe=False, awning=False,
                      wall_top=500.0, door_x=door_x, skin=skin)
    trim = SKINS[skin]['trim']
    f = Frame(x, y, z, front)
    sw, sh, sz = 256.0, 128.0, 60.0 + DOOR_H + 40          # the board over the door
    block(m, f, door_x - sw / 2 - 10, -14, door_x + sw / 2 + 10, 0, sz - 10, sz + sh + 10, trim,
          top=trim)
    m.facing([f(door_x - sw / 2, -15, sz), f(door_x + sw / 2, -15, sz), f(door_x + sw / 2, -15, sz + sh),
              f(door_x - sw / 2, -15, sz + sh)], sign, f.direction(0, -1), fit=True)
    if sign.startswith('hfsign'):                           # the trades' signs (not the Ashrunners' board)
        blade_sign(m, f, width / 2, 460.0, sign, trim)     # under the eaves
    return m


def lift_head(name, x, y, z, front, event):
    """The Lift Head: a twelve-sided white tower with blue light slots, gold bands and a dome, the lift cage in a
    bay at the front as its door."""
    m = Model(name)
    f = Frame(x, y, z, front)
    sides, radius, height = 12, 330.0, 900.0
    cx, cy = 0.0, radius                               # the tower's axis, its front tangent at y = 0
    ring = [(cx + radius * math.cos(2 * math.pi * k / sides + math.pi / sides),
             cy + radius * math.sin(2 * math.pi * k / sides + math.pi / sides)) for k in range(sides)]
    for k in range(sides):
        (x0, y0), (x1, y1) = ring[k], ring[(k + 1) % sides]
        mx, my = (x0 + x1) / 2 - cx, (y0 + y1) / 2 - cy
        m.facing([f(x0, y0, 0), f(x1, y1, 0), f(x1, y1, height), f(x0, y0, height)], 'hhliftw', f.direction(mx, my),
                 fit=True)
    for z0, z1, grow in ((0, 50, 20), (height - 40, height, 24)):  # gold bands
        band = [(cx + (radius + grow) * math.cos(2 * math.pi * k / sides + math.pi / sides),
                 cy + (radius + grow) * math.sin(2 * math.pi * k / sides + math.pi / sides)) for k in range(sides)]
        for k in range(sides):
            (x0, y0), (x1, y1) = band[k], band[(k + 1) % sides]
            mx, my = (x0 + x1) / 2 - cx, (y0 + y1) / 2 - cy
            m.facing([f(x0, y0, z0), f(x1, y1, z0), f(x1, y1, z1), f(x0, y0, z1)], 'hogold', f.direction(mx, my))
        m.facing([f(px, py, z1) for px, py in band], 'hogold', f.direction(0, 0, 1))
    origin = f(cx, cy, height)
    m.dome(origin, radius + 10, 260, 12, 4, 'hhliftrf')
    # The cage bay: a box standing out of the front, the cage its front face.
    bw, bd, bh = 300.0, 140.0, 420.0
    block(m, f, -bw / 2, -bd, bw / 2, 40, 0, bh, {'front': None, 'all': 'hhliftw'}, top='hogold')
    m.facing([f(-bw / 2 + 22, -bd, 0), f(bw / 2 - 22, -bd, 0), f(bw / 2 - 22, -bd, bh - 30),
              f(-bw / 2 + 22, -bd, bh - 30)], 'hhcage', f.direction(0, -1), event=event, fit=True)
    for px in (-bw / 2, bw / 2 - 22):                              # gold frame round the cage
        block(m, f, px, -bd - 6, px + 22, -bd + 4, 0, bh, 'hogold', top='hogold')
    block(m, f, -bw / 2, -bd - 6, bw / 2, -bd + 4, bh - 30, bh, 'hogold', top='hogold')
    block(m, f, -bw / 2 - 30, -bd - 90, bw / 2 + 30, -bd + 10, -30, 20, 'hoplate', top='hoplate')    # the step
    return m


def town_wall(name, outline, z, gates, towers, height=640.0, walk=200.0, gate_w=640.0, tower_h=900.0,
              tower_size=420.0, gate_h=520.0, inside=None):
    """Landfall's wall (landfall_plan.py): the settlers' prefab panels along a line, `walk` thick with the wall-walk on
    top, open at each gate (a point on a stretch) under a lintel with the town's sign on both faces; square towers
    (centres) rise above it. A closed outline runs counter-clockwise; an open line (inside: a point in the town)
    ends where it meets the rock. One model for the whole wall."""
    m = Model(name)
    points = [np.array(p, dtype=np.float64) for p in outline]
    gate_points = [np.array(g, dtype=np.float64) for g in gates]
    half = walk / 2
    stretches = len(points) if inside is None else len(points) - 1
    for i in range(stretches):
        a, b = points[i], points[(i + 1) % len(points)]
        length = float(np.linalg.norm(b - a))
        along = (b - a) / length
        out = np.array([along[1], -along[0]])               # the outward normal of a counter-clockwise outline
        if inside is not None and np.dot(np.array(inside) - a, out) > 0:
            out = -out                                       # an open line: away from the town
        cuts = []
        for g in gate_points:
            t = float(np.dot(g - a, along))
            if 0 < t < length and abs(float(np.dot(g - a, out))) < 1.0:
                cuts.append((t - gate_w / 2, t + gate_w / 2))
        pieces, start = [], 0.0
        for c0, c1 in sorted(cuts):
            pieces.append((start, c0))
            start = c1
        pieces.append((start, length))
        for t0, t1 in pieces:
            p0, p1 = a + along * t0, a + along * t1
            o0, o1 = p0 + out * half, p1 + out * half
            i0, i1 = p0 - out * half, p1 - out * half
            m.facing([(*o0, z - 20), (*o1, z - 20), (*o1, z + height), (*o0, z + height)], 'hhwallpf', (*out, 0))
            m.facing([(*i1, z - 20), (*i0, z - 20), (*i0, z + height), (*i1, z + height)], 'hhwallpf', (*-out, 0))
            m.facing([(*o0, z + height), (*o1, z + height), (*i1, z + height), (*i0, z + height)], 'hhpost',
                     (0, 0, 1))
            for p, sign in ((p0, -1), (p1, 1)):             # the wall's ends at the gates, unless in a tower
                covered = any(np.max(np.abs(p - np.array(c))) <= tower_size / 2 + 1 for c in towers)
                if ((sign < 0 and t0 > 0) or (sign > 0 and t1 < length)) and not covered:
                    q0, q1 = p + out * half, p - out * half
                    m.facing([(*q0, z - 20), (*q1, z - 20), (*q1, z + height), (*q0, z + height)], 'hhpost',
                             (*(along * sign), 0))
        for c0, c1 in cuts:                                  # the gate's lintel and sign
            p0, p1 = a + along * c0, a + along * c1
            f = Frame(*(p0 + p1) / 2, z, math.atan2(out[1], out[0]))
            block(m, f, -gate_w / 2, -half, gate_w / 2, half, gate_h, height, 'hhwallpf', top='hhpost', bottom=True)
            for face_y, direction in ((-half - 1, (0, -1)), (half + 1, (0, 1))):
                xs = (-200, 200) if direction[1] < 0 else (200, -200)
                m.facing([f(xs[0], face_y, gate_h + 10), f(xs[1], face_y, gate_h + 10), f(xs[1], face_y, height - 10),
                          f(xs[0], face_y, height - 10)], 'hhgatesg', f.direction(*direction), fit=True)
    for tx, ty in towers:
        f = Frame(tx, ty, z, 0.0)
        t = tower_size / 2
        block(m, f, -t, -t, t, t, -20, tower_h, 'hhwallpf', top='hhpost')
        block(m, f, -t - 20, -t - 20, t + 20, t + 20, tower_h - 60, tower_h, 'hhpost', top='hhpost')
    return m


def tall_house(name, x, y, z, front, event, width=800.0, depth=800.0, skin='prefab', sign=None):
    """A two-storey prefab house: a door and windows below, a balcony on posts across the front of the upper storey
    (its railing a trim band), windows above, a flat roof inside a low parapet. A shop's sign (sign) is fitted on the
    railing's front over the door, and its square corner sign sticks out from the upper storey's front corner, above
    the balcony."""
    t = SKINS[skin]
    m = Model(name)
    f = Frame(x, y, z, front)
    w, d, base, top = width / 2, depth, 60.0, 760.0
    block(m, f, -w - 12, -12, w + 12, d + 12, -40, base, t['plinth'], top='hoplate')
    wall_with_door(m, f, -w, w, 0.0, base, top, t['wall'], t['trim'], t['door'], event, door_x=-w * 0.3,
                   frame=t['frame'])
    door_steps(m, f, -w * 0.3, base, 12)
    block(m, f, -w, 0, w, d, base, top, t['wall'], skip=('front',))
    block(m, f, -w, 0, w, d, top, top + 10, t['roof'], top=t['roof'])
    for x0, y0, x1, y1 in ((-w, 0, w, 24), (-w, d - 24, w, d), (-w, 0, -w + 24, d), (w - 24, 0, w, d)):
        block(m, f, x0, y0, x1, y1, top + 10, top + 70, t['trim'], top=t['trim'])          # the parapet
    floor = base + 330                                      # the balcony at the upper storey's floor
    slab(m, f, [(-w, -150, floor), (w, -150, floor), (w, 0, floor), (-w, 0, floor)], 14, 'hoplate', t['trim'])
    block(m, f, -w, -150, w, -138, floor, floor + 90, t['trim'], top=t['trim'])           # its railing
    for px in (-w + 20, w - 20):
        block(m, f, px - 10, -150, px + 10, -130, -20, floor - 14, t['trim'])              # its posts
    for k in range(3):                                      # the upper storey's windows
        window(m, f, -w + width * (k + 0.5) / 3, 0.0, floor + 110, (0, -1), t['frame'], t['window'])
    window(m, f, w * 0.45, 0.0, base + 130, (0, -1), t['frame'], t['window'])
    for side in (-w, w):
        window(m, f, side, d * 0.5, floor + 110, (1 if side > 0 else -1, 0), t['frame'], t['window'])
    if sign:
        door_x, sw = -w * 0.3, 176.0                        # the railing board, 2:1 like the sign textures
        m.facing([f(door_x - sw / 2, -151, floor + 2), f(door_x + sw / 2, -151, floor + 2),
                  f(door_x + sw / 2, -151, floor + 88), f(door_x - sw / 2, -151, floor + 88)], sign,
                 f.direction(0, -1), fit=True)
        blade_sign(m, f, w, floor + 230, sign, t['trim'])
    return m


def cliff_house(name, x, y, z, front, event, width=700.0, depth=600.0, skin='prefab'):
    """A home cut into the cliff: a cut rock face (hhrockt, toned to the terrain's cliffs) with the home's front set in
    it (hhcliffdt: the door in a salvaged Ancient frame) on a sill 40 high, two treads up to it, its sides flaring
    back into the slope like the shoulders of a buttress. The rock runs 1 200 back, so the cliff, rising behind the
    front, comes up through its top and buries its back: the rooms are in the rock. depth is the footprint the plan
    keeps clear. (On the ground itself the door's foot was hidden: the smoothed terrain rises a little toward the
    cliff.)"""
    m = Model(name)
    f = Frame(x, y, z, front)
    w, high, back, flare, sill = width / 2 + 150, 760.0, 1200.0, 300.0, 40.0
    face = 480.0                                            # the fitted front's width and height; rock round it
    m.facing([f(-face / 2, 0, sill), f(face / 2, 0, sill), f(face / 2, 0, sill + face), f(-face / 2, 0, sill + face)],
             'hhcliffdt', f.direction(0, -1), event=event, fit=True)
    for x0, x1, z0, z1 in ((-w, -face / 2, -40, high), (face / 2, w, -40, high),
                           (-face / 2, face / 2, sill + face, high)):
        m.facing([f(x0, 0, z0), f(x1, 0, z0), f(x1, 0, z1), f(x0, 0, z1)], 'hhrockt', f.direction(0, -1))
    block(m, f, -face / 2, -30, face / 2, 0, -40, sill, 'hoplate', top='hoplate')            # the sill
    for k, (y0, top) in enumerate(((-130, 27), (-230, 13))):                                # its two treads
        block(m, f, -face / 2 - 20 * (k + 1), y0, face / 2 + 20 * (k + 1), -30 if k == 0 else -130, -40, top,
              'hoplate', top='hoplate')
    for side in (-1, 1):                                    # the shoulders, flaring back into the slope
        a, b = (side * w, 0.0), (side * (w + flare), back)
        normal = (side * back, -flare)
        m.facing([f(*a, -40), f(*b, -40), f(*b, high), f(*a, high)], 'hhrockt', f.direction(*normal))
    m.facing([f(-w, 0, high), f(w, 0, high), f(w + flare, back, high), f(-w - flare, back, high)], 'hhrockt',
             (0, 0, 1))
    m.facing([f(-w - flare, back, -40), f(w + flare, back, -40), f(w + flare, back, high), f(-w - flare, back, high)],
             'hhrockt', f.direction(0, 1))
    return m


def hall_house(name, x, y, z, front, event, width=1800.0, depth=900.0, skin='prefab'):
    """A long gabled hall (the crawler shed): the gable house at hall size, a wide door in the middle of its front."""
    return salvage_house(name, x, y, z, front, event, width, depth, 'gable', windows=3, pipe=False, awning=False,
                         wall_top=560.0, door_x=0.0, skin=skin)
