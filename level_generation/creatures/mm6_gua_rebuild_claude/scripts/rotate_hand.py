"""Roll the grafted right hand about the forearm axis through the wrist (after the paint: UVs untouched, the paint turns with
the hand). The palm_vec chosen for the graft put the MPFB knuckle line 47 deg off MM9's pole, so finish_gua.py needed a 50 deg
ulnar wrist turn; rolled by PHI the angle is 8 deg (search in README). Finger bones are TRANSLATED to the rolled joints (MM9 rest
rotations kept, as graft_hands.py builds them); work/hands_v1.json joints for R rolled the same into <out json>.
Args: <in blend> <out blend> <hands json in> <hands json out> <phi deg>"""
import bpy, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
IN, OUT, JI, JO, PHI = sys.argv[sys.argv.index('--') + 1:]
PHI = math.radians(float(PHI))
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.update()
mw = rig.matrix_world
W = mw @ rig.data.bones['Bip01 R Hand'].head_local; E = mw @ rig.data.bones['Bip01 R Forearm'].head_local
d = ((mw @ rig.data.bones['Bip01 R Finger1'].head_local) - W).normalized()   # the hand axis the roll was searched about
R = Matrix.Rotation(PHI, 4, d); T = Matrix.Translation(W) @ R @ Matrix.Translation(-W)
side = np.zeros(len(me.vertices), int); me.attributes['graft_side'].data.foreach_get('value', side)
hs = np.zeros(len(me.polygons), int); me.attributes['hand'].data.foreach_get('value', hs)
hv = {v for p in me.polygons if hs[p.index] for v in p.vertices}
bw = body.matrix_world; bwi = bw.inverted()
n = 0
for i in hv:
    co = bw @ me.vertices[i].co
    if co.x < 0:
        me.vertices[i].co = bwi @ (T @ co); n += 1
J = json.load(open(JI))
for k, p in J['joints']['R'].items():
    J['joints']['R'][k] = list(T @ Vector(p))
json.dump(J, open(JO, 'w'), indent=1)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o is rig)
bpy.ops.object.mode_set(mode='EDIT')
mi = mw.inverted(); moved = 0
for eb in rig.data.edit_bones:
    if eb.name.startswith('Bip01 R ') and any(f in eb.name for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')):
        h = mw @ eb.head; dd = mi.to_3x3() @ ((T @ h) - h)
        eb.head += dd; eb.tail += dd; moved += 1
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('ROLL verts', n, 'bones', moved, 'deg', round(math.degrees(PHI), 1))
