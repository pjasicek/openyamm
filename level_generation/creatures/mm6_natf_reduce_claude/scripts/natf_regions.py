"""natf per-face keep mask and groups for decimate_tex.py (REA_KEEP_FACES / REA_GROUPS), from connected components of
the welded mesh (work/comp.npy) and dominant-bone regions (work/regions.npy). Components: 0 body + head skin,
hair and eyes found by size and height, others small worn pieces (teeth, fringe, belt, anklets, bracer).
Usage: natf_regions.py <tag> <small max faces>  -> work/keep_<tag>.npy, work/groups_<tag>.npy
groups: 1 hands, 2 hair, 3 mid pieces (small max < size <= 300), 0 rest (body shells, legs, skirt)."""
import sys
import numpy as np
tag, smax = sys.argv[1], int(sys.argv[2])
lab = np.load('work/comp.npy'); reg = np.load('work/regions.npy'); cnt = np.bincount(lab)
d = np.load('work/mesh_in.npz'); cz = d['verts'][d['faces']].mean(1)[:, 2]
zmin = np.array([cz[lab == c].min() for c in range(len(cnt))]); zmean = np.array([cz[lab == c].mean() for c in range(len(cnt))])
# hair: the two head-height parts of 200-320 faces; eyes: the two parts of 150-170 faces at eye height
hair = np.isin(lab, np.where((cnt >= 200) & (cnt <= 320) & (zmin > 1.38))[0])
eyes = np.isin(lab, np.where((cnt >= 150) & (cnt <= 170) & (zmean > 1.48) & (zmean < 1.54))[0])
face = (lab == 0) & (reg == 1)
small = (cnt[lab] <= smax) & ~hair & ~eyes
keep = face | eyes | small
groups = np.zeros(len(lab), int)
groups[(lab == 0) & np.isin(reg, [2, 3])] = 1
groups[hair] = 2
groups[(cnt[lab] > smax) & (cnt[lab] <= 300) & ~hair & ~eyes] = 3
np.save(f'work/keep_{tag}.npy', keep); np.save(f'work/groups_{tag}.npy', groups)
print('KEEP', int(keep.sum()), '(face', int(face.sum()), 'eyes', int(eyes.sum()), 'small', int(small.sum()), ')',
      'GROUPS', {g: int((groups[~keep] == g).sum()) for g in range(4)})
