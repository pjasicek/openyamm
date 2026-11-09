"""mep per-face keep mask and groups for decimate_tex.py (REA_KEEP_FACES / REA_GROUPS), from connected components of
the welded mesh (work/comp.npy), dominant-bone regions (work/regions.npy) and the head-set colour classes
(work/face_skin.npy, work/face_blue.npy, work/headset.npy). Components: 0 torso + head + turban cloth, 22 turban top,
23/24 eyes, 12 sash ends, 1 belt, the rest of size <= 22 buttons.
Usage: mep_regions.py <tag> <beard: keep|group>  -> work/keep_<tag>.npy, work/groups_<tag>.npy
keep: face skin + one ring, eyes, buttons (and the beard with 'keep').
groups: 1 hands, 2 turban (blue head-set faces), 3 beard (neutral head-set faces), 4 belt + sash, 0 rest."""
import sys
import numpy as np
tag, beard = sys.argv[1], sys.argv[2]
d = np.load('work/mesh_in.npz'); faces = d['faces']
lab = np.load('work/comp.npy'); reg = np.load('work/regions.npy'); cnt = np.bincount(lab)
sk, bl, hs = np.load('work/face_skin.npy'), np.load('work/face_blue.npy'), np.load('work/headset.npy')
skin = hs & (sk > .5); turban = hs & (bl > .5) & ~skin; neutral = hs & ~skin & ~turban
eyes = np.isin(lab, [23, 24]); small = cnt[lab] <= 22
vmask = np.zeros(len(d['verts']), bool); vmask[faces[skin].ravel()] = True
ring = vmask[faces].any(1)
keep = ring | eyes | small
if beard == 'keep':
    keep |= neutral
groups = np.zeros(len(lab), int)
groups[np.isin(reg, [2, 3])] = 1
groups[turban] = 2
groups[neutral] = 3
groups[np.isin(lab, [1, 12])] = 4
np.save(f'work/keep_{tag}.npy', keep); np.save(f'work/groups_{tag}.npy', groups)
print('KEEP', int(keep.sum()), '(skin', int(skin.sum()), 'ring', int((ring & ~skin).sum()), 'eyes', int(eyes.sum()),
      'small', int(small.sum()), ')', 'GROUPS', {g: int((groups[~keep] == g).sum()) for g in range(5)})
