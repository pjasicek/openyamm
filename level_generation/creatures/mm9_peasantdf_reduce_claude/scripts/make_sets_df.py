#!/usr/bin/env python3
"""Keep / group sets per DF1 LOD0 face (body primitive PeasantDF_A, then head primitive PeasantDFHead_A) for mpqem_df.py:
work/glb_sets_<tag>.npz (keep, group, lining, lined, part). The body and hands are byte-identical in all four designs
(design_map.py), so this one cut is applied to every design; the head primitive apart from the hands stays exact per design.
Parts: body 0 dress/torso, 1 skirt (dominant skirt-chain joint Bone*), 2 boots, 3 stockings, 4 forearms, 5 small pieces,
9 twins; head 10 head skin (face, neck, eyes), 11 hair/hood shell + twin, 12 ears, 13 hands, 14 braids (DF3 only).
Keep exactly (REDUCTION_BRIEF_20261104, relaxed set for prio-2 townsfolk, face exact; task: heads exact):
- the whole head primitive apart from the hands (face skin, neck seam, ears, hair/hood shell and its twin);
- the neck/collar: body faces within NECK m of a head-skin vertex (the r6/job7 neck paint field and the seam ring);
- under the headwear: body faces within HW m of a hair/hood/braid vertex of ANY design (each design's shell clearance);
- the hand-graft junction: forearm faces within GRAFT m of a hand vertex; soles: boot faces below floor + SOLE;
- pieces of up to SMALL faces; the design-specific one-texel face (6310); the 46 skirt twins without an exact outer partner
  (emitted as installed) and every outer face within TWINLOCK m of them;
- optional SLEEVE (m): dress faces mostly weighted to an upper arm (the puffed sleeves).
Twins (twin_faces.py back-side copies, df_parts.py): role 2 faces are dropped and re-emitted from the surviving lined (role 1)
outer faces through the exact vertex map. Groups: 1 hands (MP_SEAM_GROUPS), 2 skirt, 3 boots, 4 stockings, 5 forearms,
0 dress (the ladder ratio). Usage: make_sets_df.py <tag>"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
tag = sys.argv[1]
E = lambda k, d: float(os.environ.get(k, d))
NECK, HW, GRAFT, SOLE, TWINLOCK = E('NECK', '0.03'), E('HW', '0.02'), E('GRAFT', '0.015'), E('SOLE', '0.012'), E('TWINLOCK', '0.015')
SMALL = int(E('SMALL', '80')); SLEEVE = E('SLEEVE', '0')
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantdf1.glb', 'PeasantDF')
jn = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
pp = np.load(HERE / 'work' / 'df_parts_1.npz'); dm = np.load(HERE / 'work' / 'design_map.npz')
B, H = D['PeasantDF_A'], D['PeasantDFHead_A']
role, comp = pp['role0'], pp['comp0']; hcomp = pp['comp1']
Vb = B['P'][B['T']]; Vh = H['P'][H['T']]
# ---- head primitive parts (DF1 component ids from df_parts.py)
hsize = np.bincount(hcomp)
hpart = np.full(len(H['T']), 11)
big = np.argsort(-hsize)
skin_c = [c for c in range(len(hsize)) if hsize[c] == 2081][0]
hpart[hcomp == skin_c] = 10
for c in range(len(hsize)):
    if hsize[c] == 832: hpart[hcomp == c] = 12
    if hsize[c] == 700: hpart[hcomp == c] = 13
print('head parts', {int(k): int((hpart == k).sum()) for k in np.unique(hpart)})
# hands are identical in every design (exact vertex map)
for n in '234':
    m = dm[f'map_{n}_1']; assert (m[np.unique(H['T'][hpart == 13])] >= 0).all() and dm[f'same_{n}_1'][hpart == 13].all(), n
# ---- body parts
dj = np.array([jn[j] for j in B['J'][B['T'][:, 0], 0]])
part = np.zeros(len(B['T']), int)
csize = np.bincount(comp)
torso = comp == np.argmax(csize)
skirtj = np.char.startswith(dj.astype(str), 'Bone')
part[torso & skirtj] = 1
for c in range(len(csize)):
    m = comp == c
    if c == np.argmax(csize) or not m.any(): continue
    cy = Vb[m][:, :, 1].mean()
    if (role[m] == 2).all() or (role[m] == 2).mean() > 0.9 or (csize[c] in (1257,)): part[m] = 9
    elif csize[c] <= SMALL: part[m] = 5
    elif cy < 0.1: part[m] = 2
    elif cy < 0.3: part[m] = 3
    else: part[m] = 4
part[role == 2] = 9
print('body parts', {int(k): int((part == k).sum()) for k in np.unique(part)})
# ---- keep
floor = B['P'][:, 1].min()
nearb = lambda pts, r: cKDTree(pts).query(Vb.reshape(-1, 3))[0].reshape(-1, 3).min(1) < r
skinv = H['P'][np.unique(H['T'][hpart == 10])]
hairpts = [H['P'][np.unique(H['T'][hpart == 11])]]
for n in '234':
    _, _, _, Dn = glbio.load(HERE / 'before' / f'mm9_peasantdf{n}.glb', 'PeasantDF')
    Hn = list(Dn.values())[1]; mm = dm[f'map_{n}_1']
    own = np.setdiff1d(np.arange(len(Hn['P'])), mm[mm >= 0])        # vertices not shared with DF1: shells, braids
    hairpts.append(Hn['P'][own])
hairpts = np.concatenate(hairpts)
handv = H['P'][np.unique(H['T'][hpart == 13])]
neck = (part != 9) & nearb(skinv, NECK)
under = (part != 9) & nearb(hairpts, HW)
graft = (part == 4) & nearb(handv, GRAFT)
sole = (part == 2) & (Vb[:, :, 1].min(1) < floor + SOLE)
small = part == 5
untw = (part == 9) & (role != 2)
odd = np.zeros(len(B['T']), bool); odd[6310] = True
twl = (part != 9) & nearb(B['P'][np.unique(B['T'][untw & ~odd])], TWINLOCK)
keep = neck | under | graft | sole | small | untw | odd | twl
sleeve = np.zeros(len(B['T']), bool)
if SLEEVE > 0:
    ua = np.array(['UpperArm' in x for x in jn])
    wua = (B['W'] * ua[B['J']]).sum(1)
    sleeve = (part == 0) & (wua[B['T']].mean(1) > SLEEVE); keep |= sleeve
for k, v in dict(neck=neck, under_headwear=under, graft=graft, sole=sole, small=small, untwinned=untw, twinlock=twl, sleeve=sleeve).items():
    print(f'  keep {k:15s} {int(v.sum()):5d} (new {int((v & ~(keep & ~v)).sum())})')
group = np.zeros(len(B['T']), int)
group[part == 1] = 2; group[part == 2] = 3; group[part == 3] = 4; group[part == 4] = 5
# set b+: shoulders (dress faces whose corners carry UpperArm + Clavicle weight > SHOULDER on average) -> group 6, and the
# neck-weighted upper back/chest (Neck weight > NECKW) -> group 7: the worst deviations of the first ladders (AttackMelee, Hit)
SHOULDER = E('SHOULDER', '0'); NECKW = E('NECKW', '0')
if SHOULDER > 0:
    sj = np.array([('UpperArm' in x) or ('Clavicle' in x) for x in jn])
    ws = (B['W'] * sj[B['J']]).sum(1)[B['T']].mean(1); group[(part == 0) & (ws > SHOULDER)] = 6
if NECKW > 0:
    nj = np.array([x.endswith('Neck') for x in jn])
    wn = (B['W'] * nj[B['J']]).sum(1)[B['T']].mean(1); group[(part == 0) & (group == 0) & (wn > NECKW)] = 7
print('groups (free)', {int(k): int(((group == k) & ~keep).sum()) for k in np.unique(group)})
lining = (role == 2) & ~keep
lined = (role == 1)
group[keep | lining] = 0
# ---- head primitive: keep all but the hands
hkeep = hpart != 13; hgroup = np.where(hpart == 13, 1, 0)
allpart = np.r_[part, hpart]; K = np.r_[keep, hkeep]; G = np.r_[group, hgroup]
L = np.r_[lining, np.zeros(len(hpart), bool)]; LD = np.r_[lined, np.zeros(len(hpart), bool)]
names = {0: 'dress', 1: 'skirt', 2: 'boots', 3: 'stockings', 4: 'forearms', 5: 'small', 9: 'twins', 10: 'head skin', 11: 'hair+twin',
         12: 'ears', 13: 'hands'}
for p_ in np.unique(allpart):
    s = allpart == p_
    print(f'part {p_:2d} {names[p_]:10s} {s.sum():5d} keep {int((s & K).sum()):5d} free {int((s & ~K & ~L).sum()):5d} lining {int((s & L).sum()):5d}')
prot = K.sum()
print(f'TOTAL {len(K)}: kept {prot} ({prot / len(K) * 100:.1f} %), twins to re-emit {int(L.sum())}, free {int((~K & ~L).sum())}')
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=K, group=G, lining=L, lined=LD, part=allpart)
