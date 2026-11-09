"""Broken tree stumps plant43/44/46/47 (inside Blender), after the MM6 `stump5a` radial grid (trees/dead_build.py):
radius(angle, z) is a slightly tapering trunk with root lobes flaring into the ground (a smooth union, so the bark
does not crease). The top is snapped: a jagged rim with two or three tall splinters (pale wood, material Wood) above a
break line, an inner wall and a hollow, all in pale splintered wood. Bark COLOR_0 runs from mossy green at the roots
to grey-brown higher up, with slow noise patches. Overgrowth: plant43 red anthurium spathes on stalks with a few
broad leaves; plant46 a woody vine with jagged ivy sprays climbing one side.
Materials: Bark (tiling bark, opaque), Wood (tiling pale wood, opaque), Foliage (leafy atlas, plant43/46)."""
import math
import numpy as np
from mathutils import Vector
import plant_lib as pl
import clump as cl

UP = Vector((0, 0, 1))
CONF = {
    'plant44': {'seed': 44, 'r': 0.21, 'taper': 0.18, 'flare': 0.32, 'lobe': 1.2, 'lobes': 7, 'base_top': 0.66,
                'spikes': [(0.4, 0.34, 0.45), (2.6, 0.2, 0.4), (4.4, 0.1, 0.5)],
                'moss': (0.62, 0.66, 0.36), 'bark': (0.55, 0.47, 0.36)},
    'plant47': {'seed': 47, 'r': 0.2, 'taper': 0.16, 'flare': 0.35, 'lobe': 1.35, 'lobes': 8, 'base_top': 0.7,
                'spikes': [(0.6, 0.3, 0.42), (2.9, 0.16, 0.45), (4.6, 0.12, 0.5)],
                'moss': (0.55, 0.66, 0.45), 'bark': (0.52, 0.5, 0.4)},
    'plant43': {'seed': 43, 'r': 0.2, 'taper': 0.15, 'flare': 0.3, 'lobe': 1.1, 'lobes': 7, 'base_top': 0.72,
                'spikes': [(0.5, 0.28, 0.4), (3.0, 0.16, 0.5), (4.5, 0.12, 0.45)],
                'moss': (0.58, 0.66, 0.42), 'bark': (0.55, 0.5, 0.4), 'anthurium': True},
    'plant46': {'seed': 46, 'r': 0.2, 'taper': 0.15, 'flare': 0.32, 'lobe': 1.25, 'lobes': 7, 'base_top': 0.62,
                'spikes': [(0.3, 0.3, 0.4), (2.2, 0.22, 0.4), (4.0, 0.1, 0.5)],
                'moss': (0.6, 0.66, 0.38), 'bark': (0.55, 0.5, 0.38), 'ivy': True},
}
LODS = [(28, 10, 4), (16, 6, 3), (10, 4, 2)]       # columns, bark rows, splinter rows


