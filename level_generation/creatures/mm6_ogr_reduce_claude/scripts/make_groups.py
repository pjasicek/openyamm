"""Per-face groups for decimate_tex.py from regions (work/regions.npy) and components (work/comp.npy):
1 head, 2 left hand, 3 right hand, 4 armour pieces (separate components above KEEP faces: pauldrons, skull, horns,
bracers, shin wraps, belt, loin panels, harness), 0 the rest of the body. Components up to KEEP faces (spikes,
rivets, buckles, strap bits) are kept exactly. Usage: make_groups.py <tag> [KEEP=80] -> work/groups_<tag>.npy,
work/keep_<tag>.npy"""
import sys
import numpy as np
tag = sys.argv[1]; KEEP = int(sys.argv[2]) if len(sys.argv) > 2 else 80
reg, comp = np.load('work/regions.npy'), np.load('work/comp.npy')
ids, cnt = np.unique(comp, return_counts=True); size = dict(zip(ids, cnt)); main = ids[cnt.argmax()]
fs = np.array([size[c] for c in comp])
g = np.where(comp == main, reg, 4); keep = (comp != main) & (fs <= KEEP)
np.save(f'work/groups_{tag}.npy', g); np.save(f'work/keep_{tag}.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(5)}, 'kept', int(keep.sum()))
