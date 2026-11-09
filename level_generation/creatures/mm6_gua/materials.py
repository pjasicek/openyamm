"""Native-guided guard material masks. RGBA stores four coverages, never sprite opacity."""
import numpy as np
from PIL import Image
from scipy import ndimage

REGIONS = {
    'mask_r': 'Navy sleeve cloth and blue polearm binding',
    'mask_g': 'Teal trousers',
    'mask_b': 'Warm gold-bronze mail rings and helmet trim',
    'mask_a': 'Remaining skin, leather, wood and dark metal: subtle native palette shifts',
}


def weights(rgb):
    hsv = np.array(Image.fromarray(rgb).convert('HSV')).astype(float)
    h, s, v = hsv.transpose(2, 0, 1)
    h *= 360 / 255
    s /= 255
    v /= 255
    blue = np.clip((h-195)/15, 0, 1)*np.clip((275-h)/15, 0, 1)*np.clip((s-.14)/.18, 0, 1)
    teal = np.clip((h-135)/20, 0, 1)*np.clip((200-h)/15, 0, 1)*np.clip((s-.14)/.18, 0, 1)
    gold = np.clip((h-29)/9, 0, 1)*np.clip((75-h)/15, 0, 1)*np.clip((s-.18)/.18, 0, 1)
    rest = 1-np.maximum.reduce([blue, teal, gold])
    w = np.stack([blue, teal, gold, rest], axis=2)
    w /= np.maximum(w.sum(axis=2, keepdims=True), 1)
    w *= np.clip((v-.015)/.045, 0, 1)[:, :, None]
    return w


def coverage(im):
    a = np.array(im)
    w = weights(a[:, :, :3])
    interior = ndimage.distance_transform_edt(a[:, :, 3] >= 250) > 3
    if interior.any():
        dist, indices = ndimage.distance_transform_edt(~interior, return_indices=True)
        fringe = (a[:, :, 3] > 0) & ~interior & (dist <= 5)
        w[fringe] = w[indices[0], indices[1]][fringe]
    w[a[:, :, 3] == 0] = 0
    return Image.fromarray(np.floor(w*255).astype(np.uint8), 'RGBA')


def fit(config, inv, repo):
    colors = {int(p): np.frombuffer((repo/f'assets_dev/worlds/mm6/textures/pal{p}.act').read_bytes()[:768],
              np.uint8).reshape(256, 3) for p in inv['variants']}
    used = np.zeros(256, bool)
    for name in inv['sources']:
        used[np.unique(np.array(Image.open(repo/f'assets_dev/engine/sprites/{name}.bmp')))] = True
    used[0] = False
    base = config['base_palette']
    w = weights(colors[base][None, :, :])[0]
    y = colors[base]/255 @ np.array([.2126, .7152, .0722])
    vectors = {}
    for palette, color in colors.items():
        if palette == base:
            continue
        vectors[palette] = []
        for region in range(4):
            weight = w[:, region]*used
            denominator = np.sum(weight*y*y)
            assert denominator > .001, region
            vectors[palette].append((((weight*y)[:, None]*(color/255)).sum(axis=0)/denominator).tolist())
    return vectors


def recolor(im, mask, palette, config, vectors):
    if palette == config['base_palette']:
        return im.copy()
    a = np.array(im)
    rgb = a[:, :, :3].astype(float)/255
    w = np.array(mask).astype(float)/255
    y = rgb @ np.array([.2126, .7152, .0722])
    target = np.einsum('hwk,kc->hwc', w, np.array(vectors[palette]))*y[:, :, None]
    a[:, :, :3] = np.round(np.clip(rgb*(1-w.sum(axis=2, keepdims=True))+target, 0, 1)*255).astype(np.uint8)
    return Image.fromarray(a)
