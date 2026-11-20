#!/usr/bin/env python3
"""Keep set and cut groups per face of the Ghost's runtime LOD0 (prio-1 relaxed keep set of the reduction brief) ->
work/sets_<label>.npz with keep_<material> and group_<material> per GLB face, and a share report.
Kept exactly: the whole head primitive (face skin, mouth, teeth, eye sockets; the hair dome is ~450 already coarse faces,
a 0.7 cut saves ~130 and steps its silhouette, so it stays), the collar bowl and every zero-UV face (dark patches), the
ornament region of the mask (belt knotwork and chest trims: thin painted bands), the hand/sleeve junction (faces within
JUNCTION_RINGS rings of a vertex shared by a hand face and a sleeve face), sleeve faces within CUFF_NEAR of a hand vertex
(the wrist sits inside the cuff), and pieces of up to SMALL faces.
Groups (cut on their own; borders stay): 0 jacket and sleeve cloth (ladder ratio), 1 hands (MP_GROUPS), 3 linen (shirt,
ruff, lace cuffs), 4 robe (finish_blend.py's own robe rule: chain-weighted faces and the XCENTER rows up to the belt), 5 sleeve and
shoulder cloth (Zarm*-dominant; at the ladder ratio the elbows and armpits erred 18-20 mm in Aware and Death, ladder A).
Usage: make_sets.py <label>   (env JUNCTION_RINGS=2 CUFF_NEAR=0.03 SMALL=60 KEEP_LINEN=0 ARM_GROUP=1 HAND_CONTACT=1 KEEP_TIPS=1)"""
import os, sys
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbpack as G, glbio  # noqa: E402
SRC = HERE.parent / 'mm9_ghost_claude' / 'export' / 'mm9_ghost_runtime_lod0.glb'
RINGS = int(os.environ.get('JUNCTION_RINGS', '2')); CUFF_NEAR = float(os.environ.get('CUFF_NEAR', '0.03'))
SMALL = int(os.environ.get('SMALL', '60')); KEEP_LINEN = os.environ.get('KEEP_LINEN', '0') == '1'
label = sys.argv[1]
d, b = G.read(SRC); b = bytes(b)
names = np.array([d['nodes'][j]['name'] for j in d['skins'][0]['joints']])
ishand = np.array([n.startswith('Finger') or n.startswith('Zhand') or n.startswith('Zfing') for n in names])
isrobe = np.array([n.startswith('Y') for n in names])
mask = np.asarray(Image.open(HERE / 'work' / 'img_ghost_region_mask.png'), np.float64)
prims = glbio.prims(d, b, 0)
handpts = np.concatenate([p['POSITION'][np.unique(p['T'][ishand[p['JOINTS_0'][np.arange(len(p['JOINTS_0'])), p['WEIGHTS_0'].argmax(1)]][p['T']].mean(1) > 0.5])]
                          for p in prims if p['material'] != 'GhostHead']).astype(np.float64)
