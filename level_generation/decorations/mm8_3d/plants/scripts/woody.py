"""Woody models built only from bark tubes (inside Blender), no cards:
  plant49 tumbleweed: a loose ball of curly twigs. Partial great-circle arcs round the ball with wavy radius, plus
          smaller inner arcs and curled tips, so gaps show through. Light grey-tan.
  plant48 dry bush: stems from the base that fork twice into thinning woody tips, pale tan.
LODs keep a seeded subset of the twigs, with fewer segments and sides. Material Bark (tiling bark, opaque)."""
import math
import numpy as np
from mathutils import Vector, Matrix
import plant_lib as pl
import clump as cl

UP = Vector((0, 0, 1))


def tumbleweed(sp, rng):
    H = sp.H
    R = 0.5 * H
    c = Vector((0, 0, R * 0.98))
    twigs = []
    for k in range(34):
        inner = k >= 25
        rad = R * (rng.uniform(0.5, 0.75) if inner else rng.uniform(0.88, 1.0))
        axis = Vector(rng.normal(0, 1, 3)).normalized()
        a, b, _ = pl.frame(axis)
        span = rng.uniform(0.45, 0.85) * 2 * math.pi
        t0 = rng.uniform(0, 2 * math.pi)
        waves = rng.uniform(2, 5); amp = rng.uniform(0.04, 0.1); ph = rng.uniform(0, 6.3)
        pts = []
        n = 10
        for i in range(n + 1):
            t = t0 + span * i / n
            r = rad * (1 + amp * math.sin(waves * t + ph))
            p = c + (a * math.cos(t) + b * math.sin(t)) * r + axis * (rad * 0.08 * math.sin(2 * t + ph))
            p.z = max(p.z, 0.01 * H)
            pts.append(p)
        if rng.uniform() < 0.6:                        # a curled tip
            end, prev = pts[-1], pts[-2]
            d = (end - prev).normalized(); side = d.cross(end - c).normalized()
            cr = rad * rng.uniform(0.08, 0.14)
            centre = end + side * cr
            for i in range(1, 4):
                ang = math.pi * 1.4 * i / 3
                q = centre - side * cr * math.cos(ang) + d * cr * math.sin(ang)
                q.z = max(q.z, 0.01 * H)
                pts.append(q)
        r0 = H * (0.011 if not inner else 0.009) * rng.uniform(0.8, 1.2)
        twigs.append({'pts': pts, 'r0': r0, 'r1': r0 * 0.45, 'keep': rng.uniform() + (0.0 if inner else 0.35),
                      'tint': [x * rng.uniform(0.85, 1.1) for x in (0.92, 0.86, 0.74)]})
    return twigs


def dry_bush(sp, rng):
    H = sp.H
    twigs = []

    def grow(start, d, length, r, level, keep):
        pts = [start]
        p = start.copy()
        n = 5 if level < 2 else 3
        for i in range(n):
            d = (d + Vector(rng.normal(0, 0.18, 3)) + UP * 0.08).normalized()
            p = p + d * length / n
            rr = sp.radius(min(max(p.z, 0), H * 0.99)) * 1.04
            if math.hypot(p.x, p.y) > rr or p.z > H:   # a twig ends where it leaves the sprite's silhouette
                break
            pts.append(p.copy())
        if len(pts) < 2:
            return
        twigs.append({'pts': pts, 'r0': r, 'r1': r * 0.55, 'keep': keep,
                      'tint': [x * rng.uniform(0.9, 1.08) for x in (0.95, 0.88, 0.7)]})
        if level < 2:
            for f in range(3 if level == 0 else int(rng.integers(2, 4))):
                at = pts[int(rng.integers(len(pts) // 2, len(pts)))]
                spread = 0.55 if level == 0 else 0.7
                nd = (d + Vector(rng.normal(0, spread, 3))).normalized()
                if nd.z < 0.15:
                    nd.z = 0.15; nd.normalize()
                grow(at, nd, length * rng.uniform(0.5, 0.7), r * 0.55, level + 1, keep * 0.6 + rng.uniform() * 0.3)

    for k in range(11):
        phi = 2 * math.pi * (k + rng.uniform(0, 0.6)) / 11
        out = Vector((math.cos(phi), math.sin(phi), 0))
        d = (out * rng.uniform(0.35, 0.7) + UP).normalized()
        start = out * 0.03 * H + Vector((0, 0, -0.01 * H))
        grow(start, d, H * rng.uniform(0.5, 0.65), H * 0.022 * rng.uniform(0.85, 1.15), 0, 1.0 + rng.uniform())
    return twigs


def build(sid):
    sp = cl.Sprite(sid)
    rng = np.random.default_rng({'plant48': 4802, 'plant49': 4902}[sid])
    twigs = tumbleweed(sp, rng) if sid == 'plant49' else dry_bush(sp, rng)
    bark = pl.material('Bark', 'bark', cutout=False, roughness=0.9, extension='REPEAT',
                       extras={'openyamm_wind': 0.02, 'openyamm_specular': 0.05})
    H = sp.H
    clump = pl.Clump((0, 0, H * 0.5), (sp.W * 0.5, sp.W * 0.5, H * 0.5), floor=0.45, ground=0.5, depth=0.45,
                     blend=0.0, height=H)
    order = sorted(twigs, key=lambda t: -t['keep'])
    objects = []
    for lod, (frac, step, sides) in enumerate(((1.0, 1, 3 if sid == 'plant49' else 4), (0.55, 2, 3), (0.3, 3, 3))):
        g = pl.Geo()
        for t in order[:int(round(len(order) * frac))]:
            pts = t['pts'][::step]
            if pts[-1] is not t['pts'][-1]:
                pts.append(t['pts'][-1])
            if len(pts) < 2:
                continue
            grow = 1 + 0.35 * lod
            radii = [(t['r0'] + (t['r1'] - t['r0']) * i / (len(pts) - 1)) * grow for i in range(len(pts))]
            pl.tube(g, pts, radii, sides, clump, t['tint'], mat=0, tile=(1.0, 0.25 * H))
        objects.append(g.to_object(('Plant', 'Plant_LOD1', 'Plant_LOD2')[lod], [bark]))
    return objects
