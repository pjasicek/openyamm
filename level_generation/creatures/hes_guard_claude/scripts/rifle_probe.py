"""hgd G1: how the source set holds its (invisible) rifle. Per clip and frame: the left wrist and the left hand's
rotation in the RIGHT hand's frame (constant while both hands are on one rigid gun), the right->left wrist direction
against the body's forward axis, and wrist heights. Writes work/rifle_probe.json. Args: -- <blend> <clip> [...]"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = {}
for c in a[1:]:
    act = bpy.data.actions[c]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    rows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        R = rig.matrix_world @ rig.pose.bones['B_R_Hand'].matrix
        L = rig.matrix_world @ rig.pose.bones['B_L_Hand'].matrix
        P = rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix
        rel = R.inverted() @ L
        fwd = (P.to_3x3() @ Vector((0, 0, 0))) if False else Vector((0, -1, 0))
        d = (L.translation - R.translation)
        rows.append({'f': f, 'l_in_r': list(rel.translation), 'l_rot_in_r': list(rel.to_quaternion()),
                     'dist': d.length, 'ang_fwd': math.degrees(d.normalized().angle(fwd)) if d.length > 1e-6 else 0,
                     'pitch': math.degrees(math.asin(max(-1, min(1, d.normalized().z)))),
                     'rz': R.translation.z, 'lz': L.translation.z, 'r': list(R.translation), 'l': list(L.translation)})
    lr = np.array([r['l_in_r'] for r in rows])
    q = np.array([r['l_rot_in_r'] for r in rows]); q *= np.sign(q @ q[0])[:, None]
    qm = q.mean(0); qm /= np.linalg.norm(qm)
    ang = np.degrees(2 * np.arccos(np.clip(np.abs(q @ qm), 0, 1)))
    out[c] = {'frames': len(rows), 'l_in_r_mean': lr.mean(0).tolist(), 'l_in_r_spread_cm': float(np.linalg.norm(lr - lr.mean(0), axis=1).max() * 100),
              'l_rot_spread_deg': float(ang.max()), 'dist_cm': [round(min(r['dist'] for r in rows) * 100, 1), round(max(r['dist'] for r in rows) * 100, 1)],
              'ang_fwd_deg': [round(min(r['ang_fwd'] for r in rows), 1), round(max(r['ang_fwd'] for r in rows), 1)],
              'pitch_deg': [round(min(r['pitch'] for r in rows), 1), round(max(r['pitch'] for r in rows), 1)],
              'rz': [round(min(r['rz'] for r in rows), 2), round(max(r['rz'] for r in rows), 2)], 'rows': rows}
    print('PROBE', c, json.dumps({k: (v if not isinstance(v, list) or len(v) < 4 else [round(x, 3) for x in v]) for k, v in out[c].items() if k != 'rows'}))
json.dump(out, open(os.path.join(HERE, 'work', 'rifle_probe.json'), 'w'))
