"""Bare tree / shrub / stump for one dead-tree id (work/dead_<id>/tree.blend): objects Tree, Tree_LOD1, Tree_LOD2
(and Tree_LOD3 for the stump, which has no impostor), materials Bark, Wood (stripped / cut wood), Twigs (alpha cards).
Every mesh has a 'Color' point attribute (linear) = occlusion, exported as COLOR_0.

Skeleton: our own procedural branch generator (not Sapling), one per kind:
 - snag (6tree28, 6tree27): monopodial pine snag; a trunk to the top with a stripped pale strip (6tree28), whorled
   level-1 branches whose length follows the sprite's smoothed silhouette, drooping by kind, some broken stubs with
   pale wood caps, level-2 side twigs in the branch plane, twig cards (level 3) at the twig tips and along the limbs;
 - shrub (6tree29): a fan of thin upright stems from a small base forking once or twice, twig cards at the tips;
 - gnarled (swptree4): a mound of roots (displaced dome with three dark hollows, ~30 root tubes draped over it and
   spreading over the ground), a leaning trunk forking into wavy knobby limbs that fork again down to twigs;
 - stump (stump5a): a radial grid (angle x height) with root ridges flaring into the ground, bark fibres, a cut
   top with a step and splinters (Wood: procedural end grain).
Tubes: rings with parallel-transport frames, u around (whole texture repeats per circumference), v along (arc length
/ tile); tips taper into a cone. LODs: branches whose importance (length x radius) is below the level's threshold are
dropped and replaced by one twig card each along their length; sides and ring spacing coarsen; the threshold rises until
the triangle budget holds. LOD0 cards are thinned per level and grown to keep coverage.
Occlusion: per vertex sky visibility against the LOD0 wood (rays), floor + range, and a ground term.
Usage: blender --background --python dead_build.py -- <id>"""
import bpy, bmesh, os, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dead_common as dc

spec = dc.load()
WORK = spec['work']; H = spec['height_m']; KIND = spec['kind']
BUDGET = spec['budget']
TILE = spec['bark']['tile']
rng = np.random.default_rng(spec['seed'])
prof = json.load(open(os.path.join(WORK, 'profile.json')))
P = np.array(prof['left_right_by_height'])
# silhouette half-width per height (metres): the larger side, smoothed (max over +-4 %, then a 3-tap mean)
_half = np.maximum(P[:, 1], P[:, 2])
_half = np.array([_half[max(0, k - 2):k + 3].max() for k in range(len(_half))])
_half = np.convolve(np.pad(_half, 1, mode='edge'), [0.25, 0.5, 0.25], 'valid')


def extent(z):
    return float(np.interp(z / H, P[:, 0], _half)) * H


def unit(v):
    v = np.asarray(v, float); n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def grow(start, direction, length, r0, r1, steps=10, gravity=0.0, noise=0.05, up=0.0, power=1.0, curl=None):
    """Polyline from start along direction; each step bends by gravity (down), up-attraction and noise."""
    pts = [np.asarray(start, float)]; d = unit(direction); step = length / steps
    for i in range(steps):
        d = unit(d + np.array([0, 0, up - gravity]) * step + rng.normal(0, noise, 3)
                 + (curl(i, d) if curl else 0))
        pts.append(pts[-1] + d * step)
    t = np.linspace(0, 1, steps + 1)
    rad = r1 + (r0 - r1) * (1 - t) ** power
    return np.array(pts), rad


def chaikin(pts, rad, iterations=2):
    """Corner cutting (ends kept): the grown polylines bend smoothly instead of in straight segments."""
    for _ in range(iterations):
        if len(pts) < 3:
            break
        q = [pts[0]]; r = [rad[0]]
        for i in range(len(pts) - 1):
            q += [0.75 * pts[i] + 0.25 * pts[i + 1], 0.25 * pts[i] + 0.75 * pts[i + 1]]
            r += [0.75 * rad[i] + 0.25 * rad[i + 1], 0.25 * rad[i] + 0.75 * rad[i + 1]]
        q.append(pts[-1]); r.append(rad[-1])
        pts, rad = np.array(q), np.array(r)
    return pts, rad


def branch(pts, rad, level, tip=True, cap=None, knob=0.0, strip=None, under=False, parent=None):
    pts, rad = chaikin(np.asarray(pts, float), np.asarray(rad, float))
    length = float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum())
    return {'parent': parent, 'pts': pts, 'rad': rad, 'level': level, 'tip': tip, 'cap': cap, 'knob': knob, 'strip': strip,
            'length': length, 'imp': length * float(rad[0]), 'under': under}


def point_on(br, t):
    """Point, tangent and radius at fraction t of a branch's arc length."""
    pts, rad = br['pts'], br['rad']
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
    x = t * s[-1]; i = min(int(np.searchsorted(s, x, side='right')) - 1, len(seg) - 1); i = max(i, 0)
    f = (x - s[i]) / max(seg[i], 1e-9)
    return pts[i] + (pts[i + 1] - pts[i]) * f, unit(pts[i + 1] - pts[i]), rad[i] + (rad[i + 1] - rad[i]) * f


branches, cards, extras = [], [], {}


def card(p, d, size, roll=None, owner=None):
    """A twig card: base at p, growing along d, edge `size`; roll about d measured from the vertical plane. It
    belongs to the branch it grows on (default: the last one made) and goes when a coarser level drops that branch."""
    if roll is None:
        roll = rng.uniform(-1.0, 1.0)
    cards.append({'p': np.asarray(p, float), 'd': unit(d), 'size': float(size), 'roll': float(roll),
                  'cell': int(rng.integers(4)), 'owner': owner if owner is not None else branches[-1]})


def roots(r_trunk, count, reach, z0=0.3, radius=0.6, sides_level=1):
    for k in range(count):
        a = 2 * math.pi * k / count + rng.uniform(-0.3, 0.3)
        out = np.array([math.cos(a), math.sin(a), 0.0])
        pts = []
        n = 6
        for i in range(n + 1):
            t = i / n
            rr = r_trunk * 0.2 + (r_trunk + reach * rng.uniform(0.8, 1.2) - r_trunk * 0.2) * t
            pts.append(out * rr + np.array([0, 0, z0 * (1 - t) ** 3 - 0.05 * t]))
        pts = np.array(pts); rad = r_trunk * radius * (1 - np.linspace(0, 1, n + 1)) ** 0.8 + 0.008
        branches.append(branch(pts, rad, sides_level, tip=True))


