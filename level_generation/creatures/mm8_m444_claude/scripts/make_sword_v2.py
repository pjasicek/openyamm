#!/usr/bin/env python3
"""Rebuild the Smuggler's sword (user review 2026-10-19: "ultra plain/cheap like just a slab").

The first sword was a 9 mm hexagonal slab with a box crossbar (144 triangles, 320x64 texture). The native frames show
a short broad sword: a steel blade with a dark central fuller, a gold crossguard with knobbed ends, a dark wrapped grip
and a gold pommel. This builds that in the same frame as the installed file, so the fitted grip and the `Sword` node
stay valid: grip centred on the origin along +y (radius 12 mm where the hand closes), edge along x, flat along z, the
point at 0.68 m. Blade: bevelled edges and a fuller (hard across the facets, smooth along the length); guard: a tube
curving toward the blade with ball ends; grip: a slightly swelled tube; pommel: a flattened sphere. Four LODs
(the shading follows the facets down to a diamond blade at LOD2). Texture 512x128 (colours linear, written as sRGB): steel (brushed, bright edges, dark
fuller), gold, leather wrap with a groove normal map; MR keeps this model's contract (R specular class, G roughness,
B metallic 0); the region mask is empty (the sword is not recoloured per tier). Materials, variants and the node are
those of the installed file.

Usage: make_sword_v2.py <installed sword.glb> <out.glb> [--preview dir]
"""
import io
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402

TEX_W, TEX_H = 512, 128
BLADE_BASE, BLADE_TIP = 0.068, 0.68
WIDTH = [(0.068, 0.031), (0.11, 0.031), (0.40, 0.028), (0.56, 0.022), (0.635, 0.012), (0.68, 0.0)]
THICK = [(0.068, 0.0045), (0.50, 0.0036), (0.68, 0.0010)]
GUARD_Y, GUARD_HALF = 0.064, 0.072  # bottom 54 mm, at the old guard (55 mm) above the fitted hand


def interp(table, y):
    xs, ys = zip(*table)
    return float(np.interp(y, xs, ys))


def fuller(y):
    """Fuller depth: full between 0.09 and 0.50 m, fading at both ends."""
    return float(np.clip(min((y - 0.072) / 0.02, (0.56 - y) / 0.06), 0, 1))


class Part:
    def __init__(self):
        self.p, self.uv, self.tris, self.center = [], [], [], []

    def vertex(self, p, uv, center):
        self.p.append(p)
        self.uv.append(uv)
        self.center.append(center)
        return len(self.p) - 1

    def quad(self, a, b, c, d):
        self.tris += [(a, b, c), (a, c, d)]


def blade(part, lod):
    profiles = {
        0: [(1, 0), (.55, 1), (.2, 1), (0, None), (-.2, 1), (-.55, 1), (-1, 0), (-.55, -1), (-.2, -1), (0, None),
            (.2, -1), (.55, -1)],
        1: [(1, 0), (.45, 1), (-.45, 1), (-1, 0), (-.45, -1), (.45, -1)],
        2: [(1, 0), (0, 1), (-1, 0), (0, -1)],
        3: [(1, 0), (0, 1), (-1, 0), (0, -1)],
    }[lod]
    rings = {0: [0.068, 0.09, 0.13, 0.25, 0.40, 0.50, 0.56, 0.60, 0.635], 1: [0.068, 0.11, 0.30, 0.50, 0.60, 0.635],
             2: [0.068, 0.40, 0.60], 3: [0.068, 0.55]}[lod]

    def point(y, k):
        x, z = profiles[k % len(profiles)]
        w, t = interp(WIDTH, y), interp(THICK, y)
        if z is None:
            # Fuller floor: the centre of each face sinks by up to 45 % of the thickness.
            sign = 1 if k < len(profiles) // 2 else -1
            z = sign * (1 - 0.45 * fuller(y))
        return (x * w, y, z * t)

    def uv(p):
        return (0.70 * (p[1] - BLADE_BASE) / (BLADE_TIP - BLADE_BASE), 0.25 - 0.24 * p[0] / 0.031)

    n = len(profiles)
    for k in range(n):
        # One column per facet with its own vertices: hard across the blade, smooth along it.
        column = []
        for y in rings:
            a, b = point(y, k), point(y, k + 1)
            column.append((part.vertex(a, uv(a), (0, y, 0)), part.vertex(b, uv(b), (0, y, 0))))
        for (a0, b0), (a1, b1) in zip(column, column[1:]):
            part.quad(a0, b0, b1, a1)
        tip = (0.0, BLADE_TIP, 0.0)
        t = part.vertex(tip, uv(tip), (0, BLADE_TIP - 0.01, 0))
        a, b = column[-1]
        part.tris.append((a, b, t))
    # Base cap (inside the guard).
    base = [part.vertex(point(BLADE_BASE, k), uv(point(BLADE_BASE, k)), (0, BLADE_BASE + 0.01, 0)) for k in range(n)]
    for k in range(1, n - 1):
        part.tris.append((base[0], base[k + 1], base[k]))


