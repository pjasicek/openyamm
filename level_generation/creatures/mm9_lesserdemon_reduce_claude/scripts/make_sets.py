#!/usr/bin/env python3
"""Keep set and groups per GLB face (LesserDemon primitive then LesserDemonHead) for mpqem.py, prio-1 relaxed set
(brief 2026-11-04; a non-human head's 'face' is eyes, mouth, teeth, tongue and horn roots).
Kept exactly: head face class 1 (snout, brows, lips, mouth cavity), horn roots (4), teeth/eyes/tongue (5); the neck seam
(head-shell faces within NECK of the body skin and body faces within NECK of the head shell); soles (body faces below SOLE);
small pieces of up to SMALL faces; every non-skin piece's contact faces (within CONTACT of another piece: talon roots in
the gauntlet flange, shard roots on the skirt shell, the tail's two pieces, spikes on the plates) and the holder faces
under them (HOLD).
Groups (MP_GROUPS ratios): 0 skin + armour (ladder ratio), 1 talons, 2 hand skin (Hand/Finger dominant), 3 larger small
pieces and the tail, 4 cranium (back of head), 5 horn shafts.
Usage: make_sets.py <tag>  (env NECK SOLE SMALL CONTACT HOLD EXTRA)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio
from class_render import render
E = lambda k, v: float(os.environ.get(k, v))
NECK, SOLE, SMALL, CONTACT, HOLD = E('NECK', '0.03'), E('SOLE', '0.05'), int(E('SMALL', '60')), E('CONTACT', '0.015'), E('HOLD', '0.0')
tag = sys.argv[1]
doc, b = bglbio.read(HERE / 'before' / 'mm9_lesserdemon.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'LesserDemon' and 'mesh' in n)
pr = bglbio.prims(doc, b, node['mesh']); jn = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
g = np.load(HERE / 'work' / 'glb_parts.npz'); hcls = np.load(HERE / 'work' / 'head_cls.npy')
B, Hd = pr
PB, TB = B['POSITION'].astype(np.float64), B['T']; PH, TH = Hd['POSITION'].astype(np.float64), Hd['T']
partB = g['part'][g['mat'] == 0]; compB = np.load(HERE / 'work' / 'comp_0.npy'); compH = np.load(HERE / 'work' / 'comp_1.npy')
CB, CH = PB[TB].mean(1), PH[TH].mean(1)
keepB = np.zeros(len(TB), bool); keepH = np.zeros(len(TH), bool)
grpB = np.zeros(len(TB), int); grpH = np.zeros(len(TH), int)
why = {}
def mark(arr, m, name): why[name] = int((m & ~arr).sum()); arr |= m
# head
mark(keepH, np.isin(hcls, [1, 4, 5]), 'head face/roots/small')
skinV = np.unique(TB[partB == 0]); dB = cKDTree(PB[skinV]).query(CH)[0]
mark(keepH, (hcls == 2) & (dB < NECK), 'head neck band')
grpH[hcls == 2] = 4; grpH[hcls == 3] = 5
# body
shellV = np.unique(TH[hcls != 5]); dH = cKDTree(PH[shellV]).query(CB)[0]
mark(keepB, dH < NECK, 'body neck band')
mark(keepB, PB[TB][:, :, 1].max(1) < SOLE, 'soles')
sizes = np.bincount(compB); main = sizes.argmax()
mark(keepB, sizes[compB] <= SMALL, 'small pieces')
# contact faces between pieces
cont = np.zeros(len(TB), bool); hold = np.zeros(len(TB), bool)
for c in np.unique(compB):
    if c == main: continue
    f = compB == c; vo = np.unique(TB[~f]); d = cKDTree(PB[vo]).query(CB[f])[0]
    cont[np.flatnonzero(f)[d < CONTACT]] = True
    if HOLD > 0:
        vs = np.unique(TB[f]); dh = cKDTree(PB[vs]).query(CB[~f])[0]; hold[np.flatnonzero(~f)[dh < HOLD]] = True
mark(keepB, cont, 'piece contact'); mark(keepB, hold, 'holder under pieces')
dom = np.array([jn[j] for j in B['JOINTS_0'][np.arange(len(PB)), B['WEIGHTS_0'].argmax(1)]])
handV = np.array(['Hand' in n or 'Finger' in n for n in dom])
print("hand faces by part", {int(p): int(((partB == p) & (handV[TB].sum(1) >= 2)).sum()) for p in np.unique(partB)})
grpB[partB == 5] = 1
grpB[np.isin(partB, [0, 1]) & (handV[TB].sum(1) >= 2)] = 2
grpB[(partB == 2) & (sizes[compB] > SMALL)] = 3; grpB[partB == 4] = 3
keep = np.concatenate([keepB, keepH])
if os.environ.get('EXTRA'):            # contact_lock.py: shoulder skin and arm-contact faces (gates of the first build)
    ex = np.load(os.environ['EXTRA']); why['extra (contact_lock)'] = int((ex & ~keep).sum()); keep |= ex
group = np.concatenate([grpB, grpH]); group[keep] = 0
n = len(keep)
np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', keep=keep, group=group, lining=np.zeros(n, bool), lined=np.zeros(n, bool), part=g['part'], mat=g['mat'])
print('SETS', tag, 'faces', n, 'kept', int(keep.sum()), f'({keep.mean() * 100:.1f} %)', 'by rule', why)
print('  free per group', {int(k): int(((group == k) & ~keep).sum()) for k in np.unique(group)})
cls = np.where(keep, 1, group + 2); cls[keep] = 1
P = np.vstack([PB, PH]); T = np.vstack([TB, TH + len(PB)])
render(P, T, cls, ['q34', 'back', 'side', 'below'], HERE / 'review' / f'sets_{tag}.png', size=600)
render(P, T, cls, ['q34', 'side', 'top'], HERE / 'review' / f'sets_{tag}_head.png', size=500, box=(np.array([-0.6, 1.6, 0.2]), np.array([0.6, 2.5, 1.1])))