# ---------------------------------------------------------------- generators
def make_snag():
    is28 = spec['id'] == '6tree28'
    r0 = 0.08 if is28 else 0.1
    lean = rng.normal(0, 0.005, 2)

    def trunk_curl(i, d):
        return np.array([lean[0], lean[1], 0]) + rng.normal(0, 0.004, 3)

    BREAK = 0.8                                     # 6tree28: the pale trunk snaps here, a thin leader goes on
    top = H * (BREAK if is28 else 0.995)
    pts, rad = grow((0, 0, -0.05), (0, 0, 1), top, r0, 0.006 if not is28 else r0 * 0.5, steps=26 if not is28 else 21,
                    noise=0.006, curl=trunk_curl, power=0.55 if is28 else 0.7)
    rad = rad * (1 + 0.45 * np.exp(-np.maximum(pts[:, 2], 0) / 0.14))
    strip = (0.06 * H, 0.86 * H, rng.uniform(0, 2 * math.pi), 1.0) if is28 else None
    trunk = branch(pts, rad, 0, tip=not is28, cap='wood' if is28 else None, strip=strip)
    branches.append(trunk)
    leader = None
    if is28:
        q, tq, rq = point_on(trunk, 0.86)
        side = unit(np.array([math.cos(strip[2] + math.pi), math.sin(strip[2] + math.pi), 0]))
        lp, lrad = grow(q + side * rq * 0.35, unit(np.array([0, 0, 1]) + side * 0.05), H - q[2], rq * 0.6, 0.004,
                        steps=8, noise=0.02)
        leader = branch(lp, lrad, 0, tip=True)
        branches.append(leader)
    roots(r0, 7, 0.26, z0=0.2, radius=0.95)
    n1 = 40 if is28 else 44
    z_lo, z_hi = (0.13, 0.97) if is28 else (0.16, 0.985)
    golden = math.pi * (3 - math.sqrt(5))
    az0 = rng.uniform(0, 2 * math.pi)
    for k in range(n1):
        f = (k + rng.uniform(0.1, 0.9)) / n1
        z = H * (z_lo + (z_hi - z_lo) * f)
        az = az0 + k * golden + rng.normal(0, 0.25)
        out = np.array([math.cos(az), math.sin(az), 0])
        if leader is not None and z > leader['pts'][0][2]:
            stem = leader; base_z = leader['pts'][0][2]; span = leader['pts'][-1][2] - base_z
            p, _, rt = point_on(leader, min((z - base_z) / span, 0.98))
        else:
            p, _, rt = point_on(trunk, min((z + 0.05) / (top + 0.05), 0.98))
        reach = max(extent(z) - rt, 0.15) * rng.uniform(0.75, 1.02)
        broken = rng.random() < (0.22 if is28 else 0.1) and f < 0.75
        if broken:
            reach *= rng.uniform(0.15, 0.4)
        rel = z / H
        if is28:
            elev = 0.05 + 0.45 * rel ** 2 + rng.normal(0, 0.1); grav = 0.9 * (1 - rel) + 0.25
        else:
            elev = 0.1 + 0.4 * rel ** 2 + rng.normal(0, 0.12); grav = 1.4 * (1 - rel) + 0.35
        d = unit(out * math.cos(elev) + np.array([0, 0, math.sin(elev)]))
        rb = min(rt * 0.55, (0.015 + 0.014 * (1 - rel)) * (1.0 if is28 else 1.2))
        bp, brad = grow(p - out * rt * 0.4, d, reach, rb, 0.004 if not broken else rb * 0.6, steps=9,
                        gravity=grav / max(reach, 0.3), noise=0.11, power=0.8)
        b1 = branch(bp, brad, 1, tip=not broken, cap='wood' if broken else None)
        branches.append(b1)
        if broken:
            continue
        # level-2 side twigs, alternating, in the branch's (near-horizontal) plane, turning up a little
        n2 = int(max(1, round(reach / (0.1 if is28 else 0.13))))
        for j in range(n2):
            t = 0.18 + 0.78 * (j + rng.uniform(0.0, 0.8)) / n2
            q, tq, rq = point_on(b1, min(t, 0.97))
            side = unit(np.cross(tq, [0, 0, 1])) * (1 if j % 2 else -1)
            spread = rng.uniform(0.6, 1.1)
            d2 = unit(tq * math.cos(spread) + side * math.sin(spread) + np.array([0, 0, rng.uniform(0.0, 0.35)]))
            l2 = reach * (1 - t) * rng.uniform(0.45, 0.75) + 0.08
            l2 = min(l2, 0.55 if is28 else 0.6)
            cp, crad = grow(q, d2, l2, max(rq * 0.65, 0.005), 0.002, steps=4, gravity=0.0 if is28 else 0.5,
                            up=0.25 if is28 else 0.0, noise=0.12)
            b2 = branch(cp, crad, 2, parent=b1)
            branches.append(b2)
            # twig cards at the twig's tip and on its side
            card(cp[-1] - (cp[-1] - cp[-2]) * 0.6, cp[-1] - cp[-2], rng.uniform(0.24, 0.38))
            if rng.random() < 0.8:
                qq, tt, _ = point_on(b2, rng.uniform(0.3, 0.6))
                card(qq, unit(tt + unit(np.cross(tt, [0, 0, 1])) * rng.choice([-0.8, 0.8])), rng.uniform(0.18, 0.3))
        # cards at the limb's tip and a few spurs along it
        card(bp[-2], bp[-1] - bp[-2], rng.uniform(0.3, 0.45), owner=b1)
        for j in range(int(reach / 0.35)):
            q, tq, _ = point_on(b1, rng.uniform(0.25, 0.9))
            card(q, unit(tq + np.array([0, 0, 0.9]) + rng.normal(0, 0.3, 3)), rng.uniform(0.14, 0.24), owner=b1)
    # top of the stem: a few forks and cards
    for j in range(4 if is28 else 7):
        stem = leader if leader is not None else trunk
        q, tq, rq = point_on(stem, rng.uniform(0.9, 0.99))
        card(q, unit(tq + rng.normal(0, 0.5, 3)), rng.uniform(0.18, 0.3), owner=stem)


