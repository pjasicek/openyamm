"""The Brood Spires' BModel kit (BROOD_SPIRES.md, Buildings): what Starport Reach's houses.py does not have. Built in
houses.py's frames and conventions (x along the front, y from the front to the back, z up from the floor; faces wound
to face out, door faces fitted and recessed) and textured from the K11 greenhouse keys, the settlers' prefab set, the
colonial Ancient keys (K1-K3), the organic ship (K8), the brood hive (K7) and the grafted Kreegan doorways (K5).

    greenhouse      a long sealed prefab greenhouse: amber glazing in prefab frames, a glazed gable roof, prefab end
                    walls, the airlock door in the front (east) end in a post frame
    lookout_deck    a raised deck on posts with a rail over a lean-to roof (Wren's post)
    farm_wall       the Acid Garden's rectangular prefab rampart following the terraced ground, the gate and the
                    wicket open, a lintel with the farm's sign over the gate
    sunk_dome       a colonial dome sunk to its shoulders in the marsh, one optionally torn open to walk in
    survey_mast     the old survey mast lying toppled from its plinth, its dish ring beside it
    lattice_mast    a standing four-legged lattice mast (the weather station's)
    gantry          the bone-and-resin truss ramp from the cradle's slope up to the hull breach, the breach face at its top
    hive_portal     D9's mouth: a ribbed hive arch with the membrane door
    grafted_portal  D5's door: the stolen white blast door in a Kreegan doorway arch
"""
import math

import numpy as np

from bmodels import Model
from houses import Frame, block, wall_with_door

GREEN_EAVES, GREEN_RIDGE = 520.0, 760.0


def greenhouse(name, x, y, z, front, event, width=700.0, depth=2400.0, end_wall='hhprefab', post='hhpost'):
    """A long greenhouse: its front (the end with the airlock door) faces `front`; width across the end wall, depth
    back along its length. Glazed walls (hhgreen) between prefab end walls, a glazed gable roof (hhgreenrf) running
    the length, posts at the corners and every 600 along the sides, a plinth."""
    m = Model(name)
    f = Frame(x, y, z, front)
    w, d, base = width / 2, depth, 40.0
    block(m, f, -w - 14, -14, w + 14, d + 14, -40, base, 'hoplate', top='hoplate')
    wall_with_door(m, f, -w, w, 0.0, base, GREEN_EAVES, end_wall, post, 'hhgrdoor', event, door_x=0.0,
                   door_w=160.0, door_h=300.0, frame=post)
    block(m, f, -w, 0, w, d, base, GREEN_EAVES, {'front': None, 'back': end_wall, 'left': 'hhgreen',
                                                 'right': 'hhgreen'})
    for ys, out in ((0.0, -1), (d, 1)):                                # the gable ends
        m.facing([f(-w, ys, GREEN_EAVES), f(w, ys, GREEN_EAVES), f(0, ys, GREEN_RIDGE)], end_wall,
                 f.direction(0, out))
    over = 30.0
    for side in (-1, 1):                                               # the two glazed slopes, the eaves overhanging
        lo, hi = side * (w + over), 0.0
        corners = [(lo, -over, GREEN_EAVES - over * 0.68), (hi, -over, GREEN_RIDGE), (hi, d + over, GREEN_RIDGE),
                   (lo, d + over, GREEN_EAVES - over * 0.68)]
        points = [f(*c) for c in corners]
        m.facing(points, 'hhgreenrf', f.direction(side * 0.5, 0, 1))
        m.facing(list(reversed(points)), 'hhgreenrf', f.direction(-side * 0.5, 0, -1))
    block(m, f, -14, -over - 10, 14, d + over + 10, GREEN_RIDGE - 6, GREEN_RIDGE + 22, post, top=post)   # ridge
    posts = [k * depth / round(depth / 600) for k in range(int(round(depth / 600)) + 1)]
    for py in posts:                                                   # posts standing proud of the glazing
        for px in (-w, w):
            block(m, f, px - 14, py - 14, px + 14, py + 14, base, GREEN_EAVES, post, top=post)
    return m


