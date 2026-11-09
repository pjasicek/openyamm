"""PeasantDM3 variant of the PeasantDM1 master (geometry only, rest pose; UV layers kept, head UVs re-laid later).
MM9's PEASANTDM3 is PEASANTDM1's body with long hair to the shoulders and a longer pointed beard, and no medallion.
1. delete the medallion (cord, pendant, bail), the Meshy eyeball cups (DM1 dropped them at export) and the 4-vertex shin
   sliver;
2. beard: the head shell's chin and jaw below the mouth move down and forward (wedge, tip ~4 cm lower, ~2 cm forward);
3. hair: the bob below Z_TOP is stretched down per column to a bottom height by azimuth (back lowest), then every hair
   vertex inside / near the torso + head shell is pushed out to OFFSET along the nearest surface normal, a few smoothing
   passes, again pushed out;
4. weights: the lengthened hair blends Head -> Neck -> Spine2 below the jaw (the hanging ends follow the shoulders when
   the head turns); the face, beard and scalp stay 100 % Head (rigid head).
Args: -- <in blend> <out blend> [key=value ...]"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts_lib as L
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = argv[0], argv[1]
O = dict(z_top=0.47, hair_bottom=0.39, back_bottom=0.29, side_bottom=0.33, front_bottom=0.36, offset=0.008,
         beard_dz=0.042, beard_dy=0.022, beard_top=0.400, beard_full=0.355, beard_halfwidth=0.11, smooth=2,
         weights=1, shape=1, blend_top=0.38)
for a in argv[2:]:
    k, v = a.split('='); O[k] = float(v)
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
assert all(abs(body.matrix_world[i][j] - (1 if i == j else 0)) < 1e-6 for i in range(4) for j in range(4)), 'Body not identity'
me = body.data
co = L.rest_coords(body); lab = L.loose_parts(me)
rep = {}
# 1. delete parts
drop = []
for p in np.unique(lab):
    s = lab == p; q = co[s]; n = s.sum(); lo, hi = q.min(0), q.max(0)
    if n <= 6:
        drop.append(int(p)); continue
    if n < 60 and 0.45 < lo[2] and hi[2] < 0.49 and hi[1] < -0.07:
        drop.append(int(p)); continue                        # eyeball cups
    if n < 60 and 0.19 < lo[2] and hi[2] < 0.35 and hi[1] < -0.015 and abs((lo[0] + hi[0]) / 2) < 0.03:
        drop.append(int(p)); continue                        # medallion cord, pendant, bail
rep['dropped_parts'] = [(p, int((lab == p).sum()), co[lab == p].min(0).round(3).tolist(), co[lab == p].max(0).round(3).tolist()) for p in drop]
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
dv = [bm.verts[i] for i in np.where(np.isin(lab, drop))[0]]
bmesh.ops.delete(bm, geom=dv, context='VERTS')
bm.to_mesh(me); bm.free(); me.update()
co = L.rest_coords(body); lab = L.loose_parts(me)
shell = L.find_part(lab, co, 0.266, 0.595); hair = L.find_part(lab, co, 0.393, 0.607)
torso = int(np.bincount(lab).argmax())
assert shell is not None and hair is not None
sv = np.where(lab == shell)[0]; hv = np.where(lab == hair)[0]
xc = (co[sv, 0].min() + co[sv, 0].max()) / 2; yc = (co[sv, 1].min() + co[sv, 1].max()) / 2
rep['head_axis'] = [round(xc, 4), round(yc, 4)]
new = co.copy()
if not O['shape']:
    O['beard_dz'] = O['beard_dy'] = 0.0; O['weights'] = 0
# 2. beard wedge on the shell
def smooth01(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
s = co[sv]
a = smooth01((O['beard_top'] - s[:, 2]) / (O['beard_top'] - O['beard_full']))
b = np.cos(np.clip(np.abs(s[:, 0] - xc) / O['beard_halfwidth'], 0, 1) * math.pi / 2) ** 1.2
c = smooth01((0.0 - (s[:, 1] - yc)) / 0.06)               # front half only, full in front of y-0.06
w = a * b * c
new[sv, 2] -= O['beard_dz'] * w
new[sv, 1] -= O['beard_dy'] * w
rep['beard_moved'] = int((w > 0.01).sum())
# 3. hair
h = co[hv]
theta = np.degrees(np.arctan2(h[:, 0] - xc, h[:, 1] - yc))   # 0 = back (+y), +-180 = face
at = np.abs(theta)
zb = np.where(at <= 90, O['back_bottom'] + (O['side_bottom'] - O['back_bottom']) * (at / 90) ** 1.5,
              O['side_bottom'] + (O['front_bottom'] - O['side_bottom']) * np.clip((at - 90) / 45, 0, 1))
k = (O['z_top'] - zb) / (O['z_top'] - O['hair_bottom'])
if not O['shape']: k[:] = 1.0
low = h[:, 2] < O['z_top']
nz = h[:, 2].copy()
nz[low] = O['z_top'] - (O['z_top'] - h[low, 2]) * k[low]
new[hv, 2] = nz
# push out of torso + shell (+ the arms' shoulders are in the torso part)
def bvh_of(parts, coords):
    vs = coords.tolist(); fs = []
    for f in me.polygons:
        if lab[f.vertices[0]] in parts:
            fs.append(list(f.vertices))
    return BVHTree.FromPolygons(vs, fs)
tree = bvh_of({torso, shell}, new)
moved = np.zeros(len(hv), bool)
def push(cur):
    out = cur.copy(); hit = np.zeros(len(hv), bool)
    for i, vi in enumerate(hv):
        if cur[vi, 2] > O['z_top'] + 0.02: continue
        loc, nor, idx, dist = tree.find_nearest(Vector(cur[vi]))
        if loc is None: continue
        d = (Vector(cur[vi]) - loc).dot(nor)
        if d < O['offset']:
            out[vi] = np.array(loc + nor * O['offset']); hit[i] = True
    return out, hit
if O['shape']:
    new, hit = push(new); moved |= hit
else:
    O['smooth'] = 0
# smoothing passes on the lowered hair (umbrella, hair-only neighbours), re-push each time
nb = [[] for _ in range(len(me.vertices))]
for e in me.edges:
    a_, b_ = e.vertices
    if lab[a_] == hair and lab[b_] == hair: nb[a_].append(b_); nb[b_].append(a_)
wt = np.clip((O['z_top'] - co[hv, 2]) / 0.03, 0, 1)        # only below z_top
for it in range(int(O['smooth'])):
    avg = np.array([new[nb[vi]].mean(0) if nb[vi] else new[vi] for vi in hv])
    new[hv] = new[hv] + (avg - new[hv]) * 0.5 * wt[:, None]
    new, hit = push(new); moved |= hit
rep['hair_pushed'] = int(moved.sum()); rep['hair_lowered'] = int(low.sum())
rep['hair_bottom_new'] = round(float(new[hv, 2].min()), 3)
co_flat = new.reshape(-1)
me.vertices.foreach_set('co', co_flat); me.update()
# 4. weights
if O['weights']:
    groups = {g.name: g for g in body.vertex_groups}
    H, N, S2 = groups['Bip01 Head'], groups['Bip01 Neck'], groups['Bip01 Spine2']
    for i, vi in enumerate(hv):
        z = new[vi, 2]
        t = float(np.clip((O['blend_top'] - z) / (O['blend_top'] - 0.30), 0, 1))   # 0 at blend_top, 1 at 0.30
        if t <= 0: continue
        wh = 1 - 0.65 * t; wn = 0.45 * min(1, t * 1.6) * (1 - 0.3 * t); ws = 1 - wh - wn
        for g in body.vertex_groups:
            g.remove([int(vi)])
        H.add([int(vi)], wh, 'REPLACE'); N.add([int(vi)], wn, 'REPLACE')
        if ws > 1e-3: S2.add([int(vi)], ws, 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
rep['out'] = OUT
print('RESHAPE', json.dumps(rep))
