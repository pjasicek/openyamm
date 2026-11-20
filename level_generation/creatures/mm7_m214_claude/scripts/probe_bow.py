"""Bow probe: per frame of the listed actions, the bow frame carried by the left fist (grip_pose_L.json handle in
hand space; bow X = hand Y made perpendicular to the handle, i.e. the string lies toward the forearm), the bow axis
tilt from vertical, the left wrist, the right-hand pinch point (thumb/index tips) and its position in the bow frame
(x: toward the string is negative, string at -0.155 m). Args: -- <blend> <action> [...]"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene
G = json.load(open(os.path.join(common.WORK, 'grip_pose_L.json')))
FJ = json.load(open(os.path.join(common.WORK, 'finger_joints.json')))['R']
AX = Vector(G['handle_axis_hand_local']).normalized(); GC = Vector(G['handle_centre_hand_local'])


def bow_frame(H):
    R = H.to_3x3().normalized(); y = (R @ AX).normalized(); hy = R @ Vector((0, 1, 0))
    x = (hy - y * hy.dot(y)).normalized(); z = x.cross(y)
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = H @ GC
    return M


def tip(n):
    pb = rig.pose.bones[n]
    return rig.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted() @ Vector(FJ[n + '_tip'])


out = {}
for name in a[1:]:
    act = bpy.data.actions[name]; rig.animation_data_create(); rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    rows = []
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
        scene.frame_set(f)
        H = rig.matrix_world @ rig.pose.bones['B_L_Hand'].matrix
        Bf = bow_frame(H)
        pinch = (tip('B_R_Finger0.002') + tip('B_R_Finger12')) / 2
        loc = Bf.inverted() @ pinch
        y = Bf.col[1].xyz
        tilt = math.degrees(math.acos(max(-1, min(1, y.z))))
        rows.append({'f': f, 'tilt': round(tilt, 1), 'axis': [round(v, 2) for v in y], 'xdir': [round(v, 2) for v in Bf.col[0].xyz],
                     'grip': [round(v, 3) for v in Bf.translation], 'pinch': [round(v, 3) for v in pinch],
                     'pinch_bow': [round(v, 3) for v in loc]})
    out[name] = rows
    for r in rows[::2]:
        print('BOWPROBE', name, json.dumps(r))
json.dump(out, open(os.path.join(common.WORK, 'bow_probe.json'), 'w'), indent=1)
