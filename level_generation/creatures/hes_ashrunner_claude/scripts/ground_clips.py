"""Pin both feet to the floor in planted clips (user review 2026-10-20). plant.py holds the legs' LOCAL rotations from
Standing, so the pelvis tilt it keeps swung the legs: in the Attack the feet slid 5 cm back and both ankles rose
2-3 cm while the pelvis rose up to 4 cm (he floated from 0.30 s; the set's pistol attack rises onto the balls of the
feet), and the set's get-hit hopped 5 cm. Per frame: the pelvis may sink but not rise above its frame-0 height (its
rotation and sideways motion are kept), then each leg is solved with two-bone IK (thigh, calf; the knee keeps its
current side as the pole) so the ankle returns to its frame-0 world position, and the foot takes its frame-0 world
rotation (the toes follow). Runs after aim_forward.py, before the twist bones and the cape simulation.
Args: -- <in blend> <out blend> <Action> [...]"""
import bpy, sys, os, math
from mathutils import Matrix, Vector
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene; rig = bpy.data.objects['Rig']; AW = rig.matrix_world; AI = AW.inverted()
SIDES = 'LR'


def W(n):
    return AW @ rig.pose.bones[n].matrix


def set_world(n, M):
    rig.pose.bones[n].matrix = AI @ M
    bpy.context.view_layer.update()


def aim(n, target):
    """turn bone n about its head so its tail points at target (world)"""
    M = W(n); h = M.translation.copy(); t = AW @ rig.pose.bones[n].tail
    q = (t - h).normalized().rotation_difference((target - h).normalized())
    set_world(n, Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ M)


def leg_ik(s, ankle):
    th, ca = f'B_{s}_Thigh', f'B_{s}_Calf'
    hip = W(th).translation.copy(); knee = W(ca).translation.copy()
    la = (knee - hip).length; lb = ((AW @ rig.pose.bones[ca].tail) - knee).length
    d = ankle - hip; dist = min(d.length, (la + lb) * 0.9995); dn = d.normalized()
    cos_a = (la * la + dist * dist - lb * lb) / (2 * la * dist)
    ang = math.acos(max(-1.0, min(1.0, cos_a)))
    pole = knee - hip; pole = (pole - dn * pole.dot(dn))
    if pole.length < 1e-6:
        pole = Vector((0, -1, 0)) - dn * dn.y
    pole.normalize()
    aim(th, hip + (dn * math.cos(ang) + pole * math.sin(ang)) * la)
    aim(ca, hip + dn * dist)


for name in acts:
    act = bpy.data.actions[name]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(round(x)) for x in act.frame_range)
    scene.frame_set(f0)
    z0 = W('B_Pelvis').translation.z
    FOOT = {s: W(f'B_{s}_Foot').copy() for s in SIDES}
    rise = slide = 0.0
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        P = W('B_Pelvis'); rise = max(rise, P.translation.z - z0)
        for s in SIDES:
            slide = max(slide, (W(f'B_{s}_Foot').translation - FOOT[s].translation).length)
        if P.translation.z > z0:
            set_world('B_Pelvis', Matrix.Translation(Vector((0, 0, z0 - P.translation.z))) @ P)
        for s in SIDES:
            leg_ik(s, FOOT[s].translation)
            M = FOOT[s].copy(); M.translation = W(f'B_{s}_Foot').translation; set_world(f'B_{s}_Foot', M)
        for n in ['B_Pelvis'] + [f'B_{s}_{p}' for s in SIDES for p in ('Thigh', 'Calf', 'Foot')]:
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
    err = 0.0
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        err = max([err] + [(W(f'B_{s}_Foot').translation - FOOT[s].translation).length for s in SIDES])
    print('GROUND', name, 'pelvis rise cm', round(100 * rise, 1), '-> 0; feet moved cm', round(100 * slide, 1),
          '-> pinned within', round(100 * err, 2))
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
