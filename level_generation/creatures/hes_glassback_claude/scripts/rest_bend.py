"""Rest pose with bent knees and elbows (polish 2026-10-22): the Meshy legs stand nearly straight (hip to ankle 98 %
of reach), which made walk and run pull the feet 6-18 cm in under the body. The body is lowered DROP with every
foot kept on its rest foothold (two-bone IK, each leg's own rest bend as the pole), the pose is applied as the new
rest (mesh and armature), and everything is scaled back up about the floor origin so the back stands where it did
(1.192 m: scales 100 / 125 / 143.75 stay). Args: -- <in.blend> <out.blend> [drop m]"""
import bpy, os, sys
import numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import posing as P
a = sys.argv[sys.argv.index('--') + 1:]
src, dst = a[:2]; DROP = float(a[2]) if len(a) > 2 else 0.05
bpy.ops.wm.open_mainfile(filepath=C.path(src))
rig = bpy.data.objects[C.RIG]; mesh = bpy.data.objects[C.MESH]
rig.animation_data.action = None
P.reset(rig)
LEGS = ('FL', 'FR', 'ML', 'MR', 'HL', 'HR')
REST = {b.name: (rig.matrix_world @ b.matrix).copy() for b in rig.pose.bones}
ANK = {l: REST[f'Foot_{l}'].translation.copy() for l in LEGS}
HIP = {l: REST[f'Upper_{l}'].translation.copy() for l in LEGS}
KNEE = {l: REST[f'Lower_{l}'].translation.copy() for l in LEGS}


def height():
    dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg); me = ev.to_mesh()
    z = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', z); ev.to_mesh_clear()
    return z.reshape(-1, 3)[:, 2]


h0 = height().max()
root = rig.pose.bones['Spine1']
root.matrix = Matrix.Translation(Vector((0, 0, -DROP))) @ root.matrix
bpy.context.view_layer.update()
for l in LEGS:
    pole = KNEE[l] + (KNEE[l] - (HIP[l] + ANK[l]) / 2).normalized() * 0.8 + Vector((0, 0, 0.2))
    P.two_bone_ik(rig, f'Upper_{l}', f'Lower_{l}', ANK[l], pole)
    b = rig.pose.bones[f'Foot_{l}']
    b.matrix = Matrix.LocRotScale(b.head.copy(), REST[f'Foot_{l}'].to_quaternion(), Vector((1, 1, 1)))
    bpy.context.view_layer.update()
for l in LEGS:
    reach = rig.data.bones[f'Upper_{l}'].length + rig.data.bones[f'Lower_{l}'].length
    hip = rig.matrix_world @ rig.pose.bones[f'Upper_{l}'].head
    print('BEND', l, 'hip-ankle / reach', round((hip - ANK[l]).length / reach, 3))
# bake the pose into the mesh and make it the rest pose
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
mod = next(m for m in mesh.modifiers if m.type == 'ARMATURE')
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='POSE'); bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.armature_apply(selected=False)
bpy.ops.object.mode_set(mode='OBJECT')
m2 = mesh.modifiers.new('Armature', 'ARMATURE'); m2.object = rig
h1 = height().max()
S = h0 / h1
for v in mesh.data.vertices:
    v.co *= S
bpy.ops.object.mode_set(mode='EDIT')
for eb in rig.data.edit_bones:
    eb.head *= S; eb.tail *= S
bpy.ops.object.mode_set(mode='OBJECT')
print('REST_BEND drop', DROP, 'height', round(h0, 4), '->', round(h1, 4), 'scale back x', round(S, 4),
      'final', round(height().max(), 4), 'min z', round(height().min(), 4))
bpy.ops.wm.save_as_mainfile(filepath=C.path(dst))
