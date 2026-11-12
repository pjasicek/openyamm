"""Project-and-bake geometry step (CLAUDE_CREATURE_TEXTURES.md, "Problem heads"): the v3 face skin moved onto the aligned v4 Meshy head's face
(nearest surface point), our topology, parts and seams kept. Weight 1 on the open face, 0 under the hair shell / circlet / braid (skin a ray
along the normal meets within 3 cm), under the jaw and past the cheeks; neighbour-smoothed; the displacement is low-passed once more so the
rim has no step. Args: <v3 npz> <head npz> <align json> <out npz> [report json]"""
import sys, json
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from meshlib import sample, vnormals, ss
V, H, AL, OUT = sys.argv[1:5]
v = dict(np.load(V)); h = np.load(H); M = np.array(json.load(open(AL))['M'])
co = v['co'].copy(); tri = v['tri']; part = v['part']; head = v['head']
hc = h['co'] @ M[:3, :3].T + M[:3, 3]
Q, _ = sample(hc, h['tri'], 2500000, 3); tq = cKDTree(Q)
vn = vnormals(co, tri)
skin = np.zeros(len(co), bool); skin[np.unique(tri[(part == 0) & (head == 1)])] = True
hair = np.unique(tri[np.isin(part, [8, 9, 10])])
Hp, _ = sample(co, tri[np.isin(part, [8, 9, 10])], 300000, 4); th = cKDTree(Hp)
idx = np.where(skin)[0]
cov = np.zeros(len(co), bool)
for k in np.arange(0.002, 0.032, 0.003):
    d, _ = th.query(co[idx] + vn[idx] * k); cov[idx[d < 0.0045]] = True
d0, _ = th.query(co[idx]); cov[idx[d0 < 0.004]] = True
p = co
w = skin & ~cov
w = w * ss(p[:, 2], 1.352, 1.372) * (1 - ss(np.abs(p[:, 0]), 0.047, 0.062)) * (p[:, 1] < 0.02)
dd, kk = tq.query(co); w = w * (1 - ss(dd, 0.010, 0.018))
nbr = [[] for _ in range(len(co))]
for a, b in np.r_[tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]]:
    nbr[a].append(b)
ws = w.astype(float)
for _ in range(4):
    ws = np.array([0.5 * ws[i] + 0.5 * np.mean(ws[n]) if (n and skin[i]) else ws[i] for i, n in enumerate(nbr)])
ws = np.minimum(ws, w.astype(float) * 0 + ws)
ws[~skin] = 0
disp = (Q[kk] - co) * ws[:, None]
for _ in range(2):
    disp = np.array([0.6 * disp[i] + 0.4 * np.mean(disp[n], 0) if (n and skin[i]) else disp[i] for i, n in enumerate(nbr)])
co2 = co + disp
mv = np.linalg.norm(disp, axis=1)
rep = dict(moved=int((ws > 0.01).sum()), covered=int(cov.sum()), skin=int(skin.sum()), mm_p50=round(float(np.median(mv[ws > 0.5]) * 1000), 2),
           mm_p90=round(float(np.percentile(mv[ws > 0.5], 90) * 1000), 2), mm_max=round(float(mv.max() * 1000), 2))
print('WRAP', rep)
v['co'] = co2; v['wrap_w'] = ws
np.savez(OUT, **v)
if len(sys.argv) > 5: json.dump(rep, open(sys.argv[5], 'w'), indent=1)
