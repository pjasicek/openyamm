import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v2.blend'))
arm = bpy.data.objects['Thief_Rig']; act = bpy.data.actions['Attack']; arm.animation_data.action = act; arm.animation_data.action_slot = act.slots[0]
I = json.load(open(os.path.join(common.WORK, 'attack_intent.json')))
seat = json.loads(bpy.context.scene['thf_daggers'])
for key in I['keys']:
    f = key['frame']; bpy.context.scene.frame_set(f)
    out = []
    for k, side in (('R', 'Right'), ('L', 'Left')):
        if key[k] is None: continue
        pb = arm.pose.bones['Dagger' + k]
        bone_dir = (arm.matrix_world @ pb.tail - arm.matrix_world @ pb.head).normalized()
        Rh = (arm.matrix_world @ arm.pose.bones[side + 'Hand'].matrix).to_3x3().normalized()
        Rh0 = (arm.matrix_world @ arm.data.bones[side + 'Hand'].matrix_local).to_3x3().normalized()
        local = Rh0.inverted() @ Vector(seat[k]['axis'])
        via_hand = Rh @ local
        wb = Vector(key[k]['blade']).normalized()
        wr = arm.matrix_world @ arm.pose.bones[side + 'Hand'].head
        out.append(f"{k}: bone {math.degrees(bone_dir.angle(wb)):5.1f} viahand {math.degrees(via_hand.angle(wb)):5.1f} wrist off {(wr - Vector(key[k]['wrist'])).length*100:4.1f}cm")
    print('DBG frame', f, ' | '.join(out))
bpy.context.scene.frame_set(5)
for side in ('Right', 'Left'):
    pbs = arm.pose.bones; db = arm.data.bones
    S, E_, W_ = (arm.matrix_world @ pbs[side + n].head for n in ('Arm', 'ForeArm', 'Hand'))
    s0, e0, w0 = (db[side + n].head_local for n in ('Arm', 'ForeArm', 'Hand'))
    print('LEN', side, 'pose l1 %.4f l2 %.4f' % ((E_ - S).length, (W_ - E_).length), 'rest l1 %.4f l2 %.4f' % ((e0 - s0).length, (w0 - e0).length),
          'connect', db[side + 'ForeArm'].use_connect, db[side + 'Hand'].use_connect, 'parent', db[side + 'Hand'].parent.name)
