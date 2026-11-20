"""Meshy piece id per vertex of work/uv_master.blend (fix_rig.py's split reordered the vertices): nearest raw
vertex at rest (raw shifted by the grounding offset). Writes work/piece_master.npy; the split Stalk3 eyeball keeps
piece 12."""
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
P = Path(__file__).resolve().parents[1]
raw = np.load(P / 'work/raw_st1.npz'); m = np.load(P / 'work/master_co.npz')
co = m['co']; shift = co[:, 2].min() - raw['co'][:, 2].min()
d, i = cKDTree(raw['co'] + [0, 0, shift]).query(co)
piece = raw['part'][i]
np.save(P / 'work/piece_master.npy', piece)
print('PIECES max match distance', float(d.max()), 'counts', np.bincount(piece)[:16].tolist())
