"""Clean the Smart Topology worm and add its sand mound (work/clean_v1.blend -> work/clean_v2.blend + clean_v2.json).

Meshy returned the worm as six separate ring shells (the top one the head with the maw funnel), about 31 thorn spikes
and 13 fangs, all separate pieces (rules, not indices):
- ring shells: the few small holes filled; decimated (body rings 0.45, the head 0.55 to keep the maw funnel);
- spikes (small pieces outside the maw) and fangs (small pieces in the top fifth, on the maw's side of the axis):
  decimated to 0.40 / 0.50 (they are smooth cones);
- the procedural sand mound and rubble (scripts/mound.py) around the base: a low lumpy heap 1.85x the worm's width,
  0.10 m high at the axis (0.08 m where it meets the lowest ring), with eleven angular rock chunks.
Face attributes: `part` (0 ring, 1 head ring, 2 spike, 3 fang, 4 mound, 5 rock) and `seg` (ring index 0..5 for rings
and spikes, -1 otherwise). clean_v2.json: ring joints (crease heights on the axis), the maw frame (centre, normal,
rim radius from the fangs), mound parameters."""
import bpy, bmesh, os, sys, json, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mound as MD
import common as C

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(HERE, 'work')
bpy.ops.wm.open_mainfile(filepath=os.path.join(W, 'clean_v1.blend'))
src = bpy.data.objects['Worm']


def pieces_of(me):
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    lab = -np.ones(len(bm.verts), int); out = []
    for v in bm.verts:
        if lab[v.index] >= 0: continue
        st = [v]; lab[v.index] = len(out); idx = []
        while st:
            x = st.pop(); idx.append(x.index)
            for e in x.link_edges:
                w = e.other_vert(x)
                if lab[w.index] < 0: lab[w.index] = len(out); st.append(w)
        out.append(np.array(idx))
    bm.free()
    return out, lab


co = np.array([v.co[:] for v in src.data.vertices])
P, lab = pieces_of(src.data)
rings = sorted([k for k, p in enumerate(P) if len(p) > 300], key=lambda k: co[P[k], 2].mean())
assert len(rings) == 6, len(rings)
ztop = co[:, 2].max()
small = [k for k, p in enumerate(P) if len(p) <= 300]
fang = [k for k in small if co[P[k], 2].mean() > ztop * 0.80 and co[P[k], 1].mean() < -0.02]
spike = [k for k in small if k not in fang]
print('RINGS', [(k, len(P[k]), round(float(co[P[k], 2].min()), 3), round(float(co[P[k], 2].max()), 3)) for k in rings])
print('FANGS', len(fang), 'SPIKES', len(spike))

# maw frame from the fang bases (each fang's vertex nearest the head ring) and tips
head = co[P[rings[5]]]
bases, tips = [], []
for k in fang:
    pts = co[P[k]]
    d = np.array([np.min(np.linalg.norm(head[::3] - p, axis=1)) for p in pts])
    b = pts[d < d.min() + 0.006].mean(0); t = pts[np.argmax(np.linalg.norm(pts - b, axis=1))]
    bases.append(b); tips.append(t)
bases = np.array(bases); tips = np.array(tips)
mc = bases.mean(0)
u, s, vt = np.linalg.svd(bases - mc)
n = vt[2]
if n[2] < 0: n = -n
rim = float(np.linalg.norm((bases - mc) - np.outer((bases - mc) @ n, n), axis=1).mean())
print('MAW centre', mc.round(3).tolist(), 'normal', n.round(3).tolist(), 'rim', round(rim, 3),
      'tilt deg', round(math.degrees(math.acos(n[2])), 1))

# ring joints: crease heights between consecutive ring shells on the axis side
zr = [(float(co[P[k], 2].min()), float(co[P[k], 2].max())) for k in rings]
joints = [0.0]
for i in range(1, 6):
    joints.append(round((zr[i - 1][1] + zr[i][0]) / 2, 4))
joints.append(round(float(ztop), 4))
print('JOINTS', joints)

# ---- per piece: fill holes, decimate, tag ------------------------------------------------------------------------------
bpy.context.view_layer.objects.active = src
for o in bpy.data.objects: o.select_set(o == src)
bm = bmesh.new(); bm.from_mesh(src.data)
fa_part = bm.faces.layers.int.new('part'); fa_seg = bm.faces.layers.int.new('seg')
bm.verts.ensure_lookup_table()
seg_of = {}
for i, k in enumerate(rings):
    seg_of[k] = i