def make_broad():
    """MM8 tree28: a bare broadleaf. A central leader (ridged, slightly wavy) to near the top, limbs on a golden-angle
    spiral from LIMB_LO to LIMB_HI of the height that rise and arch outward to the sprite's silhouette, each forking two
    or three ways down to fine twigs with twig cards at every tip, side shoots along the limbs, a few short sprouts
    low on the trunk, root spurs."""
    cfg = spec.get('broad', {})
    r0 = cfg.get('trunk_radius', 0.42)
    knob = cfg.get('knob', 0.1)
    lean = rng.normal(0, 0.004, 2)

    def wavy(amount, rate=1.1):
        phase = rng.uniform(0, 6.3, 3)
        return lambda i, d: amount * np.array([math.sin(rate * i + phase[0]), math.sin(0.9 * rate * i + phase[1]),
                                               0.2 * math.sin(0.7 * rate * i + phase[2])])

    top = H * cfg.get('leader_top', 0.94)
    pts, rad = grow((0, 0, -0.05), (0, 0, 1), top, r0, 0.03, steps=22, noise=0.006,
                    curl=lambda i, d: np.array([lean[0], lean[1], 0]) + wavy(0.025, 0.6)(i, d), power=0.75)
    rad = rad * (1 + 0.4 * np.exp(-np.maximum(pts[:, 2], 0) / (0.035 * H)))
    trunk = branch(pts, rad, 0, tip=False, knob=knob)
    branches.append(trunk)
    roots(r0, cfg.get('roots', 6), cfg.get('root_reach', 0.7), z0=0.5, radius=0.8)
    card_size = cfg.get('card', [0.7, 1.1])
    r_min = cfg.get('r_min', 0.022)

    def fitted(pts, length):
        """Scale a grown polyline about its start until every point lies inside the sprite silhouette (radially, with
        a little slack) and below the top; returns the points and the scaled length."""
        for _ in range(30):
            ok = all(math.hypot(q[0], q[1]) <= extent(min(max(q[2], 0.0), H)) * cfg.get('slack', 1.04) + 0.15
                     and q[2] <= H * 0.995 for q in pts[1:])
            if ok:
                break
            pts = pts[0] + (pts - pts[0]) * 0.93; length *= 0.93
        return pts, length

    def limb(p, d, length, r, level, parent):
        steps = 9 if level <= 1 else 6 if level == 2 else 4 if level == 3 else 3
        pts, rad = grow(p, d, length, r, r * 0.6, steps=steps, noise=0.06 + 0.02 * level,
                        gravity=(0.05 + 0.06 * level) / max(length, 0.5), up=0.02, curl=wavy(0.04 + 0.03 * level))
        pts, length = fitted(pts, length)
        terminal = level >= cfg.get('max_level', 5) or r * 0.6 < r_min
        b = branch(pts, rad, level, tip=terminal, knob=knob * (0.8 if level <= 1 else 0.4), parent=parent)
        branches.append(b)
        tip_d = unit(pts[-1] - pts[-2])
        if terminal:
            card(pts[-2], tip_d, rng.uniform(*card_size))
            for _ in range(int(rng.integers(*cfg.get('tip_cards', [1, 3])))):
                q, tq, _ = point_on(b, rng.uniform(0.3, 0.8))
                card(q, unit(tq + unit(np.cross(tq, rng.normal(0, 1, 3))) * 0.8 + np.array([0, 0, 0.3])),
                     rng.uniform(*card_size) * 0.8)
            return
        if level >= 2:                       # bristly limbs: twig sprays along the finer limbs too
            for _ in range(int(rng.poisson(cfg.get('limb_cards', 1.0)))):
                q, tq, _ = point_on(b, rng.uniform(0.3, 0.9))
                card(q, unit(tq + unit(np.cross(tq, rng.normal(0, 1, 3))) * 1.0 + np.array([0, 0, 0.4])),
                     rng.uniform(*card_size) * 0.75)
        n = 2 if rng.random() < cfg.get('two_fork', 0.65) else 3
        base_ax = unit(np.cross(tip_d, rng.normal(0, 1, 3)))
        for c in range(n):
            ax = unit(base_ax * math.cos(c * 2 * math.pi / n) + np.cross(tip_d, base_ax) * math.sin(c * 2 * math.pi / n))
            ang = rng.uniform(0.3, 0.65)
            cd = unit(tip_d * math.cos(ang) + ax * math.sin(ang) + np.array([0, 0, 0.12]))
            limb(pts[-1] - tip_d * r * 0.4, cd, length * rng.uniform(*cfg.get('fork_length', [0.6, 0.76])),
                 r * rng.uniform(0.58, 0.7), level + 1, b)
        # side shoots along the limb (the sprite's limbs bristle with twiggy side branches)
        for _ in range(int(rng.poisson(cfg.get('side_shoots', 1.2) * (1 if level <= 2 else 0.5)))):
            q, tq, rq = point_on(b, rng.uniform(0.25, 0.75))
            sd = unit(tq + unit(np.cross(tq, rng.normal(0, 1, 3))) * 1.0 + np.array([0, 0, 0.2]))
            limb(q, sd, length * rng.uniform(0.3, 0.45), max(rq * 0.45, r_min * 1.2), max(level + 2, 3), b)

    golden = math.pi * (3 - math.sqrt(5)); az0 = rng.uniform(0, 2 * math.pi)
    lo, hi = cfg.get('limbs_z', [0.28, 0.82]); n_limbs = cfg.get('limbs', 9)
    for k in range(n_limbs):
        f = (k + rng.uniform(0.15, 0.85)) / n_limbs
        z = H * (lo + (hi - lo) * f)
        az = az0 + k * golden + rng.normal(0, 0.2)
        out = np.array([math.cos(az), math.sin(az), 0])
        p, _, rt = point_on(trunk, min((z + 0.05) / (top + 0.05), 0.97))
        elev = math.radians(cfg.get('elevation', [32, 62])[0] + (cfg.get('elevation', [32, 62])[1]
                                                                 - cfg.get('elevation', [32, 62])[0]) * f
                            + rng.normal(0, 6))
        d = unit(out * math.cos(elev) + np.array([0, 0, math.sin(elev)]))
        # the limb system (limb + forks, ~1.9 x the limb) should reach the silhouette at about its tip height
        reach = 1.0
        for _ in range(4):
            tip_z = z + reach * 1.9 * math.sin(elev) * 0.75
            reach = max(extent(min(tip_z, H * 0.98)) - rt, 0.8) / (1.9 * math.cos(elev) * 0.9 + 0.2)
        reach *= rng.uniform(0.85, 1.05) * cfg.get('reach', 1.0)
        rl = min(rt * 0.62, r0 * cfg.get('limb_radius', 0.45) * (1.1 - 0.5 * f))
        limb(p - out * rt * 0.3, d, reach, rl, 1, trunk)
    # the leader's own crown: forks at the top
    q, tq, rq = point_on(trunk, 0.99)
    for c in range(3):
        a = az0 + 2.1 * c
        d = unit(np.array([math.cos(a) * 0.45, math.sin(a) * 0.45, 1.0]))
        limb(q, d, (H - top) * 1.2 + 0.6, rq * 0.9, 3, trunk)
    # low sprouts on the trunk (short twiggy shoots)
    for k in range(cfg.get('sprouts', 5)):
        z = H * rng.uniform(0.04, 0.24)
        az = rng.uniform(0, 2 * math.pi); out = np.array([math.cos(az), math.sin(az), 0])
        p, _, rt = point_on(trunk, min((z + 0.05) / (top + 0.05), 0.97))
        d = unit(out + np.array([0, 0, rng.uniform(0.2, 0.9)]))
        limb(p, d, rng.uniform(0.6, 1.3), min(rt * 0.2, 0.05), 3, trunk)


def make_shrub():
    """Bunched stems from a small base, wavy, forking repeatedly into short blunt Y tips (sympodial)."""
    def stem(p, d, length, r, depth, parent):
        pts, rad = grow(p, d, length, r, r * (0.62 if depth > 0 else 0.5), steps=6, noise=0.12, up=0.4)
        b = branch(pts, rad, 1 if parent is None else 2, tip=depth <= 0, parent=parent)
        branches.append(b)
        tip_d = unit(pts[-1] - pts[-2])
        if depth <= 0:
            if rng.random() < 0.7:
                card(pts[-2], tip_d, rng.uniform(0.1, 0.16))
            return
        n = 2 if rng.random() < 0.8 else 3
        base_ax = unit(np.cross(tip_d, rng.normal(0, 1, 3)))
        for c in range(n):
            ax = unit(base_ax * math.cos(c * math.pi * 2 / n) + np.cross(tip_d, base_ax) * math.sin(c * math.pi * 2 / n))
            ang = rng.uniform(0.18, 0.4)
            cd = unit(tip_d * math.cos(ang) + ax * math.sin(ang) + np.array([0, 0, 0.15]))
            stem(pts[-1] - tip_d * r * 0.5, cd, length * rng.uniform(0.55, 0.75), r * 0.64, depth - 1, b)
        if rng.random() < 0.3:
            q, tq, rq = point_on(b, rng.uniform(0.4, 0.7))
            sd = unit(tq + unit(np.cross(tq, rng.normal(0, 1, 3))) * 0.45)
            stem(q, sd, length * 0.3, rq * 0.6, 0, b)

    stems = 8
    for k in range(stems):
        a = 2 * math.pi * k / stems + rng.uniform(-0.3, 0.3)
        out = np.array([math.cos(a), math.sin(a), 0])
        tilt = rng.uniform(0.06, 0.24)
        d = unit(out * math.sin(tilt) + np.array([0, 0, math.cos(tilt)]))
        start = out * rng.uniform(0.0, 0.04) + np.array([0, 0, -0.03])
        stem(start, d, H * rng.uniform(0.38, 0.52), rng.uniform(0.018, 0.026), 2, None)


