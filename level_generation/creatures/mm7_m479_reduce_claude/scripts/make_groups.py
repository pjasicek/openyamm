#!/usr/bin/env python3
"""Per-face region labels for the Treant ladder (work/groups_<set>.npy) and the exact-keep mask (work/keep_<set>.npy).
MM7 Treant (m479, faces -y, 4.0 m): 121 connected pieces (trunk skin, ~110 loose bark strands / limb ropes / root
tendrils, 19 peg teeth, two eyes). Source labels from the production master (work/master_pieces.npz: part 1/2 teeth,
3 eyes, piece 15 the lower lip).
Labels: 0 free (trunk and crown strands), 1 face front (mouth and eye zone around the kept mouth), 2 root skirt
(faces below 0.35 m, already halved by the production build), 3 teeth, 4 eyes, 5 crown (above 1.85 m outside the
trunk, the six limb sectors), 6 small pieces (SMALL_GROUP=1).
ROOTS_KEEP=1 keeps the whole root skirt.
Kept exactly: the mouth (every face touching Jaw/UpperLip weight > 0.02, the lower lip piece, and a 3 cm ring around
them), the floor contact faces (any vertex below 1 cm), small pieces up to KEEP_SMALL faces (twig tips; their ends
taper at any cut), and teeth/eyes unless their group is listed (env TEETH_GROUP=1, EYES_GROUP=1).
Usage: make_groups.py <set> [KEEP_SMALL]"""
import os
import sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree
name = sys.argv[1]; KEEP_SMALL = int(sys.argv[2]) if len(sys.argv) > 2 else 60
d = np.load('work/mesh_in.npz'); m = np.load('work/master_pieces.npz'); w = np.load('work/src_weights.npz')
v, f = d['verts'], d['faces']; names = list(w['names']); W = w['weights']
_, nn = cKDTree(m['co']).query(v); piece = m['piece'][nn]; part = m['part'][nn]
n = len(v); e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
_, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
pc = lab[f[:, 0]]; sizes = np.bincount(pc)
fc = v[f].mean(1); fpart = np.array([np.bincount(part[t], minlength=4).argmax() for t in f])
teeth = (fpart == 1) | (fpart == 2); eyes = fpart == 3
mouthw = W[f][:, :, [names.index('Jaw'), names.index('UpperLip')]].max((1, 2)) > 0.02
mouth = (mouthw | (piece[f] == 15).any(1)) & ~teeth
ring = np.zeros(len(f), bool)
mv = np.unique(f[mouth]); dd, _ = cKDTree(v[mv]).query(v); ring = (dd[f] < float(os.environ.get('MOUTH_RING', '0.03'))).any(1)
mouth |= ring & ~teeth & ~eyes
floor = v[f][:, :, 2].min(1) < 0.01
# bark around the eyes: the eyes sink (bone scale 0.05) in Standing, and a decimated socket vertex near them took eye
# weights (51 mm in Standing): keep a ring of EYE_RING m around them exactly
ev_ = np.unique(f[eyes]); de, _ = cKDTree(v[ev_]).query(v); mouth |= (de[f] < float(os.environ.get('EYE_RING', '0.04'))).any(1) & ~eyes & ~teeth
g = np.zeros(len(f), int)
r = np.hypot(fc[:, 0], fc[:, 1] + 0.1)
g[(fc[:, 2] > 1.85) & (r > 0.35)] = 5
g[(fc[:, 1] < -0.25) & (np.abs(fc[:, 0]) < 0.8) & (fc[:, 2] > 0.15) & (fc[:, 2] < 2.05)] = 1
g[fc[:, 2] < 0.35] = 2
g[teeth] = 3; g[eyes] = 4
small = (sizes[pc] <= KEEP_SMALL) & ~teeth & ~eyes
keep = mouth | floor | small
if os.environ.get('ROOTS_KEEP') == '1':  # the root skirt was already halved by the production build: any cut shortens tendrils
    keep |= (g == 2)
if os.environ.get('SMALL_GROUP') == '1':  # small pieces as their own group 6 instead of kept
    keep &= ~small | mouth | floor | (g == 2) & (os.environ.get('ROOTS_KEEP') == '1'); g[small & ~keep] = 6
if os.environ.get('TEETH_GROUP') != '1':
    keep |= teeth
if os.environ.get('EYES_GROUP') != '1':
    keep |= eyes
if os.environ.get('EXTRA_KEEP'):
    for p in os.environ['EXTRA_KEEP'].split(','):
        keep |= np.load(p)
np.save(f'work/groups_{name}.npy', g); np.save(f'work/keep_{name}.npy', keep)
print('SET', name, 'keep', int(keep.sum()), '(mouth', int(mouth.sum()), 'floor', int(floor.sum()), 'small', int(small.sum()),
      'teeth', int(teeth.sum()), 'eyes', int(eyes.sum()), ')',
      'groups (not kept)', {k: int(((g == k) & ~keep).sum()) for k in range(7)})
