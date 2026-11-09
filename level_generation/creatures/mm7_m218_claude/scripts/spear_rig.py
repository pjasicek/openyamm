"""Spear on the m218 rig (after author_carry.py SIDE=L; before author_spear.py):
- bone 'Spear' (child of B_Pelvis, deforming; keyed in world terms per frame by author_spear.py, so the spear can sit in
  the left fist for the native low carry and through the two-handed thrust, still anchored on the left fist). Rest frame = the left fist's
  solved handle (grip_pose_L.json): +Y toward the tip along the grip axis (out of the thumb side), origin at the carry
  grip, X = the hand's finger direction made perpendicular;
- mesh SpearMesh (make_spear.py, prop space = that frame) joined into Body, 100 % Spear, material Spear, piece 1000.
Writes work/spear_rig.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
G = json.load(open(os.path.join(common.WORK, 'grip_pose_L.json')))
AX = Vector(G['handle_axis_hand_local']).normalized(); GC = Vector(G['handle_centre_hand_local'])
hy = Vector((0, 1, 0)); sx = (hy - AX * hy.dot(AX)).normalized(); sz = sx.cross(AX)
S_hand = Matrix((sx, AX, sz)).transposed().to_4x4(); S_hand.translation = GC
S_rest = rig.data.bones['B_L_Hand'].matrix_local @ S_hand
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
b = eb.get('Spear') or eb.new('Spear')
b.head = S_rest.translation; b.tail = S_rest.translation + S_rest.col[1].xyz * 0.3; b.align_roll(S_rest.col[2].xyz)
b.parent = eb['B_Pelvis']; b.use_deform = True
bpy.ops.object.mode_set(mode='OBJECT')
with bpy.data.libraries.load(os.path.join(common.WORK, 'props.blend')) as (src_lib, dst):
    dst.objects = ['SpearMesh']
sp = dst.objects[0]; bpy.context.scene.collection.objects.link(sp)
sp.matrix_world = S_rest
n = len(sp.data.vertices)
sp.vertex_groups.clear(); sp.vertex_groups.new(name='Spear').add(list(range(n)), 1.0, 'REPLACE')
sp.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [1000] * n)     # props are 1000+: Smart Topology returns can exceed 100 shells
sp.data.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set(
    'vector', np.array([tuple(sp.matrix_world @ v.co) for v in sp.data.vertices]).ravel())
for at in ('garment', 'finger'):
    if at in body.data.attributes:
        sp.data.attributes.new(at, 'INT', 'POINT').data.foreach_set('value', [9 if at == 'garment' else 0] * n)
if 'Spear' not in body.vertex_groups:
    body.vertex_groups.new(name='Spear')
if not body.data.materials:
    body.data.materials.append(bpy.data.materials.get('Body') or bpy.data.materials.new('Body'))
for o in bpy.data.objects:
    o.select_set(o in (body, sp))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
json.dump({'spear_hand_L': [list(r) for r in S_hand]}, open(os.path.join(common.WORK, 'spear_rig.json'), 'w'), indent=1)
print('SPEARRIG bone Spear (child of B_Pelvis), mesh verts', n, 'body materials', [m.name for m in body.data.materials])
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
