"""PeasantM4's white walrus moustache as a modest volume on PeasantM8's clean-shaven upper lip (positions only; UVs,
weights, topology unchanged; done BEFORE the head retexture, so the paint follows it). Front-facing face vertices inside
a moustache footprint (cm, relative to the face midline X0 and the lip crease ZL) move along their normals by up to T:
a quick rise at the lower edge (the moustache hangs over the lip), a plateau, a soft fade into the skin under the nose
and toward the up-swept tips. The lower lip, nostrils and the rest of the face do not move.
Args: -- <in blend> <out blend> <report json> [T 0.004] [X0 -0.015] [ZL 0.715]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = a[:3]
T = float(a[3]) if len(a) > 3 else 0.004
X0 = float(a[4]) if len(a) > 4 else -0.015
ZL = float(a[5]) if len(a) > 5 else 0.715
# footprint: |dx| (cm) -> lower / upper boundary dz (cm above the crease), lateral strength
DX = [0.0, 1.2, 2.2, 3.0, 3.6, 3.9]
LO = [0.15, 0.10, -0.30, 0.10, 1.00, 1.40]
UP = [2.00, 1.90, 1.70, 1.80, 2.00, 2.10]
ST = [1.00, 1.00, 0.95, 0.75, 0.45, 0.0]
bpy.ops.wm.open_mainfile(filepath=IN)
o = bpy.data.objects['Body']; me = o.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
disp = {}
for v in bm.verts:
    if v.normal.y > -0.2 or v.co.y > -0.06:
        continue
    dx = abs(v.co.x - X0) * 100; dz = (v.co.z - ZL) * 100
    if dx >= DX[-1] or dz < -1 or dz > 2.5:
        continue
    lo, up, st = np.interp(dx, DX, LO), np.interp(dx, DX, UP), np.interp(dx, DX, ST)
    s = (dz - lo) / (up - lo)
    if s <= -0.08 or s >= 1:
        continue
    rise = np.clip((s + 0.08) / 0.3, 0, 1); rise = rise * rise * (3 - 2 * rise)
    fade = np.clip((1 - s) / 0.45, 0, 1); fade = fade * fade * (3 - 2 * fade)
    disp[v.index] = T * st * rise * fade
# two smoothing passes over the moved set and their neighbours
for _ in range(2):
    nd = dict(disp)
    for i in list(disp):
        nb = [e.other_vert(bm.verts[i]).index for e in bm.verts[i].link_edges]
        nd[i] = 0.5 * disp[i] + 0.5 * np.mean([disp.get(j, 0.0) for j in nb])
    disp = nd
for i, d in disp.items():
    v = bm.verts[i]; v.co = v.co + v.normal * d
bm.to_mesh(me); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
mv = np.array(list(disp.values()))
r = dict(moved=int((mv > 1e-5).sum()), max_mm=float(mv.max() * 1000), T_mm=T * 1000, X0=X0, ZL=ZL)
json.dump(r, open(REP, 'w'), indent=1); print('MOUSTACHE', r)
