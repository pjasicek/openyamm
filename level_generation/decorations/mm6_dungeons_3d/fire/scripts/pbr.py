"""PBR texture sets derived from CC0 Poly Haven scans (fire/source/polyhaven/<asset>/, fetch_textures.py) for the
fire and torch batches: base colour, normal (OpenGL convention, as glTF) and glTF metallic-roughness (G roughness,
B metal). The base colour keeps the scan's light and dark structure, with its chroma reduced (`saturation`) and
turned toward a hue (`hue`, the native colour family), and is scaled to a mean luminance (`mean`, linear) above the
native colour, so the per-material COLOR_0 tint (linear(native) / linear(texture mean), at most one) only darkens
it. Roughness is the scan's map remapped (`rough`: scale, offset); metal is low and constant: the engine's indoor
ambient lights only the (1 - metallic) diffuse part. Pure numpy / PIL; no Blender."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

SOURCE = Path(__file__).resolve().parents[1] / 'source' / 'polyhaven'
LUMA = np.array([0.2126, 0.7152, 0.0722])


def linear(c):
    c = np.asarray(c, np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(lin):
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)


def load(asset, kind, size):
    path = SOURCE / asset / f'{asset}_{kind}_1k.png'
    image = Image.open(path)
    if kind == 'rough':                       # 8- or 16-bit grey; returned on a 0..255 scale
        values = np.asarray(image).astype(np.float64)
        values = values / 257.0 if image.mode.startswith('I') else values
        if values.ndim == 3:
            values = values[..., 0]
        image = Image.fromarray(values.astype(np.float32), 'F')
        if image.size != (size, size):
            image = image.resize((size, size), Image.BILINEAR)
        return np.asarray(image).astype(np.float64)
    image = image.convert('RGB')
    if image.size != (size, size):
        image = image.resize((size, size), Image.LANCZOS)
    return np.asarray(image).astype(np.float64)


def base_colour(asset, size, saturation, hue, mean, contrast=1.0, ramp=None, invert=False):
    """Linear base colour: the scan desaturated toward its luminance and recoloured by the hue (sRGB tuple,
    normalised to unit luminance); contrast > 1 spreads the luminance about its mean; ramp [(t, sRGB), ...] maps
    normalised luminance (1st-99th percentile; invert: dark cracks high) through a colour ramp instead (glowing
    embers)."""
    lin = linear(load(asset, 'diff', size))
    lum = lin @ LUMA
    if ramp is not None:
        lo, hi = np.percentile(lum, 1), np.percentile(lum, 99)
        t = np.clip((lum - lo) / max(hi - lo, 1e-6), 0, 1)
        t = 1 - t if invert else t
        out = np.stack([np.interp(t, [p for p, _ in ramp], [linear(c[i]) for _, c in ramp]) for i in range(3)], -1)
        return out
    chroma = lin - lum[..., None]
    lin = lum[..., None] + chroma * saturation
    if hue is not None:
        h = linear(hue)
        lin = lin * (h / max(float(h @ LUMA), 1e-6))[None, None]
    if contrast != 1.0:
        m = float((lin @ LUMA).mean())
        lin = m * (np.maximum(lin, 1e-6) / m) ** contrast
    lin *= mean / max(float((lin @ LUMA).mean()), 1e-6)
    return np.clip(lin, 0, 1)


def normal_map(asset, size, strength=1.0):
    n = load(asset, 'nor_gl', size) / 255.0 * 2 - 1
    n[..., :2] *= strength
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def roughness(asset, size, scale, offset, low=0.25, high=1.0):
    r = load(asset, 'rough', size) / 255.0
    return np.clip(r * scale + offset, low, high)


def save_set(out_dir, name, colour_linear, normal, rough, metal, mr_size=None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    Image.fromarray((srgb(colour_linear) * 255 + 0.5).astype(np.uint8)).save(out_dir / f'{name}_basecolor.png',
                                                                             optimize=True)
    Image.fromarray((normal * 255 + 0.5).astype(np.uint8)).save(out_dir / f'{name}_normal.png', optimize=True)
    mr = np.dstack([np.zeros(rough.shape), rough, np.full(rough.shape, metal)])
    image = Image.fromarray((mr * 255 + 0.5).astype(np.uint8))
    if mr_size and mr_size != image.width:
        image = image.resize((mr_size, mr_size), Image.LANCZOS)
    image.save(out_dir / f'{name}_mr.png', optimize=True)


def derive(out_dir, name, asset, size=512, saturation=0.3, hue=None, mean=0.2, contrast=1.0, ramp=None,
           normal_strength=1.0, rough=(1.0, 0.0), rough_range=(0.25, 1.0), metal=0.2, mr_size=256,
           normal_asset=None, invert=False):
    colour = base_colour(asset, size, saturation, hue, mean, contrast, ramp, invert)
    normal = normal_map(normal_asset or asset, size, normal_strength)
    r = roughness(normal_asset or asset, size, rough[0], rough[1], *rough_range)
    save_set(out_dir, name, colour, normal, r, metal, mr_size)
    return [round(float(v), 5) for v in colour.reshape(-1, 3).mean(0)]


def write_means(path, table):
    path = Path(path)
    current = json.loads(path.read_text()) if path.exists() else {}
    current.update(table)
    path.write_text(json.dumps(current, indent=1) + '\n')