def lookout_deck(m, f, x0, x1, y0, y1, z, rail_texture='hhpost', deck_texture='hoplate'):
    """A deck on four posts standing on a roof (its floor at z), a rail round it."""
    for px in (x0 + 20, x1 - 20):
        for py in (y0 + 20, y1 - 20):
            block(m, f, px - 12, py - 12, px + 12, py + 12, z - 160, z, rail_texture, top=rail_texture)
    block(m, f, x0, y0, x1, y1, z, z + 16, deck_texture, top=deck_texture, bottom=True)
    for a, b, c, d in ((x0, y0, x1, y0 + 12), (x0, y1 - 12, x1, y1), (x0, y0, x0 + 12, y1), (x1 - 12, y0, x1, y1)):
        block(m, f, a, b, c, d, z + 90, z + 106, rail_texture, top=rail_texture)
    for px, py in ((x0 + 6, y0 + 6), (x1 - 6, y0 + 6), (x0 + 6, y1 - 6), (x1 - 6, y1 - 6)):
        block(m, f, px - 6, py - 6, px + 6, py + 6, z + 16, z + 96, rail_texture)


def farm_wall(name, box, height, thickness, gate, wicket, ground, piece=480.0, sign='hhgatesg'):
    """The Acid Garden's wall round box (x0, y0, x1, y1): prefab rampart panels `thickness` thick in pieces of about
    `piece`, each standing from below the lowest ground under it to `height` above the highest, so it follows the
    terraces; open at the gate (east) and the wicket (north); a lintel with the sign over the gate. ground(x, y) is
    the terrain height."""
    m = Model(name)
    x0, y0, x1, y1 = box
    half = thickness / 2
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]                  # counter-clockwise
    openings = [gate, wicket]
    for (ax, ay), (bx, by) in zip(corners, corners[1:] + corners[:1]):
        a, b = np.array([ax, ay], float), np.array([bx, by], float)
        length = float(np.linalg.norm(b - a))
        along = (b - a) / length
        out = np.array([along[1], -along[0]])
        cuts = []
        for opening in openings:
            p = np.array(opening['position'], float)
            t = float(np.dot(p - a, along))
            if 0 < t < length and abs(float(np.dot(p - a, out))) < 1.0:
                cuts.append((t - opening['width'] / 2, t + opening['width'] / 2))
        spans, start = [], -half
        for c0, c1 in sorted(cuts):
            spans.append((start, c0))
            start = c1
        spans.append((start, length + half))
        for s0, s1 in spans:
            count = max(1, int(round((s1 - s0) / piece)))
            for k in range(count):
                t0, t1 = s0 + (s1 - s0) * k / count, s0 + (s1 - s0) * (k + 1) / count
                p0, p1 = a + along * t0, a + along * t1
                samples = [ground(*(p0 + (p1 - p0) * u + out * v)) for u in (0, 0.5, 1) for v in (-half, half)]
                low, top = min(samples) - 40, max(samples) + height
                o0, o1, i0, i1 = p0 + out * half, p1 + out * half, p0 - out * half, p1 - out * half
                m.facing([(*o0, low), (*o1, low), (*o1, top), (*o0, top)], 'hhwallpf', (*out, 0))
                m.facing([(*i1, low), (*i0, low), (*i0, top), (*i1, top)], 'hhwallpf', (*-out, 0))
                m.facing([(*o0, top), (*o1, top), (*i1, top), (*i0, top)], 'hhpost', (0, 0, 1))
                for p, sign_ in ((p0, -1), (p1, 1)):                    # ends: at the openings and between steps
                    q0, q1 = p + out * half, p - out * half
                    m.facing([(*q0, low), (*q1, low), (*q1, top), (*q0, top)], 'hhpost', (*(along * sign_), 0))
        for c0, c1 in cuts:                                              # the gate's lintel and sign
            if c1 - c0 < gate['width'] - 1:
                continue
            mid = a + along * (c0 + c1) / 2
            z = max(ground(*(mid + out * v)) for v in (-half, half))
            f = Frame(*mid, z, math.atan2(out[1], out[0]))
            w = (c1 - c0) / 2
            lintel = min(height + 160, 560.0)
            block(m, f, -w, -half, w, half, lintel, lintel + 160, 'hhwallpf', top='hhpost', bottom=True)
            for face_y, direction in ((-half - 1, (0, -1)), (half + 1, (0, 1))):
                xs = (-180, 180) if direction[1] < 0 else (180, -180)
                m.facing([f(xs[0], face_y, lintel + 10), f(xs[1], face_y, lintel + 10), f(xs[1], face_y, lintel + 150),
                          f(xs[0], face_y, lintel + 150)], sign, f.direction(*direction), fit=True)
            for px in (-w - 40, w + 40):                                 # the gate posts carry the lintel
                block(m, f, px - 40, -half - 20, px + 40, half + 20, -40, lintel + 160, 'hhpost', top='hhpost')
    return m


