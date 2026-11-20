"""Walk/run head-height smoothness and foot roll (user review 2026-10-20): per action, the B_Head world height per
frame, its largest frame step and second difference (cm), and the floor-contact sole roll per foot (deg, sole = the
Foot/Toe0 vertices within 2.5 cm of the floor at rest; stance frames only: the foot carrying the frame's lowest point; roll about its heel -> toe line).
Args: -- <blend> action [...]"""
import bpy, sys, os, math
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
vg = [g.name for g in body.vertex_groups]
def P_():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = np.array([tuple(body.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear(); return P
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update(); R = P_(); S = {}
for sd in 'LR':
    m = np.array([sum(e.weight for e in v.groups if vg[e.group] in (f'B_{sd}_Foot', f'B_{sd}_Toe0')) > 0.5 for v in me.vertices])
    S[sd] = np.where(m & (R[:, 2] < 0.025))[0]
for an in a[1:]:
    act = bpy.data.actions[an]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); hz = []; rolls = {'L': [], 'R': []}
    for f in range(f0, f1 + 1):
        sc.frame_set(f); hz.append((rig.matrix_world @ rig.pose.bones['B_Head'].head).z); P = P_()
        low = min(P[S[s_], 2].min() for s_ in 'LR')
        for sd in 'LR':
            Q = P[S[sd]]
            if Q[:, 2].min() > low + 0.015:          # stance only: this foot carries the frame's lowest point
                continue
            n = np.linalg.svd(Q - Q.mean(0))[2][2]; n = n if n[2] > 0 else -n
            fwd = Q[np.argmin(Q[:, 1])] - Q[np.argmax(Q[:, 1])]; fwd[2] = 0; fwd /= np.linalg.norm(fwd)
            n_p = n - fwd * (n @ fwd); n_p /= np.linalg.norm(n_p)                 # roll about the heel -> toe line
            rolls[sd].append(math.degrees(math.atan2(np.cross(n_p, [0, 0, 1]) @ fwd, n_p[2])))
    hz = np.array(hz) * 100
    print(f'HEADBOB {an}: step {np.abs(np.diff(hz)).max():.2f} cm, second difference {np.abs(np.diff(hz, 2)).max():.2f} cm; '
          f'grounded sole roll L {min(rolls["L"], default=0):.1f}..{max(rolls["L"], default=0):.1f} R {min(rolls["R"], default=0):.1f}..{max(rolls["R"], default=0):.1f} deg')
