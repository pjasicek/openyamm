"""Clean neckline (orchestrator review of r6, 2026-11-02: the throat a patchwork of lighter flat rectangles, the skin-to-collar
edge a blocky stepped line). The head set's lower faces (the apron of head_split.py's level cut) lay on top of the body's collar
with a zigzag outline; the body's collar continues under them everywhere.

Positions only (faces, UVs, weights unchanged), on the master before neck_tuck.py (work/mouth_v14.blend):
1. neckline curve z_n(angle) about the neck axis: the top of the body set's collar per 10-degree bin, smoothed round the neck
   (circular window of SMOOTH bins), never below ZFRONT (just above the brooch) - a round neckline;
2. every head edge crossing the curve: its endpoint nearer the curve (within SNAP) moves onto it (height only), so the visible
   edge of the neck is a polyline lying on the smooth curve;
3. every head vertex below the curve moves BEHIND mm behind the nearest point of the body surface (along that face's normal):
   the apron is hidden under the collar, never coplanar with it.
Args (Blender): <in blend> <out blend> [zfront 0.645] [smooth 7] [snap 0.009] [behind 0.004]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
ZFRONT = float(a[2]) if len(a) > 2 else 0.645
SMOOTH = int(a[3]) if len(a) > 3 else 7
SNAP = float(a[4]) if len(a) > 4 else 0.009
BEHIND = float(a[5]) if len(a) > 5 else 0.004
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data; rig = body.parent
nb = rig.data.bones['Bip01 Neck']
C = np.array((rig.matrix_world @ nb.head_local)[:2])
P = np.array([v.co[:] for v in me.vertices])
hf = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hf)
hn = np.zeros(len(me.polygons), np.int32); me.attributes['hand'].data.foreach_get('value', hn)
head = np.zeros(len(P), bool); bodyv = np.zeros(len(P), bool)
for p in me.polygons:
    if hn[p.index]:
        continue
    (head if hf[p.index] else bodyv)[list(p.vertices)] = True
bodyv &= ~head
d = P[:, :2] - C
r = np.hypot(d[:, 0], d[:, 1]); ang = np.degrees(np.arctan2(d[:, 0], -d[:, 1]))
bins = np.arange(-180, 181, 10)
neckb = bodyv & (P[:, 2] > 0.55) & (r < 0.13)
top = np.array([P[neckb & (ang >= b) & (ang < b + 10), 2].max() if (neckb & (ang >= b) & (ang < b + 10)).any() else np.nan
                for b in bins[:-1]])
top = np.where(np.isnan(top), np.nanmin(top), top)
top = np.maximum(top, ZFRONT)
h = SMOOTH // 2
top = np.convolve(np.r_[top[-h:], top, top[:h]], np.ones(SMOOTH) / SMOOTH, 'valid')
top = np.maximum(top, ZFRONT)
zn = lambda angd: np.interp(angd, bins[:-1] + 5, top, period=360)
zv = zn(ang)
newP = P.copy()
# 2. snap the nearer endpoint of every crossing head edge onto the curve
headf = set(i for i in np.nonzero(head)[0].tolist())
snapped = set()
for e in me.edges:
    i, j = e.vertices
    if i not in headf or j not in headf or r[i] > 0.16 or r[j] > 0.16:
        continue
    ai, aj = P[i, 2] - zv[i], P[j, 2] - zv[j]
    if ai * aj >= 0:
        continue
    k = i if abs(ai) < abs(aj) else j
    if abs(P[k, 2] - zv[k]) <= SNAP and k not in snapped:
        newP[k, 2] = zv[k]; snapped.add(k)
# 3. below the curve: BEHIND behind the nearest body surface
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
lh = bm.faces.layers.int['head']; lhn = bm.faces.layers.int['hand']
keep = [f for f in bm.faces if not f[lh] and not f[lhn]]
verts = [v.co.copy() for v in bm.verts]
tris = [[v.index for v in f.verts] for f in keep]
tree = BVHTree.FromPolygons(verts, tris)
below = [k for k in np.nonzero(head & (r < 0.16) & (P[:, 2] < zv - 0.0005))[0].tolist() if k not in snapped]
moved = 0; maxmv = 0.0
for k in below:
    loc, nrm, fi, dist = tree.find_nearest(Vector(newP[k]), 0.05)
    if loc is None:
        continue
    # outward normal: away from the neck axis
    o = Vector((loc.x - C[0], loc.y - C[1], 0.0))
    if nrm.dot(o) < 0:
        nrm = -nrm
    tgt = np.array(loc - nrm * BEHIND)
    # never move a vertex outward (it may already be deep inside)
    rk = np.hypot(*(newP[k, :2] - C)); rt = np.hypot(*(tgt[:2] - C))
    if rt < rk or dist < BEHIND:
        mv = np.linalg.norm(tgt - newP[k]); maxmv = max(maxmv, mv)
        newP[k] = tgt; moved += 1
bm.free()
me.vertices.foreach_set('co', newP.ravel()); me.update()
# 4. r7b TRIM=1: delete head faces lying wholly on or below the curve (moving them behind the collar did not hide the apron
#    in front of the brooch); the head shell then ends on the snapped polyline. Faces, not paint: the remaining faces keep their
#    UVs. Loose vertices removed.
import os
ntrim = 0
if os.environ.get('TRIM') == '1':
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
    lh = bm.faces.layers.int['head']; lhn = bm.faces.layers.int['hand']
    kill = []
    for f in bm.faces:
        if not f[lh] or f[lhn]:
            continue
        vs = [v.index for v in f.verts]
        if r[vs].max() > 0.16:
            continue
        dz = newP[vs, 2] - zv[vs]
        if dz.max() <= 0.0005 and dz.min() < -0.0005:
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    ntrim = len(kill)
    bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('NECKLINE ' + json.dumps({'trimmed_faces': ntrim, 'snapped': len(snapped), 'below': len(below), 'moved_behind': moved,
                                'max_move_mm': round(maxmv * 1000, 1), 'neckline_z_every_60deg': [round(float(t), 3) for t in top[::6]]}))
