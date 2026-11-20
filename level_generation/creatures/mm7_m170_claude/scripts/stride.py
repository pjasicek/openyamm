import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
import armik
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1])); rig = bpy.data.objects['Rig']; sc = bpy.context.scene
sc.render.fps = 30
for name in (sys.argv[sys.argv.index('--') + 2:] or ['Walking', 'Running', 'Standing']):
    act = bpy.data.actions[name]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    S = 4; P = {s: [] for s in 'LR'}; top = []
    for k in range((f1 - f0) * S + 1):
        f = f0 + k / S; sc.frame_set(int(f), subframe=f - int(f))
        for s in 'LR': P[s].append(np.array(armik.W(rig, f'B_{s}_Foot').translation))
        top.append(max((rig.matrix_world @ rig.pose.bones['B_Head'].matrix).translation.z, 0))
    T = (f1 - f0) / 30
    vs = []
    for s in 'LR':
        A = np.array(P[s]); z = A[:, 2]; low = z < z.min() + 0.01
        vy = np.gradient(A[:, 1]) * 30 * S
        vs.append(np.median(vy[low]))
    v = float(np.mean(vs))
    print(f'STRIDE {name}: cycle {T:.3f} s, planted foot speed {v:.3f} m/s -> stride {v * T:.3f} m; head joint z max {max(top):.3f}')
