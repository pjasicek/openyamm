"""xatlas unwrap of the Ashrunner body faces (after hes_crawler_claude/scripts/uv_atlas.py). Run with a Python that has
xatlas (python3 -m venv <v> && <v>/bin/pip install xatlas numpy):  <v>/bin/python -I scripts/uv_atlas.py
work/uvpack_in.npz work/uv_pack.npz
Charts by xatlas from the rest mesh (body faces only: the head has its own 1K set), scaled per chart by how much it is
seen (CHART_SCALE by garment: the back pack and its gear 0.8; faces whose Meshy UVs are one texel, the goggles' brass
and strap from face_fix.py, 0.15), then packed into PAGES 1024 pages (default 2, side by side: one 2048 x 1024 body
page) with PAD-texel padding (default 6) at the largest density that fits (bisection on texels per metre).
Measured (6.69 m2 of body faces, 524 charts): one 1K page 265 texels/m at padding 4; two pages 382 at padding 6, 348 at
8 (xatlas's brute-force packing came out lower, 240 on one page). Env PAGES, PAD, PACK_SCALE, MAX_COST, NDW, BRUTE. Output corner UVs in Blender's convention, triangle order = input order."""
import os, sys
import numpy as np
import xatlas

d = np.load(sys.argv[1]); out = sys.argv[2]
co, vid, old = d['co'], d['vid'], d['old_uv']
E = os.environ.get
RES, PAD, PAGES = 1024, int(E('PAD', '6')), int(E('PAGES', '2'))   # PAGES 2: a 2048 x 1024 body page
CHART_SCALE = {7: float(E('PACK_SCALE', '0.8'))}
used = np.unique(vid); remap = -np.ones(len(co), np.int64); remap[used] = np.arange(len(used))
pos = co[used].astype(np.float32); idx = remap[vid].astype(np.uint32)
e1, e2 = old[:, 1] - old[:, 0], old[:, 2] - old[:, 0]
olda = 0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]) * 1024 * 1024
degenerate = olda < 0.05
co_ = xatlas.ChartOptions(); co_.max_iterations = 4; co_.max_cost = float(E('MAX_COST', '4'))
co_.normal_deviation_weight = float(E('NDW', '2'))
po = xatlas.PackOptions(); po.padding = PAD; po.resolution = RES; po.bilinear = True; po.rotate_charts = True
atlas = xatlas.Atlas(); atlas.add_mesh(pos, idx); atlas.generate(co_, po)
vmap, tri, uv = atlas[0]
assert len(tri) == len(idx)
parent = np.arange(len(uv))
def f(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]; i = parent[i]
    return i
for t in tri:
    r = f(t[0])
    for b in t[1:]:
        parent[f(b)] = r
_, chart = np.unique(np.array([f(t[0]) for t in tri]), return_inverse=True)
print('CHARTS', chart.max() + 1, 'stage-1 utilization', round(float(atlas.utilization), 3))
uv = uv.copy()
for c in range(chart.max() + 1):
    tris = chart == c
    s = 0.15 if degenerate[tris].mean() > 0.5 else float(np.mean([CHART_SCALE.get(int(g), 1.0) for g in d['garment'][tris]]))
    if s != 1.0:
        vs = np.unique(tri[tris]); centre = uv[vs].mean(0); uv[vs] = centre + (uv[vs] - centre) * s
pos2 = pos[vmap]


def run(tpu):
    a = xatlas.Atlas(); a.add_mesh(pos2.astype(np.float32), tri.astype(np.uint32), uvs=uv.astype(np.float32))
    c = xatlas.ChartOptions(); c.use_input_mesh_uvs = True; c.fix_winding = False
    p = xatlas.PackOptions(); p.padding = PAD; p.bilinear = True; p.bruteForce = bool(int(E('BRUTE', '0'))); p.rotate_charts = True
    p.resolution = RES; p.texels_per_unit = tpu
    a.generate(c, p)
    return a


lo, hi, best = 100.0, 1200.0, None
for it in range(10):
    tpu = (lo + hi) / 2
    a = run(tpu)
    if a.atlas_count <= PAGES:
        best = (tpu, a); lo = tpu
    else:
        hi = tpu
    print('TRY', round(tpu, 1), a.atlas_count, flush=True)
tpu, a = best
_, tri2, uv2 = a[0]
assert len(tri2) == len(idx)
page = np.asarray(a.get_mesh_vertex_assignment(0)[0]).astype(np.int64) if PAGES > 1 else np.zeros(len(uv2), int)
uv2 = uv2.astype(np.float64).copy(); uv2[:, 0] = (uv2[:, 0] + page) / PAGES     # page 0 left, page 1 right
corner = uv2[tri2]
corner[..., 1] = 1.0 - corner[..., 1]         # xatlas v runs down the image; Blender's up
print('PACKED texels/m', round(tpu, 1), 'utilization', round(float(a.utilization), 3), 'atlas', a.width, a.height)
np.savez(out, uv=corner, tpu=tpu, utilization=a.utilization, charts=chart.max() + 1, degenerate=degenerate)
