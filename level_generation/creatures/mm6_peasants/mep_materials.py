"""Four native-guided material coverages for MEP; RGBA channels are data, not image opacity."""
import numpy as np
from PIL import Image
from scipy import ndimage

REGIONS = {
    'mask_r': 'Red sash and coat buttons',
    'mask_g': 'Cool blue cap and trousers, including cool inner-shirt shading',
    'mask_b': 'Pale coat, shirt and white hair/beard',
    'mask_a': 'Warm skin, wood and leather; retain their native subtle palette shifts',
}


def weights(rgb):
    hsv = np.array(Image.fromarray(rgb).convert('HSV')).astype(float)
    h, s, v = hsv.transpose(2, 0, 1)
    h *= 360 / 255
    s /= 255
    v /= 255
    red = np.clip((18 - np.minimum(h, 360-h))/8, 0, 1) * np.clip((s-.32)/.2, 0, 1)
    cool = np.clip((h-185)/20, 0, 1) * np.clip((275-h)/20, 0, 1) * np.clip((s-.06)/.12, 0, 1)
    warm = np.clip((h-10)/10, 0, 1) * np.clip((80-h)/20, 0, 1) * np.clip((s-.16)/.18, 0, 1)
    neutral = 1-np.maximum.reduce([red, cool, warm])
    w = np.stack([red, cool, neutral, warm], axis=2)
    w /= np.maximum(w.sum(axis=2, keepdims=True), 1)
    # Near-black pixels have no reliable material hue and need no forced recolor.
    w *= np.clip((v-.025)/.06, 0, 1)[:, :, None]
    return w


def coverage(im):
    a = np.array(im)
    w = weights(a[:, :, :3])
    depth = ndimage.distance_transform_edt(a[:, :, 3] >= 250)
    interior = depth > 3
    if interior.any():
        dist, idx = ndimage.distance_transform_edt(~interior, return_indices=True)
        fringe = (a[:, :, 3] > 0) & ~interior & (dist <= 5)
        w[fringe] = w[idx[0], idx[1]][fringe]
    w[a[:, :, 3] == 0] = 0
    # Flooring guarantees integer channel sums never exceed 255.
    return Image.fromarray(np.floor(w*255).astype(np.uint8), 'RGBA')


def fit(config, inv, repo):
    base = config['base_palette']
    colors = {int(p): np.frombuffer((repo/f'assets_dev/worlds/mm6/textures/pal{p}.act').read_bytes()[:768],
              np.uint8).reshape(256,3) for p in inv['variants']}
    used = np.zeros(256, bool)
    for name in inv['sources']:
        used[np.unique(np.array(Image.open(repo/f'assets_dev/engine/sprites/{name}.bmp')))] = True
    used[0] = False
    # Fit once from native indexed colors with the same semantic hue classes.
    w = weights(colors[base][None, :, :])[0]
    y = colors[base] / 255 @ np.array([.2126, .7152, .0722])
    vectors = {}
    for p, c in colors.items():
        if p == base:
            continue
        vectors[p] = []
        for region in range(4):
            weight = w[:, region] * used
            denom = np.sum(weight*y*y)
            assert denom > .01, region
            fitted = ((weight*y)[:,None] * (c/255)).sum(axis=0) / denom
            vectors[p].append(fitted.tolist())
    return vectors


def recolor(im, mask, palette, config, vectors):
    if palette == config['base_palette']:
        return im.copy()
    a = np.array(im)
    rgb = a[:, :, :3].astype(float)/255
    w = np.array(mask).astype(float)/255
    assert np.all(w.sum(axis=2) <= 1.000001)
    y = rgb @ np.array([.2126, .7152, .0722])
    target = np.einsum('hwk,kc->hwc', w, np.array(vectors[palette])) * y[:, :, None]
    rgb = rgb * (1-w.sum(axis=2, keepdims=True)) + target
    a[:, :, :3] = np.round(np.clip(rgb, 0, 1)*255).astype(np.uint8)
    return Image.fromarray(a)
