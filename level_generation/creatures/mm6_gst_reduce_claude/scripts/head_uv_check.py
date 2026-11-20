"""Head UV layout check before the Meshy job: coverage, overlapping texels, skull vs hood texel density and a layout
image (texturing/head_uv_layout.png, skull orange, hood grey). Usage: head_uv_check.py"""
import numpy as np
from PIL import Image, ImageDraw
d = np.load('work/head_uv.npz'); uv, pos, skull = d['uv'], d['pos'], d['skull']; N = 1024
count = np.zeros((N, N), np.int32)
img = Image.new('RGB', (N, N)); dr = ImageDraw.Draw(img)
for t, s in zip(uv, skull):
    p = [(float(u * N), float((1 - v) * N)) for u, v in t]
    q = np.array(t) * N; lo = np.maximum(0, np.floor(q.min(0)).astype(int)); hi = np.minimum(N - 1, np.ceil(q.max(0)).astype(int))
    xx, yy = np.meshgrid(np.arange(lo[0], hi[0] + 1) + .5, np.arange(lo[1], hi[1] + 1) + .5)
    m = np.column_stack([q[1] - q[0], q[2] - q[0]])
    if abs(np.linalg.det(m)) > 1e-9:  # texel centres strictly inside (shared edges do not count)
        w = (np.stack([xx, yy], -1) - q[0]) @ np.linalg.inv(m).T
        count[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1] += (w[..., 0] > 1e-4) & (w[..., 1] > 1e-4) & (w.sum(-1) < .9999)
    dr.polygon(p, fill=(230, 140, 40) if s else (150, 150, 150), outline=(20, 20, 20))
img.save('texturing/head_uv_layout.png')
area3 = lambda q: np.linalg.norm(np.cross(q[:, 1] - q[:, 0], q[:, 2] - q[:, 0]), axis=1) / 2
area2 = lambda q: np.abs((q[:, 1, 0] - q[:, 0, 0]) * (q[:, 2, 1] - q[:, 0, 1]) - (q[:, 1, 1] - q[:, 0, 1]) * (q[:, 2, 0] - q[:, 0, 0])) / 2
dens = lambda m: np.sqrt(area2(uv[m]).sum() * N * N / (area3(pos[m]).sum() * 1e4))  # texels per cm
print('coverage', round(float((count > 0).mean()), 3), 'overlapping texels', int((count > 1).sum()),
      'skull texels/cm', round(float(dens(skull)), 2), 'hood texels/cm', round(float(dens(~skull)), 2))