def tube(part, path, radii, sides, uvRect, capStart=True, capEnd=True):
    """Tube along a polyline `path` with elliptical radii (r_a, r_b) per station; UV u by angle, v by station."""
    path = np.asarray(path, float)
    u0, v0, u1, v1 = uvRect
    rings = []
    for i, centre in enumerate(path):
        tangent = path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]
        tangent /= np.linalg.norm(tangent)
        helper = np.array([0, 0, 1.0]) if abs(tangent[2]) < 0.9 else np.array([1.0, 0, 0])
        a = np.cross(helper, tangent)
        a /= np.linalg.norm(a)
        b = np.cross(tangent, a)
        ring = []
        for s in range(sides + 1):
            angle = 2 * math.pi * s / sides
            p = centre + radii[i][0] * math.cos(angle) * a + radii[i][1] * math.sin(angle) * b
            ring.append(part.vertex(tuple(p), (u0 + (u1 - u0) * s / sides, v0 + (v1 - v0) * i / (len(path) - 1)),
                                    tuple(centre)))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for s in range(sides):
            part.quad(r0[s], r0[s + 1], r1[s + 1], r1[s])
    for ring, centre, start in ((rings[0], path[0], True), (rings[-1], path[-1], False)):
        if (start and capStart) or (not start and capEnd):
            c = part.vertex(tuple(centre), (u0, v0), tuple(centre + (path[1] - path[0] if start else path[-2] - path[-1])
                                                          * 0.5))
            for s in range(sides):
                part.tris.append((c, ring[s + 1], ring[s]) if start else (c, ring[s], ring[s + 1]))


def sphere(part, centre, radii, segments, rings, uvRect):
    u0, v0, u1, v1 = uvRect
    top = part.vertex((centre[0], centre[1] + radii[1], centre[2]), (u0, v0), centre)
    bottom = part.vertex((centre[0], centre[1] - radii[1], centre[2]), (u0, v1), centre)
    grid = []
    for r in range(1, rings):
        phi = math.pi * r / rings
        row = []
        for s in range(segments + 1):
            theta = 2 * math.pi * s / segments
            p = (centre[0] + radii[0] * math.sin(phi) * math.cos(theta), centre[1] + radii[1] * math.cos(phi),
                 centre[2] + radii[2] * math.sin(phi) * math.sin(theta))
            row.append(part.vertex(p, (u0 + (u1 - u0) * s / segments, v0 + (v1 - v0) * r / rings), centre))
        grid.append(row)
    for s in range(segments):
        part.tris.append((top, grid[0][s + 1], grid[0][s]))
        part.tris.append((bottom, grid[-1][s], grid[-1][s + 1]))
    for r0, r1 in zip(grid, grid[1:]):
        for s in range(segments):
            part.quad(r0[s], r0[s + 1], r1[s + 1], r1[s])


GOLD, LEATHER = (0.72, 0.0, 1.0, 0.5), (0.0, 0.5, 0.70, 1.0)


