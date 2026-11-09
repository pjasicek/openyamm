#!/usr/bin/env python3
"""Clear mane-mask spill on the chest (islands of mask_islands.py: 14 chest faces below the beard at partial mask
that showed gold / green / red flecks in the chest crease, in the installed model too). Their UV triangles (1 px
dilation) are cleared in the region mask's red channel, except texels any mane face (mask > 0.5) also covers. The base
colour there holds gold hair strokes (tier A's mane colour), so those texels are filled from the surrounding grey skin
(diffusion fill from skin texels only). Usage: mask_fix.py -> work/region_mask_fixed.png,
work/basecolor_fixed.png"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
d = np.load('work/mesh_in.npz'); f = d['faces']; v = d['verts']; fm = np.load('work/mask_faces.npy')
c = v[f].mean(1)
# chest spill: partial-mask faces on the chest front, below the beard (z < 1.12) and inside the torso width
spill = (fm > .02) & (fm < .5) & (c[:, 2] < 1.12) & (c[:, 2] > .95) & (np.abs(c[:, 0]) < .15) & (c[:, 1] < 0) & (c[:, 1] > -.2)
img = Image.open('work/img3.png'); a = np.array(img); H, W = a.shape[:2]
uv = d['wuv'].reshape(-1, 3, 2)
def raster(faces):
    m = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(m)
    for t in uv[faces]:
        dr.polygon([((u % 1) * W, (1 - vv % 1) * H) for u, vv in t], fill=255)
    return np.asarray(m.filter(ImageFilter.MaxFilter(3))) > 0
clear = raster(np.where(spill)[0]) & ~raster(np.where(fm > .5)[0])
before = int((a[..., 0][clear] > 0).sum()); a[..., 0][clear] = 0
Image.fromarray(a).save('work/region_mask_fixed.png')
print('MASKFIX faces', int(spill.sum()), np.round(c[spill], 3).tolist(), 'texels cleared', before)

base = np.asarray(Image.open('work/img0.png').convert('RGB'), np.float32)
skin = raster(np.where(fm < .02)[0]) & ~clear   # fill only from skin texels (UV charts, not gutters or the mane)
known = ~clear; out = base.copy(); out[clear] = 0
ys, xs = np.where(clear); y0, y1, x0, x1 = ys.min() - 8, ys.max() + 9, xs.min() - 8, xs.max() + 9
sub, kn = out[y0:y1, x0:x1].copy(), skin[y0:y1, x0:x1].copy()
for _ in range(400):  # diffusion fill of the unknown texels from their known 4-neighbours
    pad = np.pad(sub, ((1, 1), (1, 1), (0, 0)), mode='edge'); pk = np.pad(kn, 1, mode='edge').astype(np.float32)
    acc = sum(np.roll(np.roll(pad * pk[..., None], dy, 0), dx, 1)[1:-1, 1:-1] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    cnt = sum(np.roll(np.roll(pk, dy, 0), dx, 1)[1:-1, 1:-1] for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    fill = ~kn & (cnt > 0); sub[fill] = acc[fill] / cnt[fill][:, None]; kn = kn | fill
    if kn[clear[y0:y1, x0:x1]].all():
        break
m = clear[y0:y1, x0:x1]
out[y0:y1, x0:x1][m] = sub[m]
Image.fromarray(out.astype(np.uint8)).save('work/basecolor_fixed.png')
print('BASEFIX texels filled', int(clear.sum()))
