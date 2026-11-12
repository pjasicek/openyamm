"""PartUV study: per-head tile layouts (each head unwrapped and packed into its own square, as the Hydra's heads are
painted one Meshy job per head) placed back into the heads set's grid of tiles (Hydra: 3 x 2 tiles of 512 in a
1536 x 1024 image).

  partuv_compose_tiles.py <heads mesh.npz> <cols> <rows> <out.npz> <k>=<tile uv.npz> [...]
Faces of the heads set are assigned to tile k = column + cols * row by the centre of their current UVs (the rule of
partuv_split_sets.py box sets, which keep the face order); the tile's UVs (0..1) go to that tile's cell.
"""
import sys

import numpy as np

mesh_path, cols, rows, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
tiles = dict(a.split('=', 1) for a in sys.argv[5:])
centre = np.load(mesh_path)['uv'].mean(1)
col = np.minimum((centre[:, 0] * cols).astype(int), cols - 1)
row = np.minimum((centre[:, 1] * rows).astype(int), rows - 1)
tile = col + cols * row
uv = np.full((len(centre), 3, 2), np.nan)
for k, path in tiles.items():
    k = int(k)
    faces = np.nonzero(tile == k)[0]
    t = np.load(path)['uv']
    assert len(t) == len(faces), (k, len(t), len(faces))
    uv[faces, :, 0] = (k % cols + t[..., 0]) / cols
    uv[faces, :, 1] = (k // cols + t[..., 1]) / rows
assert not np.isnan(uv).any(), 'faces without a tile'
np.savez(out, uv=uv)
print('COMPOSED', out)