def build(sid):
    c = CONF[sid]
    sp = cl.Sprite(sid)
    H = sp.H
    rng = np.random.default_rng(c['seed'])
    la = np.sort(rng.uniform(0, 2 * math.pi, c['lobes'])) + rng.uniform(0, 1)
    lw = rng.uniform(0.18, 0.3, c['lobes']); ls = rng.uniform(0.7, 1.2, c['lobes'])
    lumps = rng.normal(0, 1, 10); lp = rng.uniform(0, 6.3, 10)
    pn = rng.normal(0, 1, 8); pp = rng.uniform(0, 6.3, 8)
    R = c['r'] * H
    base_top = c['base_top'] * H

    def radius(a, z, lod):
        t = max(z, 0) / H
        r = R * (1 + c['taper'] * (1 - t / c['base_top']))
        keep = 1.0
        for ra, rw, rs in zip(la, lw, ls):
            d = abs(math.remainder(a - ra, 2 * math.pi))
            keep *= 1 - min(rs, 1.0) * math.exp(-(d / (rw * (0.8 + 1.5 * t))) ** 2)
        ridge = 1 - keep
        flare = max(0.0, 1 - t / c['flare']) ** 1.6
        r *= 1 + flare * (0.15 + c['lobe'] * ridge)
        if t < 0.05:
            r *= 1 - 0.15 * (1 - t / 0.05) ** 2 * ridge
        if lod == 0:
            r *= 1 + 0.025 * sum(lumps[j] * math.sin((j + 3) * a + lp[j] + 5 * t * lumps[j]) for j in range(8))
        return r

    def top_z(a):
        z = base_top + 0.03 * H * math.sin(5 * a + 1.0)
        for sa, sh, sw in c['spikes']:
            d = abs(math.remainder(a - sa, 2 * math.pi))
            z += sh * H * max(0.0, 1 - d / sw) ** 1.6
        return z

    def patch(a, z):
        return sum(pn[j] * math.sin((j + 1) * a + pp[j] + 3 * z / H * pn[(j + 3) % 8]) for j in range(4)) * 0.25

    def bark_tint(a, z):
        t = min(1.0, max(z, 0) / (0.45 * H))
        m = max(0.0, min(1.0, 1 - t + 0.35 * patch(a, z)))
        tint = [c['moss'][i] * m + c['bark'][i] * (1 - m) for i in range(3)]
        o = 0.55 + 0.45 * min(1.0, max(z, 0) / (0.12 * H)) ** 0.7
        return [x * o * (0.9 + 0.1 * math.sin(3 * a)) for x in tint]

    bark = pl.material('Bark', 'bark', cutout=False, roughness=0.9, extension='REPEAT',
                       extras={'openyamm_specular': 0.05})
    wood = pl.material('Wood', 'wood', cutout=False, roughness=0.85, extension='REPEAT',
                       extras={'openyamm_specular': 0.05})
    mats = [bark, wood]
    green = c.get('anthurium') or c.get('ivy')
    if green:
        mats.append(pl.material('Foliage', 'leafy', cutout=True, roughness=0.6,
                                extras={'openyamm_specular': 0.1, 'openyamm_translucency': 0.3}))
    atlas = pl.Atlas('leafy')
    # overgrowth layout (shared by every LOD)
    extras = []
    if c.get('anthurium'):
        for k in range(9):
            a = rng.uniform(0, 2 * math.pi)
            rr = radius(a, 0.05 * H, 1) + rng.uniform(0.02, 0.12) * H
            foot = Vector((math.cos(a) * rr, math.sin(a) * rr, 0.0))
            h = rng.uniform(0.18, 0.4) * H
            out = Vector((math.cos(a), math.sin(a), 0))
            top = foot + out * rng.uniform(0.0, 0.05) * H + UP * h
            extras.append(('stalk', foot, top, rng.uniform()))
            extras.append(('spathe', top, out, rng.uniform(0.12, 0.16) * H, rng.uniform()))
        for k in range(6):
            a = rng.uniform(0, 2 * math.pi)
            rr = radius(a, 0.05 * H, 1) + 0.02 * H
            extras.append(('leaf', Vector((math.cos(a) * rr, math.sin(a) * rr, 0.0)), a,
                           rng.uniform(0.18, 0.26) * H, rng.uniform()))
    if c.get('ivy'):
        a0 = rng.uniform(0, 2 * math.pi)
        vine = []
        for k in range(9):
            z = k / 8 * (base_top + 0.15 * H)
            a = a0 + 0.35 * math.sin(k * 0.9)
            r = radius(a, min(z, base_top), 1) + 0.015 * H
            vine.append(Vector((math.cos(a) * r, math.sin(a) * r, z)))
        extras.append(('vine', vine))
        for k in range(18):
            i = int(rng.integers(0, 9))
            p = vine[i]
            a = math.atan2(p.y, p.x) + rng.normal(0, 0.45)
            z = min(max(p.z + rng.normal(0, 0.08) * H, 0.05 * H), base_top)
            r = radius(a, z, 1)
            out = Vector((math.cos(a), math.sin(a), 0))
            ctr = Vector((math.cos(a) * r, math.sin(a) * r, z)) + out * 0.03 * H
            extras.append(('ivy', ctr, out, rng.uniform(0.13, 0.19) * H, rng.uniform()))
    objects = []
    for lod, (na, nb, ns) in enumerate(LODS):
        g = pl.Geo()
        cols = [2 * math.pi * j / na for j in range(na)]
        around = max(1, round(2 * math.pi * R * 1.2 / (0.45 * H)))
        rows = []
        # bark rows up to the break line, then splinter rows up to the jagged top (material Wood)
        zs = [-0.02 * H] + [(base_top - 0.06 * H) * (i / nb) ** 1.1 for i in range(1, nb + 1)]
        for i, z in enumerate(zs):
            row = []
            for a in cols:
                r = radius(a, z, lod)
                row.append((g.vert(Vector((math.cos(a) * r, math.sin(a) * r, z)), bark_tint(a, z)), z))
            rows.append(row)
        top_rows = []
        z0 = base_top - 0.06 * H
        for i in range(1, ns + 1):
            t = i / ns
            row = []
            for j, a in enumerate(cols):
                z = z0 + (top_z(a) - z0) * t
                r = radius(a, base_top, lod) * (1 - 0.18 * t ** 2)
                o = 0.85 - 0.15 * t
                row.append((g.vert(Vector((math.cos(a) * r, math.sin(a) * r, z)), (o, o * 0.97, o * 0.92)), z))
            top_rows.append(row)
        tile = 0.45 * H

        def quads(A, B, mat, vscale):
            for j in range(na):
                j2 = (j + 1) % na
                u0 = around * j / na; u1 = around * (j + 1) / na
                g.face([A[j][0], A[j2][0], B[j2][0], B[j][0]],
                       [(u0, A[j][1] / vscale), (u1, A[j2][1] / vscale), (u1, B[j2][1] / vscale),
                        (u0, B[j][1] / vscale)], None, mat)
        for i in range(len(rows) - 1):
            quads(rows[i], rows[i + 1], 0, tile)
        # the break line: the last bark row joins the first splinter row with a wood band
        quads(rows[-1], top_rows[0], 1, tile)
        for i in range(len(top_rows) - 1):
            quads(top_rows[i], top_rows[i + 1], 1, tile)
        # inner wall and hollow: an inset ring below the lowest rim point, then a dish to the centre
        rim = top_rows[-1]
        low = min(top_z(a) for a in cols)
        inner = []
        for j, a in enumerate(cols):
            r = radius(a, base_top, lod) * 0.72
            z = low - 0.06 * H
            inner.append((g.vert(Vector((math.cos(a) * r, math.sin(a) * r, z)), (0.55, 0.5, 0.42)), z))
        for j in range(na):
            j2 = (j + 1) % na
            u0 = around * j / na; u1 = around * (j + 1) / na
            g.face([rim[j][0], rim[j2][0], inner[j2][0], inner[j][0]],
                   [(u0, rim[j][1] / tile), (u1, rim[j2][1] / tile), (u1, inner[j2][1] / tile),
                    (u0, inner[j][1] / tile)], None, 1)
        centre = g.vert(Vector((0, 0, low - 0.12 * H)), (0.35, 0.3, 0.25))
        for j in range(na):
            j2 = (j + 1) % na
            pa, pb = g.v[inner[j][0]], g.v[inner[j2][0]]
            g.face([inner[j][0], inner[j2][0], centre], [(pa.x / tile, pa.y / tile), (pb.x / tile, pb.y / tile),
                                                         (0, 0)], None, 1)
        # overgrowth
        for e in extras:
            kind = e[0]
            if kind in ('spathe', 'leaf', 'ivy', 'stalk') and lod == 2 and e[-1] < 0.45:
                continue
            if kind == 'stalk':
                if lod < 2:
                    rect = atlas.rect('stems'); half = (rect[0] + rect[2]) * 0.5
                    pl.tube(g, [e[1], e[2]], [0.008 * H, 0.006 * H], 3, None, (0.7, 0.9, 0.5),
                            mat=2, uv_rect=(rect[0], rect[1], half, rect[3]))
            elif kind == 'spathe':
                top, out, size = e[1], e[2], e[3]
                d = (out * 0.4 + UP).normalized()          # standing on the stalk, face turned outward
                pl.leaf(g, atlas, 'h_anthurium', top, d, size * (1 + 0.15 * lod), None, (1.0, 0.85, 0.85),
                        droop=0.15, segs=2 if lod == 0 else 1, across=2 if lod == 0 else 1, fold=0.2, mat=2)
            elif kind == 'leaf':
                base, a, L = e[1], e[2], e[3]
                d = Vector((math.cos(a) * 0.5, math.sin(a) * 0.5, 1.0)).normalized()
                pl.leaf(g, atlas, 'l_broad', base, d, L * (1 + 0.15 * lod), None, (0.6, 0.75, 0.55), droop=0.6,
                        segs=3 if lod == 0 else 1, across=2 if lod == 0 else 1, fold=0.3, mat=2)
            elif kind == 'vine':
                rect = atlas.rect('stems'); half = (rect[0] + rect[2]) * 0.5
                path = e[1] if lod == 0 else e[1][::2]
                pl.tube(g, path, [0.016 * H * (1 - 0.5 * i / len(path)) for i in range(len(path))],
                        [4, 3, 3][lod], None, (0.8, 0.7, 0.6), mat=2, uv_rect=(half, rect[1], rect[2], rect[3]))
            elif kind == 'ivy':
                ctr, out, size = e[1], e[2], e[3] * (1 + 0.2 * lod)
                side = UP.cross(out).normalized()
                pl.card(g, atlas, 's_ivy', ctr - UP * size * 0.5, side * size, UP * size, None, (0.85, 0.95, 0.8),
                        mat=2, normal=(out + UP * 0.3).normalized())
        objects.append(g.to_object(('Plant', 'Plant_LOD1', 'Plant_LOD2')[lod], mats))
    return objects
