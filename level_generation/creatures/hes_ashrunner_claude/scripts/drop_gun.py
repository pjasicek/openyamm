"""The dying Ashrunner lets his gun fall (the rifle held in the fist through a face-down fall pierced the floor by
49 cm). In the Death clip the gun bones (children of B_R_Hand) are keyed from RELEASE (a fraction of the clip) on: the
gun's world pose at the release falls with gravity over FALL seconds onto the floor beside the right hand, turned to
lie on its side (barrel level, its up axis horizontal, heading kept), the lowest point of that gun's own mesh on
FLOOR + 5 mm; before the release the bone keeps its rest (in the fist). Each listed bone gets its own floor height
(rifle, carbine and pistol have different shapes). Keys location/rotation of the bone in the hand's space per frame.
Args: -- <in blend> <out blend> <Death action> <bone=object> [...]"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]
src, out, act_name, items = a[0], a[1], a[2], a[3:]
RELEASE, FALL, FLOOR = float(os.environ.get('RELEASE', '0.30')), float(os.environ.get('FALL', '0.40')), 0.0
SIDE = float(os.environ.get('SIDE', '0.12'))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene; AW = rig.matrix_world; fps = sc.render.fps / sc.render.fps_base
act = bpy.data.actions[act_name]; rig.animation_data.action = act
if len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
f0, f1 = (int(x) for x in act.frame_range); n = f1 - f0 + 1
fr = f0 + int(round(RELEASE * (n - 1))); nf = max(2, int(round(FALL * fps)))
for it in items:
    bone, obn = it.split('=')
    pb = rig.pose.bones[bone]; ob = bpy.data.objects[obn]
    pb.rotation_mode = 'QUATERNION'
    rest = rig.data.bones[bone].matrix_local; hand_rest = rig.data.bones[bone].parent.matrix_local
    # the gun's mesh in its bone's rest space (the object is in armature rest space, rigid on the bone)
    V = [rest.inverted() @ v.co for v in ob.data.vertices]
    sc.frame_set(fr); G0 = AW @ pb.matrix                              # world pose at the release (rest keys there)
    y = (G0.to_3x3() @ Vector((0, 1, 0))); y.z = 0; y.normalize()
    z = Vector((0, 0, 1)).cross(y).normalized()                         # its up axis made horizontal: lying on its side
    x = y.cross(z)
    R1 = Matrix((x, y, z)).transposed()
    low = min((R1 @ v).z for v in V)
    rh = (AW @ rig.pose.bones['B_R_Hand'].matrix).to_3x3() @ Vector((1, 0, 0))
    p1 = G0.translation.copy(); p1.z = FLOOR + 0.005 - low
    sc.frame_set(f1); side = (AW @ rig.pose.bones['B_Pelvis'].matrix).to_3x3() @ Vector((-1, 0, 0)); side.z = 0; side.normalize()
    p1 += side * SIDE
    q0, q1 = G0.to_quaternion(), R1.to_quaternion()
    if q0.dot(q1) < 0:
        q1 = -q1
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        if f < fr:
            pb.location = (0, 0, 0); pb.rotation_quaternion = Quaternion()
        else:
            t = min(1.0, (f - fr) / nf); tz = t * t                     # gravity: the height falls as t^2
            pos = G0.translation.lerp(p1, t); pos.z = G0.translation.z + (p1.z - G0.translation.z) * tz
            Mw = Matrix.Translation(pos) @ q0.slerp(q1, min(1.0, t * 1.2)).to_matrix().to_4x4()
            # pose-bone basis from the wanted world matrix (the parent is animated)
            pb.matrix = AW.inverted() @ Mw
            bpy.context.view_layer.update()
        pb.keyframe_insert('location', frame=f); pb.keyframe_insert('rotation_quaternion', frame=f)
    print('DROP', bone, 'release frame', fr, 'fall frames', nf, 'lies at', [round(v, 3) for v in p1])
# every other clip keys the gun bones at rest (in the fist): without channels Blender keeps the last evaluated pose
# (the lying gun) in every clip, and the export would carry no channel for them
dropped = [it.split('=')[0] for it in items]
GUNS = [b for b in ('Rifle', 'Carbine', 'Pistol') if b in rig.pose.bones]
for other in bpy.data.actions:
    if other.name.startswith('_'):
        continue
    bones = [b for b in GUNS if b not in dropped] if other == act else GUNS
    rig.animation_data.action = other
    if len(other.slots):
        rig.animation_data.action_slot = other.slots[0]
    g0, g1 = (int(x) for x in other.frame_range)
    for bone in bones:
        pb = rig.pose.bones[bone]; pb.rotation_mode = 'QUATERNION'
        for f in (g0, g1):
            pb.location = (0, 0, 0); pb.rotation_quaternion = Quaternion()
            pb.keyframe_insert('location', frame=f); pb.keyframe_insert('rotation_quaternion', frame=f)
rig.animation_data.action = act
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
