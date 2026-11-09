#!/usr/bin/env python3
"""Sets for mpqem.py per GLB LOD0 face (work/mesh_in.npz keeps the GLB face order; checked in grip_contact.py):
(evil sorcerer fix pass: the dump order is the GLB face order, Up_A, Low_A, Head; checked) keep = <keep npy> (make_groups.py),
group = <groups npy> (1 neck guard, 2 crown, 3 palms, 6 plates), lining/lined all False (no linings).
Usage: glb_sets.py <keep npy> <tag> [groups npy, default work/groups_f.npy]
-> work/glb_sets_<tag>.npz"""
import sys
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parents[1] / 'work'
keep = np.load(sys.argv[1]).astype(bool); group = np.load(sys.argv[3] if len(sys.argv) > 3 else W / 'groups_f.npy').astype(int); group[keep] = 0
z = np.zeros(len(keep), bool)
np.savez(W / f'glb_sets_{sys.argv[2]}.npz', keep=keep, group=group, lining=z, lined=z)
print('SETS', sys.argv[2], 'keep', int(keep.sum()), 'groups', np.bincount(group[~keep]))
