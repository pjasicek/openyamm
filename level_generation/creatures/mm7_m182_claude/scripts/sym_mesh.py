"""Symmetric rest pose before rigging and UVs (Meshy built the three-quarter master's asymmetry into the mesh):
the right wing (-X) turns about its shoulder onto the mirror of the left wing (ICP rotation, soft root falloff),
and the tail, curved toward -X, is unbent onto the midline by arc length (cross-sections and length preserved).
System Python (SciPy): work/rest_co_v2.npy -> work/rest_co_v3.npy, work/sym_report.json; then
scripts/apply_coords.py (Blender) writes them into work/static_v2.blend -> work/static_v3.blend."""
import json
import numpy as np
from pathlib import Path
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
P = Path(__file__).resolve().parents[1]
co = np.load(P / 'work/rest_co_v2.npy'); x, y, z = co.T
ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))
report = {}

# --- right wing: ICP rotation about the shoulder onto the mirrored left wing
pivot = np.array([-.08, -.25, .30])
left = co[(x > .12) & (z > .26)] * np.array([-1, 1, 1]); right_ids = np.where((x < -.12) & (z > .26))[0]
Q = np.eye(3); tree = cKDTree(left)
for _ in range(60):
    moved = (co[right_ids] - pivot) @ Q.T + pivot; d, i = tree.query(moved); keep = d < np.percentile(d, 90)
    H = (co[right_ids][keep] - pivot).T @ (left[i[keep]] - pivot); U, S, Vt = np.linalg.svd(H)
    Q = Vt.T @ np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
rotvec = Rotation.from_matrix(Q).as_rotvec()
w = ss((-x - .085) / .05) * ss((z - .22) / .05) * (x < 0)
new = co.copy()
for k in np.where(w > 0)[0]:
    R = Rotation.from_rotvec(rotvec * w[k]).as_matrix(); new[k] = (co[k] - pivot) @ R.T + pivot
d, _ = tree.query(new[right_ids])
report['wing'] = {'pivot': pivot.tolist(), 'angle_deg': float(np.degrees(np.linalg.norm(rotvec))), 'axis': (rotvec / np.linalg.norm(rotvec)).tolist(),
                  'mirror_residual_median_m': float(np.median(d)), 'mirror_residual_p90_m': float(np.percentile(d, 90)), 'moved_vertices': int((w > 0).sum())}

# --- tail: arc-length unbend onto x = 0
ys = np.arange(-.02, .43, .01); cx = []
for yy in ys:
    m = (np.abs(y - yy) < .008) & (z < .22) & (z > .06) & (np.abs(x - (cx[-1] if cx else -.02)) < .06)
    cx.append(float(np.median(x[m])) if m.sum() > 5 else (cx[-1] if cx else -.02))
coef = np.polyfit(ys, cx, 3); c = lambda t: np.polyval(coef, t); dc = np.polyder(coef)
dense = np.linspace(-.02, .45, 2000); line = np.c_[c(dense), dense]
seg = np.linalg.norm(np.diff(line, axis=0), axis=1); arc = np.r_[0, np.cumsum(seg)]
tail = (y > -.02) & (z > .05) & (z < .24) & (np.abs(x - c(np.clip(y, -.02, .45))) < .07)
lt = cKDTree(line); _, j = lt.query(np.c_[new[tail, 0], new[tail, 1]])
tangent = np.gradient(line, axis=0); tangent /= np.linalg.norm(tangent, axis=1)[:, None]; normal = np.c_[tangent[:, 1], -tangent[:, 0]]
off = np.c_[new[tail, 0], new[tail, 1]] - line[j]; n = np.sum(off * normal[j], 1); s = arc[j] + np.sum(off * tangent[j], 1)
base = line[0]; straight = np.c_[n * np.sign(normal[0, 0]) + 0. , -.02 + s]
blend = ss((new[tail, 1] + .02) / .06)[:, None]
new[tail, :2] = new[tail, :2] * (1 - blend) + straight * blend
report['tail'] = {'centreline_x_at': {f'{t:.2f}': round(float(c(t)), 3) for t in (0., .1, .2, .3, .4)}, 'moved_vertices': int(tail.sum()),
                  'arc_length_m': float(arc[-1])}
np.save(P / 'work/rest_co_v3.npy', new)
report['bounds'] = [new.min(0).tolist(), new.max(0).tolist()]
(P / 'work/sym_report.json').write_text(json.dumps(report, indent=2) + '\n'); print('SYM', json.dumps(report))