def build(lod):
    parts = []
    b = Part()
    blade(b, lod)
    parts.append((b, False))
    # Guard: curves 6 mm toward the blade at the ends, thinner toward its ball ends.
    stations = {0: 7, 1: 5, 2: 3, 3: 2}[lod]
    sides = {0: 8, 1: 6, 2: 4, 3: 4}[lod]
    xs = np.linspace(-GUARD_HALF, GUARD_HALF, stations)
    path = [(x, GUARD_Y + 0.006 * (x / GUARD_HALF) ** 2, 0.0) for x in xs]
    radii = [(0.010 - 0.003 * abs(x / GUARD_HALF), 0.013 - 0.005 * abs(x / GUARD_HALF)) for x in xs]
    g = Part()
    tube(g, path, radii, sides, GOLD, capStart=lod >= 2, capEnd=lod >= 2)
    if lod < 2:
        for x in (-GUARD_HALF - 0.006, GUARD_HALF + 0.006):
            sphere(g, (x, GUARD_Y + 0.0065, 0.0), (0.011, 0.011, 0.011), 8 if lod == 0 else 6, 5 if lod == 0 else 3,
                   GOLD)
    parts.append((g, True))
    # Grip and ferrule: swelled leather tube; a gold band under the guard.
    gripSides = {0: 10, 1: 8, 2: 6, 3: 4}[lod]
    ys = {0: [-0.072, -0.05, -0.02, 0.01, 0.046], 1: [-0.072, -0.02, 0.046], 2: [-0.072, 0.046],
          3: [-0.072, 0.056]}[lod]
    grip = Part()
    tube(grip, [(0, y, 0) for y in ys], [(0.0118 + 0.0008 * math.cos(math.pi * (y + 0.018) / 0.11),) * 2 for y in ys],
         gripSides, LEATHER, capStart=False, capEnd=lod == 3)
    parts.append((grip, True))
    if lod < 3:
        band = Part()
        tube(band, [(0, 0.044, 0), (0, 0.056, 0)], [(0.0135, 0.0135)] * 2, gripSides, GOLD, capStart=True,
             capEnd=True)
        parts.append((band, True))
    pommel = Part()
    sphere(pommel, (0.0, -0.086, 0.0), (0.0165, 0.014, 0.0165), {0: 10, 1: 8, 2: 6, 3: 4}[lod],
           {0: 6, 1: 4, 2: 3, 3: 2}[lod], GOLD)
    parts.append((pommel, True))
    return parts


def assemble(parts):
    """Merge parts, orient every triangle outward from its part centre, and compute vertex normals."""
    positions, uvs, normals, tris = [], [], [], []
    for part, smooth in parts:
        p = np.asarray(part.p, np.float64)
        centre = np.asarray(part.center, np.float64)
        t = np.asarray(part.tris, np.int64)
        face = np.cross(p[t[:, 1]] - p[t[:, 0]], p[t[:, 2]] - p[t[:, 0]])
        outward = p[t].mean(1) - centre[t].mean(1)
        flip = (face * outward).sum(1) < 0
        t[flip] = t[flip][:, [0, 2, 1]]
        face[flip] *= -1
        n = np.zeros_like(p)
        for k in range(3):
            np.add.at(n, t[:, k], face)
        if smooth:
            # One normal per position across UV seams (the blade keeps its hard facets).
            _, group = np.unique(np.round(p, 6), axis=0, return_inverse=True)
            summed = np.zeros((group.max() + 1, 3))
            np.add.at(summed, group, n)
            n = summed[group]
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        tris.append(t + sum(len(x) for x in positions))
        positions.append(p)
        uvs.append(np.asarray(part.uv, np.float64))
        normals.append(n)
    return (np.concatenate(positions).astype(np.float32), np.concatenate(normals).astype(np.float32),
            np.concatenate(uvs).astype(np.float32), np.concatenate(tris).astype(np.uint16))


