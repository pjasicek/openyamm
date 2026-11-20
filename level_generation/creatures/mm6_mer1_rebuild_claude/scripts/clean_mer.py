"""MM6 merchant on the MM9 HIGHWAYMAN/FIGHTERBASE skeleton (Yrsa route), step 1: the Codex project's round-2 Smart Topology parts
(mm6_mer1_codex/work/round2/raw_parts.blend, P00..P19, from the gated round-2 HD masters) joined into 'Body', parts decimated to the
budget, scaled to MM9's shoulder height on MM9's floor, centred, MM9 rig imported (rest pose, no action).
Face attribute `part`: 1 torso + sleeves, 2 face/head skin (+ eyes, mouth), 3 cap, 4 hand, 5 legs, 6 boot foot, 7 tunic skirt,
10 pouch, 12 buckles/studs, 13 belt.  Args: <raw_parts blend> <mm9 true glb> <out blend> <report json>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
SRC, MM9, OUT, REP = a[:4]
rep = {}
LAB = {'P00': 2, 'P01': 5, 'P02': 1, 'P03': 7, 'P04': 4, 'P05': 4, 'P06': 3, 'P07': 10, 'P08': 13, 'P09': 2, 'P10': 2,
       'P11': 2, 'P12': 2, 'P13': 2, 'P14': 12, 'P15': 12, 'P16': 12, 'P17': 12, 'P18': 12, 'P19': 12}
# triangle targets (None = keep); hands are replaced by MPFB grafts later
TGT = {'P00': 2300, 'P01': 1500, 'P02': 2000, 'P06': 320, 'P07': 280, 'P09': 110, 'P10': 110}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=MM9)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE'); arm.name = 'MM9_Rig'
if arm.animation_data: arm.animation_data.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
J = {b.name: np.array(tuple(arm.matrix_world @ b.head_local)) for b in arm.data.bones}
for x in list(bpy.data.objects):
    if x.type == 'MESH': bpy.data.objects.remove(x)
with bpy.data.libraries.load(SRC) as (src_, dst_):
    dst_.objects = [n for n in src_.objects if n in LAB]
objs = []
for o in dst_.objects:
    sc.collection.objects.link(o)
    me = o.data
    for k in list(me.attributes.keys()):
        if k == 'sharp_face': me.attributes.remove(me.attributes[k])
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    n0 = len(me.polygons)
    if TGT.get(o.name):
        mod = o.modifiers.new('dec', 'DECIMATE'); mod.ratio = min(1.0, TGT[o.name] / n0); mod.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = o
        for x in bpy.data.objects: x.select_set(x is o)
        bpy.ops.object.modifier_apply(modifier='dec')
    me.attributes.new('part', 'INT', 'FACE').data.foreach_set('value', [LAB[o.name]] * len(me.polygons))
    rep[o.name] = [n0, len(me.polygons)]
    objs.append(o)
bpy.context.view_layer.objects.active = objs[0]
for x in bpy.data.objects: x.select_set(x in objs)
bpy.ops.object.join()
o = bpy.context.view_layer.objects.active
o.name = 'Body'; o.data.name = 'Body'
me = o.data
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
co = np.array([tuple(o.matrix_world @ v.co) for v in me.vertices])
o.matrix_world.identity()
vp = np.zeros(len(co), int)
for p in me.polygons:
    for v in p.vertices: vp[v] = fp[p.index]
floor9 = J['Bip01 L Toe0'][2]
tor = co[vp == 1]
sh = tor[np.abs(tor[:, 0]) > 0.15][:, 2].max()
s = (J['Bip01 L UpperArm'][2] + 0.04 - floor9) / (sh - co[:, 2].min())
t = np.array([-(co[:, 0].max() + co[:, 0].min()) / 2 * s, 0.0, floor9 - co[:, 2].min() * s])
leg = co[vp == 5]; ly = leg[leg[:, 2] > np.percentile(leg[:, 2], 90)][:, 1].mean()
t[1] = J['Bip01 Pelvis'][1] - ly * s
co = co * s + t
for v, c in zip(me.vertices, co): v.co = Vector(c)
# boot foot: leg vertices of faces lower than the ankle band
zfoot = floor9 + 0.12 * s / 1.0
fc = np.array([co[list(p.vertices)].mean(0) for p in me.polygons])
fp = np.where((fp == 5) & (fc[:, 2] < co[:, 2].min() + 0.13), 6, fp)
me.attributes['part'].data.foreach_set('value', fp.tolist())
rep.update(scale=s, shift=t.tolist(), shoulder_src=float(sh), tris=len(me.polygons))
rep['labels'] = {int(k): int((fp == k).sum()) for k in np.unique(fp)}
rep['bounds'] = [co.min(0).round(3).tolist(), co.max(0).round(3).tolist()]
rep['mm9_floor'] = float(floor9)
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bm.normal_update(); bm.to_mesh(me); bm.free()
if 'UVMap' not in me.uv_layers: me.uv_layers.new(name='UVMap')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('CLEAN', json.dumps(rep))
