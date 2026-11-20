#!/usr/bin/env python3
"""Region labels per face of work/mesh_in.npz (dominant bone of the face's vertices): 1 head, 2 torso (Chest/Waist/
Neck), 3 arms (upper arm, forearm, hand), 4 rollers -> work/regions.npy."""
import numpy as np
d = np.load('work/mesh_in.npz'); g = np.load('work/groups.npz'); names = [str(n) for n in g['names']]; W = g['W']
fw = W[d['faces']].sum(1); dom = [names[i] for i in fw.argmax(1)]
lab = np.array([1 if n == 'Head' else 2 if n in ('Chest', 'Waist', 'Neck') else 3 if n.startswith(('UpperArm', 'Forearm', 'Hand')) else 4 if n.startswith('Roller') else 0 for n in dom])
np.save('work/regions.npy', lab); print('REGIONS', np.bincount(lab))
