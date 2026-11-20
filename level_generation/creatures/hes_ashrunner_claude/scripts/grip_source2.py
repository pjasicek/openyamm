"""hgd: both hands' grip axes in the RPG set (finger-curl circle centres, as grip_from_source.py) for a two-handed
rifle, in each hand's bone frame (identical to ours in every pose: the retarget copies world rotations), plus the
left grip centre/axis in the RIGHT hand's frame (scaled to our size by SCALE). Writes work/grip_source2.json.
Args: -- <set glb> <clip> <frame> <scale>"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
glb, clip, frame, SCALE = a[0], a[1], int(a[2]), float(a[3])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
acts = {x.name.split('@')[-1].split('|')[-1]: x for x in bpy.data.actions}
act = acts.get(clip) or next(x for k, x in acts.items() if k.endswith(clip))
arm.animation_data.action = act
if len(act.slots): arm.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(frame)
W = arm.matrix_world


def circle(pts):
    c = pts.mean(0); u, s, vt = np.linalg.svd(pts - c); e1, e2 = vt[0], vt[1]
    xy = np.stack([(pts - c) @ e1, (pts - c) @ e2], 1)
    A = np.column_stack([2 * xy, np.ones(len(xy))]); b = (xy ** 2).sum(1)
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy = sol[:2]; r = math.sqrt(sol[2] + cx * cx + cy * cy)
    return c + cx * e1 + cy * e2, r


out = {}
for s in ('R', 'L'):
    cs, rs = [], []
    for i in (1, 2, 3, 4):
        pts = np.array([np.array(W @ arm.pose.bones[n].head) for n in (f'B_{s}_Finger{i}', f'B_{s}_Finger{i}1', f'B_{s}_Finger{i}2')])
        c, r = circle(pts); cs.append(c); rs.append(r)
    cs = np.array(cs); m = cs.mean(0); ax = np.linalg.svd(cs - m)[2][0]
    if np.dot(np.array(W @ arm.pose.bones[f'B_{s}_Finger1'].head) - np.array(W @ arm.pose.bones[f'B_{s}_Finger4'].head), ax) < 0:
        ax = -ax                                               # out of the index/thumb side
    H = W @ arm.pose.bones[f'B_{s}_Hand'].matrix
    out[s] = {'centre_world': m.tolist(), 'axis_world': ax.tolist(), 'radius': float(np.median(rs)),
              'centre_hand': list(H.inverted() @ Vector(m)), 'axis_hand': list((H.inverted().to_3x3() @ Vector(ax)).normalized()),
              'hand_world': [list(r) for r in H]}
HR = Matrix(out['R']['hand_world']); inv = HR.inverted()
cL = inv @ Vector(out['L']['centre_world']); aL = (inv.to_3x3() @ Vector(out['L']['axis_world'])).normalized()
cR = Vector(out['R']['centre_hand'])
out['L_in_R'] = {'centre': list(cL), 'axis': list(aL), 'dist_scaled': (cL - cR).length * SCALE,
                 'angle_axes_deg': math.degrees(Vector(out['R']['axis_hand']).angle(aL))}
json.dump(out, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'grip_source2.json'), 'w'), indent=1)
for s in ('R', 'L'):
    print('SRCGRIP', s, 'axis_hand', [round(x, 3) for x in out[s]['axis_hand']], 'centre_hand', [round(x * SCALE, 3) for x in out[s]['centre_hand']],
          'radius_scaled', round(out[s]['radius'] * SCALE, 3), 'axis_world', [round(x, 2) for x in out[s]['axis_world']])
print('SRCGRIP L in R', {k: (round(v, 3) if isinstance(v, float) else [round(x, 3) for x in v]) for k, v in out['L_in_R'].items()})
