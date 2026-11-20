#!/usr/bin/env python3
"""Sample the relayout lookup (tex_resample.py): the 2K Meshy body return into the re-packed UVMap
(texturing/body_relayout/texture_urls_0_*.png) and the installed arm base colour (texturing/arms_installed_*.png)."""
from pathlib import Path
import numpy as np
from PIL import Image
P = Path(__file__).resolve().parents[1]; INST = P.parent / 'mm6_pman_claude_20261013'
L = np.load(P / 'work/relayout_lookup.npz'); muv, iuv = L['meshy_uv'], L['inst_uv']


def bilinear(img, uv):
    h, w = img.shape[:2]; x = np.clip(uv[..., 0] * w - .5, 0, w - 1.001); y = np.clip((1 - uv[..., 1]) * h - .5, 0, h - 1.001)
    x0, y0 = x.astype(int), y.astype(int); fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy) + img[y0 + 1, x0] * (1 - fx) * fy
            + img[y0 + 1, x0 + 1] * fx * fy)


load = lambda p: np.asarray(Image.open(p).convert('RGB'), np.float32) / 255
save = lambda a, p: Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + .5)).save(p)
D = P / 'texturing/body_relayout'; D.mkdir(parents=True, exist_ok=True); m = muv[..., 0] >= 0
from scipy import ndimage  # noqa: E402
# padded (nearest fill): compose downsizes with Lanczos, which rang at hard black chart borders (light seam lines)
fill_m = tuple(ndimage.distance_transform_edt(~m, return_distances=False, return_indices=True))
for k in ('base_color', 'normal', 'roughness', 'metallic'):
    out = np.zeros(muv.shape[:2] + (3,), np.float32); out[m] = bilinear(load(P / f'meshy/body_texture_r45/texture_urls_0_{k}.png'), muv[m])
    save(out[fill_m], D / f'texture_urls_0_{k}.png')
# The installed base colour is sampled from its covered texels only (its raster, ../mm6_pman_claude_20261013/work/
# uvraster_UVMap.npz): bilinear taps on its gutter drew light lines along the installed chart borders.
inst = load(INST / 'textures/pman_body_basecolor_1k.png'); icov = np.load(INST / 'work/uvraster_UVMap.npz')['coverage']


def covered_bilinear(img, cov, uv):
    h, w = img.shape[:2]; x = np.clip(uv[..., 0] * w - .5, 0, w - 1.001); y = np.clip((1 - uv[..., 1]) * h - .5, 0, h - 1.001)
    x0, y0 = x.astype(int), y.astype(int); fx, fy = x - x0, y - y0
    acc = np.zeros(uv.shape[:-1] + (3,)); wsum = np.zeros(uv.shape[:-1])
    for dy, dx, wt in ((0, 0, (1 - fx) * (1 - fy)), (0, 1, fx * (1 - fy)), (1, 0, (1 - fx) * fy), (1, 1, fx * fy)):
        ok = cov[y0 + dy, x0 + dx] * wt; acc += img[y0 + dy, x0 + dx] * ok[..., None]; wsum += ok
    # a tap set entirely in the gutter takes the nearest covered texel
    near = tuple(ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True))
    fallback = img[near][np.rint(y).astype(int), np.rint(x).astype(int)]
    return np.where(wsum[..., None] > 1e-6, acc / np.maximum(wsum, 1e-6)[..., None], fallback)


from scipy import ndimage  # noqa: E402
a = iuv[..., 0] >= 0; arm = np.zeros(muv.shape[:2] + (3,), np.float32); arm[a] = covered_bilinear(inst, icov, iuv[a])
save(arm[tuple(ndimage.distance_transform_edt(~a, return_distances=False, return_indices=True))], P / 'texturing/arms_installed_basecolor.png'); Image.fromarray(np.uint8(a) * 255).save(P / 'texturing/arms_mask.png')
print('SAMPLED', int(m.sum()), 'body texels;', int(a.sum()), 'arm texels from the installed model')