def make_gnarled():
    """Root skirt (a concave cone, MOUND_TOP x H high) under a thick twisted trunk that forks into long wavy limbs."""
    mound_r, mound_h = extras['mound']
    knob = 0.16

    def wavy(amount, rate=1.2):
        phase = rng.uniform(0, 6.3, 3)
        return lambda i, d: amount * np.array([math.sin(rate * i + phase[0]), math.sin(0.9 * rate * i + phase[1]),
                                               0.3 * math.sin(0.7 * rate * i + phase[2])])

    lean_az = rng.uniform(0, 2 * math.pi)
    lean = np.array([math.cos(lean_az), math.sin(lean_az), 0])
    trunk_pts, trunk_rad = grow((0, 0, mound_h * 0.6), unit(np.array([0, 0, 1]) + lean * 0.15), 0.25 * H, 0.36,
                                0.25, steps=10, noise=0.02, curl=wavy(0.05, 0.8))
    trunk = branch(trunk_pts, trunk_rad, 0, tip=False, knob=knob)
    branches.append(trunk)
    fork = trunk_pts[-1]

    def limb(p, d, length, r, level, parent=None):
        steps = 10 if level <= 2 else 6 if level == 3 else 4
        pts, rad = grow(p, d, length, r, r * 0.62, steps=steps, noise=0.07,
                        gravity=0.3 if level >= 3 else 0.12, up=0.08, curl=wavy(0.1 + 0.03 * level))
        terminal = level >= 5 or r < 0.026
        b = branch(pts, rad, level, tip=terminal, knob=knob if level <= 2 else 0.1, parent=parent)
        branches.append(b)
        tip_d = unit(pts[-1] - pts[-2])
        if terminal:
            card(pts[-2], tip_d, rng.uniform(0.4, 0.6))
            if rng.random() < 0.5:
                card(pts[-3], unit(tip_d + rng.normal(0, 0.5, 3)), rng.uniform(0.3, 0.45))
            return
        n = 2 if (level >= 3 or rng.random() < 0.75) else 3
        base_ax = unit(np.cross(tip_d, rng.normal(0, 1, 3)))
        for c in range(n):
            ax = unit(base_ax * math.cos(c * 2 * math.pi / n) + np.cross(tip_d, base_ax) * math.sin(c * 2 * math.pi / n))
            ang = rng.uniform(0.35, 0.7)
            cd = unit(tip_d * math.cos(ang) + ax * math.sin(ang) + np.array([0, 0, 0.1]))
            limb(pts[-1] - tip_d * r * 0.5, cd, length * rng.uniform(0.62, 0.78), r * rng.uniform(0.55, 0.66),
                 level + 1, b)
        # a side shoot from the limb's middle
        if level == 2 and rng.random() < 0.6:
            q, tq, rq = point_on(b, rng.uniform(0.3, 0.6))
            sd = unit(tq + unit(np.cross(tq, rng.normal(0, 1, 3))) * 0.9)
            limb(q, sd, length * 0.45, rq * 0.5, 5, b)

    n_limbs = 4
    for k in range(n_limbs):
        az = lean_az + 2 * math.pi * k / n_limbs + rng.uniform(-0.35, 0.35)
        out = np.array([math.cos(az), math.sin(az), 0])
        ang = rng.uniform(0.55, 0.85)
        d = unit(out * math.sin(ang) + np.array([0, 0, math.cos(ang)]))
        limb(fork - np.array([0, 0, 0.2]), d, H * rng.uniform(0.15, 0.18), rng.uniform(0.16, 0.2), 1, trunk)
    # roots: from inside the trunk foot down the skirt, winding round the hollows, then out over the ground
    nroots, nshort = 20, 12
    for k in range(nroots + nshort):
        short = k >= nroots                 # shorter roots from the middle of the skirt fill its lower band
        az = 2 * math.pi * (k + rng.uniform(0, 0.8)) / (nroots if not short else nshort)
        zt = mound_h * (rng.uniform(0.75, 1.0) if not short else rng.uniform(0.3, 0.55))
        reach = mound_r * rng.uniform(1.05, 1.35)
        wander = rng.normal(0, 0.3); wob = rng.uniform(0, 6.3); amp = rng.uniform(0.08, 0.2)
        n = 16
        pts = []
        for i in range(n + 1):
            t = i / n
            a = az + wander * t + amp * math.sin(7 * t + wob)
            if t < 0.75:
                z = zt * (1 - t / 0.75) ** 1.15
                a = avoid_pits(a, z)
                r_s = mound_surface_r(z, a) + 0.05 + 0.04 * math.sin(11 * t + wob)
            else:
                z = 0.0
                r_s = mound_surface_r(0.0, a) + (reach - mound_r) * (t - 0.75) / 0.25
            pts.append(np.array([math.cos(a) * r_s, math.sin(a) * r_s, z + (0.03 if t < 1 else -0.08)]))
        if short:                           # starts sunk in the skirt
            pts[0] = pts[0] * np.array([0.8, 0.8, 1.0])
        else:                               # starts inside the trunk, near its axis
            pts[0] = np.array([pts[0][0] * 0.15, pts[0][1] * 0.15, pts[0][2] + 0.25])
        pts = np.array(pts)
        r_root = rng.uniform(0.08, 0.15) if not short else rng.uniform(0.06, 0.1)
        rad = r_root * (1 - 0.8 * np.linspace(0, 1, n + 1) ** 1.3)
        root = branch(pts, rad, 1, tip=True, knob=0.14)
        root['sides'] = (5, 3, 3) if not short else (4, 3, 3)
        root['imp'] *= 0.4                  # coarse levels keep the crown limbs before the lesser roots
        branches.append(root)
    # a thick rim of root round every hollow, and a few arches between them
    for (pa, pz, pr) in PITS:
        pts = []
        R0 = mound_surface_r(pz, pa)
        for i in range(19):
            t = 2 * math.pi * i / 18
            a = pa + math.cos(t) * pr * 1.0 / R0
            z = pz + math.sin(t) * pr * 1.0
            rs = mound_surface_r(z, a) + 0.02
            pts.append(np.array([math.cos(a) * rs, math.sin(a) * rs, z]))
        pts[-1] = pts[0]
        rim = branch(np.array(pts), np.full(19, pr * 0.32), 1, tip=False, knob=0.15)
        rim['seg'] = 0.16; rim['imp'] = 1.0; rim['sides'] = (6, 4, 3)     # kept on every level
        branches.append(rim)
    for k in range(5):
        az = rng.uniform(0, 2 * math.pi); z = mound_h * rng.uniform(0.45, 0.8)
        span = rng.uniform(0.5, 0.8)
        pts = []
        for i in range(11):
            t = i / 10
            a = az + span * t
            rs = mound_surface_r(z, a) + 0.25 * math.sin(math.pi * t) - 0.12 * (i in (0, 10))
            pts.append(np.array([math.cos(a) * rs, math.sin(a) * rs, z + 0.3 * math.sin(math.pi * t) - 0.25 * t]))
        arch = branch(np.array(pts), np.full(11, rng.uniform(0.07, 0.1)), 1, tip=False, knob=0.12)
        arch['sides'] = (5, 4, 3)
        branches.append(arch)


def avoid_pits(a, z):
    """Deflect a root's azimuth round the hollows it would cover."""
    for (pa, pz, pr) in PITS:
        R0 = mound_surface_r(pz, pa)
        dz = z - pz
        half = pr * 1.35
        if abs(dz) < half:
            da = math.remainder(a - pa, 2 * math.pi) * R0
            need = math.sqrt(half * half - dz * dz)
            if abs(da) < need:
                a = pa + math.copysign(need, da if da != 0 else 1.0) / R0
    return a


_mound_noise = np.random.default_rng(spec['seed'] + 3).normal(0, 1, (6, 4))


def mound_surface_r(z, a):
    """Concave root skirt: wide at the ground, narrowing to the trunk at the top, wobbly in plan."""
    R, Hm = extras['mound']
    t = min(max(z / Hm, 0.0), 1.0)
    top = 0.34
    base = top + (R - top) * (1 - t) ** 2.2
    wob = sum(_mound_noise[k, 0] * 0.05 * math.sin((k + 2) * a + _mound_noise[k, 1] * 3 + _mound_noise[k, 2] * 3 * t)
              for k in range(6))
    lumps = sum(_mound_noise[k, 3] * 0.035 * math.sin((k + 7) * a + 9 * t * (1 + 0.3 * k) + _mound_noise[k, 1] * 5)
                for k in range(6))
    return base * (1 + wob + lumps)


PITS = []


# ---------------------------------------------------------------- mesh building
class MeshOut:
    def __init__(self):
        self.bm = bmesh.new(); self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.occ = {}                # vert -> occlusion override (dark hollows)

    def quad(self, vs, uvs, mat=0):
        f = self.bm.faces.new(vs); f.smooth = True; f.material_index = mat
        for loop, t in zip(f.loops, uvs):
            loop[self.uv].uv = t
        return f


def frames(tangents):
    n0 = unit(np.cross(tangents[0], [1, 0, 0] if abs(tangents[0][0]) < 0.9 else [0, 1, 0]))
    ns = [n0]
    for i in range(1, len(tangents)):
        a, b = tangents[i - 1], tangents[i]
        v = np.cross(a, b); s = np.linalg.norm(v); c = float(np.dot(a, b))
        n = ns[-1]
        if s > 1e-8:
            k = v / s; ang = math.atan2(s, c)
            n = n * math.cos(ang) + np.cross(k, n) * math.sin(ang) + k * np.dot(k, n) * (1 - math.cos(ang))
        n = unit(n - b * np.dot(n, b))
        ns.append(n)
    return ns


