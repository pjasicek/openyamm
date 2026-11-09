"""Face faces of the source (work/mesh_in.npz): head-atlas faces (u > 0.5) whose base colour at the centroid is skin
(not hair brown, hood green or choker gold, nor in the cloth region) and that sit above the choker (z > 1.416 m), plus one ring of neighbours.
-> work/face_faces.npy (bool per face); prints counts. Usage: python3 scripts/face_faces.py"""
import numpy as np
from PIL import Image
d = np.load('work/mesh_in.npz'); faces = d['faces']; w = d['wuv'].reshape(-1, 3, 2)
img = np.asarray(Image.open('work/dru1_basecolor_1k_head_atlas.png').convert('RGB')).astype(float) / 255
H, W = img.shape[:2]
def sample(uv):
    x = np.clip((uv[:, 0] * W).astype(int), 0, W - 1); y = np.clip(((1 - uv[:, 1]) * H).astype(int), 0, H - 1)
    return img[y, x]
pts = np.concatenate([w.mean(1)[:, None]] + [w[:, k:k + 1] * .6 + w.mean(1)[:, None] * .4 for k in range(3)], 1)
col = np.stack([sample(pts[:, k]) for k in range(4)], 1).mean(1)
r, g, b = col.T
skin = (r > .45) & (r > g * 1.12) & (g > b * 1.05) & (r - b > .15)
z = d['verts'][faces].mean(1)[:, 2]
mask = np.asarray(Image.open('work/dru1_region_mask_head_atlas.png').convert('RGBA')).astype(float) / 255
mk = (img, mask)[1]
def msample(uv):
    x = np.clip((uv[:, 0] * W).astype(int), 0, W - 1); y = np.clip(((1 - uv[:, 1]) * H).astype(int), 0, H - 1)
    return mask[y, x]
cloth = np.stack([msample(pts[:, k]) for k in range(4)], 1).mean(1)[:, 0] > .3  # hood lining (cloth region)
face = (w.mean(1)[:, 0] > .5) & skin & (z > 1.416) & ~cloth
ring = np.isin(faces, np.unique(faces[face])).any(1)
print('FACE', int(face.sum()), 'with ring', int(ring.sum()), 'head-atlas', int((w.mean(1)[:, 0] > .5).sum()))
np.save('work/face_faces.npy', ring)
