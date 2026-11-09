#!/usr/bin/env python3
"""Keep / group / lining sets per installed LOD0 face (work/glb_labels.npz, label_glb.py) for mpqem.py, PeasantF4
(prio-2 townsfolk, relaxed keep set of REDUCTION_BRIEF_20261104).
Exact (kept): the whole head comp (face skin, eyes, ears, neck seam, the hidden skull: 3,612), F1's hidden old hood ('scarf', SCARF=1),
the hood's and sleeves' rim strips, the sleeve caps (inner faces without an outer twin), the bodice hole fills (job 8: faces not in
the asm), the soles (shoe faces within SOLE m of the floor), optionally the bodice's front placket column (PLACKET half width m) and its bright painted trims
(TRIM luminance threshold, TRIM_RINGS rings: the apron band across the back, the collar embroidery), connected pieces of up to SMALL faces.
Linings (hood4 and sleeve4 inner faces with an outer twin face) are not cut: mpqem.py re-emits them from the surviving lined outer
faces through the twin map (outer GLB vertex -> lining GLB vertex, from the asm's f4_twin_v).
Groups (own ratio in mpqem MP_GROUPS): 1 hands (dominant Hand / finger bone), 2 hood outer shell, 3 skirt, 4 sleeve tube outer,
5 F1's skirt lining (hidden in the skirt, its own mesh), 6 legs above the soles, 7 F1's short sleeves and shoulders (dress faces
on UpperArm / Clavicle), 8 the MPFB arm (non-hand faces); 0 = the rest of the dress (bodice).
Usage: make_sets_pf4.py <tag>   -> work/glb_sets_<tag>.npz"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as g  # noqa: E402
tag = sys.argv[1]
E = lambda k, d: os.environ.get(k, d)
SMALL = int(E('SMALL', '60')); SOLE = float(E('SOLE', '0.03'))
d, b = g.read(HERE / 'before' / 'mm9_peasantf4.glb')
node = next(n for n in d['nodes'] if n.get('name') == 'PeasantF4' and 'mesh' in n)
prims = g.prims(d, b, node['mesh'])
joints = [d['nodes'][j]['name'] for j in d['skins'][0]['joints']]
L = np.load(HERE / 'work' / 'glb_labels.npz'); names = [str(x) for x in L['names']]; K = names.index
A = np.load(HERE.parent / 'mm9_peasantf4_claude' / 'work' / 'asm_frozen.npz')
nv = [len(p['POSITION']) for p in prims]; voff = np.cumsum([0] + nv)
P = np.vstack([p['POSITION'] for p in prims]).astype(np.float64)
T = np.vstack([p['T'] + voff[k] for k, p in enumerate(prims)])
J = np.vstack([p['JOINTS_0'] for p in prims]); W = np.vstack([p['WEIGHTS_0'] for p in prims]).astype(np.float64)
comp, mat, fasm = L['comp'], L['mat'], L['fasm']
dom = np.array([joints[j] for j in J[np.arange(len(J)), W.argmax(1)]])
fd = dom[T]
FING = ('Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
handv = np.array([any(f in n for f in FING) for n in dom])
twin_face = np.where(fasm >= 0, A['f4_twin_face'][np.maximum(fasm, 0)], -1)
inner = L['inner']; rim = L['rim']
lining = inner & (twin_face >= 0)
cap = inner & (twin_face < 0)
keep = np.zeros(len(T), bool)
keep |= comp == K('head')
if E('SCARF', '1') == '1':
    keep |= comp == K('scarf')
keep |= rim | cap
keep |= fasm < 0                                                    # bodice hole fills (job 8)
if float(E('PLACKET', '0')) > 0:                                    # the bodice's front column (F1's lacing, painted plain and pressed)
    cen = P[T].mean(1); W_ = float(E('PLACKET', '0'))
    plk = (comp == K('dress')) & (np.abs(cen[:, 0]) < W_) & (cen[:, 2] > 0.03) & (cen[:, 1] > -0.05) & (cen[:, 1] < 0.45)
    keep |= plk; print('placket kept', int(plk.sum()))
if float(E('TRIM', '0')) > 0:                                       # painted cream trims on the bodice (the apron band across the back,
    from PIL import Image                                             # the collar embroidery): faces whose body tone is bright, + RINGS
    tone = np.asarray(Image.open(HERE / 'work' / 'tex_pf_body_tone.png').convert('L'), np.float64); th, tw = tone.shape
    UV = np.vstack([p['TEXCOORD_0'] for p in prims]).astype(np.float64)
    Bt = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4]], float); Bt /= Bt.sum(1, keepdims=True)
    su = np.einsum('sk,fkc->fsc', Bt, UV[T]); lum = tone[(su[..., 1] % 1 * th).astype(int), (su[..., 0] % 1 * tw).astype(int)].mean(1)
    trim = (comp == K('dress')) & (mat == 0) & (lum > float(E('TRIM', '0')))
    kp = np.round(P, 6); _, tv = np.unique(kp, axis=0, return_inverse=True); tv = tv.ravel(); TV = tv[T]
    for _ in range(int(E('TRIM_RINGS', '1'))):
        hot = np.zeros(tv.max() + 1, bool); hot[TV[trim].ravel()] = True; trim |= (comp == K('dress')) & hot[TV].any(1)
    keep |= trim; print('trims kept', int(trim.sum()))
floor = P[:, 1].min(); sole = (comp == K('legs')) & (P[T][:, :, 1].min(1) < floor + SOLE); keep |= sole
# connected pieces by welded position, per primitive
key = np.round(P, 6); _, wv = np.unique(np.c_[key, np.repeat(np.arange(len(prims)), nv)], axis=0, return_inverse=True); wv = wv.ravel()
FT = wv[T]; nW = wv.max() + 1
r_ = np.concatenate([FT[:, 0], FT[:, 1], FT[:, 2]]); c_ = np.concatenate([FT[:, 1], FT[:, 2], FT[:, 0]])
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(nW, nW)), directed=False)
fl = lab[FT[:, 0]]; cnt = np.bincount(fl)
small = (cnt[fl] <= SMALL) & ~lining & ~keep; keep |= small
for c in np.unique(comp):
    s = comp == c; sz = np.bincount(fl[s]); print(f'  {names[c]:8s} pieces {sorted(sz[sz > 0].tolist(), reverse=True)[:12]}')
# lined outer faces: twins of lining faces (asm face -> GLB face)
glb_of_asm = -np.ones(len(A['tri']), np.int64); glb_of_asm[fasm[fasm >= 0]] = np.flatnonzero(fasm >= 0)
lined = np.zeros(len(T), bool); tf_glb = glb_of_asm[twin_face[lining]]; assert (tf_glb >= 0).all(); lined[tf_glb] = True
# twin map per GLB vertex: outer corner -> lining corner (the lining vertex's asm twin is the outer corner's asm vertex)
vasm, vtwin = L['vasm'], L['vtwin']
twin = -np.ones(len(P), np.int64)
for lf, of in zip(np.flatnonzero(lining), tf_glb):
    for lv in T[lf]:
        oa = vtwin[lv]; hit = [ov for ov in T[of] if vasm[ov] == oa]
        assert len(hit) == 1, (lf, of)
        twin[hit[0]] = lv
print('twin map', int((twin >= 0).sum()), 'outer vertices; lining faces', int(lining.sum()), 'lined outer faces', int(lined.sum()))
groups = np.zeros(len(T), int)
hand_f = (comp == K('hands')) & handv[T].sum(1).astype(bool) & (handv[T].sum(1) >= 2)
groups[hand_f] = 1
groups[(comp == K('hands')) & ~hand_f] = 8                           # the MPFB arm (stub inside the short sleeve, forearm inside the bell)
groups[(comp == K('hood4')) & ~inner & ~rim] = 2
groups[comp == K('skirt')] = 3
groups[(comp == K('sleeve4')) & ~inner & ~rim] = 4
groups[comp == K('lining')] = 5
groups[comp == K('legs')] = 6
armd = np.array(['UpperArm' in n or 'Clavicle' in n for n in dom])
groups[(comp == K('dress')) & (armd[T].sum(1) >= 2)] = 7            # F1's short sleeves and shoulders
SLX = float(E('SLEEVEX', '0'))
if SLX > 0:                                                         # the short sleeves as sleeve_poke_pf1.py sees them (|x| > SLX): exact
    slv = (comp == K('dress')) & (np.abs(P[T][:, :, 0]) > SLX).all(1); keep |= slv; groups[slv] = 0
    print('short sleeves kept', int(slv.sum()))
groups[keep | lining] = 0

for c in np.unique(comp):
    s = comp == c
    print(f'{names[c]:8s} {s.sum():6d} keep {int((s & keep).sum()):5d} lining {int((s & lining).sum()):4d} lined {int((s & lined).sum()):4d} '
          f'free {int((s & ~keep & ~lining).sum()):5d} groups {dict(zip(*np.unique(groups[s & ~keep & ~lining], return_counts=True)))}')
print('soles', int(sole.sum()), 'small', int(small.sum()), 'caps', int(cap.sum()), 'rims', int(rim.sum()))
print('TOTAL keep', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'lining', int(lining.sum()), 'free', int((~keep & ~lining).sum()), 'of', len(T))
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep & ~lining, group=groups, lining=lining, lined=lined, twin=twin, comp=comp, mat=mat)
