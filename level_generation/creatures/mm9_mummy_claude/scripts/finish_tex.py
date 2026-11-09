#!/usr/bin/env python3
"""After the grade: strip swatch into its rectangle of each tier's 2K body colour; head colour grade, head normal from the paint's luminance, head ORM. Args: none (project folder)."""
import numpy as np
from PIL import Image
from scipy import ndimage as ni
U = np.load('work/uv_final.npz'); r = U['rect']
sw = np.asarray(Image.open('references_hd/strip_swatch.png').convert('RGB'), np.float32)
S = 2048
ys, xs = np.mgrid[0:S, 0:S]; px = np.stack([(xs + .5) / S, 1 - (ys + .5) / S], 2)
e1, e2 = r[1] - r[0], r[3] - r[0]
M = np.linalg.inv(np.c_[e1, e2]); q = (px - r[0]) @ M.T
ins = (q[..., 0] > -0.002) & (q[..., 0] < 1.002) & (q[..., 1] > -0.01) & (q[..., 1] < 1.01)
sx = np.clip(q[..., 0], 0, 1) * (sw.shape[1] - 1); sy = (1 - np.clip(q[..., 1], 0, 1)) * (sw.shape[0] - 1)
cloth = np.array([0.50, 0.42, 0.29]) * 255; sw = sw * (cloth / sw.reshape(-1, 3).mean(0))
tile = np.stack([ni.map_coordinates(sw[..., c], [sy[ins], sx[ins]], order=1) for c in range(3)], 1)
for t in 'ABC':
    im = np.array(Image.open(f'textures/mummy_{t}_base_linen_graded.png').convert('RGB'), np.float32)
    im[ins] = tile
    Image.fromarray(im.astype(np.uint8)).save(f'textures/mummy_{t}_base_final.png')
print('strips', ins.mean())
ao = np.asarray(Image.open('textures/ao_head.png').convert('L').resize((1024, 1024), Image.LANCZOS), np.float32)
for t in 'ABC':
    im = np.asarray(Image.open(f'textures/head_{t}_proj_graded.png').convert('RGB'), np.float32) / 255
    br = im[(im @ [.2126, .7152, .0722]) > .42]; gain = np.clip(np.array([.50, .42, .29]) / br.mean(0), .85, 1.0).mean(); print('head', t, 'cloth', br.mean(0), 'gain', gain); im = im * gain
    Image.fromarray((np.clip(im, 0, 1) * 255 + .5).astype(np.uint8)).save(f'textures/head_{t}_final.png')
    lum = im @ [.2126, .7152, .0722]
    h = ni.gaussian_filter(lum, 1.1)
    gx = ni.sobel(h, axis=1) / 8; gy = ni.sobel(h, axis=0) / 8
    k = 14.0
    n = np.stack([-gx * k, gy * k, np.ones_like(h)], 2); n /= np.linalg.norm(n, axis=2, keepdims=True)
    Image.fromarray(((n * .5 + .5) * 255 + .5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(f'textures/head_{t}_normal_1k.png')
    orm = np.stack([ao, np.full_like(ao, 0.85 * 255), np.zeros_like(ao)], 2)
    Image.fromarray(orm.astype(np.uint8)).save(f'textures/head_{t}_orm_1k.png')