def tube(mo, br, sides, seg_len):
    pts, rad = br['pts'], br['rad']
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)]); L = s[-1]
    rings = max(2, int(math.ceil(L / seg_len)) + 1)
    if br['tip'] and rings < 3:
        rings = 3
    if br['tip']:
        # the last ring sits just short of the end: a short cone, so tips read blunt rather than spiked
        cone = min(float(rad[-1]) * 1.5 + 0.004, L * 0.3)
        ss = np.concatenate([np.linspace(0, L - cone, rings - 1), [L]])
    else:
        ss = np.linspace(0, L, rings)
    P_ = np.stack([np.interp(ss, s, pts[:, k]) for k in range(3)], 1); R_ = np.interp(ss, s, rad)
    T_ = np.array([unit(P_[min(i + 1, rings - 1)] - P_[max(i - 1, 0)]) for i in range(rings)])
    N_ = frames(T_)
    around = max(1, round(2 * math.pi * float(rad.max()) * 0.8 / TILE))
    kn = br['knob']
    tone = TONE[min(br['level'], len(TONE) - 1)]
    phase = rng.uniform(0, 6.3, 3)
    ring_vs = []
    last = rings - 1 if br['tip'] else rings
    for i in range(last):
        n = N_[i]; b = np.cross(T_[i], n); vs = []
        for j in range(sides):
            a = 2 * math.pi * j / sides
            r = R_[i]
            if kn:
                r *= 1 + kn * (math.sin(ss[i] * 7 + phase[0] + 2 * a) * 0.6 + math.sin(ss[i] * 13 + phase[1] + 3 * a) * 0.4)
            vs.append(mo.bm.verts.new(Vector(P_[i] + (n * math.cos(a) + b * math.sin(a)) * r)))
            if tone != 1.0:
                mo.occ[vs[-1]] = tone
        ring_vs.append(vs)
    vcoord = ss / TILE
    strip = br['strip']
    for i in range(len(ring_vs) - 1):
        for j in range(sides):
            j2 = (j + 1) % sides
            mat = 0
            if strip:
                z = P_[i][2]; a = 2 * math.pi * (j + 0.5) / sides
                if strip[0] < z < strip[1] and abs(math.remainder(a - strip[2], 2 * math.pi)) < strip[3] \
                        * (0.6 + 0.4 * math.sin(z * 3.1)):
                    mat = 1
            mo.quad((ring_vs[i][j], ring_vs[i][j2], ring_vs[i + 1][j2], ring_vs[i + 1][j]),
                    ((j / sides * around, vcoord[i]), ((j + 1) / sides * around, vcoord[i]),
                     ((j + 1) / sides * around, vcoord[i + 1]), (j / sides * around, vcoord[i + 1])), mat)
    if br['tip']:
        tip = mo.bm.verts.new(Vector(P_[-1]))
        if tone != 1.0:
            mo.occ[tip] = tone
        i = len(ring_vs) - 1
        for j in range(sides):
            j2 = (j + 1) % sides
            f = mo.bm.faces.new((ring_vs[i][j], ring_vs[i][j2], tip)); f.smooth = True
            for loop, t in zip(f.loops, ((j / sides * around, vcoord[i]), ((j + 1) / sides * around, vcoord[i]),
                                         ((j + 0.5) / sides * around, vcoord[-1]))):
                loop[mo.uv].uv = t
    elif br['cap']:
        # broken end: a jagged pale wood cap
        i = len(ring_vs) - 1
        centre = mo.bm.verts.new(Vector(P_[-1] - T_[-1] * R_[-1] * 0.5))
        for v in ring_vs[i]:
            v.co += Vector(T_[-1] * R_[-1] * rng.uniform(-0.6, 1.4))
        for j in range(sides):
            j2 = (j + 1) % sides
            f = mo.bm.faces.new((ring_vs[i][j], ring_vs[i][j2], centre)); f.smooth = False; f.material_index = 1
            for loop, a in zip(f.loops, (j, j2, None)):
                loop[mo.uv].uv = (0.5, 0.5) if a is None else (0.5 + 0.4 * math.cos(2 * math.pi * a / sides),
                                                                0.5 + 0.4 * math.sin(2 * math.pi * a / sides))


SKIRT_TONE = spec.get('native_shading', {}).get('skirt', 0.62)      # the skirt between the roots is in their shade


def mound(mo, lod):
    R, Hm = extras['mound']
    na, nz = ((30, 9), (18, 6), (12, 4))[lod]
    rows = []
    for i in range(nz + 1):
        t = i / nz; z = Hm * t ** 0.9 - 0.05 * (i == 0)
        row = []
        for j in range(na):
            a = 2 * math.pi * j / na
            r = mound_surface_r(max(z, 0), a) if i < nz else 0.0
            p = np.array([math.cos(a) * r, math.sin(a) * r, z if i < nz else Hm])
            # hollows: pits pushed into the mound
            for (pa, pz, pr) in PITS:
                d = math.hypot(math.remainder(a - pa, 2 * math.pi) * mound_surface_r(pz, pa), z - pz)
                if d < pr:
                    w = math.cos(d / pr * math.pi / 2) ** 2
                    p[:2] *= 1 - 0.6 * w
            row.append(mo.bm.verts.new(Vector(p)))
        rows.append(row)
    around = max(1, round(2 * math.pi * R * 0.8 / TILE))
    for i in range(nz):
        for j in range(na):
            j2 = (j + 1) % na
            uvs = ((j / na * around, i / nz * Hm / TILE), ((j + 1) / na * around, i / nz * Hm / TILE),
                   ((j + 1) / na * around, (i + 1) / nz * Hm / TILE), (j / na * around, (i + 1) / nz * Hm / TILE))
            if i == nz - 1:
                f = mo.bm.faces.new((rows[i][j], rows[i][j2], rows[i + 1][0])); f.smooth = True
                for loop, t in zip(f.loops, uvs[:3]):
                    loop[mo.uv].uv = t
            else:
                mo.quad((rows[i][j], rows[i][j2], rows[i + 1][j2], rows[i + 1][j]), uvs)
    # the skirt between the roots is in their shade; hollows go dark by distance to the pit centres
    for row in rows:
        for v in row:
            mo.occ[v] = SKIRT_TONE
            a = math.atan2(v.co.y, v.co.x)
            for (pa, pz, pr) in PITS:
                d = math.hypot(math.remainder(a - pa, 2 * math.pi) * mound_surface_r(pz, pa), v.co.z - pz)
                if d < pr * 0.85:
                    mo.occ[v] = min(mo.occ.get(v, 1.0), 0.03 + 0.95 * (d / (pr * 0.85)) ** 2.5)
    if NATIVE and NATIVE.get('pit_cups'):
        pit_cups(mo, lod)


def pit_cups(mo, lod):
    """Native shading only: a black shallow funnel over every hollow, its rim just outside the undented skirt under
    the root rim, its centre a little inside it. The skirt's coarse rows put few vertices in a hollow, so vertex colour alone leaves it a
    mid tone where the sprite shows a black hole (Eevee's occlusion hid this in the review renders)."""
    sides = (10, 8, 6)[lod]
    for (pa, pz, pr) in PITS:
        R0 = mound_surface_r(pz, pa)
        # shallow: the coarse skirt's dent is shallower than its formula, and a deeper funnel would sit behind it
        centre = mo.bm.verts.new(Vector((math.cos(pa) * (R0 - 0.12), math.sin(pa) * (R0 - 0.12), pz)))
        mo.occ[centre] = 0.0
        rim = []
        for j in range(sides):
            t = 2 * math.pi * j / sides
            a = pa + math.cos(t) * pr * 0.8 / R0
            z = pz + math.sin(t) * pr * 0.8
            r = mound_surface_r(z, a) + 0.08          # clear of the skirt's chords, under the root rim
            rim.append(mo.bm.verts.new(Vector((math.cos(a) * r, math.sin(a) * r, z))))
            mo.occ[rim[-1]] = 0.05
        for j in range(sides):
            f = mo.bm.faces.new((centre, rim[j], rim[(j + 1) % sides])); f.smooth = True     # facing out
            for loop in f.loops:
                loop[mo.uv].uv = (loop.vert.co.z / TILE, math.atan2(loop.vert.co.y, loop.vert.co.x) * R0 / TILE)


