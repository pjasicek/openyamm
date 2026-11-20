"""Knight per-face groups for decimate_tex.py from regions (work/regions.npy) and components (work/comp.npy):
1 helmet (head-dominated faces), 2 left gauntlet, 3 right gauntlet (the two largest hand-dominated components), 4 cape
(component CAPE), 0 the rest. Components up to KEEP faces (knee cops, crest strips, rivets, small plates) are kept
exactly. Usage: make_groups.py <tag> [KEEP=80] [CAPE=9] -> work/groups_<tag>.npy, work/keep_<tag>.npy"""
import sys
import numpy as np
tag = sys.argv[1]; KEEP = int(sys.argv[2]) if len(sys.argv) > 2 else 80; CAPE = int(sys.argv[3]) if len(sys.argv) > 3 else 9
reg, comp = np.load('work/regions.npy'), np.load('work/comp.npy')
ids, cnt = np.unique(comp, return_counts=True); size = dict(zip(ids, cnt))
fs = np.array([size[c] for c in comp])
g = np.zeros(len(comp), int); g[reg == 1] = 1
# the two largest hand-dominated components (in the unreduced source the helmet is the largest piece)
dom = {c: np.bincount(reg[comp == c], minlength=4).argmax() for c in ids}
for c in [c for c in ids[np.argsort(-cnt)] if dom[c] in (2, 3)][:2]:
    g[comp == c] = dom[c]
g[comp == CAPE] = 4
keep = fs <= KEEP
np.save(f'work/groups_{tag}.npy', g); np.save(f'work/keep_{tag}.npy', keep)
print('GROUPS', {k: int(((g == k) & ~keep).sum()) for k in range(5)}, 'kept', int(keep.sum()))
