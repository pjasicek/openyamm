"""Final weights: mirrored heat, smoothing, fingers on their chain, tail on its bones, optional head/jaw rules, half joints. Args: <mesh npz> <heat npz> <labels npy> <out npz>.
Mesh keys used: co, tri, optional part (per vertex: 0 body, 1 head, 2 jaw, 3 teeth upper, 4 teeth lower, 5 spine), neckw (head weight of a vertex 0..1)."""
import sys, os, json
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
sys.path.insert(0, 'scripts')
from rig_bones import half_pairs, FN, fk, TAIL
J_, H_, L_, OUT = sys.argv[1:5]
D = np.load(J_); co, tri = D['co'].astype(float), D['tri']
H = np.load(H_); W = H['W'].astype(np.float64); names = [str(x) for x in H['names']]
if len(W) < len(co): W = np.vstack([W, np.zeros((len(co) - len(W), W.shape[1]))])
for n in ('Box04',):
    if n not in names: names.append(n); W = np.c_[W, np.zeros(len(W))]
ix = {n: i for i, n in enumerate(names)}
labels = np.load(L_)
if len(labels) < len(co): labels = np.r_[labels, np.zeros(len(co) - len(labels), int)]
nb = int(D['nb']) if 'nb' in D else len(co)
part = D['part'] if 'part' in D else np.zeros(len(co), int)
def swap(n): return n.replace(' L ', ' _ ').replace(' R ', ' L ').replace(' _ ', ' R ')
perm = np.array([ix[swap(n)] for n in names])
d, m = cKDTree(co[:nb] * [-1, 1, 1]).query(co[:nb])
print('mirror max', d.max())
W[:nb] = .5 * (W[:nb] + W[:nb][m][:, perm])
e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
A = coo_matrix((np.ones(len(e) * 2), (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(len(co), len(co))).tocsr(); A.data[:] = 1
deg = np.maximum(np.asarray(A.sum(1)).ravel(), 1)
fingers = labels > 0
for it in range(int(os.environ.get('PASSES', '6'))):
    S_ = (A @ W) / deg[:, None]; W[~fingers] = .5 * W[~fingers] + .5 * S_[~fingers]
import rig_bones
P_, tips = rig_bones.joints()
# wider blend round the shoulders and hips
for b, r, n_ in (('Bip02 L UpperArm', .15, 10), ('Bip02 L Thigh', .17, 10)):
    j = P_[b]; zone = (np.minimum(np.linalg.norm(co - j, axis=1), np.linalg.norm(co - j * [-1, 1, 1], axis=1)) < r) & ~fingers
    for it in range(n_):
        S_ = (A @ W) / deg[:, None]; W[zone] = .5 * W[zone] + .5 * S_[zone]
# fingers
for lab, f in enumerate(FN, 1):
    for s, sg in (('L', 1), ('R', -1)):
        vs = np.where((labels == lab) & (co[:, 0] * sg > 0))[0]
        allow = [ix[f'Bip02 {s} {fk(f, k)}'] for k in range(3)] + [ix[f'Bip02 {s} Hand']]
        mask = np.zeros(W.shape[1]); mask[allow] = 1; W[vs] *= mask
# no arm bone on the torso or legs and no leg on the arms: cut by connectivity later if the gates ask
# tail: only tail bones and the pelvis
tv = (np.abs(co[:, 0]) < .13) & (co[:, 1] < -.0) & (co[:, 2] < -.45)
allow = np.zeros(W.shape[1]); allow[[ix[t] for t in TAIL[:3]] + [ix['Bip01 Pelvis']]] = 1; W[tv] *= allow
# head rules
if 'neckw' in D:
    nw = D['neckw']
    hd = ix['Bip01 Head']; nk = ix['Bip02 Neck']; jw = ix['Box05']
    rig = (part > 0) & (part != 5)
    W[rig] = 0; W[part == 1, hd] = 1; W[part == 3, hd] = 1; W[part == 6, hd] = 1
    W[part == 2, jw] = 1; W[part == 4, jw] = 1
    if 'jawk' in D:          # lips and corners: blend head <-> jaw
        jk = D['jawk']; sel = (jk > 0) & (part == 1)
        W[sel] = 0; W[sel, jw] = jk[sel]; W[sel, hd] = 1 - jk[sel]
    b = (part == 0) & (nw > 0)     # body side of the neck ring blends into the head
    W[b] *= (1 - nw[b])[:, None]; W[b, hd] += nw[b]
if os.environ.get('NOHALF') is None:
    pairs = half_pairs()
    names = names + [h for h, _, _, _ in pairs]
    W = np.c_[W, np.zeros((len(W), len(pairs)))]
    ix = {n: i for i, n in enumerate(names)}
    for h, c, _, ps in pairs:
        ic = ix[c]; ip = [ix[x] for x in ps]
        a = W[:, ip].sum(1); b = W[:, ic]; m_ = np.minimum(a, b)
        sel = (m_ > 1e-4) & ((part == 0) | (part == 5) | ((part == 1) & (c == 'Box05')))
        W[sel, ix[h]] = 2 * m_[sel]; W[sel, ic] -= m_[sel]
        W[np.ix_(np.where(sel)[0], ip)] *= (1 - m_[sel] / a[sel])[:, None]
if (part == 5).any():
    i5 = np.where(part == 5)[0]; dd_, mm_ = cKDTree(co[:nb]).query(co[i5]); W[i5] = W[mm_]
    # one spine, one blend
    for s_ in range(0, len(i5), 11): W[i5[s_:s_ + 11]] = W[i5[s_]]
ord_ = np.argsort(-W, axis=1)[:, :4]
ww = np.take_along_axis(W, ord_, 1); ww[ww < .012] = 0; ww /= np.maximum(ww.sum(1, keepdims=True), 1e-9)
print('max influences', (ww > 1e-3).sum(1).max(), 'unweighted', int((W.sum(1) < 1e-5).sum()))
np.savez(OUT, wj=ord_, ww=ww.astype('f4'), wnames=np.array(names))
