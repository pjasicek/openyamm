"""Build REA_KEEP_FACES / REA_GROUPS arrays from work/labels.npz. Usage: make_config.py <name> <small max faces>
[keep_head 0/1] -> work/keep_<name>.npy, work/groups_<name>.npy (1 head set, 2 hands+fingers, 3 braid, 0 rest)."""
import sys, numpy as np
name, smax = sys.argv[1], int(sys.argv[2]); keep_head = len(sys.argv) > 3 and sys.argv[3] == '1'
L = np.load('work/labels.npz')
keep = L['size'] <= smax
if keep_head: keep |= L['headset'] & ~L['dark']
groups = np.zeros(len(keep), int)
groups[L['headset']] = 1; groups[L['hand']] = 2; groups[L['braid']] = 3
np.save(f'work/keep_{name}.npy', keep); np.save(f'work/groups_{name}.npy', groups)
print(name, 'keep', keep.sum(), {g: int(((groups == g) & ~keep).sum()) for g in range(4)})
