"""Move the dragonfly bones of a blend to work/rig_plan.json and replace its weights with work/weights.npz, keeping
UVs (clips are re-keyed afterwards by anim_dfly.py). Args: blend (relative to the project, saved in place)."""
import bpy, os, sys, json
import numpy as np
from mathutils import Vector
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
blend = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, blend))
mesh = bpy.data.objects['Dragonfly']; rig = bpy.data.objects['Dragonfly_Rig']
raw = np.load(os.path.join(P, 'work/raw_st1.npz'))['co']
co = np.array([tuple(v.co) for v in mesh.data.vertices]); shift = Vector((0, 0, float(co[:, 2].min() - raw[:, 2].min())))
plan = json.load(open(os.path.join(P, 'work/rig_plan.json')))
rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for b in eb: b.use_connect = False
for name, parent, h, t in plan['bones']:
    b = eb[name]; b.head = Vector(h) + shift; b.tail = Vector(t) + shift
    b.align_roll(Vector((0, 0, 1)) if abs((b.tail - b.head).normalized().z) < 0.9 else Vector((0, -1, 0)))
s = eb['HeadSocket']; hd = eb['Head']; s.head = hd.tail; s.tail = hd.tail + (hd.tail - hd.head).normalized() * 0.02
bpy.ops.object.mode_set(mode='OBJECT')
d = np.load(os.path.join(P, 'work/weights.npz')); W, names = d['W'], [str(n) for n in d['names']]
for g in list(mesh.vertex_groups): mesh.vertex_groups.remove(g)
for j, n in enumerate(names):
    g = mesh.vertex_groups.new(name=n)
    for v in np.nonzero(W[:, j] > 1e-5)[0]: g.add([int(v)], float(W[v, j]), 'REPLACE')
bpy.ops.wm.save_mainfile()
print('RERIGGED', blend, tuple(round(x, 4) for x in shift))
