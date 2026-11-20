"""xatlas unwrap of the crawler (run with a python that has xatlas: python3 -m venv <v> && <v>/bin/pip install xatlas).
Charts by xatlas from the rest mesh; head charts (face, mandibles, sac, eyes, head shield) scaled 2x about their centre;
repacked brute force into one 2048 page with 8-texel padding at the largest density that fits (bisection).
Smart UV Project shattered this decimated Meshy mesh into 821 islands at 27 % coverage (work/uv_smart_v1_mask.png).
Args: work/uv_in.npz work/uv_atlas.npz"""
import sys
import numpy as np
import xatlas

d = np.load(sys.argv[1]); out = sys.argv[2]
pos, idx, head = d['pos'], d['idx'], d['head']
RES, PAD, HEAD_SCALE = 2048, 8, 2.0

co = xatlas.ChartOptions(); co.max_iterations = 4
po = xatlas.PackOptions(); po.padding = PAD; po.resolution = RES; po.bilinear = True; po.bruteForce = False
po.rotate_charts = True
atlas = xatlas.Atlas(); atlas.add_mesh(pos, idx); atlas.generate(co, po)
vmap, tri, uv = atlas[0]
assert len(tri) == len(idx)
# charts = connected components of the output triangles
parent = np.arange(len(uv))
def f(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
for t in tri:
    a = f(t[0])
    for b in t[1:]:
        parent[f(b)] = a
chart = np.array([f(t[0]) for t in tri])
ids, chart = np.unique(chart, return_inverse=True)
print('CHARTS', len(ids), 'utilization stage 1', atlas.utilization)
uv = uv.copy()
for c in range(len(ids)):
    tris = chart == c
    if head[tris].mean() >= 0.5:
        vs = np.unique(tri[tris]); centre = uv[vs].mean(0)
        uv[vs] = centre + (uv[vs] - centre) * HEAD_SCALE
pos2 = pos[vmap]


def run(tpu):
    a = xatlas.Atlas(); a.add_mesh(pos2.astype(np.float32), tri.astype(np.uint32), uvs=uv.astype(np.float32))
    c = xatlas.ChartOptions(); c.use_input_mesh_uvs = True; c.fix_winding = False
    p = xatlas.PackOptions(); p.padding = PAD; p.bilinear = True; p.bruteForce = True; p.rotate_charts = True
    p.resolution = RES; p.texels_per_unit = tpu
    a.generate(c, p)
    return a


lo, hi, best = 200.0, 6000.0, None
for it in range(11):
    tpu = (lo + hi) / 2
    a = run(tpu)
    if a.atlas_count == 1:
        best = (tpu, a); lo = tpu
    else:
        hi = tpu
tpu, a = best
vm2, tri2, uv2 = a[0]
assert len(tri2) == len(idx)
corner = uv2[tri2]                       # (T, 3, 2), triangle order = input order
print('PACKED texels/m', round(tpu, 1), 'utilization', round(a.utilization, 3), 'atlas', a.width, a.height)
np.savez(out, uv=corner.astype(np.float32), tpu=tpu, utilization=a.utilization, charts=len(ids))
