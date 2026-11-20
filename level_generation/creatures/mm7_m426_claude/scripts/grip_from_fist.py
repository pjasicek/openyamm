"""Grip axis of a closed fist (the HD masters show the staff hand as an empty fist with a grip opening) from the rest
mesh, for the staff seat (work/grip_pose.json, as natm/m460: handle_axis_hand_local, handle_centre_hand_local).
Candidate lines run through points near the fist centre in directions 60-120 deg from the forearm (a fist holds a
shaft across the palm); per line, ENCLOSURE = share of 16 angular sectors round the line (in the slab |along| < SLAB)
that hold fist vertices within ENC_R, CLEAR = distance from the line to the nearest fist vertex in the slab. Best =
highest enclosure, then clearance (the tunnel). Args: -- <blend> <side L|R> [radius]"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg, common
a = sys.argv[sys.argv.index('--') + 1:]
blend, side = a[0], a[1]; RADIUS = float(a[2]) if len(a) > 2 else 0.016
SLAB, ENC_R = 0.035, 0.06
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([v.co[:] for v in me.vertices]); pv = np.array([x.value for x in me.attributes['piece'].data])
J = lambda n: np.array(rig.data.bones[n].head_local)
wr, fa = J(f'B_{side}_Hand'), J(f'B_{side}_Forearm')
fd = (wr - fa) / np.linalg.norm(wr - fa)
hv = co[cfg.hand_mask(co, pv, side, wr, fa, -0.01, 0.2)]
c0 = hv.mean(0)
dirs = []
rng = np.random.default_rng(1)
for k in range(4000):
    d = rng.normal(size=3); d /= np.linalg.norm(d)
    if d[2] < 0:
        d = -d
    if abs(d @ fd) <= math.cos(math.radians(60)):         # 60-120 deg from the forearm
        dirs.append(d)
best = None
offs = [np.array(o) * 0.012 for o in np.ndindex(5, 5, 5)]
offs = [o - 0.024 for o in offs]
for d in dirs[:600]:
    u = np.cross(d, [0, 0, 1.0]) if abs(d[2]) < 0.95 else np.cross(d, [1.0, 0, 0]); u /= np.linalg.norm(u); w = np.cross(d, u)
    for o in offs:
        c = c0 + o
        rel = hv - c; along = rel @ d
        sl = rel[np.abs(along) < SLAB]
        if len(sl) < 20:
            continue
        perp = sl - np.outer(sl @ d, d); dist = np.linalg.norm(perp, axis=1)
        near = dist < ENC_R
        if near.sum() < 10:
            continue
        ang = np.arctan2(perp[near] @ w, perp[near] @ u)
        enc = len(set(((ang + math.pi) / (2 * math.pi) * 16).astype(int) % 16)) / 16
        clear = float(dist.min())
        score = (round(enc, 2), clear)
        if best is None or score > best[0]:
            best = (score, d.copy(), c.copy())
(enc, clear), d, c = best
H = rig.data.bones[f'B_{side}_Hand'].matrix_local
Hi = H.inverted()
axis_l = (H.to_3x3().inverted() @ Vector(d)).normalized(); cen_l = Hi @ Vector(c)
ang_f = math.degrees(math.acos(abs(float(d @ fd))))
json.dump({'side': side, 'handle_axis_hand_local': list(axis_l), 'handle_centre_hand_local': list(cen_l),
           'enclosure': enc, 'clearance_m': clear, 'angle_to_forearm_deg': ang_f, 'rest_axis_world': d.tolist(),
           'rest_centre_world': c.tolist()}, open(os.path.join(common.WORK, 'grip_pose.json'), 'w'), indent=1)
print('GRIP', side, 'enclosure', enc, 'clearance mm', round(clear * 1000, 1), 'axis world', np.round(d, 3).tolist(),
      'angle to forearm', round(ang_f, 1), 'centre', np.round(c, 3).tolist(), 'fist verts', len(hv))
