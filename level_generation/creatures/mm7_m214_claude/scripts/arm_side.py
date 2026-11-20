"""Side clearance of a carrying arm: per action and frame, the wrist's lateral distance outside the body surface at its
height (pelvis frame: the body's lateral extent among the torso/thigh vertices within 6 cm of the wrist height and
not on that arm), and the wrist's position in the pelvis frame (x out, y forward, z up). Prints min / median / max.
Args: -- <blend> <side L|R> <action> [...]"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); S = a[1]; acts = a[2:]
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
names = [g.name for g in body.vertex_groups]
LEG = ('Thigh', 'Calf', 'Foot', 'Toe')
arm = np.array([sum(e.weight for e in v.groups if f'_{S}_' in names[e.group] and
                    not any(k in names[e.group] for k in LEG)) > 0.3 for v in me.vertices])
OUT = 1.0 if S == 'L' else -1.0                                    # +X = character left
for an in acts:
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1]); rows = []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); ev.to_mesh_clear()
        co = co.reshape(-1, 3)
        Pm = rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix
        R = np.array(Pm.to_3x3().normalized()); t = np.array(Pm.translation)
        loc = (co - t) @ R                                           # pelvis frame (bone axes)
        w = np.array((rig.matrix_world @ rig.pose.bones[f'B_{S}_Hand'].head) - Pm.translation) @ R
        # pelvis bone axes: find the lateral axis as the one closest to world X at rest
        rows.append((f, w, loc))
    # bone-axis mapping from the first frame's rest-like orientation
    Pm = rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix
    R0 = np.array(Pm.to_3x3().normalized())
    ix = int(np.argmax(np.abs(R0[0]))); iy = int(np.argmax(np.abs(R0[1]))); iz = int(np.argmax(np.abs(R0[2])))
    sx, sy, sz = np.sign(R0[0, ix]), np.sign(R0[1, iy]), np.sign(R0[2, iz])
    res = []
    for f, w, loc in rows:
        X = loc[:, ix] * sx * OUT; Y = -loc[:, iy] * sy; Z = loc[:, iz] * sz
        wx, wy, wz = w[ix] * sx * OUT, -w[iy] * sy, w[iz] * sz
        band = (~arm) & (np.abs(Z - wz) < 0.06) & (np.abs(Y - wy) < 0.15)
        surf = X[band].max() if band.any() else float('nan')
        res.append((f, wx - surf, wx, wy, wz))
    r = np.array(res)
    print(f'ARMSIDE {an} {S}: clearance outside body min {np.nanmin(r[:, 1]) * 100:+.1f} median '
          f'{np.nanmedian(r[:, 1]) * 100:+.1f} max {np.nanmax(r[:, 1]) * 100:+.1f} cm; wrist out '
          f'{r[:, 2].min() * 100:.0f}..{r[:, 2].max() * 100:.0f} fwd {r[:, 3].min() * 100:.0f}..{r[:, 3].max() * 100:.0f} '
          f'up {r[:, 4].min() * 100:.0f}..{r[:, 4].max() * 100:.0f} cm (pelvis frame)')
