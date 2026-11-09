"""Front orthographic picture of the face built from the texels' rest positions (front-most texel per pixel), for
designing and checking the close-up fixes. Usage: face_ortho.py <basecolor png> <classes png> <out png> [scale px/m]"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
base_path, cls_path, out = sys.argv[1:4]
SC = float(sys.argv[4]) if len(sys.argv) > 4 else 3000
xyz = np.load(HERE / 'work' / 'texel_xyz2048.npy')
r = np.load(HERE / 'work' / 'approved_fine_raster2048.npz')
cov = r['tri_id'] >= 0
base = np.asarray(Image.open(base_path).convert('RGB').resize((2048, 2048)))
cls = np.asarray(Image.open(cls_path).resize((2048, 2048), Image.NEAREST))
X0, X1, Y0, Y1 = -0.07, 0.07, 1.38, 1.56
sel = cov & (xyz[..., 0] > X0) & (xyz[..., 0] < X1) & (xyz[..., 1] > Y0) & (xyz[..., 1] < Y1) & (xyz[..., 2] > 0.06)
p = xyz[sel]
W, H = int((X1 - X0) * SC), int((Y1 - Y0) * SC)
px = ((p[:, 0] - X0) * SC).astype(int).clip(0, W - 1)
py = ((Y1 - p[:, 1]) * SC).astype(int).clip(0, H - 1)
order = np.argsort(p[:, 2])                       # front-most written last
img = np.zeros((H, W, 3), np.uint8)
cimg = np.zeros((H, W, 3), np.uint8)
zimg = np.zeros((H, W), np.float32)
pal = {1: (240, 180, 150), 2: (255, 140, 0), 6: (0, 0, 255), 8: (60, 60, 60), 9: (255, 230, 0), 11: (0, 255, 255)}
cols = base[sel][order]
cl = cls[sel][order]
img[py[order], px[order]] = cols
cimg[py[order], px[order]] = np.array([pal.get(int(k), (255, 0, 0)) for k in cl], np.uint8)
zimg[py[order], px[order]] = p[order, 2]
filled = zimg > 0
from scipy import ndimage  # noqa: E402
_, (iy, ix) = ndimage.distance_transform_edt(~filled, return_indices=True)
near = ndimage.distance_transform_edt(~filled) <= 2
img = np.where(near[..., None], img[iy, ix], 0).astype(np.uint8)
cimg = np.where(near[..., None], cimg[iy, ix], 0).astype(np.uint8)
zimg = np.where(near, zimg[iy, ix], 0)
z = ((zimg - zimg[zimg > 0].min()) / np.ptp(zimg[zimg > 0]) * 255).clip(0, 255).astype(np.uint8) if (zimg > 0).any() \
    else zimg.astype(np.uint8)
sheet = Image.new('RGB', (W * 3, H))
sheet.paste(Image.fromarray(img), (0, 0))
sheet.paste(Image.fromarray(cimg), (W, 0))
sheet.paste(Image.fromarray(z).convert('RGB'), (2 * W, 0))
sheet.save(out)
print('ORTHO', out, sheet.size, f'x {X0}..{X1} y {Y1}..{Y0} at {SC} px/m')
