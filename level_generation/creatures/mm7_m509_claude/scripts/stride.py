"""Natural stride of the in-place locomotion clips: while a foot is planted (lowest 1 cm of its path) it slides
backward at the body's travel speed; stride_length = that speed x cycle length (m per cycle), plus the posed height
(top of the head and of the mesh) for the binding scale. Args: -- <blend> [action ...]"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
sc = bpy.context.scene; sc.render.fps = 30
for name in a[1:] or ['Walking', 'Running']:
    act = bpy.data.actions[name]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    S = 4; P = {s: [] for s in 'LR'}
    for k in range((f1 - f0) * S + 1):
        f = f0 + k / S; sc.frame_set(int(f), subframe=f - int(f))
        for s in 'LR':
            P[s].append(np.array(rig.matrix_world @ rig.pose.bones['FrontPaw_' + s].head))
    T = (f1 - f0) / 30; vs = []
    for s in 'LR':
        A = np.array(P[s]); low = A[:, 2] < A[:, 2].min() + 0.01
        vs.append(float(np.median((np.gradient(A[:, 1]) * 30 * S)[low])) if low.any() else 0.0)
    v = float(np.mean(vs))
    print(f'STRIDE {name}: cycle {T:.3f} s, planted foot speed {v:+.3f} m/s (L {vs[0]:+.3f} R {vs[1]:+.3f}), stride {abs(v) * T:.3f} m')
st = bpy.data.actions['Standing']; rig.animation_data.action = st; rig.animation_data.action_slot = st.slots[0]; sc.frame_set(0)
dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); m = ev.to_mesh()
z = np.array([v.co.z for v in m.vertices]); ev.to_mesh_clear()
print(f'STRIDE Standing frame 0 mesh height {z.max() - z.min():.3f} m')
