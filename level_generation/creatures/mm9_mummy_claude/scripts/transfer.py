"""Runtime body maps on layout L2 from the 4K paints on layout L1: colour per tier at 2K (rendered at 4K through the L1 UVs, downsampled once), normal per tier and ORM at 1K, AO at 2K.
Charts moved and turned, so normal XY is rotated per triangle by the L1->L2 UV rotation. Meshy normals are +y down; output is glTF +y up. Strip swatch in the reserved top band.
Args: <L2 npz (uv)>"""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ni
Image.MAX_IMAGE_PIXELS = None
L2 = np.load(sys.argv[1])['ub'].astype(np.float64).reshape(-1, 3, 2)             # M x 3 x 2, Blender v up
L1 = np.load('work/pack_in.npz')['uv'].astype(np.float64)
N = 4096
def to_px(uv): return np.c_[uv[..., 0].ravel() * N, (1 - uv[..., 1]).ravel() * N].reshape(-1, 3, 2)
a2, a1 = to_px(L2), to_px(L1)
mx = np.zeros((N, N), np.float32); my = np.zeros((N, N), np.float32); cov = np.zeros((N, N), bool); rc = np.ones((N, N), np.float32); rs = np.zeros((N, N), np.float32)
for i in range(len(a2)):
    a, b, c = a2[i]; p, q, r = a1[i]
    x0, x1 = max(int(min(a[0], b[0], c[0])) - 2, 0), min(int(max(a[0], b[0], c[0])) + 3, N)
    y0, y1 = max(int(min(a[1], b[1], c[1])) - 2, 0), min(int(max(a[1], b[1], c[1])) + 3, N)
    d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(d) < 1e-9 or x1 <= x0 or y1 <= y0: continue
    xs, ys = np.meshgrid(np.arange(x0, x1) + .5, np.arange(y0, y1) + .5)
    l0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / d
    l1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / d
    l2 = 1 - l0 - l1
    m = (l0 > -0.02) & (l1 > -0.02) & (l2 > -0.02)
    if not m.any(): continue
    Y, X = ys[m].astype(int), xs[m].astype(int)
    mx[Y, X] = l0[m] * p[0] + l1[m] * q[0] + l2[m] * r[0]; my[Y, X] = l0[m] * p[1] + l1[m] * q[1] + l2[m] * r[1]
    # rotation of the chart in image space: from the triangle's edges
    e2 = b - a; e1 = q - p
    ang = np.arctan2(e2[1], e2[0]) - np.arctan2(e1[1], e1[0])
    rc[Y, X] = np.cos(ang); rs[Y, X] = np.sin(ang); cov[Y, X] = True
print('coverage', cov.mean())
np.savez_compressed('work/l2_cov.npz', cov=cov[::2, ::2])
def pad(img):
    idx = ni.distance_transform_edt(~cov, return_distances=False, return_indices=True)
    return img[idx[0], idx[1]]
def sample(path, srgb=True):
    im = np.asarray(Image.open(path).convert('RGB'), np.float32)
    sc = 4096 / im.shape[0]
    return np.stack([ni.map_coordinates(im[..., c], [(my - .5) / sc, (mx - .5) / sc], order=1, mode='nearest') for c in range(3)], 2)
def down(a, size):
    return Image.fromarray(np.clip(a + .5, 0, 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)
ao = pad(sample('textures/ao_body_L1.png'))
Image.fromarray(np.clip(ao + .5, 0, 255).astype(np.uint8)).resize((2048, 2048), Image.LANCZOS).save('textures/mummy_ao.png')
rough = None
for t in 'ABC':
    J = Path(f'meshy/retexture_{t}')
    col = pad(sample(J / 'texture_urls_0_base_color.png'))
    down(col, 2048).save(f'textures/mummy_{t}_base_raw.png')
    n = sample(J / 'texture_urls_0_normal.png') / 255 * 2 - 1
    nx, ny = n[..., 0].copy(), -n[..., 1].copy()               # to +y up in UV space... image y is down, Meshy +y down means ny(image) = n1
    # rotate XY by the chart turn (image space angle, y down): work in image axes
    ix, iy = n[..., 0], n[..., 1]                              # Meshy: +y down = image axes
    jx = ix * rc - iy * rs; jy = ix * rs + iy * rc
    out = np.stack([jx, -jy, np.clip(n[..., 2], 0, 1)], 2)     # glTF: +y up
    out /= np.maximum(np.linalg.norm(out, axis=2, keepdims=True), 1e-6)
    nm = (out * .5 + .5) * 255
    nm = pad(nm); nm[~cov] = nm[~cov]
    down(nm, 1024).save(f'textures/mummy_{t}_normal_1k.png')
    if t == 'A':
        r = pad(sample(J / 'texture_urls_0_roughness.png'))
    r_ = pad(sample(J / 'texture_urls_0_roughness.png'))
    orm = np.stack([ao[..., 0], np.maximum(r_[..., 0], 0.55 * 255), np.zeros_like(ao[..., 0])], 2)
    down(orm, 1024).save(f'textures/mummy_{t}_orm_1k.png')
    print('tier', t, 'done')
