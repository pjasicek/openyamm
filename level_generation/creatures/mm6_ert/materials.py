"""Native Earth palette curves retain the dark green variant's nonlinear shadows."""
import numpy as np
from PIL import Image

LUMA = np.array([.2126, .7152, .0722])


def coverage(image):
    a = np.array(image)
    y = a[:, :, :3].astype(float) @ LUMA
    w = np.clip((y - 2) / 6, 0, 1) * (a[:, :, 3] > 0)
    return Image.fromarray(np.round(w * 255).astype(np.uint8), 'L')


def fit(config, inv, repo):
    colors = {int(p): np.fromfile(repo / f'assets_dev/worlds/mm6/textures/pal{p}.act', np.uint8)
              [:768].reshape(256, 3) / 255 for p in inv['variants']}
    counts = np.zeros(256)
    for source in inv['sources'].values():
        if source['referenced']:
            counts += np.bincount(np.array(Image.open(repo / source['path'])).ravel(), minlength=256)
    counts[0] = 0
    selected = counts > 0
    y = (colors[725] @ LUMA)[selected] * 255
    result = {}
    for palette in (726, 727):
        curve = []
        for level in range(256):
            distance = (y - level) ** 2
            weight = counts[selected] * np.exp(-(distance - distance.min()) / 32)
            target = weight @ colors[palette][selected] / weight.sum()
            if level < y.min():
                target *= level / (weight @ y / weight.sum())
            curve.append(target.tolist())
        result[palette] = curve
    return result


def recolor(image, mask, palette, config, vectors):
    if palette == 725:
        return image.copy()
    a = np.array(image)
    c = a[:, :, :3].astype(float) / 255
    w = np.array(mask).astype(float)[:, :, None] / 255
    level = np.clip(np.round((c @ LUMA) * 255), 0, 255).astype(int)
    out = c * (1 - w) + np.array(vectors[palette])[level] * w
    a[:, :, :3] = np.round(np.clip(out, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(a)