htree = cKDTree(handpts)
out = {}; total = Counter()
for p in prims:
    name = p['material']; T = p['T']; P = p['POSITION'].astype(np.float64); UV = p['TEXCOORD_0'].astype(np.float64)
    nf = len(T)
    keep = np.zeros(nf, bool); group = np.zeros(nf, np.int64)
    if name == 'GhostHead':
        keep[:] = True
    else:
        J = p['JOINTS_0']; W = p['WEIGHTS_0'].astype(np.float64)
        dom = J[np.arange(len(J)), W.argmax(1)]
        fh = ishand[dom][T].mean(1) > 0.5
        zero = (UV[T].max(1) - UV[T].min(1)).max(1) < 1e-6
        # region per face: majority over centroid and corners pulled 25 % to the centroid
        H = mask.shape[0]; reg = np.zeros(nf, np.int64)
        votes = []
        for wgt in ([1 / 3, 1 / 3, 1 / 3], [.5, .25, .25], [.25, .5, .25], [.25, .25, .5]):
            uv = np.einsum('k,fkc->fc', np.array(wgt), UV[T])
            c = mask[np.clip((uv[:, 1] * H).astype(int), 0, H - 1), np.clip((uv[:, 0] * H).astype(int), 0, H - 1)]
            votes.append(c.argmax(1))
        votes = np.stack(votes, 1)
        reg = np.array([Counter(v).most_common(1)[0][0] for v in votes])
        orn = (votes == 1).any(1)                                   # any sample on the ornament: keep the band whole
        # finish_blend's robe rule
        vr = isrobe[dom]
        if vr.any():
            vr = vr | ((names[dom] == 'XCENTER') & (P[:, 1] < P[vr, 1].max() + 0.075))
        robe = vr[T].mean(1) > 0.6
        # finish_blend.py takes the XCENTER rows up to 7.5 cm above the highest chain-weighted vertex left in the buffer:
        # keep the faces on that vertex, or a cut moves the threshold and drops the lining under the top rows (8 faces)
        top = np.zeros(nf, bool)
        if isrobe[dom].any():
            ch = np.flatnonzero(isrobe[dom]); vtop = ch[P[ch, 1] >= P[ch, 1].max() - 1e-6]
            top = np.isin(T, vtop).any(1)
        # topology by position
        _, tp = np.unique(np.round(P, 6), axis=0, return_inverse=True); tp = tp.reshape(-1)
        TF = tp[T]
        vf = [[] for _ in range(tp.max() + 1)]
        for f, t in enumerate(TF):
            for v in t:
                vf[v].append(f)
        hv = np.zeros(tp.max() + 1, bool); hv[TF[fh].ravel()] = True
        sv = np.zeros(tp.max() + 1, bool); sv[TF[~fh].ravel()] = True
        ring = hv & sv
        junction = np.zeros(nf, bool)
        for _ in range(RINGS):
            fs = np.unique([f for v in np.flatnonzero(ring) for f in vf[v]]).astype(int)
            junction[fs] = True
            ring = np.zeros_like(ring); ring[TF[junction].ravel()] = True
        cuff = (~fh) & (htree.query(P[T].reshape(-1, 3))[0].reshape(-1, 3).min(1) < CUFF_NEAR)
        # small pieces
        parent = np.arange(tp.max() + 1)
        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]; a = parent[a]
            return a
        for t in TF:
            ra, rb, rc = find(t[0]), find(t[1]), find(t[2]); parent[rb] = ra; parent[find(rc)] = ra
        comp = np.array([find(t[0]) for t in TF]); cc = Counter(comp)
        small = np.array([cc[c] <= SMALL for c in comp])
        keep = zero | orn | junction | cuff | small | top
        tips = np.zeros(nf, bool)
        if os.environ.get('KEEP_TIPS', '1') == '1':          # distal finger and thumb segments: Dr45 cut the thumb tips to 36-50 %
            istip = np.array([n.startswith('Finger') and n.endswith('3') for n in names])   # and the left fingertips read 2.5 cm inside
            tips = istip[dom][T].mean(1) > 0.5                                           # the coarse right thumb (AttackMelee)
            keep |= tips
        hc = np.zeros(nf, bool)
        if os.environ.get('HAND_CONTACT', '1') == '1':      # hand_contact.py: body faces a hand comes within 4 cm of, hand faces near the other hand
            hc = np.load(HERE / 'work' / 'hand_contact.npz')[name]
            keep |= hc
        if KEEP_LINEN:
            keep |= reg == 2
        group[:] = 0
        group[(reg == 2)] = 3
        group[fh] = 1
        if os.environ.get('ARM_GROUP', '1') == '1':
            isarm = np.array([n.startswith('Zarm') for n in names])
            group[(isarm[dom][T].mean(1) > 0.5) & (reg != 2) & ~fh] = 5
        group[robe] = 4
        for k, v in (('zero', zero), ('ornament', orn), ('junction', junction), ('cuff', cuff & ~junction), ('small', small), ('robe top', top), ('hand contact', hc), ('fingertips', tips)):
            total[(name, 'keep ' + k)] += int(v.sum())
        total[(name, 'small pieces')] = len([c for c in cc if cc[c] <= SMALL])
        for g in (0, 1, 3, 4, 5):
            total[(name, f'free group {g}')] += int(((group == g) & ~keep).sum())
    total[(name, 'faces')] = nf; total[(name, 'kept')] = int(keep.sum())
    out['keep_' + name] = keep; out['group_' + name] = group
np.savez(HERE / 'work' / f'sets_{label}.npz', **out)
for k, v in total.items():
    print('SET', *k, v)
nk = sum(v for (m, k), v in total.items() if k == 'kept'); nt = sum(v for (m, k), v in total.items() if k == 'faces')
print(f'KEPT {nk} of {nt} pre-lining faces ({100 * nk / nt:.1f} %)')
