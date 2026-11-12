"""MM6 thief on the MM9 HIGHWAYMAN skeleton (Yrsa route), step 1: the old project's cleaned Smart Topology (mm6_thf_claude/work/step1_v1.blend,
'Thief', 9,266 tris, face attribute `part` = index into Torso, Cloak, Skirt, Legs, Hand, Boot, Head, Sheath, Pouch, Strap, Bracer, Buckle) scaled to
MM9's proportions on MM9's floor, centred, labels renamed to this project's numbering, MM9 rig imported (rest pose, no action).
Labels: 1 torso (jerkin top, sleeves, neck, skull), 2 face, 4 hand, 5 legs, 6 boot, 7 jerkin skirt, 8 bracer, 9 strap, 10 pouch, 11 sheath, 12 buckle,
14 cloak (hood, mantle, long cloak: one shell).  Args: <step1 blend> <mm9 true glb> <out blend> <report json> [scale_ref]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
SRC, MM9, OUT, REP = a[:4]
rep = {}
OLD = ['Torso', 'Cloak', 'Skirt', 'Legs', 'Hand', 'Boot', 'Head', 'Sheath', 'Pouch', 'Strap', 'Bracer', 'Buckle']
NEW = {'Torso': 1, 'Cloak': 14, 'Skirt': 7, 'Legs': 5, 'Hand': 4, 'Boot': 6, 'Head': 2, 'Sheath': 11, 'Pouch': 10, 'Strap': 9, 'Bracer': 8, 'Buckle': 12}
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
    dst_.objects = ['Thief']
o = dst_.objects[0]; sc.collection.objects.link(o)
o.name = 'Body'; o.data.name = 'Body'
me = o.data
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
newp = np.array([NEW[OLD[k]] for k in fp])
co = np.array([tuple(v.co) for v in me.vertices])
# scale: shoulder (top of the torso shell's sleeves ~ UpperArm joint height) to sole, against MM9's UpperArm height above its floor
floor9 = J['Bip01 L Toe0'][2]
vp = np.zeros(len(co), int)
for p in me.polygons:
    for v in p.vertices: vp[v] = newp[p.index]
# our shoulder estimate: the highest torso-shell vertex at |x| > 0.15 (shoulder cap)
tor = co[(vp == 1)]
sh = tor[np.abs(tor[:, 0]) > 0.15][:, 2].max()
s = float(a[4]) if len(a) > 4 else (J['Bip01 L UpperArm'][2] + 0.04 - floor9) / (sh - co[:, 2].min())
t = np.array([-(co[:, 0].max() + co[:, 0].min()) / 2 * s, 0.0, floor9 - co[:, 2].min() * s])
# y: put the pelvis (mid legs at the crotch height) on MM9's pelvis y
leg = co[vp == 5]; ly = leg[leg[:, 2] > np.percentile(leg[:, 2], 90)][:, 1].mean()
t[1] = J['Bip01 Pelvis'][1] - ly * s
for v, c in zip(me.vertices, co):
    v.co = Vector(c * s + t)
rep.update(scale=s, shift=t.tolist(), shoulder_src=float(sh))
# hood / mantle / cloak split of the old cloak shell by height (refined later on the scaled body)
co = co * s + t
fc = np.array([co[list(p.vertices)].mean(0) for p in me.polygons])
HOOD_Z, MANTLE_Z = float(J['Bip01 Neck'][2] + 0.03), float(J['Bip01 Spine2'][2])
me.attributes.remove(me.attributes['part'])
me.attributes.new('part', 'INT', 'FACE').data.foreach_set('value', newp.tolist())
rep['labels'] = {int(k): int((newp == k).sum()) for k in np.unique(newp)}
rep['bounds'] = [co.min(0).round(3).tolist(), co.max(0).round(3).tolist()]
rep['mm9_floor'] = float(floor9)
if 'UVMap' not in me.uv_layers: me.uv_layers.new(name='UVMap')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('CLEAN', json.dumps(rep))