# spikes: the ring whose shell is nearest
ringtrees = []
for k in rings:
    ringtrees.append(co[P[k]])
for k in spike:
    c = co[P[k]].mean(0)
    seg_of[k] = int(np.argmin([np.min(np.linalg.norm(r - c, axis=1)) for r in ringtrees]))
for f in bm.faces:
    k = lab[f.verts[0].index]
    if k in rings:
        f[fa_part] = 1 if k == rings[5] else 0; f[fa_seg] = seg_of[k]
    elif k in fang:
        f[fa_part] = 3; f[fa_seg] = -1
    else:
        f[fa_part] = 2; f[fa_seg] = seg_of[k]
# fill the small holes of the ring shells
ring_set = set(rings)
bnd = [e for e in bm.edges if e.is_boundary and lab[e.verts[0].index] in ring_set]
res = bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
for f in res['faces']:
    nb = next((g for e in f.edges for g in e.link_faces if g is not f), None)
    if nb: f[fa_part] = nb[fa_part]; f[fa_seg] = nb[fa_seg]
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
print('FILLED', len(res['faces']), 'faces from', len(bnd), 'boundary edges')
bm.to_mesh(src.data); bm.free()

# decimate per class by separating loose parts, then join
RATIO = {0: 0.45, 1: 0.55, 2: 0.40, 3: 0.50}
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
parts = [o for o in bpy.data.objects if o.type == 'MESH']
for o in parts:
    cls = o.data.attributes['part'].data[0].value
    m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = RATIO[cls]; m.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = o
    for x in bpy.data.objects: x.select_set(x == o)
    bpy.ops.object.modifier_apply(modifier='dec')
for x in bpy.data.objects: x.select_set(x in parts)
keep = next(o for o in parts if o.data.attributes['part'].data[0].value == 0)
bpy.context.view_layer.objects.active = keep
bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
obj.name = obj.data.name = 'Worm'
for p in obj.data.polygons:
    p.use_smooth = True

# ---- mound + rubble ----------------------------------------------------------------------------------------------------
R0 = float(np.linalg.norm(co[P[rings[0]]][:, :2], axis=1).max())
R1 = 1.85 * R0; HM = 0.10
bm = bmesh.new(); bm.from_mesh(obj.data)
fa_part = bm.faces.layers.int['part']; fa_seg = bm.faces.layers.int['seg']
mf = MD.build_mound(bm, R0, R1, HM)
for f in mf:
    f[fa_part] = 4; f[fa_seg] = -1
rocks = MD.build_rocks(bm, R0, R1, HM)
for fl in rocks:
    for f in fl:
        f[fa_part] = 5; f[fa_seg] = -1
bmesh.ops.recalc_face_normals(bm, faces=[f for fl in rocks for f in fl] + mf)
bm.to_mesh(obj.data); bm.free()
for p in obj.data.polygons:
    p.use_smooth = obj.data.attributes['part'].data[p.index].value != 5     # rock chunks faceted
obj.data.update()
cnt = {}
for d in obj.data.attributes['part'].data:
    cnt[d.value] = cnt.get(d.value, 0) + 1
print('TRIS', len(obj.data.polygons), 'by part', dict(sorted(cnt.items())))
print('MOUND R0', round(R0, 3), 'R1', round(R1, 3), 'H', HM)
json.dump(dict(joints=joints, maw=dict(centre=mc.tolist(), normal=n.tolist(), rim=rim,
                                       bases=bases.tolist(), tips=tips.tolist()),
               mound=dict(R0=R0, R1=R1, H=HM)), open(os.path.join(W, 'clean_v2.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W, 'clean_v2.blend'))
H = 1.15
for name, (loc, tgt, s) in {'front': ((0, -4, 0.55), (0, 0, 0.55), 1.4), 'side': ((-4, 0, 0.55), (0, 0, 0.55), 1.4),
                            'quarter': ((-2.2, -2.6, 2.0), (0, 0, 0.5), 1.5), 'top': ((0, 0, 4), (0, 0, 0), 1.1),
                            'low': ((-1.5, -2.5, 0.35), (0, 0, 0.1), 1.2)}.items():
    C.render(loc, tgt, s, os.path.join(HERE, 'review', f'clean_{name}.png'), res=(500, 600), floor=False)