def stump_mesh(mo, lod):
    """Radial grid: radius(angle, z) = trunk profile x (1 + root ridges flaring toward the ground) + fibre noise."""
    Hs = H
    na, nz = ((52, 16), (30, 9), (16, 5), (10, 3))[lod]
    rr = np.random.default_rng(spec['seed'])
    root_a = np.sort(rr.uniform(0, 2 * math.pi, 9)); root_w = rr.uniform(0.13, 0.19, 9); root_s = rr.uniform(0.7, 1.2, 9)
    fib = rr.normal(0, 1, 40); fib_p = rr.uniform(0, 6.3, 40)
    r_top = 0.235 / 0.88 * Hs

    def radius(a, z):
        t = z / Hs
        r = r_top * (1.02 + 0.12 * (1 - t))
        flare = max(0.0, 1 - t / 0.6) ** 1.1
        keep = 1.0                      # smooth union of the root lobes (a plain max creases the bark)
        for ra, rw, rs in zip(root_a, root_w, root_s):
            d = abs(math.remainder(a - ra, 2 * math.pi))
            keep *= 1 - min(rs, 1.0) * math.exp(-(d / (rw * (0.7 + 1.2 * t))) ** 2)
        ridge = 1 - keep
        r *= 1 + flare * (0.1 + 1.55 * ridge)
        if t < 0.08:                    # root ends round over onto the ground
            r *= 1 - 0.18 * (1 - t / 0.08) ** 2 * ridge
        if lod <= 1:                    # gentle lumps: frequencies well below half the column count (no aliasing)
            r *= 1 + 0.012 * sum(fib[k] * math.sin((k + 3) * a + fib_p[k] + 4 * t * fib[k + 20]) for k in range(10))
        return r

    def top_z(a):
        # stepped cut: the far side ~5 cm lower, plus splinters near the step edge
        step = 0.06 / 0.88 * Hs
        s = 0.5 + 0.5 * math.tanh(4 * math.sin(a - 0.4))
        z = Hs - step * s
        if lod <= 1:
            z += 0.012 * Hs * math.sin(7 * a + 1.3) + 0.02 * Hs * max(0, math.sin(11 * a)) ** 6
        return z

    zs = np.linspace(-0.03, 1.0, nz + 1) ** 1.0
    if lod >= 2:
        # coarse levels: columns on the root lobes (and between them at LOD2), so the lobes survive the sparse ring
        cols = list(root_a) + ([(root_a[k] + (root_a[(k + 1) % 9] + (2 * math.pi if k == 8 else 0))) / 2
                                for k in range(9)] if lod == 2 else [])
        cols = sorted(c % (2 * math.pi) for c in cols)
    else:
        cols = [2 * math.pi * j / na for j in range(na)]
    na = len(cols)
    rows = []
    for i, f in enumerate(zs):
        row = []
        for j in range(na):
            a = cols[j]
            # rows stay level below the cut (columns of different height would crease the bark); the top ring
            # follows the stepped cut
            z = top_z(a) if i == len(zs) - 1 else (f * (Hs - 0.07 / 0.88 * Hs) if f > 0 else -0.03)
            row.append(mo.bm.verts.new(Vector((math.cos(a) * radius(a, max(z, 0)), math.sin(a) * radius(a, max(z, 0)),
                                               z))))
        rows.append(row)
    around = max(1, round(2 * math.pi * r_top * 1.3 / TILE))
    for i in range(nz):
        for j in range(na):
            j2 = (j + 1) % na
            v0, v1 = zs[i] * Hs / TILE, zs[i + 1] * Hs / TILE
            u0 = cols[j] / (2 * math.pi) * around
            u1 = (cols[j2] + (2 * math.pi if j2 == 0 else 0)) / (2 * math.pi) * around
            mo.quad((rows[i][j], rows[i][j2], rows[i + 1][j2], rows[i + 1][j]),
                    ((u0, v0), (u1, v0), (u1, v1), (u0, v1)))
    # cut top: a slightly inset rim ring and a fan to a centre (end grain, material Wood)
    top = rows[-1]
    rim = []
    for j, v in enumerate(top):
        a = 2 * math.pi * j / na
        rim.append(mo.bm.verts.new(Vector((v.co.x * 0.93, v.co.y * 0.93, v.co.z - 0.004))))
    centre = mo.bm.verts.new(Vector((0, 0, sum(v.co.z for v in top) / na - 0.01)))
    rmax = max(Vector((v.co.x, v.co.y)).length for v in top)

    def tuv(co):
        return (0.5 + 0.5 * co.x / rmax, 0.5 + 0.5 * co.y / rmax)

    for j in range(na):
        j2 = (j + 1) % na
        f = mo.bm.faces.new((top[j], top[j2], rim[j2], rim[j])); f.material_index = 1
        for loop in f.loops:
            loop[mo.uv].uv = tuv(loop.vert.co)
        f = mo.bm.faces.new((rim[j], rim[j2], centre)); f.material_index = 1
        for loop in f.loops:
            loop[mo.uv].uv = tuv(loop.vert.co)


# COLOR_0 tone per branch level (the sprites draw pale trunks with much darker limbs and twigs)
TONE = spec.get('tone_by_level', [1.0])
SIDES_BROAD = {0: lambda r: 8 if r > 0.3 else 6 if r > 0.12 else 4 if r > 0.045 else 3,
               1: lambda r: 6 if r > 0.3 else 4 if r > 0.12 else 3,
               2: lambda r: 5 if r > 0.3 else 3}
SIDES = {0: lambda r: 10 if r > 0.15 else 8 if r > 0.06 else 6 if r > 0.025 else 4 if r > 0.008 else 3,
         1: lambda r: 7 if r > 0.15 else 5 if r > 0.06 else 4 if r > 0.025 else 3,
         2: lambda r: 5 if r > 0.15 else 4 if r > 0.06 else 3}
SEG = {0: 1.0, 1: 1.7, 2: 2.8}


SEG_CAP = 0.32 if KIND == 'gnarled' else 0.7          # gnarled limbs and roots wind: shorter rings


def seg_len(r, lod, length):
    if KIND == 'broad':                                # a 12 m tree: longer rings, never micro segments
        return max(min(r * 8, 1.1), 0.3) * SEG[lod]
    return max(min(r * 7, SEG_CAP), 0.1 if KIND != 'gnarled' else 0.16) * SEG[lod]


def build_wood(lod, threshold):
    mo = MeshOut()
    if KIND == 'stump':
        stump_mesh(mo, lod)
        return mo, []
    if KIND == 'gnarled':
        mound(mo, lod)
    dropped = [br for br in branches if br['level'] > 0 and br['imp'] < threshold and br['imp'] < 1.0]
    gone = {id(b) for b in dropped}
    children = {}
    for br in branches:
        if br['parent'] is not None:
            children.setdefault(id(br['parent']), []).append(br)
    for br in branches:
        if id(br) in gone:
            continue
        # a kept limb whose children are all dropped tapers off instead of ending in an open cut
        kids = children.get(id(br), [])
        if not br['tip'] and not br['cap'] and kids and all(id(k) in gone for k in kids):
            br = dict(br, tip=True, rad=br['rad'] * np.linspace(1.0, 0.45, len(br['rad'])))
        r = float(br['rad'].max())
        sides = SIDES_BROAD[lod](r) if KIND == 'broad' else SIDES[lod](r)
        if KIND == 'shrub' and lod == 0 and r > 0.008:
            sides = 5
        if KIND == 'gnarled':           # by level: the many fine forks stay cheap
            sides = ((10, 8, 6, 5, 4, 3, 3), (7, 6, 4, 4, 3, 3, 3), (5, 4, 3, 3, 3, 3, 3))[lod][min(br['level'], 6)]
        if 'sides' in br:
            sides = br['sides'][lod]
        tube(mo, br, sides, br.get('seg', seg_len(r, lod, br['length'])) * (SEG[lod] if 'seg' in br else 1.0))
    return mo, dropped


