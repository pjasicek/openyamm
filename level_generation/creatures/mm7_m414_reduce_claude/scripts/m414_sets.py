#!/usr/bin/env python3
"""Keep set and region groups for the m414 Titan ladder (work/pieces.npy, soles.npy, gold.npy, visible_head.npy,
groups.npz).
Kept exactly: the eyes; both hands (every face touching a vertex with hand + finger weight > 0.3: the right fist holds
the sword with a solved grip); the sandal soles (faces below 6 cm); the painted gold lines (faces with >= 2 of 7
base-colour samples gold, M414_GOLD_MIN) on the helmet (trim), cheek and neck guards (rims), torso (shoulder edges,
collar), vambraces and greaves (lightning bolts) and the whole belt (lion; M414_BELT=0 lets its stone and blue faces
into group 8); the visible face front (head-set faces seen from some view, in front of y = M414_FRONT_Y); the crest's
top band (faces within M414_CREST_BAND of the crest's highest point per 10-degree sector about its fan centre: the
crest top is the model's top, 711 units at the binding scale). M414_KEEP_CREST=1 keeps the whole crest.
Groups (decimated on their own): 1 visible head sides (head set, not the face front), 2 hidden head skin (under the
helmet and guards), 3 helmet dome, 4 cheek and neck guard, 5 crest, 6 skirt tiers, 7 legs (greaves; kept apart from
the free cut), 8 belt (when not kept); label 0 (torso, arms) takes the ladder budget.
Usage: m414_sets.py <name> -> work/keep_<name>.npy, work/groups_<name>.npy"""
import os
import sys
import numpy as np
E = os.environ.get
d = np.load('work/mesh_in.npz'); f, v = d['faces'], d['verts']; c = v[f].mean(1)
p = np.load('work/pieces.npy'); soles = np.load('work/soles.npy'); gold = np.load('work/gold.npy')
seen = np.load('work/visible_head.npy')
g = np.load('work/groups.npz'); W = g['W']; names = list(g['names'])
hand = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n]].sum(1)
head = p == 1; vis = head & (seen > 0); front = vis & (c[:, 1] < float(E('M414_FRONT_Y', '-0.06')))
# M414_VIS_RINGS (default 2): head faces within this many vertex rings of a visible face count as visible
# sides (group 1, not the kept front; g85: the
# neck under the jaw beside the guards was labelled hidden at 6 pixels and creased at the hidden ratio)
for _ in range(int(E('M414_VIS_RINGS', '0'))):
    vv = np.zeros(len(v), bool); vv[f[vis]] = True; vis = head & vv[f].any(1)
isgold = gold >= float(E('M414_GOLD_MIN', '0.28'))
goldkeep = isgold & np.isin(p, [1, 2, 3, 4, 5, 7, 8, 9]) & ~(head & ~vis)
# crest top band: the fan's outline in the y-z plane about its lowest-centre point
cv = np.unique(f[p == 10]); ctr = np.array([v[cv, 1].mean(), v[cv, 2].min()])
ang = np.arctan2(v[:, 2] - ctr[1], v[:, 1] - ctr[0]); rad = np.hypot(v[:, 2] - ctr[1], v[:, 1] - ctr[0])
sec = ((ang + np.pi) / (2 * np.pi) * 36).astype(int) % 36
top = np.zeros(36)
np.maximum.at(top, sec[cv], rad[cv])
band = rad > top[sec] - float(E('M414_CREST_BAND', '0.02'))
crest_top = (p == 10) & band[f].any(1)
# M414_FACE_FEAT=1: keep only patches (M414_FEATURE_R, default 0.022 m) around the eyes, nose, mouth and chin of the
# face front; the rest of the front goes to group 9 (decimated on its own)
feat = np.zeros(len(f), bool)
for q in ((0.024, -0.13, 1.602), (-0.039, -0.13, 1.603), (-0.007, -0.163, 1.57), (-0.007, -0.151, 1.535),
          (-0.007, -0.145, 1.51)):
    feat |= head & (np.linalg.norm(v - np.array(q), axis=1) < float(E('M414_FEATURE_R', '0.022')))[f].any(1)
facekeep = (front & feat) if E('M414_FACE_FEAT') == '1' else front
# M414_GOLD_INNER=1: fully gold faces whose neighbours are all fully gold (broad gold: belt plates, sandal straps,
# greave bands) go into their region's cut; only the gold lines and borders stay kept
if E('M414_GOLD_INNER') == '1':
    goldkeep &= ~np.load('work/gold_inner.npy')
# helmet brim (m406 rule): helmet faces within M414_RIM_H (default 0.025 m) of the helmet's lowest point in their
# 15-degree azimuth sector about the helmet axis; the gold-sample test alone kept a zigzag of the trim band
hv = np.unique(f[p == 8]); axis = v[hv, :2].mean(0)
az = np.arctan2(*(v[:, :2] - axis).T[::-1]); sector = ((az + np.pi) / (2 * np.pi) * 24).astype(int) % 24
low = np.full(24, 9.0)
np.minimum.at(low, sector[hv], v[hv, 2])
rim = (p == 8) & (v[:, 2] < low[sector] + float(E('M414_RIM_H', '0.025')))[f].all(1)
keep = rim | (p == 11) | (hand[f] > 0.3).any(1) | soles | goldkeep | crest_top | facekeep
if E('M414_BELT', '1') == '1':
    keep |= p == 7
if E('M414_KEEP_CREST') == '1':
    keep |= p == 10
if E('M414_KEEP_HELMET') == '1':
    keep |= np.isin(p, [8, 9])
extra = E('M414_EXTRA_KEEP')  # e.g. a drift lock or patch set on top
if extra:
    for x in extra.split(','):
        keep |= np.load(x)
groups = np.zeros(len(f), int)
groups[vis & ~front] = 1; groups[head & ~vis] = 2
for lab, piece in ((3, 8), (4, 9), (5, 10), (6, 6), (7, 5), (8, 7)):
    groups[p == piece] = lab
groups[front & ~facekeep] = 9
groups[keep] = 0
name = sys.argv[1]; np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print('KEEP', int(keep.sum()), '(rim', int(rim.sum()), 'gold', int(goldkeep.sum()), 'front', int(front.sum()), 'crest top', int(crest_top.sum()),
      'hands', int((hand[f] > 0.3).any(1).sum()), ')', {k: int((groups == k).sum()) for k in range(10)})
