"""Per-face labels of the welded source (work/mesh_in.npz): connected piece and region-mask channel at the face's UV
centroid (R skin, G face/horns/teeth, B iris; ../mm6_bh_claude/textures/bh_region_mask.png).
-> work/components.npy, work/mask_region.npy; prints the pieces."""
import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']; uv = d['wuv'].reshape(-1, 3, 2)
n = len(v); a = np.concatenate([f[:, 0], f[:, 1], f[:, 2]]); b = np.concatenate([f[:, 1], f[:, 2], f[:, 0]])
_, vc = connected_components(coo_matrix((np.ones(len(a)), (a, b)), shape=(n, n)), directed=False)
comp = vc[f[:, 0]]
m = np.asarray(Image.open('../mm6_bh_claude/textures/bh_region_mask.png').convert('RGB')).astype(float)
H, W = m.shape[:2]; c = uv.mean(1)
px = m[np.clip(((1 - c[:, 1]) * H).astype(int), 0, H - 1), np.clip((c[:, 0] * W).astype(int), 0, W - 1)]
reg = np.where(px.max(1) < 40, 3, px.argmax(1))  # 0 skin, 1 face, 2 iris, 3 none (painted pupil/mouth)
np.save('work/components.npy', comp); np.save('work/mask_region.npy', reg)
for k in np.unique(comp):
    s = comp == k; ctr = v[np.unique(f[s])].mean(0); lo = v[np.unique(f[s])].min(0); hi = v[np.unique(f[s])].max(0)
    print(f'piece {k}: {s.sum()} faces centre {np.round(ctr, 3)} size {np.round(hi - lo, 3)} regions',
          {r: int((reg[s] == r).sum()) for r in range(4)})
