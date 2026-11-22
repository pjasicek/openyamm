"""Exoskeleton rig of the scorpion (quadruped playbook, "Spiders and other segmented creatures"): bones and weights
from scripts/joints.py (work/joints.json, work/weights.npz: rigid pieces, ~1 cm blends at the joints of the
continuous leg, pedipalp and tail tubes, the front claw finger on its own bone). Writes work/rig_v1.blend (rig
Scorpion_Rig, mesh Scorpion) and review/rig_<view>.png (bones drawn) and review/weights_<view>.png (dominant bone
colours)."""
import bpy, os, sys, json, random
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
m = bpy.data.objects['Scorpion']
J = json.load(open(os.path.join(HERE, 'work', 'joints.json')))
Wd = np.load(os.path.join(HERE, 'work', 'weights.npz'))
names = [str(x) for x in Wd['names']]; IDX = Wd['index']; WT = Wd['weight']
assert len(IDX) == len(m.data.vertices)
arm = bpy.data.armatures.new('Scorpion_Rig'); rig = bpy.data.objects.new('Scorpion_Rig', arm)
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
groups = {n: m.vertex_groups.new(name=n) for n in names}
for v in range(len(IDX)):
    for j in range(2):
        if WT[v, j] > 1e-4:
            groups[names[IDX[v, j]]].add([v], float(WT[v, j]), 'REPLACE')
unw = sum(1 for v in m.data.vertices if not v.groups)
print('RIG bones', len(J['bones']), 'unweighted', unw)
m.parent = rig
mod = m.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
VIEWS = {'front': ((0, -4, 0.42), (0, 0, 0.42)), 'side': ((-4, 0, 0.42), (0, 0, 0.42)),
         'quarter': ((-2.6, -3.0, 1.9), (0, 0, 0.3)), 'top': ((0, 0, 4), (0, 0, 0))}
for view, (loc, tgt) in VIEWS.items():
    C.render(loc, tgt, 1.8, os.path.join(HERE, 'review', f'rig_{view}.png'), res=(700, 700), bones=True, floor=False)
# dominant-bone colours
random.seed(5)
m.data.materials.clear()
for n in names:
    mat = bpy.data.materials.new('w_' + n); mat.diffuse_color = (random.random(), random.random(), random.random(), 1)
    m.data.materials.append(mat)
dom = IDX[:, 0]
for p in m.data.polygons:
    vs = list(p.vertices)
    p.material_index = int(np.bincount(dom[vs]).argmax())
for view, (loc, tgt) in VIEWS.items():
    C.render(loc, tgt, 1.8, os.path.join(HERE, 'review', f'weights_{view}.png'), res=(700, 700), floor=False,
             color='MATERIAL')
