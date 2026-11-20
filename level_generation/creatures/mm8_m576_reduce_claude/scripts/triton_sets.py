"""Keep / protect / group sets for the Triton ladder from work/classes.npz.
keep exactly: left gripping hand + fingers (fitted trident grip, gates), eyes, the four thin harness straps and the
buckle (small separate pieces; strips go wavy at any cut), sole band (foot faces in the lowest 6 cm: sole gates).
protect (REA_PROTECT_FACES, decimated alone at REA_PROTECT_RATIO): head skin of the body piece.
groups: 1 crest/hair piece, 2 right hand + fingers, 3 collar, 4 pauldrons + shoulder guards; label 0 = the rest.
Usage: triton_sets.py <label>  -> work/keep_<label>.npy, work/prot_<label>.npy, work/groups_<label>.npy"""
import sys
import numpy as np
c = np.load('work/classes.npz', allow_pickle=True); piece, region, sole = c['piece'], c['region'], c['sole']
keep = (region == 'lhand') | np.isin(piece, [6, 7, 8, 9, 10, 12, 13]) | sole
prot = (region == 'head') & (piece == 0) & ~keep
groups = np.zeros(len(piece), int)
groups[piece == 11] = 1; groups[region == 'rhand'] = 2; groups[piece == 1] = 3; groups[np.isin(piece, [2, 3, 4, 5])] = 4
groups[keep | prot] = 0
lab = sys.argv[1]
np.save(f'work/keep_{lab}.npy', keep); np.save(f'work/prot_{lab}.npy', prot); np.save(f'work/groups_{lab}.npy', groups)
print('KEEP', int(keep.sum()), 'PROT', int(prot.sum()), 'GROUPS', {g: int((groups == g).sum()) for g in range(5)})
