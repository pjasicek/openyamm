"""v2 symmetry pass, step 1 (system Python): straighten the rest mesh onto the x = 0 plane before mirroring.

1. Head: Meshy turned the head ~10 deg (yaw) and rolled it ~4 deg. Its mirror plane is fitted on the head and crest
   (rigid reflection fit, Nelder-Mead over yaw/roll/offset), and the head is turned rigidly about the head joint onto
   x = 0; the upper neck takes the turn gradually (smoothstep in z) so the neck does not shear.
2. Trunk, neck and tail: rows along +X on a 2 mm (y, z) grid give the body interval; its midpoint field c(y, z)
   (scripts/midline_field.py on the turned mesh) is subtracted from x. Wings move with the field value at their
   shoulder, so they stay rigid.
Writes work/v2/rest_co_v5a.npy and work/v2/sym_report.json. Usage: sym_v2.py (expects work/v2/static_v4.npz)."""
import json, subprocess, sys
import numpy as np
from pathlib import Path
from scipy.spatial import cKDTree
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation
from scipy.ndimage import map_coordinates
P = Path(__file__).resolve().parents[1]; W = P / 'work/v2'
d = np.load(W / 'static_v4.npz'); co = d['co'].copy(); part = d['part']; x, y, z = co.T; ax = np.abs(x)
ss = lambda t: np.clip(t, 0, 1) ** 2 * (3 - 2 * np.clip(t, 0, 1))
report = {}

def plane_fit(mask):
    Pm = co[mask]; tree = cKDTree(Pm)
    def normal(q): return np.array([np.cos(q[0]) * np.cos(q[1]), np.sin(q[0]), np.cos(q[0]) * np.sin(q[1])])
    def cost(q):
        n = normal(q); s = Pm @ n - q[2]; dd, _ = tree.query(Pm - 2 * s[:, None] * n); return np.mean(np.minimum(dd, .01))
    best = min((minimize(cost, [y0, 0, c0], method='Nelder-Mead', options={'xatol': 1e-6, 'fatol': 1e-8, 'maxiter': 600})
                for c0 in np.arange(-.03, .031, .01) for y0 in (-.15, 0, .15)), key=lambda r: r.fun)
    return normal(best.x), best.x[2], best.fun, cost([0, 0, 0])

# ---- 1. head
wing0 = (ax > .085) & (z > .255) & (y > -.33) & (y < -.08)
head = (y < -.31) & (z > .37) & ~wing0 & (ax < .10)
n, c, fit_cost, cost0 = plane_fit(head)
pivot = np.array([0., -.306, .392]); pivot = pivot - (pivot @ n - c) * n        # head joint, projected onto the plane
R = Rotation.align_vectors([[1, 0, 0]], [n])[0]; rv = R.as_rotvec()
target = pivot.copy(); target[0] = 0.
neck_band = (y < -.24) & (z > .30) & ~wing0 & (ax < .10)
w = np.where(head, 1., np.where(neck_band, ss((z - .325) / .06), 0.))
for i in np.where(w > 0)[0]:
    Ri = Rotation.from_rotvec(rv * w[i]).as_matrix(); co[i] = (co[i] - pivot) @ Ri.T + pivot + w[i] * (target - pivot)
np.savez(W / 'sym_params.npz', pivot=pivot, rotvec=rv, target=target)
report['head'] = {'plane_normal': n.tolist(), 'yaw_deg': float(np.degrees(np.arctan2(n[1], n[0]))),
                  'roll_deg': float(np.degrees(np.arctan2(n[2], n[0]))), 'mirror_cost_mm_before': cost0 * 1000,
                  'mirror_cost_mm_fitted_plane': fit_cost * 1000, 'turn_deg': float(np.degrees(np.linalg.norm(rv))),
                  'moved_vertices': int((w > 0).sum())}

# ---- 2. midline field on the turned mesh
np.savez(W / 'sym_step1.npz', co=co, tris=d['tris'], part=part)
subprocess.run([sys.executable, str(P / 'scripts/midline_field.py'), str(W / 'sym_step1.npz'), str(W / 'midline_field.npz'),
                str(P / 'review/symmetry_field.png')], check=True)
f = np.load(W / 'midline_field.npz'); ys, zs, cf = f['ys'], f['zs'], f['c']
def field(p):
    iy = (p[:, 1] - ys[0]) / (ys[1] - ys[0]); iz = (p[:, 2] - zs[0]) / (zs[1] - zs[0])
    return map_coordinates(cf, [iy, iz], order=1, mode='nearest')
x, y, z = co.T; ax = np.abs(x)
wing = (ax > .085) & (z > .255) & (y > -.33) & (y < -.08)
shift = field(co)
for s in (1, -1):
    sw = wing & (x * s > 0); shoulder = np.array([[s * .075, -.262, .30]])
    root = ss((ax - .085) / .05)                                        # wing root blends from the field to the shoulder value
    shift[sw] = (1 - root[sw]) * shift[sw] + root[sw] * field(shoulder)[0]
co[:, 0] -= shift
report['field'] = {'shift_mm_percentiles_1_50_99': np.round(np.percentile(shift, [1, 50, 99]) * 1000, 2).tolist()}

# ---- mirror distance before cutting (diagnostic)
d0 = cKDTree(d['co']).query(d['co'] * [-1, 1, 1])[0]; d1 = cKDTree(co).query(co * [-1, 1, 1])[0]
report['mirror_distance_mm'] = {'v4_median_p99': [float(np.median(d0) * 1000), float(np.percentile(d0, 99) * 1000)],
                                'straightened_median_p99': [float(np.median(d1) * 1000), float(np.percentile(d1, 99) * 1000)]}
np.save(W / 'rest_co_v5a.npy', co)
(W / 'sym_report.json').write_text(json.dumps(report, indent=2) + '\n'); print('SYM_V2', json.dumps(report))
