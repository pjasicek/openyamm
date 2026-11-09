"""Re-measure the attack blow on the final clip: the frame of peak right-hand speed (world), half frames.
Args: -- <blend> [hand side]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); s = a[1] if len(a) > 1 else 'R'
rig = bpy.data.objects['Rig']; act = bpy.data.actions['Attack']; rig.animation_data.action = act
if len(act.slots): rig.animation_data.action_slot = act.slots[0]
f0, f1 = act.frame_range; P = []; F = np.arange(f0, f1 + 1e-6, 0.5)
for f in F:
    bpy.context.scene.frame_set(int(f), subframe=float(f - int(f)))
    P.append(np.array(rig.matrix_world @ rig.pose.bones[f'B_{s}_Hand'].head))
v = np.linalg.norm(np.diff(np.array(P), axis=0), axis=1) / (0.5 / 30); k = int(np.argmax(v))
print('BLOW peak hand speed', round(float(v[k]), 2), 'm/s at', round(float((F[k] + F[k + 1]) / 2 / 30), 4), 's; clip', round(float((f1 - f0) / 30), 3), 's')