def sunk_dome(name, centre, z, radius, rise, sink, torn=None, sides=16, rings=6):
    """A colonial dome sunk `sink` into the marsh (its base ring below the ground), gold rims at its foot and crown;
    torn: the bearing (radians) of a torn panel three sectors wide, open from below ground to about head height."""
    m = Model(name)
    cx, cy = centre

    def ring(k, r_scale=1.0):
        angle = math.pi / 2 * k / rings
        r = radius * math.cos(angle) * r_scale
        zz = z - sink + rise * math.sin(angle)
        return [(cx + r * math.cos(2 * math.pi * i / sides), cy + r * math.sin(2 * math.pi * i / sides), zz)
                for i in range(sides)]
    gone = set()
    if torn is not None:
        sector = int(round(torn / (2 * math.pi) * sides)) % sides
        head = z + 230
        for i in (sector - 1, sector, sector + 1):
            for k in range(rings - 1):
                if ring(k)[0][2] < head:
                    gone.add((i % sides, k))
    for k in range(rings - 1):
        a, b = ring(k), ring(k + 1)
        for i in range(sides):
            if (i, k) in gone:
                continue
            j = (i + 1) % sides
            m.both([a[i], a[j], b[j], b[i]], 'hodome')
    top = ring(rings - 1)
    m.face(top, 'hogold')
    crown = ring(rings - 1, 1.08)
    m.face([(p[0], p[1], p[2] + 18) for p in crown], 'hogold')
    return m


def survey_mast(name, base, z, heading, ground, length=3000.0):
    """The old survey mast: its stepped plinth at `base`, the lattice mast lying toppled from it along `heading`
    (radians) as three long boxes (its legs and spine), braces across, and its dish ring fallen at its far end."""
    m = Model(name)
    f = Frame(base[0], base[1], z, heading - math.pi / 2)                 # local +y runs along the fallen mast
    block(m, f, -260, -260, 260, 260, -60, 120, 'hoplate', top='hogold')
    block(m, f, -180, -180, 180, 180, 120, 260, 'hopylon', top='hogold')
    for lx in (-110, 110):                                               # the two lower legs
        p0, p1 = np.array(f(lx, 220, 0)), np.array(f(lx, 220 + length, 0))
        g0, g1 = ground(*p0[:2]), ground(*p1[:2])
        m.tube((p0[0], p0[1], g0 + 50), (p1[0], p1[1], g1 + 50), 40, 'hopylon', sides=6)
    p0, p1 = np.array(f(0, 220, 0)), np.array(f(0, 220 + length, 0))
    m.tube((p0[0], p0[1], ground(*p0[:2]) + 230), (p1[0], p1[1], ground(*p1[:2]) + 230), 36, 'hopylon', sides=6)
    for k in range(1, 8):                                                # braces between the legs
        q = np.array(f(0, 220 + length * k / 8, 0))
        g = ground(*q[:2])
        a, b = np.array(f(-110, 220 + length * k / 8, 0)), np.array(f(110, 220 + length * k / 8, 0))
        m.tube((a[0], a[1], g + 50), (q[0], q[1], g + 230), 16, 'hogold', sides=4)
        m.tube((b[0], b[1], g + 50), (q[0], q[1], g + 230), 16, 'hogold', sides=4)
    dish = np.array(f(240, 220 + length + 380, 0))                        # the dish ring, fallen on its side
    m.prism((dish[0], dish[1], ground(*dish[:2]) - 20), 360, 60, 12, 'hogold', top='hoplate')
    m.prism((dish[0], dish[1], ground(*dish[:2]) + 40), 260, 40, 12, 'hoplate', top='hopylon')
    return m


