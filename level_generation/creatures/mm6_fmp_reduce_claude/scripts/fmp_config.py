"""REA_KEEP_FACES / REA_GROUPS arrays for PeasantF2 from work/comp.npy, work/dom.npy and the head-set UVs (u > 0.5).
Kept: small pieces (<= 80 faces: lashes, teeth), the eyeballs (pieces 14, 15) and the face/neck skin of the head set;
with keep_head=1 the whole head set (hair, cap, ponytail too). Groups: 1 hair and cap pieces, 2 hands (whole hand
pieces), 3 feet, 4 skirt-weighted faces (skirt_group=1), 0 rest (torso, arms, bodice, apron).
Usage: fmp_config.py <name> [skirt_group 0/1] [keep_head 0/1] -> work/keep_<name>.npy, work/groups_<name>.npy"""
import sys, numpy as np
name = sys.argv[1]; skirt_group = len(sys.argv) > 2 and sys.argv[2] == '1'
keep_head = len(sys.argv) > 3 and sys.argv[3] == '1'
d = np.load('work/mesh_in.npz'); comp = np.load('work/comp.npy'); dom = np.load('work/dom.npy')
head = d['wuv'].reshape(-1, 3, 2).mean(1)[:, 0] > 0.5
size = np.bincount(comp)[comp]
keep = (size <= 80) | (head & np.isin(comp, [0, 14, 15]))  # face skin, eyes
if keep_head:
    keep |= head
groups = np.zeros(len(comp), int)
groups[head & (comp != 0)] = 1
groups[np.isin(comp, [2, 3])] = 2
groups[np.isin(comp, [4, 5])] = 3
if skirt_group:
    groups[np.array([n.startswith('Skirt') for n in dom]) & (groups == 0)] = 4
np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print(name, 'keep', int(keep.sum()), {g: int(((groups == g) & ~keep).sum()) for g in range(5)})
