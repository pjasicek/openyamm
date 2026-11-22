"""Forearm as a hinge (the set's convention, retarget_mixamo.py HINGE): the IK steps (author_carry, arm_push) carried
the forearm's roll about its own axis with the upper arm, so the elbow skin met a forearm rolled 25-120 deg against it
(G4: elbow ring -62 deg in Cast 0, inner-elbow vertices pulled 20 cm). Per action and frame each forearm keeps only
its swing (local rotation minus the twist about local Y); the hand keeps its world rotation, so it takes the roll and
twist_bones.py spreads it along the forearm. Args: -- <in blend> <out blend>"""
import bpy, sys, os, math
from mathutils import Quaternion, Vector
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
for act in [a for a in bpy.data.actions if a.use_fake_user]:
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    keys = []; worst = 0.0
    for f in range(f0, f1 + 1):
        sc.frame_set(f); k = {}
        for s in 'LR':
            fa, hd = rig.pose.bones[f'B_{s}_Forearm'], rig.pose.bones[f'B_{s}_Hand']
            q = fa.rotation_quaternion.copy()
            t = 2 * math.atan2(q.y, q.w); t = (t + math.pi) % (2 * math.pi) - math.pi
            worst = max(worst, abs(math.degrees(t)))
            Hw = rig.matrix_world @ hd.matrix
            fa.rotation_quaternion = q @ Quaternion((0, 1, 0), -t)
            bpy.context.view_layer.update()
            hd.matrix = rig.matrix_world.inverted() @ Hw
            bpy.context.view_layer.update()
            k[fa.name] = fa.rotation_quaternion.copy(); k[hd.name] = hd.rotation_quaternion.copy()
        keys.append(k)
    for i, k in enumerate(keys):
        for n, q in k.items():
            pb = rig.pose.bones[n]
            if i and q.dot(keys[i - 1][n]) < 0:
                q = -q; k[n] = q
            pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f0 + i)
    print(f'HINGE {act.name}: forearm roll moved to the hand, max {worst:.0f} deg')
rig.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
