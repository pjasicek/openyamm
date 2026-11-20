#!/usr/bin/env python3
"""Sets for mpqem.py per GLB LOD0 face (work/mesh_in.npz keeps the GLB face order, checked by analyse.py) from
make_sets.py's work/sets.npz: keep = the s82 keep set (face set, claw tips, helper-heavy membrane, knuckles, plane face) plus the
whole body except the feet (s82 cut it at ratio 1); group 0 = wing front sheet (the ladder ratio), 1 hair, 3 feet;
lining = the wing back copies, lined = their front faces (mpqem cuts the front and re-emits the back from the twins).
Usage: glb_sets.py <tag> -> work/glb_sets_<tag>.npz"""
import sys
from pathlib import Path
import numpy as np
W = Path(__file__).resolve().parents[1] / 'work'
S = np.load(W / 'sets.npz')
keep = S['keep'].astype(bool) | (S['group'] == 0) & ~S['back']
group = np.where(S['group'] == 2, 0, S['group']); group[keep | S['back']] = 0
lining = S['back'].astype(bool); lined = np.zeros(len(keep), bool); lined[S['front_of'][lining]] = True
keep &= ~lining
np.savez(W / f'glb_sets_{sys.argv[1]}.npz', keep=keep, group=group, lining=lining, lined=lined, front_of=S['front_of'])
free = ~keep & ~lining
print('SETS', sys.argv[1], 'keep', int(keep.sum()), 'lining', int(lining.sum()), 'lined', int(lined.sum()),
      'free per group', {int(g): int((free & (group == g)).sum()) for g in np.unique(group[free])})
