"""Final weights on the joined mesh from the heat weights. Args: <joined npz> <heat npz> <rig json> <labels npy> <out npz>"""
import sys, json, os
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from rig_bones import FINGERS, half_pairs
J_, H_, R_, L_, OUT = sys.argv[1:6]
D = np.load(J_); co, tri, head = D['co'], D['tri'], D['head']
H = np.load(H_); W = H['W'].astype(np.float64); names = [str(x) for x in H['names']]
ix = {n: i for i, n in enumerate(names)}
labels = np.load(L_)
hv = np.zeros(len(co), bool); hv[tri[head == 1].ravel()] = True
def swap(n):
    return n.replace(' L ', ' _ ').replace(' R ', ' L ').replace(' _ ', ' R ')
perm = np.array([ix[swap(n)] for n in names])
d, m = cKDTree(co * [-1, 1, 1]).query(co)
print('mirror max', d.max())
W = 0.5 * (W + W[m][:, perm])
# edges
e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
A = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(len(co), len(co))).tocsr()
A.data[:] = 1
deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
fingers = labels > 0
import os
for it in range(int(os.environ.get('PASSES', '6'))):
    S = (A @ W) / deg[:, None]
    W[~fingers] = 0.5 * W[~fingers] + 0.5 * S[~fingers]
# shoulders: a wider blend round the joint (anterior armpit when the arm crosses the chest)
sj = np.array(json.load(open(sys.argv[3]))['joints']['Bip01 L UpperArm'])
zone = (np.minimum(np.linalg.norm(co - sj, axis=1), np.linalg.norm(co - sj * [-1, 1, 1], axis=1)) < 0.13) & ~fingers
for it in range(int(os.environ.get('SHPASS', '8'))):
    S = (A @ W) / deg[:, None]
    W[zone] = 0.5 * W[zone] + 0.5 * S[zone]
# fingers: only their own chain and the hand
for lab, f in enumerate(FINGERS, 1):
    for s, sgn in (('L', -1), ('R', 1)):
        vs = np.where((labels == lab) & (co[:, 0] * sgn > 0))[0]
        allow = [ix[f'Bip01 {s} {f}{k}'] for k in (1, 2, 3)] + [ix[f'Bip01 {s} Hand']]
        mask = np.zeros(W.shape[1]); mask[allow] = 1
        W[vs] *= mask
        # no bone of another finger on the palm side either
for s, sgn in (('L', -1), ('R', 1)):
    # palm verts: finger bones only from the knuckle band
    side = co[:, 0] * sgn > 0
    pass
# head rigid, neck tube blends into it
W[hv] = 0; W[hv, ix['Bip01 Head']] = 1
tube = (~hv) & (co[:, 2] > 1.59)
u = np.clip((co[tube, 2] - 1.585) / (1.675 - 1.585), 0, 1); u = u * u * (3 - 2 * u)
Wt = np.zeros((tube.sum(), W.shape[1])); Wt[:, ix['Bip01 Neck']] = 1 - u; Wt[:, ix['Bip01 Head']] = u
W[tube] = Wt
# half joints: where a child and its parent side overlap, the shared part goes to a helper turned half way (no pinch at a deep bend)
if os.environ.get('NOHALF') is None:
    pairs = half_pairs()
    names = names + [h for h, _, _, _ in pairs]
    W = np.c_[W, np.zeros((len(W), len(pairs)))]
    ix = {n: i for i, n in enumerate(names)}
    for h, c, _, ps in pairs:
        ic = ix[c]; ip = [ix[x] for x in ps]
        a = W[:, ip].sum(1); b = W[:, ic]; m_ = np.minimum(a, b)
        sel = (m_ > 1e-4) & ~hv
        W[sel, ix[h]] = 2 * m_[sel]; W[sel, ic] -= m_[sel]
        W[np.ix_(np.where(sel)[0], ip)] *= (1 - m_[sel] / a[sel])[:, None]
# top 4
ord_ = np.argsort(-W, axis=1)[:, :4]
ww = np.take_along_axis(W, ord_, 1); ww /= ww.sum(1, keepdims=True)
print('max influences used', (ww > 1e-3).sum(1).max(), 'unweighted', int((W.sum(1) < 1e-5).sum()))
np.savez(OUT, wj=ord_, ww=ww.astype('f4'), wnames=np.array(names))
