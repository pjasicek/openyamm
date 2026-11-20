#!/usr/bin/env python3
"""Keep / group sets per installed GLB LOD0 face (primitive order Yanmir, YanmirHead, YanmirAcc) for mpqem.py ->
work/glb_sets_<tag>.npz (keep, group, lining, lined, cls, mat). glTF rest frame: y up, face towards +z.
Classes (cls): 0 body rest, 1 hand (Hand/fingers dominant), 2 wrist graft (hand face with any Forearm weight), 3 grip pads
(right-hand finger faces within GRIP m of the staff surface), 4 sole, 5 neck seam (body), 10 face skin (incl. mustache,
ears, under-crown forehead), 11 eyes, 12 hair, 13 beard, 14 head neck seam, 20 staff head (cup, petals, ring, gem),
21 shaft, 22 shaft grip band, 23 staff foot, 24 crown band, 25 crown spikes.
Keep exactly (brief + boss extras): face skin, eyes, ears, both neck seam sides (+ RING face rings), the wrist graft, the grip
pads, soles, the staff head, the shaft round the fist (SHAFTGRIP m from right-hand finger vertices), the staff foot, the ice
spikes. Groups: 1 hands (MP_GROUPS 1:..), 2 hair, 3 beard, 4 shaft, 5 crown band; 0 = body rest (the ladder ratio).
Usage: make_sets_yan.py <tag>"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
tag = sys.argv[1]
E = lambda k, d: float(os.environ.get(k, d))
YBEARD, ZBACK, YTOP = E('YBEARD', '2.462'), E('ZBACK', '-0.06'), E('YTOP', '2.715')
YJAW, XJAW, YLOCK, ZLOCK, XLOCK = E('YJAW', '2.48'), E('XJAW', '0.07'), E('YLOCK', '2.53'), E('ZLOCK', '0.03'), E('XLOCK', '0.10')
GRIP, SHAFTGRIP, SOLE, RING = E('GRIP', '0.006'), E('SHAFTGRIP', '0.03'), E('SOLE', '0.012'), int(E('RING', '1'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_yanmir.glb', 'Yanmir')
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
PR = ['Yanmir', 'YanmirHead', 'YanmirAcc']
assert list(D) == PR, list(D)


def comps(P, T):
    _, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
    r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
    return lab[FT[:, 0]], w


def dominant(J, W, T):
    acc = np.zeros((len(T), len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
    return acc


def grow(T, sel, w, rings):
    for _ in range(rings):
        v = np.zeros(w.max() + 1, bool); v[w[T[sel]].ravel()] = True; sel = sel | v[w[T]].any(1)
    return sel


B, H, A = D['Yanmir'], D['YanmirHead'], D['YanmirAcc']
floor = B['P'][:, 1].min()
# ---- body
acc = dominant(B['J'], B['W'], B['T']); dom = acc.argmax(1)
isj = lambda *keys: np.array([any(k in n for k in keys) for n in jn])
handj = isj(' Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'); fingj = isj('Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
forej = isj('Forearm'); headj = isj('Head', 'Ponytail', 'Neck')
Tb = B['T']; Vb = B['P'][Tb]; _, wb = comps(B['P'], Tb)
cb = np.zeros(len(Tb), int)
cb[handj[dom]] = 1
cb[(cb == 1) & (acc[:, forej].sum(1) > 1e-3)] = 2
# grip pads: right-hand finger faces near the staff surface (rest)
acomp, aw = comps(A['P'], A['T'])
staffv = np.unique(A['T'][np.isin(np.arange(len(A['T'])), np.flatnonzero(np.array([jn[j] for j in dominant(A['J'], A['W'], A['T']).argmax(1)]) == 'Ystaff'))])
def surf(P, T, step=0.004):
    out = []
    for t in T:
        a, b, c = P[t]; k = int(np.clip(max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b)) / step, 1, 60))
        i, j = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); m = i + j <= k
        w = np.stack([i[m], j[m], k - i[m] - j[m]], 1) / k; out.append(w @ P[t])
    return np.concatenate(out)
sfaces = A['T'][np.isin(A['T'], staffv).all(1)]
dstaff = cKDTree(surf(A['P'], sfaces)).query(Vb.reshape(-1, 3))[0].reshape(-1, 3).min(1)
print('right finger faces: min staff distance', dstaff[np.array([' R ' in n for n in jn])[dom] & fingj[dom]].min().round(4))
rfing = np.array([' R ' in n for n in jn])[dom] & fingj[dom]
cb[rfing & (dstaff < GRIP)] = 3
cb[Vb[:, :, 1].min(1) < floor + SOLE] = 4
dh = cKDTree(H['P']).query(B['P'])[0]
seamb = (dh[Tb] < 1e-4).any(1) | headj[dom]
seamb = grow(Tb, seamb, wb, RING)
cb[seamb] = 5
# ---- head
Th = H['T']; Vh = H['P'][Th]; hcomp, wh = comps(H['P'], Th); ch = np.full(len(Th), 10)
cen = Vh.mean(1)
ch[cen[:, 1] < YBEARD] = 13
ch[(cen[:, 1] < YJAW) & (np.abs(cen[:, 0]) > XJAW)] = 13                     # beard on the jaw beside the mouth
ch[(cen[:, 2] < ZBACK) | (cen[:, 1] > YTOP)] = 12
ch[(cen[:, 1] < YLOCK) & (cen[:, 2] < ZLOCK) & (np.abs(cen[:, 0]) > XLOCK)] = 12   # side locks below the ears
sz = np.bincount(hcomp); ch[sz[hcomp] < 200] = 11
db = cKDTree(B['P']).query(H['P'])[0]
seamh = grow(Th, (db[Th] < 1e-4).any(1), wh, RING)
ch[seamh & (ch != 11)] = 14
# ---- accessories
Ta = A['T']; Va = A['P'][Ta]; ca = np.full(len(Ta), 20)
sza = np.bincount(acomp); adom = np.array([jn[j] for j in dominant(A['J'], A['W'], Ta).argmax(1)])
crown = adom == 'Bip01 Head'
ca[crown & (sza[acomp] > 100)] = 24; ca[crown & (sza[acomp] <= 100)] = 25
shaft = (~crown) & (sza[acomp] == 512); foot = (~crown) & (sza[acomp] == 160)
assert shaft.sum() == 512 and foot.sum() == 160
ca[foot] = 23; ca[shaft] = 21
fingv = np.unique(Tb[rfing | ((cb == 1) & np.array([' R ' in n for n in jn])[dom])].ravel())
dgrip = cKDTree(B['P'][fingv]).query(Va.reshape(-1, 3))[0].reshape(-1, 3).min(1)
ca[shaft & (dgrip < SHAFTGRIP)] = 22
# set c: the right fist's fingers whole (RFIST=1: the staff gate's finger wrap fell 15-30 deg with the fingers at 0.65), and the
# body faces the hands/forearms touch in a clip window (CONTACT=Death2:0.8:2.0, CONTACT_R m from a posed hand/forearm vertex: the
# arm/hand gate's Death2 left hand went 4 -> 7 frames over 1 cm when the torso under it was cut)
if os.environ.get('RFIST') == '1':
    rf = np.array([' R ' in n for n in jn])[dom] & fingj[dom] & np.isin(cb, (1,))
    cb[rf] = 6; print('right fist fingers kept', int(rf.sum()))
if os.environ.get('CONTACT'):
    sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
    from glb_pose import Glb, Model
    clip, t0, t1 = os.environ['CONTACT'].split(':'); t0, t1 = float(t0), float(t1); CR = float(os.environ.get('CONTACT_R', '0.03'))
    mdl = Model(Glb(str(HERE / 'before' / 'mm9_yanmir.glb')))
    armj = isj(' Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Forearm')
    av = np.unique(Tb[armj[dom]].ravel()); bodyf = ~armj[dom] & (cb == 0)
    hit = np.zeros(len(Tb), bool)
    for t in np.arange(t0, t1, 1 / 48):
        pz = mdl.skinned_positions(mdl.world(mdl.sample(clip, t)))[0][0]
        d = cKDTree(pz[av]).query(pz[Tb].mean(1))[0]
        hit |= bodyf & (d < CR)
    cb[hit] = 7; print('contact faces kept', int(hit.sum()))
cls = np.concatenate([cb, ch, ca]); mat = np.concatenate([np.full(len(Tb), 0), np.full(len(Th), 1), np.full(len(Ta), 2)])
keep = np.isin(cls, (2, 3, 4, 5, 6, 7, 10, 11, 14, 20, 22, 23, 25) + tuple(int(c) for c in os.environ.get('KEEPCLS', '').split(',') if c))
gmap = {0: 0, 1: 1, 12: 2, 13: 3, 21: 4, 24: 5}
group = np.array([gmap.get(int(c), 0) for c in cls]); group[keep] = 0
names = {0: 'body', 1: 'hand', 2: 'wrist graft', 3: 'grip pads', 4: 'sole', 5: 'neck seam body', 6: 'right fist fingers', 7: 'arm contact', 10: 'face skin', 11: 'eyes',
         12: 'hair', 13: 'beard', 14: 'neck seam head', 20: 'staff head', 21: 'shaft', 22: 'shaft grip', 23: 'staff foot',
         24: 'crown band', 25: 'spikes'}
for c in np.unique(cls):
    m = cls == c; print(f'cls {c:2d} {names[c]:15s} {m.sum():5d} keep {int(keep[m].sum()):5d}')
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %) free', int((~keep).sum()), 'of', len(cls))
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=np.zeros(len(cls), bool),
         lined=np.zeros(len(cls), bool), cls=cls, mat=mat)
