#!/usr/bin/env python3
"""Keep / group sets per installed LOD0 face (primitive order Krohn, KrohnHead, KrohnProps) for mpqem.py ->
work/glb_sets_<tag>.npz (keep, group, lining, lined, cls, mat). glTF rest frame: y up, face towards +z, true-handed (mirrored).
Labels: work/glb_labels.npz (master `lined`/`hand`/graft by centroid), work/lining_pairs.npz (band/lining/rim, twins),
work/head_charts.npy (head UV charts; chart 32 = the face, one island by relayout_head_k.py).
Body classes: 0 rest (ladder ratio), 1 band (lined outer cloth: cut, lining re-emitted), 2 lining (re-emitted), 3 rim strip, 4 sole,
5 neck seam, 6 hand graft seam (forearm faces on the hand graft), 7 medallions / buckle / baldric / knee discs (small loose parts),
8 belt band, 9 greaves + bracers (painted relief plates).
Head classes: 10 face skin (face chart, ears), 11 eyes, 12 hair + beard, 13 hairline (hair faces touching face skin), 14 neck seam,
15 crown, 16 hand palm/back, 17 fingers, 18 wrist graft (hand faces with Forearm weight).
Props: 20 glaive guard disc + socket, 21 sword (scabbard spiral, wrapped grip: exact), 22 glaive shaft (group 4), 23 shaft round
the fist (SHAFTGRIP m of the right fingers, exact), 24 glaive blade (group 5).
Exact: 2(re-emitted), 3, 4, 5, 6, 7, 8, 10, 11, 13, 14, 15, 17, 18, 20, 21 (+ KEEPCLS). Groups: 1 palm/back (MP_GROUPS 1:..),
2 hair+beard, 3 greaves+bracers, 4 shaft, 5 blade; 0 = body rest and bands (the ladder ratio).
Usage: make_sets_kr.py <tag>   env KEEPCLS=9 (keep the relief plates), EAR box, BELT y range"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
tag = sys.argv[1]
E = lambda k, d: float(os.environ.get(k, d))
SOLE, RING = E('SOLE', '0.012'), int(E('RING', '1'))
BELT0, BELT1 = E('BELT0', '1.525'), E('BELT1', '1.725')
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_krohn.glb', 'Krohn')
jn = [doc['nodes'][j]['name'] for j in doc['skins'][nd['skin']]['joints']]
assert list(D) == ['Krohn', 'KrohnHead', 'KrohnProps'], list(D)
L = np.load(HERE / 'work' / 'glb_labels.npz'); LP = np.load(HERE / 'work' / 'lining_pairs.npz')
B, H, A = D['Krohn'], D['KrohnHead'], D['KrohnProps']; nb, nh = len(B['T']), len(H['T'])


def comps(P, T):
    _, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
    r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
    return lab[FT[:, 0]], w


def wacc(J, W, T):
    acc = np.zeros((len(T), len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
    return acc


def grow(T, sel, w, rings, within=None):
    for _ in range(rings):
        v = np.zeros(w.max() + 1, bool); v[w[T[sel]].ravel()] = True; new = v[w[T]].any(1)
        sel = sel | (new if within is None else new & within)
    return sel


isj = lambda *keys: np.array([any(k in n for k in keys) for n in jn])
fingj = isj('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'); forej = isj('Forearm'); handj = isj(' Hand') | fingj
# ---- body
Tb = B['T']; Vb = B['P'][Tb]; cenb = Vb.mean(1); bcomp, wb = comps(B['P'], Tb); accb = wacc(B['J'], B['W'], Tb); domb = accb.argmax(1)
cb = np.zeros(nb, int)
cb[LP['band']] = 1; cb[LP['lining']] = 2
legj = isj('Calf', 'Foot', 'Toe', 'Thigh'); armj = isj('Forearm', ' Hand', 'UpperArm')
# relief plates: greaves (front shin plates below the knee discs) and bracers (forearm, wrist to the plate's elbow end)
grv = isj('Calf')[domb] & (cenb[:, 1] > 0.2) & (cenb[:, 1] < 0.84) & (cenb[:, 2] > -0.02)
brc = forej[domb] & (np.abs(cenb[:, 0]) > 0.66)
cb[(grv | brc) & (cb == 0)] = 9
sz = np.bincount(bcomp)
buckle = np.unique(bcomp[(cenb[:, 2] > 0.33) & (cenb[:, 1] > 1.5) & (cenb[:, 1] < 1.7)])
small = (sz[bcomp] < 100) | np.isin(bcomp, buckle[sz[buckle] < 400])     # medallions, baldric pieces, knee discs; the ram buckle
cb[small] = 7
belt = (cenb[:, 1] > BELT0) & (cenb[:, 1] < BELT1) & ~armj[domb] & (np.abs(cenb[:, 0]) < 0.5)
cb[belt & ~LP['lining'] & ~small] = 8
cb[LP['rim']] = 3
cb[Vb[:, :, 1].min(1) < B['P'][:, 1].min() + SOLE] = 4
Th = H['T']; hcomp, wh = comps(H['P'], Th)
# seams: body vertices coincident with head-prim vertices (neck: head faces; wrists: hand faces)
handf = L['hand'][nb:nb + nh] > 0
from scipy.spatial import cKDTree
hv_neck = np.unique(H['T'][~handf]); hv_hand = np.unique(H['T'][handf])
dn = cKDTree(H['P'][hv_neck]).query(B['P'])[0]; dhh = cKDTree(H['P'][hv_hand]).query(B['P'])[0]
neck = grow(Tb, (dn[Tb] < 1e-4).any(1), wb, RING) & ~LP['lining']
# the MPFB hands are separate pieces pushed into the bracers (not welded): the bracer faces round each hand's open end
from collections import Counter
ec = Counter(tuple(sorted((a, c))) for t in wh[Th[handf]] for a, c in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])))
bnd = np.unique([v for k, n in ec.items() if n == 1 for v in k])
hpos = np.zeros((wh.max() + 1, 3)); hpos[wh] = H['P']
dwr = cKDTree(hpos[bnd]).query(cenb)[0]
wrist = (dwr < E('WRIST', '0.04')) & ~LP['lining']
cb[neck] = 5; cb[wrist] = 6
# ---- head prim
Th = H['T']; Vh = H['P'][Th]; cenh = Vh.mean(1); hcomp, wh = comps(H['P'], Th); acch = wacc(H['J'], H['W'], Th); domh = acch.argmax(1)
ch = np.full(nh, 12)
hsz = np.bincount(hcomp); shell = hcomp == np.argmax(hsz * (np.bincount(hcomp, weights=~handf) > 0))
charts = np.load(HERE / 'work' / 'head_charts.npy')
ax = np.abs(cenh[:, 0])
ear = shell & (ax > E('EARX', '0.105')) & (cenh[:, 1] > E('EARY0', '2.455')) & (cenh[:, 1] < E('EARY1', '2.635')) & \
    (cenh[:, 2] > E('EARZ0', '-0.135')) & (cenh[:, 2] < E('EARZ1', '0.035'))
face = shell & (charts == 32)
ch[face | ear] = 10
ch[shell & ~(face | ear) & grow(Th, face | ear, wh, 1)] = 13
loose = ~shell & ~handf
eyes = loose & np.isin(hcomp, [c for c in np.unique(hcomp[loose]) if np.abs(cenh[hcomp == c, 2]).min() > 0.05 and
                               cenh[hcomp == c, 1].max() < 2.6])
ch[loose] = 15; ch[eyes] = 11
dbh = cKDTree(B['P']).query(H['P'])[0]
seamh = grow(Th, (dbh[Th] < 1e-4).any(1) & ~handf, wh, RING, within=~handf)
ch[seamh & shell & (ch != 10)] = 14
ch[handf] = 16
ch[handf & fingj[domh]] = 17
gs = L['graft'][nb:nb + nh]
ch[handf & ((acch[:, forej].sum(1) > 1e-3) | ((gs > 0) & (gs < 1)))] = 18
ch[handf & grow(Th, (dbh[Th] < 1e-4).any(1) & handf, wh, RING, within=handf)] = 18
# ---- props
acomp, _ = comps(A['P'], A['T']); adom = np.array([jn[j] for j in wacc(A['J'], A['W'], A['T']).argmax(1)])
ca = np.where(adom == 'Xspear', 20, 21)
asz = np.bincount(acomp); Va = A['P'][A['T']]
shaft = (adom == 'Xspear') & (asz[acomp] == 360); blade = (adom == 'Xspear') & (asz[acomp] == 140)
assert shaft.sum() == 360 and blade.sum() == 140
ca[shaft] = 22; ca[blade] = 24
# the fist closes round the shaft only in the clips (grip_keys.py): distances in Standing 0.5 (one grip pose in every clip)
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
mdl = Model(Glb(str(HERE / 'before' / 'mm9_krohn.glb'))); pz = [p for p, _ in mdl.skinned_positions(mdl.world(mdl.sample('Standing', 0.5)))[:3]]
fingv = np.unique(H['T'][handf & (fingj[domh] | isj(' Hand')[domh]) & (cenh[:, 0] < 0)].ravel())   # right hand (true-handed: -x)
ftree = cKDTree(pz[1][fingv]); dgrip = np.full(len(A['T']), 9.0)
for f in np.flatnonzero(shaft):          # the shaft is a lathe of long sliver quads: sample each face, not its corners
    a_, b_, c_ = pz[2][A['T'][f]]; k = int(np.clip(max(np.linalg.norm(b_ - a_), np.linalg.norm(c_ - a_), np.linalg.norm(c_ - b_)) / 0.005, 1, 200))
    i_, j_ = np.meshgrid(np.arange(k + 1), np.arange(k + 1)); mm = i_ + j_ <= k
    w_ = np.stack([i_[mm], j_[mm], k - i_[mm] - j_[mm]], 1) / k; dgrip[f] = ftree.query(w_ @ pz[2][A['T'][f]])[0].min()
ca[shaft & (dgrip < E('SHAFTGRIP', '0.03'))] = 23
cls = np.concatenate([cb, ch, ca]); mat = np.concatenate([np.full(nb, 0), np.full(nh, 1), np.full(len(ca), 2)])
keep = np.isin(cls, (3, 4, 5, 6, 7, 8, 10, 11, 13, 14, 15, 17, 18, 20, 21, 23) + tuple(int(c) for c in os.environ.get('KEEPCLS', '').split(',') if c))
lining = np.concatenate([LP['lining'], np.zeros(nh + len(ca), bool)])
lined = np.concatenate([LP['band'], np.zeros(nh + len(ca), bool)])
keep[lining] = False
gmap = {0: 0, 1: 0, 16: 1, 12: 2, 9: 3, 22: 4, 24: 5}
group = np.array([gmap.get(int(c), 0) for c in cls]); group[keep | lining] = 0
names = {0: 'body rest', 1: 'band (lined)', 2: 'lining', 3: 'rim strip', 4: 'sole', 5: 'neck seam body', 6: 'wrist seam body',
         7: 'medallions/buckle', 8: 'belt band', 9: 'greaves+bracers', 10: 'face skin+ears', 11: 'eyes', 12: 'hair+beard',
         13: 'hairline', 14: 'neck seam head', 15: 'crown', 16: 'palm/back', 17: 'fingers', 18: 'wrist graft', 20: 'glaive head', 21: 'sword', 22: 'shaft', 23: 'shaft grip', 24: 'glaive blade'}
for c in np.unique(cls):
    m = cls == c; print(f'cls {c:2d} {names[c]:18s} {m.sum():5d} keep {int(keep[m].sum()):5d}')
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %), lining', int(lining.sum()), 'free', int((~keep & ~lining).sum()), 'of', len(cls))
print('groups free', {int(g): int(((group == g) & ~keep & ~lining).sum()) for g in np.unique(group)})
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=lining, lined=lined, cls=cls, mat=mat)
