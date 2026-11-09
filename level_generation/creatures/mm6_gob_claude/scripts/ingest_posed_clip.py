"""Turn hand-blocked keys from a posing file (make_posing_file.py) into a finished clip on the runtime rig.

Two modes:
  export  (run on the posing .blend): writes <json> with the evaluated armature-space matrix of every deform bone
          on each keyed frame (IK/copy-rotation constraints resolved).
  apply   (run on work/final_v1.blend or rig_v2.blend): rebuilds each key on the constraint-free rig, re-solves the
          sword fist (finger wrap, thumb), limits wrist bend, keeps grip roll continuous, writes the action with
          Bezier in-betweens and saves. Bake forearm twist afterwards (twist_bones.py bake).
Args: export <json> <action>      |      apply <json> <action_out>
"""
import bpy, sys, os, json
from mathutils import Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

args = sys.argv[sys.argv.index('--') + 1:]
mode, path, action_name = args[0], args[1], args[2]
rig = bpy.data.objects['Peasant_Rig']
scene = bpy.context.scene

if mode == 'export':
    act = bpy.data.actions[action_name]
    rig.animation_data.action = act
    keys = json.loads(act.get('posing_keys', '[]')) or sorted(
        {int(kp.co.x) for layer in act.layers for strip in layer.strips for bag in strip.channelbags
         for fc in bag.fcurves for kp in fc.keyframe_points})
    out = {'keys': keys, 'frames': {}}
    for f in keys:
        scene.frame_set(f)
        out['frames'][str(f)] = {b.name: [list(r) for r in b.matrix] for b in rig.pose.bones
                                 if not b.name.startswith('CTRL_')}
        out['frames'][str(f)]['__sword_scale'] = list(rig.pose.bones['Sword'].scale)
    json.dump(out, open(path, 'w'))
    print('EXPORTED keys', keys)
    sys.exit(0)

import author_clips as A
import posing as P
data = json.load(open(path))
order = [b.name for b in rig.data.bones]                        # parents precede children
frames = []
A.PREV_WRIST.clear()
for f in data['keys']:
    pose = data['frames'][str(f)]
    rig.animation_data.action = None
    P.reset(rig)
    for name in order:
        if name in pose:
            rig.pose.bones[name].matrix = Matrix(pose[name])
            bpy.context.view_layer.update()
    rig.pose.bones['Sword'].scale = pose['__sword_scale']
    for side in ('Right', 'Left'):
        # keep the user's wrist/elbow/hand, but rebuild the arm with the anatomical hinge (Blender IK leaves an
        # arbitrary upper-arm roll, which wrings the shoulder skin)
        hand = rig.pose.bones[f'mixamorig:{side}Hand']
        hand_m = hand.matrix.copy()
        wrist = rig.matrix_world @ hand.head
        elbow = rig.matrix_world @ rig.pose.bones[f'mixamorig:{side}ForeArm'].head
        shoulder = rig.matrix_world @ rig.pose.bones[f'mixamorig:{side}Arm'].head
        line = (wrist - shoulder).normalized()
        off = (elbow - shoulder) - line * (elbow - shoulder).dot(line)
        P.two_bone_ik_hinge(rig, f'mixamorig:{side}Arm', f'mixamorig:{side}ForeArm', wrist,
                            elbow + off.normalized() * 0.3)
        hand.matrix = Matrix.LocRotScale(hand.head.copy(), hand_m.to_quaternion(), hand_m.to_scale())
        bpy.context.view_layer.update()
        A.limit_wrist(side)
    A.wrap_grip('Right'); A.wrap_thumb('Right')
    for side in ('Left', 'Right'):
        A.PREV_WRIST[side] = A.wrist_relative(side)
    frames.append((f, A.capture()))
A.PREV_WRIST.clear()
A.write_action(action_name, frames, loop=False)
rig.animation_data.action = bpy.data.actions['Standing']
bpy.ops.wm.save_mainfile()
print('APPLIED', action_name, 'keys', data['keys'])