def tri_count(mo):
    return sum(len(f.verts) - 2 for f in mo.bm.faces)


# ---------------------------------------------------------------- occlusion
def wood_bvh(mo):
    bm = mo.bm.copy(); bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return BVHTree.FromBMesh(bm), bm


dirs = rng.normal(0, 1, (4096, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
RAYS = 24


def visibility(bvh, p, n, reach):
    hits = 0; total = 0
    n = Vector(n)
    for d in dirs[rng.choice(len(dirs), RAYS * 2, replace=False)]:
        d = Vector(d)
        if d.dot(n) < 0:
            d = -d
        if d.z < -0.2:                                    # the ground blocks
            hits += 1; total += 1; continue
        loc, *_ = bvh.ray_cast(p + n * 0.01 + d * 0.005, d, reach)
        total += 1; hits += loc is not None
        if total >= RAYS:
            break
    return 1 - hits / total


LOD_TONE = spec.get('lod_tone', [1.0, 1.0, 1.0, 1.0])     # coarse levels lose dark crevices: tone them to match
OCC = {'snag': (0.62, 0.38), 'shrub': (0.5, 0.5), 'gnarled': (0.4, 0.6), 'stump': (0.45, 0.55),
       'broad': tuple(spec.get('occ', (0.55, 0.45)))}[KIND]


def ground_term(z):
    t = min(max(z / (0.5 if KIND != 'stump' else 0.25 * H), 0), 1)
    return 0.72 + 0.28 * t * t * (3 - 2 * t)


def set_colours(me, colours):
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.concatenate([np.append(c, 1.0) for c in colours]))
    me.color_attributes.active_color = attr


NATIVE = spec.get('native_shading')
NATIVE_REFERENCE = []                 # LOD0's sorted shading values and their area ranks (every level uses them)


def native_colours(mo, shading):
    """Native shading transfer for tiled bark (dead_prepare.native_ramp): each vertex's shading value (occlusion and
    hollows x up-facing light x the sprite's height profile) is ranked against LOD0's values, and that rank picks the
    sprite colour at the same luminance quantile. COLOR_0 = that colour / the bark texture mean (linear), so the
    texture keeps only its fine luminance detail. A slow positional noise shifts red/blue a little (moss patches)."""
    ramp = np.array(NATIVE_RAMP['ramp_linear']); heights = np.array(NATIVE_RAMP['height_luminance'])
    profile = heights / NATIVE_RAMP['median_luminance']
    texture_mean = dc.lin(np.array(spec['bark']['target_srgb']) / 255.0)
    up = NATIVE.get('up', 0.25); strength = NATIVE.get('height_strength', 1.0)
    values = []
    for v, base in zip(mo.bm.verts, shading):
        h = min(max(v.co.z / H, 0.0), 0.999) * len(profile)
        k = min(int(h), len(profile) - 1)
        values.append(base * (1 - up + up * max(v.normal.z, 0.0)) * (1 + strength * (profile[k] - 1)))
    values = np.array(values)
    if not NATIVE_REFERENCE:
        # ranks by surface area (each vertex a third of its faces), so the rank follows what is seen on screen
        area = np.array([sum(f.calc_area() / len(f.verts) for f in v.link_faces) for v in mo.bm.verts])
        order = np.argsort(values, kind='stable')
        cumulative = np.cumsum(area[order]); cumulative /= cumulative[-1]
        NATIVE_REFERENCE.extend([values[order].tolist(), cumulative.tolist()])
    rank = np.interp(values, np.array(NATIVE_REFERENCE[0]), np.array(NATIVE_REFERENCE[1]))
    low, high = NATIVE.get('quantiles', [0.0, 1.0])
    q = np.clip(low + (high - low) * rank, 0, 0.9999) * (len(ramp) - 1)
    i = q.astype(int); f = (q - i)[:, None]
    colour = ramp[i] * (1 - f) + ramp[np.minimum(i + 1, len(ramp) - 1)] * f
    grey = (colour @ np.array([0.2126, 0.7152, 0.0722]))[:, None]
    colour = np.maximum(grey + (colour - grey) * NATIVE.get('chroma', 1.0), 0.0)
    moss = NATIVE.get('moss', 0.0)
    out = []
    for v, c in zip(mo.bm.verts, colour):
        x, y, z = v.co
        n = (math.sin(x * 1.7 + z * 0.9) * math.sin(y * 1.9 - z * 0.7 + 1.3) + 0.5 * math.sin(z * 2.3 + x * 0.6)) / 1.5
        tint = np.array([1 + moss * n, 1 + 0.3 * moss * n, 1 - moss * n])
        out.append(np.clip(c * tint / texture_mean, 0.0, 1.0))
    return out


def wood_object(mo, lod, bvh0):
    me = bpy.data.meshes.new(f'wood{lod}')
    occ_override = {v.index: o for v, o in mo.occ.items()} if mo.occ else {}
    mo.bm.verts.index_update()
    occ_override = {v.index: o for v, o in mo.occ.items()}
    mo.bm.normal_update()
    vals = []
    reach = 1.5 if KIND != 'stump' else 0.5
    for v in mo.bm.verts:
        vis = visibility(bvh0, v.co, v.normal, reach)
        o = (OCC[0] + OCC[1] * vis) * ground_term(v.co.z) * occ_override.get(v.index, 1.0) * LOD_TONE[lod]
        vals.append(np.array([o, o, o]))
    if NATIVE:
        vals = native_colours(mo, [c[0] for c in vals])
    for m in MATS:
        me.materials.append(m)
    mo.bm.to_mesh(me)
    set_colours(me, vals)
    obj = bpy.data.objects.new(f'wood{lod}', me); bpy.context.scene.collection.objects.link(obj)
    return obj


def card_corners(c, grow=1.0):
    d = Vector(c['d']); size = c['size'] * grow
    # plane containing d; its normal starts horizontal (a vertical card) and rolls about d
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize(); n = side.cross(d).normalized()
    side = (side * math.cos(c['roll']) + n * math.sin(c['roll'])).normalized()
    p = Vector(c['p'])
    w = size / 2
    return [p - side * w, p + side * w, p + side * w + d * size, p - side * w + d * size]


def card_object(card_list, lod, bvh0, grow):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    normals, colours = [], []
    for c in card_list:
        cs = card_corners(c, c.get('grow', grow))
        f = bm.faces.new([bm.verts.new(q) for q in cs]); f.material_index = 2
        row, col = divmod(c['cell'], 2)
        u0, v0 = 0.5 * col, 0.5 * (1 - row)
        for loop, (du, dv) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[uvl].uv = (u0 + 0.5 * du, v0 + 0.5 * dv)
        p = Vector(c['p'])
        out = Vector((p.x, p.y, 0)); out = out.normalized() if out.length > 1e-3 else Vector((1, 0, 0))
        shade_n = (out + Vector((0, 0, 0.8))).normalized()
        if 'occ' not in c:
            vis = visibility(bvh0, p + Vector(c['d']) * c['size'] * 0.4, shade_n, 1.5)
            c['occ'] = (OCC[0] + OCC[1] * vis) * ground_term(p.z)
        for q in cs:
            normals.append(shade_n); colours.append(np.array([c['occ']] * 3) * c.get('tone', 1.0))
    me = bpy.data.meshes.new(f'twigs{lod}')
    for m in MATS:
        me.materials.append(m)
    bm.to_mesh(me); bm.free()
    me.normals_split_custom_set_from_vertices(normals)
    set_colours(me, colours)
    obj = bpy.data.objects.new(f'twigs{lod}', me); bpy.context.scene.collection.objects.link(obj)
    return obj


def proxy_cards(dropped, lod):
    """One card per dropped branch: base at the branch start, along its chord, as long as the branch."""
    out = []
    pr = np.random.default_rng(spec['seed'] + 100 + lod)
    gone = {id(b) for b in dropped}
    for br in dropped:
        if br['parent'] is not None and id(br['parent']) in gone:
            continue                  # the parent's own card stands for it
        if KIND == 'gnarled' and (br['parent'] is None or br['level'] < 3):
            continue                  # roots and thick limbs are no twig sprays: they just go
        p0, p1 = br['pts'][0], br['pts'][-1]
        size = max(float(np.linalg.norm(p1 - p0)) * 1.1, 0.12)
        out.append({'p': p0, 'd': unit(p1 - p0), 'size': size, 'roll': float(pr.uniform(-1, 1)),
                    'cell': int(pr.integers(4)), 'grow': spec.get('proxy_grow', [1.0, 1.0, 1.0])[lod]})
    return out


# ---------------------------------------------------------------- materials
def image(name, colorspace):
    img = bpy.data.images.load(os.path.join(WORK, name)); img.colorspace_settings.name = colorspace
    return img


def material(name, stem, roughness, alpha=False, normal_strength=1.0, mr=True):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tb = nt.nodes.new('ShaderNodeTexImage'); tb.image = image(f'{stem}_basecolor.png', 'sRGB')
    nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color'])
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = image(f'{stem}_normal.png', 'Non-Color')
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    nm.inputs['Strength'].default_value = normal_strength
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = roughness; bsdf.inputs['Metallic'].default_value = 0.0
    if mr and os.path.exists(os.path.join(WORK, f'{stem}_mr.png')):
        tr = nt.nodes.new('ShaderNodeTexImage'); tr.image = image(f'{stem}_mr.png', 'Non-Color')
        sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tr.outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
        nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
        bsdf.inputs['Roughness'].default_value = 1.0
    if alpha:
        m.use_backface_culling = False
        m.surface_render_method = 'DITHERED'
        clip = nt.nodes.new('ShaderNodeMath'); clip.operation = 'GREATER_THAN'; clip.inputs[1].default_value = 0.5
        nt.links.new(tb.outputs['Alpha'], clip.inputs[0]); nt.links.new(clip.outputs[0], bsdf.inputs['Alpha'])
    return m


# ---------------------------------------------------------------- main
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
if KIND == 'snag':
    make_snag()
elif KIND == 'shrub':
    make_shrub()
elif KIND == 'broad':
    make_broad()
    # twig cards reach past their limb tips: shorten each until its far end is inside the silhouette and below the
    # top, dropping those that would shrink below 40 %
    kept = []
    slack = spec.get('broad', {}).get('slack', 1.04)
    for c in cards:
        size0 = c['size']
        while c['size'] > 0.4 * size0:
            e = c['p'] + c['d'] * c['size']
            if e[2] <= H * 0.995 and math.hypot(e[0], e[1]) <= extent(min(max(e[2], 0.0), H)) * slack + 0.15:
                break
            c['size'] *= 0.9
        if c['size'] > 0.4 * size0:
            kept.append(c)
    print('SKELETON cards fitted', len(kept), 'of', len(cards))
    # density thinning: overlapping twig cards read as dark blobs; keep at most `crowd` card centres within `radius`
    crowd, radius = spec.get('broad', {}).get('crowd', [3, 0.7])
    centres, thinned = [], []
    for k in rng.permutation(len(kept)):
        c = kept[k]; m = c['p'] + c['d'] * c['size'] * 0.5
        if sum(1 for q in centres if np.linalg.norm(q - m) < radius) < crowd:
            centres.append(m); thinned.append(c)
    print('SKELETON cards thinned', len(thinned), 'of', len(kept))
    cards[:] = thinned
elif KIND == 'gnarled':
    R_, Hm_ = 0.25 * H, 0.42 * H
    extras['mound'] = (R_, Hm_)
    # hollows (angle, height, radius as fractions of the skirt height)
    PITS.extend([(a, Hm_ * z, Hm_ * r) for a, z, r in ((0.4, 0.28, 0.17), (1.6, 0.3, 0.15), (3.3, 0.22, 0.16),
                                                        (4.9, 0.32, 0.13))])
    make_gnarled()
print('SKELETON branches', len(branches), 'cards', len(cards))

WIND = {'snag': 0.04, 'shrub': 0.03, 'gnarled': 0.03, 'stump': 0.0, 'broad': 0.05}[KIND]
bark_mat = material('Bark', 'bark', 0.9, normal_strength=1.4)
wood_mat = material('Wood', 'wood', 0.9, normal_strength=1.0) if os.path.exists(
    os.path.join(WORK, 'wood_basecolor.png')) else None
twig_mat = material('Twigs', 'twigs', 0.85, alpha=True, mr=False) if KIND != 'stump' else None
for m in (bark_mat, wood_mat, twig_mat):
    if m is not None and WIND:
        m['openyamm_wind'] = WIND

MATS = (bark_mat, wood_mat or bark_mat, twig_mat or bark_mat)
NATIVE_RAMP = json.load(open(os.path.join(WORK, 'native_ramp.json'))) if NATIVE else None
levels = 4 if KIND == 'stump' else 3
mo0, _ = build_wood(0, 0.0)
bvh0, bm_tri0 = wood_bvh(mo0)
CARD_KEEP = dict(enumerate(spec.get('card_keep', [1.0, 0.55, 0.2])))
CARD_GROW = dict(enumerate(spec.get('card_grow', [1.0, 1.3, 1.9])))
names = ['Tree', 'Tree_LOD1', 'Tree_LOD2', 'Tree_LOD3']
order = rng.permutation(len(cards))
for lod in range(levels):
    budget = BUDGET[lod]
    if KIND == 'stump':
        mo = mo0 if lod == 0 else build_wood(lod, 0)[0]
        wood = wood_object(mo, lod, bvh0); parts = [wood]
        print('LOD', lod, 'wood tris', tri_count(mo))
    else:
        threshold = 0.0
        while True:
            mo, dropped = (mo0, []) if (lod == 0 and threshold == 0.0) else build_wood(lod, threshold)
            gone = {id(b) for b in dropped}
            keep = [cards[k] for k in order[:int(len(cards) * CARD_KEEP[lod])] if id(cards[k]['owner']) not in gone]
            proxies = proxy_cards(dropped, lod)
            total = tri_count(mo) + 2 * (len(keep) + len(proxies))
            if total <= budget:
                break
            threshold = max(threshold * 1.08, 1e-4)
            mo.bm.free()
        wood = wood_object(mo, lod, bvh0)
        for c in proxies:
            c['tone'] = 1.0
        twigs = card_object(keep + proxies, lod, bvh0, CARD_GROW[lod])
        parts = [wood, twigs]
        print('LOD', lod, 'threshold', round(threshold, 5), 'wood tris', tri_count(mo), 'cards', len(keep),
              'proxies', len(proxies), 'total', total)
    for x in bpy.data.objects:
        x.select_set(x in parts)
    bpy.context.view_layer.objects.active = parts[0]
    if len(parts) > 1:
        bpy.ops.object.join()
    obj = parts[0]
    bm = bmesh.new(); bm.from_mesh(obj.data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(obj.data); bm.free()
    # drop unused material slots (glTF primitives per used material only)
    used = sorted({p.material_index for p in obj.data.polygons})
    obj.name = names[lod]; obj.data.name = names[lod]
    print('LOD', lod, names[lod], 'tris', len(obj.data.polygons), 'materials used', used)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'tree.blend'))
print('SAVED', os.path.join(WORK, 'tree.blend'))
