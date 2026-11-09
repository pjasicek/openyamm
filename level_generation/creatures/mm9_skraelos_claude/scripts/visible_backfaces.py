"""Faces whose BACK side is the first hit of a view ray (one-sided cloth seen from behind: these show the background in game).
Orthographic ray grids (STEP m apart) from 8 azimuths at the given elevations over the rest mesh (all parts), BVH ray cast.
Writes <out npy>: the asm face indices hit from behind, with hit counts. Args: <asm npz> <out npy> [step 0.003] [elev 0,20,-20,50]"""
import bpy, sys, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
D = np.load(a[0]); co, tri = D['co'], D['tri']; STEP = float(a[2]) if len(a) > 2 else 0.003
ELEV = [float(x) for x in (a[3] if len(a) > 3 else '0,20,-20,50').split(',')]
bvh = BVHTree.FromPolygons([Vector(p) for p in co], [tuple(int(i) for i in t) for t in tri], epsilon=0.0)
fn = np.cross(co[tri[:, 1]] - co[tri[:, 0]], co[tri[:, 2]] - co[tri[:, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-12)
lo, hi = co.min(0), co.max(0); c = (lo + hi) / 2; R = np.linalg.norm(hi - lo) / 2 + 0.05
cnt = np.zeros(len(tri), int)
for el in ELEV:
    for az in range(0, 360, 45):
        th, ph = math.radians(az), math.radians(el)
        d = -np.array([math.sin(th) * math.cos(ph), -math.cos(th) * math.cos(ph), math.sin(ph)])     # ray direction (camera looks along d)
        u = np.cross(d, [0, 0, 1.0]); u = u / np.linalg.norm(u) if np.linalg.norm(u) > 1e-6 else np.array([1.0, 0, 0]); v = np.cross(u, d)
        n = int(2 * R / STEP)
        for i in range(n):
            for j in range(n):
                o = c - d * (R + 1) + u * (-R + i * STEP) + v * (-R + j * STEP)
                loc, nor, fi, dist = bvh.ray_cast(Vector(o), Vector(d))
                if fi is not None and fn[fi] @ d > 0: cnt[fi] += 1
hit = np.where(cnt > 0)[0]
np.save(a[1], np.c_[hit, cnt[hit]]); print('BACKFACES', len(hit), 'faces seen from behind')