def lattice_mast(name, x, y, z, height=1600.0, span=160.0):
    """A standing lattice mast: four legs, girdles every 400, a beacon cap, crept over at its foot."""
    m = Model(name)
    for lx in (-span, span):
        for ly in (-span, span):
            m.box((x + lx, y + ly, z - 40), (40, 40, height + 40), 'hopylon', top='hogold')
    for level in np.arange(400, height, 400):
        for (ax, ay), (bx, by) in (((-span, -span), (span, -span)), ((span, -span), (span, span)),
                                   ((span, span), (-span, span)), ((-span, span), (-span, -span))):
            m.tube((x + ax, y + ay, z + level), (x + bx, y + by, z + level), 14, 'hogold', sides=4, caps=False)
    m.box((x, y, z + height), (2 * span + 80, 2 * span + 80, 50), 'hoplate', top='hogold')
    m.prism((x, y, z + height + 50), 70, 120, 8, 'hopylon', top='hogold')
    return m


def gantry(name, foot, top, deck_z0, deck_z1, ground, width=500.0, breach_event=None, breach_size=(460.0, 560.0)):
    """The cradle gantry: a deck of bone plates (hsfloor) from foot (x, y) at deck_z0 up to top (x, y) at deck_z1,
    sides and three trestles of cradle bone (hscradle), rails of ship trim (hstrim); at its top the hull breach face
    (hsdoor, event breach_event) standing across the deck's end, facing back down it."""
    m = Model(name)
    foot, top = np.array(foot, float), np.array(top, float)
    length = float(np.linalg.norm(top - foot))
    along = (top - foot) / length
    side = np.array([-along[1], along[0]])
    half = width / 2

    def deck(t, s, dz=0.0):
        p = foot + along * t + side * s
        return (p[0], p[1], deck_z0 + (deck_z1 - deck_z0) * t / length + dz)
    thick = 50.0
    m.facing([deck(0, -half), deck(length, -half), deck(length, half), deck(0, half)], 'hsfloor', (0, 0, 1))
    m.facing([deck(0, -half, -thick), deck(0, half, -thick), deck(length, half, -thick), deck(length, -half, -thick)],
             'hscradle', (0, 0, -1))
    for s in (-half, half):                                              # its two sides
        n = side * np.sign(s)
        m.facing([deck(0, s, -thick), deck(length, s, -thick), deck(length, s), deck(0, s)], 'hscradle', (*n, 0))
    m.facing([deck(0, -half, -thick), deck(0, -half), deck(0, half), deck(0, half, -thick)], 'hscradle',
             (*-along, 0))
    for s in (-half + 20, half - 20):                                    # rails: posts and a top rail
        for k in range(9):
            t = length * k / 8
            p = deck(t, s)
            m.box((p[0], p[1], p[2]), (30, 30, 110), 'hstrim', top='hstrim')
        a, b = deck(0, s, 110), deck(length, s, 110)
        m.tube(a, b, 14, 'hstrim', sides=6)
    for t in (length * 0.3, length * 0.62, length * 0.9):                # three bone trestles down to the ground
        for s in (-half + 60, half - 60):
            p = deck(t, s, -thick)
            g = ground(p[0], p[1])
            if p[2] - g > 30:
                m.box((p[0], p[1], g - 40), (70, 70, p[2] - g + 40), 'hscradle', top='hscradle')
        a, b = deck(t, -half + 60, -thick - 30), deck(t, half - 60, -thick - 30)
        m.tube(a, b, 26, 'hscradle', sides=6)
    if breach_event is not None:                                         # the breach: across the deck's top end
        bw, bh = breach_size
        p = foot + along * (length + 4)
        e = side * bw / 2
        zb = deck_z1
        m.facing([(p[0] - e[0], p[1] - e[1], zb), (p[0] + e[0], p[1] + e[1], zb), (p[0] + e[0], p[1] + e[1], zb + bh),
                  (p[0] - e[0], p[1] - e[1], zb + bh)], 'hsdoor', (*-along, 0), event=breach_event, fit=True)
        for s in (-1, 1):                                                # ragged bone jambs either side
            q = p + side * s * (bw / 2 + 40) - along * 20
            m.box((q[0], q[1], zb - 20), (90, 90, bh + 60), 'hscradle', yaw=math.atan2(along[1], along[0]),
                  top='hscradle')
        q = p - along * 20
        m.box((q[0], q[1], zb + bh), (90, bw + 170, 70), 'hscradle', yaw=math.atan2(along[1], along[0]),
              top='hscradle')
    return m


