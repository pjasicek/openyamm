"""Exoskeleton rig of the mantis (quadruped playbook, "Spiders and other segmented creatures"): Smart Topology returned
56 rigid chitin pieces; every piece binds 100 % to one bone (work/joints.json from joints.py). Ball joints (hips,
knees, shoulders, elbows) ride on the distal bone and turn about their own centre. Writes work/rig_v1.blend (rig
Mantis_Rig, mesh Mantis) and review/rig_<view>.png with the bones drawn."""
import bpy, os, sys, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
m = bpy.data.objects['Mantis']
J = json.load(open(os.path.join(HERE, 'work', 'joints.json')))
lab = np.load(os.path.join(HERE, 'work', 'pieces.npz'))['label']
assert len(lab) == len(m.data.vertices)
arm = bpy.data.armatures.new('Mantis_Rig'); rig = bpy.data.objects.new('Mantis_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones
for name, b in J['bones'].items():
    e = eb.new(name); e.head = Vector(b['head']); e.tail = Vector(b['tail'])
    if (e.tail - e.head).length < 0.01:
        e.tail = e.head + Vector((0, 0, 0.03))
for name, b in J['bones'].items():
    if b['parent']:
        eb[name].parent = eb[b['parent']]
bpy.ops.object.mode_set(mode='OBJECT')
for g in list(m.vertex_groups): m.vertex_groups.remove(g)
for name, b in J['bones'].items():
    g = m.vertex_groups.new(name=name)
    g.add([int(x) for x in np.where(np.isin(lab, b['pieces']))[0]], 1.0, 'REPLACE')
unw = sum(1 for v in m.data.vertices if not v.groups)
print('RIG bones', len(J['bones']), 'unweighted', unw)
m.parent = rig
mod = m.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
for view, (loc, tgt) in {'front': ((0, -4, 0.55), (0, 0, 0.55)), 'side': ((-4, 0, 0.55), (0, 0, 0.55)),
                         'quarter': ((-2.6, -3.0, 1.6), (0, 0, 0.45))}.items():
    C.render(loc, tgt, 1.4, os.path.join(HERE, 'review', f'rig_{view}.png'), res=(700, 700), bones=True, floor=False)
