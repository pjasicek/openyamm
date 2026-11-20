"""Dump a Mixamo FBX clip for retarget_idle.py: per bone the world rotation (quaternion) and head position at rest and
on every frame, in Blender's world frame, plus the parent map and frame rate. Args: -- <fbx> <out npz>"""
import bpy, sys, os
import numpy as np
fbx, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); act = arm.animation_data.action
sc = bpy.context.scene; f0, f1 = (int(round(x)) for x in act.frame_range); fps = sc.render.fps / sc.render.fps_base
names = [b.name for b in arm.data.bones]
W = arm.matrix_world
rest_q = np.array([tuple((W @ b.matrix_local).to_quaternion()) for b in arm.data.bones])   # (w, x, y, z)
rest_p = np.array([tuple(W @ b.head_local) for b in arm.data.bones])
pose_q, pose_p = [], []
for f in range(f0, f1 + 1):
    sc.frame_set(f)
    pose_q.append([tuple((W @ arm.pose.bones[n].matrix).to_quaternion()) for n in names])
    pose_p.append([tuple(W @ arm.pose.bones[n].head) for n in names])
parents = [b.parent.name if b.parent else '' for b in arm.data.bones]
np.savez(out, names=np.array(names), parents=np.array(parents), rest_q=rest_q, rest_p=rest_p,
         pose_q=np.array(pose_q), pose_p=np.array(pose_p), fps=fps)
print('DUMP', len(names), 'bones', f1 - f0 + 1, 'frames at', fps, 'fps')
