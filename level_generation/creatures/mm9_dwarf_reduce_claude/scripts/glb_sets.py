#!/usr/bin/env python3
"""Sets for mpqem.py per GLB LOD0 face (work/mesh_in.npz keeps the GLB face order; checked in grip_contact.py):
keep = work/keep_<KEEP>.npy (make_sets.py + err_lock + extra_keep.py), group = work/groups_d.npy (1 beard, 2 helmet,
3 horns, 4 pants, 5 hands), lining/lined all False (every lined face is kept). Usage: glb_sets.py <keep npy> <tag>
-> work/glb_sets_<tag>.npz"""
import sys
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parents[1] / 'work'
keep = np.load(sys.argv[1]).astype(bool); group = np.load(W / 'groups_d.npy').astype(int); group[keep] = 0
z = np.zeros(len(keep), bool)
np.savez(W / f'glb_sets_{sys.argv[2]}.npz', keep=keep, group=group, lining=z, lined=z)
print('SETS', sys.argv[2], 'keep', int(keep.sum()), 'groups', np.bincount(group[~keep]))
