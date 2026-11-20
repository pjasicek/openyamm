"""Per-face selections on the welded source mesh (work/mesh_in.npz) for the per-region ladder:
face = the head-set faces (atlas u > 0.505: face, lips, circlet); hair = body-set faces whose base colour is
hair red; gloves = hand/finger-dominated faces (work/regions.npy); small = connected components
of at most SMALL faces (studs, buckles, rings). -> work/face_keep.npy (bool), work/groups.npy (1 hair, 2 gloves),
work/small_keep.npy (bool); prints counts."""
import sys
import numpy as np
from PIL import Image
SMALL = int(sys.argv[1]) if len(sys.argv) > 1 else 80
d = np.load('work/mesh_in.npz'); faces, wuv = d['faces'], d['wuv'].reshape(-1, 3, 2)
img = np.asarray(Image.open('work/img0.png').convert('RGB'), np.float32) / 255
H, W = img.shape[:2]
def sample(uv):
    x = np.clip((uv[..., 0] % 1) * W, 0, W - 1).astype(int); y = np.clip((1 - uv[..., 1] % 1) * H, 0, H - 1).astype(int)
    return img[y, x]
cen = wuv.mean(1); print('u range', wuv[..., 0].min(), wuv[..., 0].max())
pts = np.concatenate([cen[:, None], (wuv * 2 + cen[:, None]) / 3], 1)  # centroid + three inner points
col = sample(pts)  # (F, 4, 3)
r, g, b = col[..., 0], col[..., 1], col[..., 2]
hairish = (r > 1.7 * g + 0.02) & (r > 1.4 * b)  # deep red hair; skin is orange (g/r ~0.6-0.75)
hair_vote = hairish.mean(1) > 0.5
head_set = cen[:, 0] % 1 > 0.505
face = head_set  # the head set holds only the face, lips and circlet (hair is on the body atlas)
hair = ~head_set & hair_vote
reg = np.load('work/regions.npy'); gloves = np.isin(reg, [2, 3]) & ~head_set
# connected components by shared vertices
parent = np.arange(len(d['verts']))
def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a
for f in faces:
    ra, rb, rc = find(f[0]), find(f[1]), find(f[2]); parent[rb] = ra; parent[find(rc)] = ra
comp = np.array([find(f[0]) for f in faces]); ids, cnt = np.unique(comp, return_counts=True)
size = dict(zip(ids, cnt)); csize = np.array([size[c] for c in comp])
small = (csize <= SMALL) & ~head_set
groups = np.zeros(len(faces), int); groups[hair] = 1; groups[gloves] = 2
np.save('work/face_keep.npy', face); np.save('work/groups.npy', groups); np.save('work/small_keep.npy', small)
print('FACES', len(faces), 'head set', head_set.sum(), 'face', face.sum(), 'hair', hair.sum(), 'gloves', gloves.sum(),
      'small', small.sum(), 'in', int((csize <= SMALL).sum() and len(set(comp[small]))), 'pieces;', 'components', len(ids),
      'largest', sorted(cnt)[-6:])
