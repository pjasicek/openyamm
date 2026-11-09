"""Per-viewer-frame series of a bone (world Z and speed) in one clip. Usage: blender -b -P series.py -- <glb> <clip> <bone,...>"""
import bpy, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
glb, clip, bones = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); act = bpy.data.actions[clip]
rig.animation_data.action = act; f0, f1 = act.frame_range; fps = sc.render.fps / sc.render.fps_base
n = int(round((f1 - f0) / fps * 48)) + 1
for b in bones.split(','):
    P = []
    for i in range(n):
        fr = f0 + i / 48 * fps; sc.frame_set(int(fr), subframe=fr - int(fr)); P.append(list(rig.matrix_world @ rig.pose.bones[b].head))
    P = np.array(P); sp = np.r_[0, np.linalg.norm(np.diff(P, axis=0), axis=1) * 48]
    print('SERIES', clip, b, 'z_cm', ' '.join(f'{i}:{z*100:.1f}' for i, z in enumerate(P[:, 2])))
    print('SPEED', clip, b, 'm/s', ' '.join(f'{i}:{s:.2f}' for i, s in enumerate(sp)))
