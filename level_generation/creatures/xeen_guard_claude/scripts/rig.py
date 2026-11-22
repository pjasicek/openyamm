"""Rig the segmented guard (work/seg_v1.blend): armature Guard_Rig with the stand-in mm8_m592's B_* bone names (the
clip source, D-19) on our joints (scripts/joints.json), all bones unconnected (retarget.py sets world matrices), and
rigid weights: every vertex 100 % on the bone of its plate (face attribute `bone`). Socket_Gem (child of B_Head) sits
1.5 cm in front of the gem. Saves work/rig_v1.blend and renders an X-ray (review/rig_*.png)."""
import bpy, os, sys, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = json.load(open(os.path.join(HERE, 'scripts', 'joints.json')))
info = json.load(open(os.path.join(HERE, 'work', 'seg_info.json')))
BONES = info['bones']
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'seg_v1.blend'))
ob = bpy.data.objects['Guard']
me = ob.data
me.materials.clear()


def jp(name, side='L'):
    p = Vector(J[name])
    if side == 'R':
        p.x = -p.x
    return p


part = np.array([me.attributes['part'].data[i].value for i in range(len(me.polygons))])
gem = [me.vertices[i].co for p in me.polygons if part[p.index] == 1 for i in p.vertices]
gc = sum(gem, Vector()) / len(gem)
front = min(gem, key=lambda v: v.y)
sock = Vector((0, front.y - 0.015, gc.z))
print('GEM centre', [round(x, 3) for x in gc], 'socket', [round(x, 3) for x in sock])

arm = bpy.data.armatures.new('Guard_Rig')
rig = bpy.data.objects.new('Guard_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones


def bone(name, head, tail, parent=None, roll_up=None):
    b = eb.new(name)
    b.head = head; b.tail = tail
    if parent:
        b.parent = eb[parent]
    b.use_connect = False
    if roll_up is not None:
        b.align_roll(roll_up)
    return b


fwd = Vector((0, -1, 0))
bone('B_Pelvis', jp('pelvis'), jp('spine'), roll_up=fwd)
bone('B_Spine', jp('spine'), jp('spine1'), 'B_Pelvis', fwd)
bone('B_Spine1', jp('spine1'), jp('spine2'), 'B_Spine', fwd)
bone('B_Spine2', jp('spine2'), jp('neck'), 'B_Spine1', fwd)
bone('B_Neck', jp('neck'), jp('head'), 'B_Spine2', fwd)
bone('B_Head', jp('head'), jp('head_top'), 'B_Neck', fwd)
bone('Socket_Gem', sock, sock + Vector((0, -0.05, 0)), 'B_Head', Vector((0, 0, 1)))
for s in ('L', 'R'):
    bone(f'B_{s}_Clavicle', jp('clavicle', s), jp('shoulder', s), 'B_Spine2', fwd)
    bone(f'B_{s}_UpperArm', jp('shoulder', s), jp('elbow', s), f'B_{s}_Clavicle', fwd)
    bone(f'B_{s}_Forearm', jp('elbow', s), jp('wrist', s), f'B_{s}_UpperArm', fwd)
    bone(f'B_{s}_Hand', jp('wrist', s), jp('hand_end', s), f'B_{s}_Forearm', fwd)
    bone(f'B_{s}_Thigh', jp('hip', s), jp('knee', s), 'B_Pelvis', fwd)
    bone(f'B_{s}_Calf', jp('knee', s), jp('ankle', s), f'B_{s}_Thigh', fwd)
    bone(f'B_{s}_Foot', jp('ankle', s), jp('toe', s), f'B_{s}_Calf', Vector((0, 0, 1)))
bpy.ops.object.mode_set(mode='OBJECT')
for b in arm.bones:
    b.use_deform = not b.name.startswith('Socket')
# rigid weights
ob.vertex_groups.clear()
vg = {b: ob.vertex_groups.new(name=b) for b in BONES}
bonev = [me.attributes['bone'].data[i].value for i in range(len(me.polygons))]
vb = {}
for p in me.polygons:
    for i in p.vertices:
        vb.setdefault(i, set()).add(bonev[p.index])
shared = sum(1 for s in vb.values() if len(s) > 1)
print('VERTS', len(me.vertices), 'on two bones', shared, 'unweighted', len(me.vertices) - len(vb))
for i, s in vb.items():
    vg[BONES[min(s)]].add([i], 1.0, 'REPLACE')
ob.parent = rig
mod = ob.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
C.MESH = 'Guard'
C.RIG = 'Guard_Rig'
for name, (loc, tgt) in {'front': ((0, -5, 0.95), (0, 0, 0.95)), 'left': ((5, 0, 0.95), (0, 0, 0.95))}.items():
    C.render(loc, tgt, 2.1, os.path.join(HERE, 'review', f'rig_{name}.png'), res=(600, 600), floor=False, bones=True)
