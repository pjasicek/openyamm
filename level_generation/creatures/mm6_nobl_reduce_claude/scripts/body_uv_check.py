"""Body UV layout check before the Meshy job: coverage, body/detail texel density (installed body for comparison),
layout image texturing/body_uv_layout.png (detail parts orange). Usage: body_uv_check.py"""
import numpy as np
from PIL import Image, ImageDraw
d = np.load('work/body_uv.npz'); keep = d['part'] == 0
uv, pos, det = d['uv'][keep], d['pos'][keep], d['detail'][keep]; N = 1024
img = Image.new('RGB', (N, N)); dr = ImageDraw.Draw(img)
for t, s in zip(uv, det):
    dr.polygon([(float(u * N), float((1 - v) * N)) for u, v in t], fill=(230, 140, 40) if s else (150, 150, 150))
img.save('texturing/body_uv_layout.png')
area3 = lambda p: np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1) / 2
area2 = lambda q: np.abs((q[:, 1, 0] - q[:, 0, 0]) * (q[:, 2, 1] - q[:, 0, 1]) - (q[:, 1, 1] - q[:, 0, 1]) * (q[:, 2, 0] - q[:, 0, 0])) / 2
dens = lambda q, p: np.sqrt(area2(q).sum() * N * N / (area3(p).sum() * 1e4))
s = np.load('work/mesh_in.npz'); w = s['wuv'].reshape(-1, 3, 2); b = w[:, :, 0].mean(1) < .5
old = w[b].copy(); old[..., 0] *= 2080 / 1024
print('coverage', round(float((np.asarray(img).sum(-1) > 0).mean()), 3), 'texels/cm body', round(dens(uv[~det], pos[~det]), 2),
      'detail', round(dens(uv[det], pos[det]), 2), 'installed body', round(dens(old, s['verts'][s['faces']][b]), 2))
