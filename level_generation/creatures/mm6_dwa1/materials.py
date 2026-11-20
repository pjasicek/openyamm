"""Two native cloth ramps on enhanced-art coverage; remaining channels are unused."""
import numpy as np
from scipy import ndimage
from PIL import Image

REGIONS = {'mask_r': 'Green tunic including sleeves', 'mask_g': 'Dark teal trousers',
           'mask_b': 'Unused', 'mask_a': 'Unused; not sprite alpha'}


def coverage(im):
    a = np.array(im)
    c = a[:, :, :3].astype(float)/255
    r, g, b = c.transpose(2, 0, 1)
    strength = np.maximum(0, g-np.maximum(r, b))
    w = np.clip((strength-.002)/.014, 0, 1)*np.clip(
        (strength/np.maximum(g, .01)-.015)/.075, 0, 1)
    labels, count = ndimage.label((w>.6)&(a[:, :, 3]>128))
    sizes = np.bincount(labels.ravel())
    keep = sizes >= 300
    keep[0] = False
    core = keep[labels]
    distance, nearest = ndimage.distance_transform_edt(~core, return_indices=True)
    w *= distance <= 3
    w[a[:, :, 3]==0] = 0
    result = np.zeros((*w.shape, 4))
    result[:, :, 0] = w
    return Image.fromarray(np.floor(result*255).astype(np.uint8), 'RGBA')


def fit(config, inv, repo):
    colors = {int(p): np.frombuffer((repo/f'assets_dev/worlds/mm6/textures/pal{p}.act').read_bytes()[:768],
              np.uint8).reshape(256, 3)/255 for p in inv['variants']}
    used = np.zeros(256, bool)
    for name in inv['sources']:
        used[np.unique(np.array(Image.open(repo/f'assets_dev/engine/sprites/{name}.bmp')))] = True
    base = colors[config['base_palette']]
    y = base @ np.array([.2126, .7152, .0722])
    ids = np.arange(256)
    green = (base[:, 1]>base[:, 0]+.012)&(base[:, 1]>base[:, 2]+.012)
    selections = [used&green&(ids<240), used&green&(ids>=240)]
    result = {}
    for palette, color in colors.items():
        if palette == config['base_palette']:
            continue
        result[palette] = [((y[s, None]*color[s]).sum(axis=0)/(y[s]**2).sum()).tolist()
                           for s in selections] + [[0,0,0], [0,0,0]]
    return result


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