def hive_portal(name, x, y, z, front, event, width=900.0, height=700.0, depth=500.0):
    """D9's mouth: a ribbed arch of hive resin (hobhive) set into the pit's wall, the membrane door (hbdoor, fitted,
    event) recessed in it; the arch's sides run back into the rock."""
    m = Model(name)
    f = Frame(x, y, z, front)
    w = width / 2
    door_w, door_h = width - 260, height - 140
    wall_with_door(m, f, -w, w, 0.0, -40, height, 'hobhive', 'hobhive', 'hbdoor', event, door_x=0.0,
                   door_w=door_w, door_h=door_h + 40, inset=60)
    block(m, f, -w, 0, w, depth, -40, height, {'front': None, 'all': 'hobhive'}, top='hobhive')
    for k in range(5):                                                   # ribs arching over the opening
        px = -w + 40 + (width - 80) * k / 4
        block(m, f, px - 26, -50, px + 26, 0, -40, height + 30 - 60 * abs(k - 2), 'hobhive', top='hobhive')
    block(m, f, -w - 30, -60, w + 30, 0, height - 40, height + 60, 'hobhive', top='hobhive')
    return m


def grafted_portal(name, x, y, z, front, event, depth=900.0):
    """D5's door: a white Ancient blast door (hkblast, fitted, event) half open in a Kreegan doorway (hokdoor round
    it, hokwall sides), a sill plate in front; the doorway runs back into the root mound."""
    m = Model(name)
    f = Frame(x, y, z, front)
    w, h = 420.0, 640.0
    wall_with_door(m, f, -w, w, 0.0, -40, h + 120, 'hokdoor', 'hokspine', 'hkblast', event, door_x=0.0,
                   door_w=360.0, door_h=520.0, inset=40, frame='hokspine')
    block(m, f, -w, 0, w, depth, -40, h + 120, {'front': None, 'all': 'hokwall'}, top='hokwall')
    block(m, f, -w - 60, -260, w + 60, 0, -40, 8, 'hoplate', top='hoplate')            # the sill plate
    for side in (-1, 1):                                                 # spines flaring out of the mound
        block(m, f, side * (w + 30) - 40, -120, side * (w + 30) + 40, depth * 0.6, -40, h + 220, 'hokspine',
              top='hokspine')
    return m
