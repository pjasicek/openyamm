#!/usr/bin/env python3
"""Set e = make_sets.py's set a + the belt (part 9: thin painted gold trims stepped under the cut) kept exactly."""
import numpy as np
part = np.load('work/face_part.npy'); k = np.load('work/keep_a.npy') | (part == 9); k &= ~np.load('work/drop_a.npy')
g = np.load('work/groups_a.npy').copy(); g[k] = 0
np.save('work/keep_e.npy', k); np.save('work/groups_e.npy', g); print('SET e keep', int(k.sum()))
