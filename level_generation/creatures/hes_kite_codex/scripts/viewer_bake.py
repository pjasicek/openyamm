"""The engine's region-ramp rule (game/shaders/fs_model.sc) on a texture, for review images and the three.js viewer:
lum = linear luminance of the base, per channel t = clamp((lum - lo) / (hi - lo)), colour = mix(colour, ramp(t), mask)."""
import numpy as np

W = np.array([0.2126, 0.7152, 0.0722])


def lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def bake(base_srgb, mask, ramps):
    """base_srgb HxWx3 0..1, mask HxWx4 0..1, ramps list of {'range', 'colors'} -> baked sRGB HxWx3."""
    col = lin(base_srgb)
    lum = col @ W
    for ch, r in enumerate(ramps):
        if ch >= mask.shape[-1]:
            break
        lo, hi = r['range']
        t = np.clip((lum - lo) / max(hi - lo, 1e-4), 0, 1)
        c = np.array(r['colors'])
        x = t * 15
        i = np.minimum(x.astype(int), 14); f = (x - i)[..., None]
        rc = c[i] * (1 - f) + c[i + 1] * f
        m = mask[..., ch:ch + 1]
        col = col * (1 - m) + rc * m
    return srgb(col)
