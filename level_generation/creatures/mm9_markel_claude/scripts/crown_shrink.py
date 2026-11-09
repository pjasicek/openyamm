"""Shrink the hair cap onto the scalp over the bald crown (mm9_markel, 2026-11-02). Smart Topology modelled a full hair
cap (a separate shell up to 1.4 cm above the face shell's skull); with the crown painted bald (bald_crown.py) the cap's
front edge stood as a step across the upper forehead and the bald head read bulky. Hair-shell vertices inside the
bald_crown.py ellipse (same AX/AZ/Z0/YMIN, no noise, feathered over FEATHER of the ellipse radius) move toward the nearest
point of the face shell plus GAP along its normal. Positions only: UVs, weights, attributes and topology are unchanged,
so the paid textures stay valid. Bind pose, Blender coordinates (z up = glTF y minus the export LIFT).
Args: -- <in blend> <out blend> [ax 0.068] [az 0.080] [z0 0.012] [ymin 1.700] [lift 0.8487] [gap 0.0015]"""
import bpy, bmesh, sys
import numpy as np
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
AX, AZ, Z0, YMIN, LIFT, GAP = (float(x) for x in (a[2:8] + ['0.068', '0.080', '0.012', '1.700', '0.8487', '0.0015'][len(a[2:8]):]))
FEATHER = 0.22
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
me = body.data
head = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', head)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
comp = -np.ones(len(bm.verts), np.int32); cid = 0
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    st = [v]; comp[v.index] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0:
                comp[y.index] = cid; st.append(y)
    cid += 1
CO = np.array([v.co[:] for v in bm.verts])
fpart = np.array([comp[f.verts[0].index] for f in bm.faces])
hp = [k for k in np.unique(fpart[head == 1])]
info = {k: (int((fpart == k).sum()), CO[comp == k].min(0).round(3).tolist(), CO[comp == k].max(0).round(3).tolist()) for k in hp}
print('PARTS', info)
# hair = the head part reaching furthest back (Blender +y is the back); face = the head part reaching furthest forward
hair = max(hp, key=lambda k: CO[comp == k][:, 1].max())
face = min(hp, key=lambda k: CO[comp == k][:, 1].min())
print('HAIR part', hair, 'FACE part', face)
ff = [f for f in bm.faces if fpart[f.index] == face]
fverts = sorted({v.index for f in ff for v in f.verts}); remap = {v: i for i, v in enumerate(fverts)}
bvh = BVHTree.FromPolygons([bm.verts[v].co.copy() for v in fverts], [[remap[v.index] for v in f.verts] for f in ff])
cx = float(np.median(CO[comp == face][:, 0]))
moved, mx = 0, 0.0
for v in bm.verts:
    if comp[v.index] != hair:
        continue
    x, y, z = v.co
    d = np.sqrt(((x - cx) / AX) ** 2 + ((-y - Z0) / AZ) ** 2)
    w = np.clip((1.0 - d) / FEATHER + 0.5, 0, 1) * np.clip((z + LIFT - YMIN) / 0.018, 0, 1)
    w = w * w * (3 - 2 * w)
    if w <= 0:
        continue
    loc, nor, _, dist = bvh.find_nearest(v.co)
    if loc is None:
        continue
    tgt = loc + nor.normalized() * GAP
    off = (tgt - v.co)
    if off.dot(nor) > 0:          # never push the cap outward
        continue
    v.co = v.co + off * w
    moved += 1; mx = max(mx, off.length * w)
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('CROWN_SHRINK moved', moved, 'max_mm', round(mx * 1000, 1))
