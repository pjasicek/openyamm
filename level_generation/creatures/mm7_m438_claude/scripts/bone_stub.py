"""Broken bone shafts for the stump and the severed forearm's cut end (review 2026-10-20: Smart Topology's four rods
read as a small hand). bone_shaft() returns vertices and triangles of one 6-sided shaft from `base` along `axis`:
rings at the base and mid-length, a jagged broken tip (each tip vertex shifted along the shaft by up to JAG) closed
by a centre vertex below the highest tip vertex; radius tapers 15 %. Deterministic per seed."""
import math
import numpy as np

JAG = 0.006


def frame(axis):
    a = np.asarray(axis, float); a /= np.linalg.norm(a)
    t = np.cross(a, (0.0, 0.0, 1.0)) if abs(a[2]) < 0.9 else np.cross(a, (1.0, 0.0, 0.0))
    t /= np.linalg.norm(t); b = np.cross(a, t)
    return a, t, b


def bone_shaft(base, axis, length, radius, seed, sides=6):
    rng = np.random.default_rng(seed)
    a, t, b = frame(axis)
    base = np.asarray(base, float)
    V, F = [], []
    rings = []
    for s, r in ((0.0, radius), (0.55, radius * 0.95), (1.0, radius * 0.85)):
        ring = []
        for k in range(sides):
            ang = 2 * math.pi * (k + 0.5 * (s == 1.0)) / sides
            off = (t * math.cos(ang) + b * math.sin(ang)) * r * (1 + rng.uniform(-0.08, 0.08))
            along = s * length + (rng.uniform(-JAG, JAG) if s == 1.0 else 0.0)
            ring.append(len(V)); V.append(base + a * along + off)
        rings.append(ring)
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for k in range(sides):
            k1 = (k + 1) % sides
            F += [(r0[k], r0[k1], r1[k1]), (r0[k], r1[k1], r1[k])]
    c = len(V); V.append(base + a * (length - JAG * 0.5))
    tip = rings[-1]
    for k in range(sides):
        F.append((tip[k], tip[(k + 1) % sides], c))
    c0 = len(V); V.append(base - a * radius * 0.3)                # closed bottom (hidden inside the flesh)
    for k in range(sides):
        F.append((rings[0][(k + 1) % sides], rings[0][k], c0))
    return np.array(V), F


def two_bones(end_centre, axis, across, seed=0, lengths=(0.034, 0.026), radii=(0.011, 0.0095), gap=0.013, depth=0.022):
    """Radius and ulna: two shafts side by side along `across`, based `depth` inside the cut, splayed 4 deg apart."""
    a = np.asarray(axis, float) / np.linalg.norm(axis); u = np.asarray(across, float)
    u = u - a * (u @ a); u /= np.linalg.norm(u)
    out = []
    for i, sgn in enumerate((1, -1)):
        ax = a * math.cos(math.radians(4)) + u * sgn * math.sin(math.radians(4))
        out.append(bone_shaft(np.asarray(end_centre) + u * sgn * gap - a * depth, ax, lengths[i] + depth, radii[i], seed + i))
    return out