def textures():
    rng = np.random.default_rng(444)
    u = (np.arange(TEX_W) + 0.5) / TEX_W
    v = (np.arange(TEX_H) + 0.5) / TEX_H
    U, V = np.meshgrid(u, v)
    colour = np.zeros((TEX_H, TEX_W, 3), np.float32)
    mr = np.zeros((TEX_H, TEX_W, 3), np.float32)
    height = np.zeros((TEX_H, TEX_W), np.float32)
    # Steel: brushed along the blade, bright bevelled edges, the dark fuller down the middle where it is cut.
    steel = (U < 0.71) & (V < 0.5)
    across = np.abs((0.25 - V) / 0.24)  # 0 centre .. 1 edge
    y = BLADE_BASE + U / 0.70 * (BLADE_TIP - BLADE_BASE)
    full = np.vectorize(fuller)(y)
    streaks = np.repeat(rng.normal(0, 1, (TEX_H, 1)), TEX_W, 1) * 0.025 + rng.normal(0, 0.012, (TEX_H, TEX_W))
    tone = 0.34 + streaks + 0.14 * np.clip((across - 0.55) / 0.45, 0, 1) ** 1.5
    tone *= 1 - 0.6 * full * np.clip(1 - across / 0.26, 0, 1)
    tone *= 1 - 0.3 * np.clip(1 - (y - BLADE_BASE) / 0.03, 0, 1)
    colour[steel] = (tone[..., None] * np.array([0.95, 1.0, 1.06]))[steel]
    mr[steel] = (230, 80, 0)
    # Gold: warm brass with soft wear.
    gold = (U >= 0.71) & (V < 0.5)
    wear = rng.normal(0, 0.05, (TEX_H, TEX_W))
    colour[gold] = (np.array([0.50, 0.32, 0.08]) * (1 + wear)[..., None])[gold]
    mr[gold] = (200, 100, 0)
    # Leather wrap: diagonal bands with dark grooves between them.
    leather = V >= 0.5
    phase = ((U / 0.70) * 6 + (V - 0.5) / 0.5 * 7) % 1.0
    groove = np.clip(1 - np.abs(phase - 0.5) / 0.08, 0, 1)
    band = 0.75 + 0.25 * np.sin(math.pi * phase)
    leatherTone = band * (1 - 0.55 * groove) * (1 + rng.normal(0, 0.06, (TEX_H, TEX_W)))
    colour[leather] = (np.array([0.085, 0.045, 0.025]) * leatherTone[..., None])[leather]
    mr[leather] = (38, 170, 0)
    height[leather] = (np.sin(math.pi * phase) * (1 - groove))[leather]
    dx = np.gradient(height * 1.5, axis=1)
    dy = np.gradient(height * 1.5, axis=0)
    normal = np.stack([-dx, dy, np.ones_like(dx)], -1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    to8 = lambda a: np.clip(a, 0, 255).astype(np.uint8)  # noqa: E731
    return {
        'basecolor': to8(colour ** (1 / 2.2) * 255 + 0.5),
        'metal_rough': to8(mr),
        'normal': to8((normal + 1) * 127.5 + 0.5),
        'region_mask': np.zeros((TEX_H, TEX_W, 4), np.uint8),
    }


def main():
    source, target = Path(sys.argv[1]), Path(sys.argv[2])
    preview = Path(sys.argv[sys.argv.index('--preview') + 1]) if '--preview' in sys.argv else None
    doc, binary = read_glb(source)
    assert not doc.get('animations') and not doc.get('skins')
    material = doc['materials'][0]
    roles = {
        material['pbrMetallicRoughness']['baseColorTexture']['index']: 'basecolor',
        material['pbrMetallicRoughness']['metallicRoughnessTexture']['index']: 'metal_rough',
        material['normalTexture']['index']: 'normal',
        material['extras']['openyamm_region_mask']['index']: 'region_mask',
    }
    maps = textures()
    if preview:
        preview.mkdir(parents=True, exist_ok=True)
        for name, array in maps.items():
            Image.fromarray(array).save(preview / f'{name}.png')
    new = bytearray()
    views, accessors = [], []

    def add(data, target=None):
        new.extend(b'\0' * (-len(new) % 4))
        view = {'buffer': 0, 'byteOffset': len(new), 'byteLength': len(data)}
        if target:
            view['target'] = target
        new.extend(data)
        views.append(view)
        return len(views) - 1

    def accessor(array, kind, component, target, bounds=False):
        entry = {'bufferView': add(array.tobytes(), target), 'componentType': component, 'count': len(array),
                 'type': kind}
        if bounds:
            entry['min'] = array.min(0).tolist()
            entry['max'] = array.max(0).tolist()
        accessors.append(entry)
        return len(accessors) - 1

    counts = []
    for lod, mesh in enumerate(doc['meshes']):
        positions, normals, uvs, tris = assemble(build(lod))
        primitive = mesh['primitives'][0]
        primitive['attributes'] = {
            'POSITION': accessor(positions, 'VEC3', 5126, 34962, True),
            'NORMAL': accessor(normals, 'VEC3', 5126, 34962),
            'TEXCOORD_0': accessor(uvs, 'VEC2', 5126, 34962),
        }
        primitive['indices'] = accessor(tris.reshape(-1), 'SCALAR', 5123, 34963)
        counts.append(len(tris))
    for image in doc['images']:
        texture = next(i for i, t in enumerate(doc['textures']) if t['source'] == doc['images'].index(image))
        buffer = io.BytesIO()
        Image.fromarray(maps[roles[texture]]).save(buffer, 'PNG', optimize=True)
        image['bufferView'] = add(buffer.getvalue())
    doc['bufferViews'] = views
    doc['accessors'] = accessors
    write_glb(target, doc, bytes(new))
    print('SWORD triangles per LOD', counts, f'{len(new) / 1e3:.0f} kB')


if __name__ == '__main__':
    main()
