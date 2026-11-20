#!/usr/bin/env python3
"""Keep / group sets per installed LOD0 face (work/glb_parts.npz order: Sigmund (body), SigmundHead) for mpqem.py ->
work/glb_sets_<tag>.npz (keep, group, lining, lined, pair, twin, cls, mat).
Head prim: the head shell (face + hair one shell), eyes, hair twin (hair_lining.py, 1.5 mm), MPFB hands. Body prim: mail hauberk,
gold collar, belt, arms with bracers, trousers, boots, rim linings (rim_lining.py: band linings 3 mm / 0.5 mm + rim strips).
Keep exactly (REDUCTION_AGENT_TOWNSFOLK relaxed set, face exact):
 20 skin: every head-shell UV island that is mostly skin by paint (the face chart with eyes, brows, mouth and forehead; ears;
    neck; nostrils), whole; in the hair islands every face painted skin (G/R < SKIN_GR) and its ring;
 22 hairline: hair faces within HAIREDGE m of a skin face;
 10 collar: body faces above COLLAR_Y painted gold (R-B > 40, R > 110) and their ring + body faces within NECK m of the head shell;
 11 belt: body faces with the centroid between BELT_Y0 and BELT_Y1 (strap, buckle, studs);
 12 soles; 13 faces within RIM m of a rim strip (every open rim: collar, sleeves, bracer ends, hem, boot tops) and round ambiguous
    twin vertices; 14 fingertips (distal finger faces within TIP m of the tip); 15 hand-graft junction (hand faces dominated by a
    Forearm joint); 16 connected pieces of up to SMALL faces; 30 rim strips and unpaired twins (added faces without an outer face).
Cut: 0 body cloth (the ladder ratio), 1 hands (MP_GROUPS), 2 hair, 3 boots, 4 arm skin + bracers, 5 trousers.
Linings (paired added faces) are re-emitted by mpqem.py from the twins of the surviving outer faces.
Usage: make_sets_sig.py <tag>  (env HAIREDGE, SKIN_GR, COLLAR_Y, NECK, BELT_Y0, BELT_Y1, SOLE, RIM, TIP, SMALL, KEEPCLS=cls,..
 (whole classes of the cut groups kept, e.g. 4 bracers), EXTRA=<npy>)"""
import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
tag = sys.argv[1]
E = lambda k, d: os.environ.get(k, d)
HAIREDGE = float(E('HAIREDGE', '0.012')); SKIN_GR = float(E('SKIN_GR', '0.66')); COLLAR_Y = float(E('COLLAR_Y', '1.30'))
NECK = float(E('NECK', '0.012')); BELT_Y0 = float(E('BELT_Y0', '1.025')); BELT_Y1 = float(E('BELT_Y1', '1.115'))
SOLE = float(E('SOLE', '0.012')); RIM = float(E('RIM', '0.01')); TIP = float(E('TIP', '0.006')); SMALL = int(E('SMALL', '40'))
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_sigmund.glb', 'Sigmund')
g = np.load(HERE / 'work' / 'glb_parts.npz'); jn = [str(x) for x in g['jnames']]; joint = g['joint']
PR = ['Sigmund', 'SigmundHead']
offs = g['voff']; foff = g['foff']
P = np.concatenate([D[k]['P'] for k in PR]); UV = np.concatenate([D[k]['UV'] for k in PR])
T = np.concatenate([D[k]['T'] + offs[i] for i, k in enumerate(PR)])
n = len(T); mat = g['mat']; head = g['head'].astype(bool); hand = g['hand'].astype(bool); added = g['added'].astype(bool)
lining = g['lining'].astype(bool); rim = g['rim'].astype(bool); outer = ~added
V = P[T]; cen = V.mean(1); floor = P[:, 1].min()
# paint per face (7 barycentric samples of the base colour)
B = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4], [1, 1, 0], [0, 1, 1], [1, 0, 1]], float); B /= B.sum(1, keepdims=True)
col = np.zeros((n, 3))
for k, name in enumerate(PR):
    im = np.asarray(Image.open(HERE / 'work' / f'tex_{name}_B.png').convert('RGB'), np.float64); H, W = im.shape[:2]
    sl = slice(foff[k], foff[k + 1]); uv = np.einsum('sk,fkd->fsd', B, UV[T[sl]])
    col[sl] = im[np.clip((uv[..., 1] * H).astype(int), 0, H - 1), np.clip((uv[..., 0] * W).astype(int), 0, W - 1)].mean(1)
gr = col[:, 1] / np.maximum(col[:, 0], 1)
_, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]
nw = w.max() + 1


def ring(m):
    vv = np.zeros(nw, bool); vv[FT[m].ravel()] = True
    return vv[FT].any(1)


