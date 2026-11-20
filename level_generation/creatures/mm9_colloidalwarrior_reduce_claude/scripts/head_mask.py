"""Per-face head region mask sample (alpha = the head/body rim) at the face's UV centroid -> work/head_mask.npy (N x 4,
0-255, zeros for body faces). Run before head_classes.py (Blender's Python has no PIL)."""
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); wuv = d['wuv'].reshape(-1, 3, 2); mat = (wuv[:, 0, 0] // 2).astype(int)
m = np.array(Image.open('../mm9_colloidalwarrior_claude/textures/cw_head_region_mask.png').convert('RGBA'))
uv = wuv.mean(1); px = np.clip(((uv[:, 0] - 2) * m.shape[1]).astype(int), 0, m.shape[1] - 1)
py = np.clip(((1 - uv[:, 1]) * m.shape[0]).astype(int), 0, m.shape[0] - 1)
s = m[py, px].astype(np.uint8); s[mat != 1] = 0
np.save('work/head_mask.npy', s); print('MASK', int((s[:, 3] > 40).sum()), 'rim faces')
