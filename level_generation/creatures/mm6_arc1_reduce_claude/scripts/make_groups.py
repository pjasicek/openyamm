"""Keep set and region groups for the Archer from work/components.npy and work/regions.npy (pieces.py,
region_faces.py). keep: face/neck skin (head region of the main body), eyes and mouth pieces, quiver arrows, bowstring
and tiny bits. groups: 1 hair, 2 hands, 3 bracers/pauldrons/cuffs; 0 body and quiver.
-> work/keep_<tag>.npy, work/groups_<tag>.npy. Usage: make_groups.py <tag>"""
import sys
import numpy as np

tag = sys.argv[1]
comp, reg = np.load('work/components.npy'), np.load('work/regions.npy')
HAIR, HANDS, SHELLS = [21], [1, 2], [15, 8, 16, 12, 10, 14]
FACE_PIECES = [22, 25, 24, 27, 23, 26]
ARROWS, STRING, BITS = [4, 9, 13, 11, 19, 17, 18], [20], [5, 6, 7]
keep = np.isin(comp, FACE_PIECES + ARROWS + STRING + BITS) | ((comp == 0) & (reg == 1))
groups = np.zeros(len(comp), int)
groups[np.isin(comp, HAIR)] = 1; groups[np.isin(comp, HANDS)] = 2; groups[np.isin(comp, SHELLS)] = 3
groups[keep] = 0
np.save(f'work/keep_{tag}.npy', keep); np.save(f'work/groups_{tag}.npy', groups)
print('KEEP', int(keep.sum()), 'GROUPS', {g: int((groups == g).sum()) for g in range(4)}, 'rest', int(((groups == 0) & ~keep).sum()))