def near(m, r):
    return cKDTree(P[np.unique(T[m])]).query(V.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r


cls = np.full(n, -1)
# head shell islands (by GLB vertex = UV island)
hs = outer & head & ~hand
f = np.flatnonzero(hs); r_ = np.r_[T[f, 0], T[f, 1], T[f, 2]]; c_ = np.r_[T[f, 1], T[f, 2], T[f, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(len(P), len(P))), directed=False)
isl = -np.ones(n, np.int64); isl[f] = lab[T[f, 0]]
skin = np.zeros(n, bool)
for L in np.unique(isl[f]):
    m = isl == L
    if (gr[m] < 0.68).mean() >= 0.8:
        skin |= m
# skin painted inside the hair islands, grown from the skin islands (GROW rings; isolated dark hair streaks stay hair)
for _ in range(int(E('GROW', '3'))):
    skin |= hs & ~skin & ring(skin & hs) & (gr < SKIN_GR)
hair = hs & ~skin
hairline = hair & near(skin, HAIREDGE)
cls[skin] = 20; cls[hairline] = 22; cls[hair & ~hairline] = 2
# hands
handj = np.array([any(t in x for t in (' Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Finger')) for x in jn])
hf = outer & hand
graft = hf & ~handj[joint]
tips = np.zeros(n, bool)
for x in range(len(jn)):
    if jn[x].endswith('3') and handj[x]:
        m = hf & (joint == x)
        if not m.any(): continue
        par = jn.index(jn[x][:-1] + '2')
        # the tip: the vertex farthest from the bone's parent joint region (the mean of the faces dominated by the middle segment)
        base = cen[hf & (joint == par)].mean(0) if (hf & (joint == par)).any() else cen[m].mean(0)
        vs = np.unique(T[m]); dv = np.linalg.norm(P[vs] - base, axis=1); tip = P[vs[dv.argmax()]]
        tips |= m & (np.linalg.norm(V - tip, axis=2).min(1) < TIP)
cls[hf] = 1; cls[graft] = 15; cls[tips] = 14
# body
bo = outer & ~head & ~hand
gold = (col[:, 0] - col[:, 2] > 40) & (col[:, 0] > 110)
collar = bo & (cen[:, 1] > COLLAR_Y) & gold
collar = (ring(collar) & bo & (cen[:, 1] > COLLAR_Y - 0.02)) | (bo & near(hs, NECK))
belt = bo & (cen[:, 1] > BELT_Y0) & (cen[:, 1] < BELT_Y1) & (np.abs(cen[:, 0]) < 0.22)
jname = np.array(jn)[joint]
boots = bo & np.array(['Calf' in x or 'Foot' in x or 'Toe' in x for x in jname]) & (cen[:, 1] < 0.27)
armj = np.array(['Forearm' in x or 'UpperArm' in x or ' Hand' in x for x in jname])
arms = bo & armj & (np.abs(cen[:, 0]) > 0.22)
trous = bo & np.array(['Thigh' in x or 'Calf' in x for x in jname]) & (cen[:, 1] < 0.86) & ~boots
cls[bo] = 0; cls[arms] = 4; cls[trous] = 5; cls[boots] = 3
sole = bo & (V[:, :, 1].min(1) < floor + SOLE)
cls[collar] = 10; cls[belt] = 11; cls[sole] = 12
rimnear = ~added & (near(rim, RIM) if rim.any() and RIM > 0 else np.zeros(n, bool))
amb = np.flatnonzero(g['ambig'])
ambn = np.isin(FT, w[amb]).any(1) & ~added if E('AMBKEEP', '0') == '1' else np.zeros(n, bool)
cls[rimnear | ambn] = 13
# ambiguous twin vertices (on the border of two rim_lining bands: two twins) are locked instead (mpqem MP lockpos)
lockpos = np.isin(w, w[amb])
# vertices (by position) on lined faces of two or more lining bands: locked, so each cut lined face keeps vertices of its own band
band = g['band']
bv = {}
for f in np.flatnonzero(band >= 0):
    for x in FT[f]:
        bv.setdefault(x, set()).add((mat[f], band[f]))
multi = np.array([x for x, b in bv.items() if len(b) > 1], np.int64)
lockpos |= np.isin(w, multi)
print('band-border positions locked', len(multi), 'ambiguous', len(amb))
# small pieces (outer faces)
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab2 = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nw, nw)), directed=False)
fl = lab2[FT[:, 0]]; cnt = np.bincount(fl[outer], minlength=lab2.max() + 1)
small = outer & (cnt[fl] <= SMALL) & (cls != 20)
cls[small] = 16
cls[rim] = 30; cls[lining] = 31
keep = np.isin(cls, (10, 11, 12, 13, 14, 15, 16, 20, 22, 30))
for x in E('KEEPCLS', '').split(','):
    if x: keep |= cls == int(x)
if E('EXTRA', ''):
    for x in E('EXTRA', '').split(','):
        ex = np.load(x); keep |= ex & ~lining; print('extra keep', x, int(ex.sum()))
group = np.where(np.isin(cls, (0, 1, 2, 3, 4, 5)), cls, 0)
group[keep] = 0
lined = g['lined'].astype(bool)
names = {0: 'body cloth', 1: 'hands', 2: 'hair', 3: 'boots', 4: 'arms+bracers', 5: 'trousers', 10: 'collar', 11: 'belt',
         12: 'soles', 13: 'rim/ambig near', 14: 'fingertips', 15: 'hand graft', 16: 'small pieces', 20: 'skin', 22: 'hairline',
         30: 'rim strips', 31: 'linings'}
for c in np.unique(cls):
    m = cls == c
    print(f'cls {c:2d} {names.get(int(c), "?"):16s} {int(m.sum()):5d} keep {int((m & keep).sum()):5d} lined {int((m & lined).sum()):5d}')
kl = keep & ~lining
pk = int(kl.sum()) + int((lined & keep).sum())
print('TOTAL keep', int(kl.sum()), f'({kl.mean() * 100:.1f} %)', '+ their linings', int((lined & keep).sum()), f'= protected {pk} ({pk / n * 100:.1f} %)',
      'free', int((~keep & ~lining).sum()), 'lining', int(lining.sum()), 'of', n)
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep & ~lining, group=group, lining=lining, lined=lined, pair=g['pair'],
         twin=g['twin'], cls=cls, mat=mat, lockpos=lockpos, band=band,
         **{k: g[k] for k in g.files if k.startswith('twinb')})
