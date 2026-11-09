#!/usr/bin/env python3
"""Flying demon textures from the Meshy retexture (one shared skin; tiers come from the material tint, like the
Sorpigal mage). Texels are classed by hue: purple skin (the tint mask), dark grey chest/belly, dark wing membrane,
ivory horns/spikes/claws, blue eyes. Skin is pulled to the tier-A native skin colour and the wing membrane to the native membrane colour (Meshy
luminance detail kept).
Writes textures/wdm_basecolor.png, wdm_normal_1k.png, wdm_metal_rough_1k.png (R = tint mask, G = roughness,
B = metallic 0), textures/tints.json (per tier: native mean linear skin colour / masked source mean luminance,
shader colour = luminance * tint inside the mask) and review/texture_classes.png."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / 'mm6_gob_claude' / 'scripts'))
import compose_textures_v2 as C
SRC = ROOT / 'meshy/retexture_v2/texture_urls_0'
OUT = ROOT / 'textures'; OUT.mkdir(exist_ok=True)
NATIVE = ROOT.parent / 'mm6_wdm'
FRAMES = ['wdmflya0', 'wdmflyd0', 'wdmflya2', 'wdmflyb1', 'wdmflyc1', 'wdmflye1']
PALETTES = {'a': '684', 'b': '685', 'c': '683'}
SKIN_GAIN = 1.15
MEMBRANE_GAIN = 1.3                     # sprites carry baked shading; the model is lit at runtime
W = np.array([0.2126, 0.7152, 0.0722])


def lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def native_region(pal, channel):
    out = []
    for f in FRAMES:
        nv = np.asarray(Image.open(NATIVE / 'native_variants' / f'{f}_{pal}.png').convert('RGBA'), np.float32) / 255
        m = np.asarray(Image.open(NATIVE / 'masks_2x' / f'{f}.png').convert('RGBA').resize(
            (nv.shape[1], nv.shape[0]), Image.NEAREST), np.float32) / 255
        out.append(nv[(nv[..., 3] > 0.5) & (m[..., channel] > 0.5), :3])
    return np.concatenate(out)


def native_membrane(pal):
    return native_region(pal, 1)


def native_skin(pal):
    """Native skin texels (restored region mask R) of the fly frames in one palette, sRGB."""
    out = []
    for f in FRAMES:
        nv = np.asarray(Image.open(NATIVE / 'native_variants' / f'{f}_{pal}.png').convert('RGBA'), np.float32) / 255
        m = np.asarray(Image.open(NATIVE / 'masks_2x' / f'{f}.png').convert('RGBA').resize(
            (nv.shape[1], nv.shape[0]), Image.NEAREST), np.float32) / 255
        out.append(nv[(nv[..., 3] > 0.5) & (m[..., 0] > 0.5), :3])
    return np.concatenate(out)


data = np.load(ROOT / 'work/uv3d.npz')
part_map, xyz = C.rasterise(data)
strict, _ = C.rasterise(data, tol=0.0)
interior = ndimage.binary_erosion(strict >= 0, iterations=2)
_, (iy, ix) = ndimage.distance_transform_edt(~interior, return_indices=True)


def pad(a):
    o = a[iy, ix]; o[interior] = a[interior]; return o


base = pad(C.load(str(SRC) + '_base_color.png'))
normal = pad(C.load(str(SRC) + '_normal.png'))
rough = pad(C.load(str(SRC) + '_roughness.png'))[..., 0]
h, s, v = C.hsv(base)
valid = part_map >= 0
eyes = valid & (h > 170) & (h < 250) & (s > 0.35) & (v > 0.35)
bone = valid & ~eyes & (s < 0.25) & (v > 0.55)
skin = valid & ~eyes & ~bone & (((h > 255) | (h < 15)) & (s > 0.18) & (v > 0.12))
dark = valid & ~eyes & ~bone & ~skin                # chest/belly and wing membrane: kept as Meshy painted them
skin = ndimage.binary_opening(skin, iterations=1) & (part_map != 1)      # membranes never take the tier tint
print('CLASSES', {k: int(m.sum()) for k, m in (('skin', skin), ('bone', bone), ('eyes', eyes), ('dark', dark))})

# tier A skin: native colour with Meshy luminance detail
a_native = lin(native_skin(PALETTES['a'])).mean(0) * SKIN_GAIN
lum = lin(base) @ W
ref = np.median(lum[skin])
shade = np.clip(lum / ref, 0.25, 2.5)[..., None]
skin_lin = a_native[None, None] * shade
soft = ndimage.gaussian_filter(skin.astype(np.float32), 1.0)[..., None] * valid[..., None]
out = srgb(lin(base) * (1 - soft) + skin_lin * soft)
# wing membrane: native dark membrane colour (sprite region G) with Meshy's luminance detail; Meshy painted purple
# blotches into it, which would read as skin
membrane = valid & (part_map == 1) & ~bone
mem_native = lin(native_membrane(PALETTES['a'])).mean(0) * MEMBRANE_GAIN
mref = np.median(lum[membrane])
mem_lin = mem_native[None, None] * np.clip(lum / mref, 0.3, 2.5)[..., None]
msoft = ndimage.gaussian_filter(membrane.astype(np.float32), 1.0)[..., None] * valid[..., None]
out = srgb(lin(out) * (1 - msoft) + mem_lin * msoft)
out = np.where(valid[..., None], out, base)
Image.fromarray((np.clip(pad(out), 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / 'wdm_basecolor.png', optimize=True)

# tint mask + roughness, tints
mask = Image.fromarray((skin * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
mask = np.asarray(mask.resize((1024, 1024), Image.LANCZOS))
r = (np.clip(rough, 0, 1) * 255).astype(np.uint8)
r = np.asarray(Image.fromarray(r).resize((1024, 1024), Image.LANCZOS))
Image.fromarray(np.stack([mask, r, np.zeros_like(r)], 2)).save(OUT / 'wdm_metal_rough_1k.png')
Image.fromarray((np.clip(normal, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(
    OUT / 'wdm_normal_1k.png')
composed_lin = lin(np.clip(out, 0, 1))
src_lum = float((composed_lin[skin] @ W).mean())
tints = {t: (lin(native_skin(p)).mean(0) * SKIN_GAIN / src_lum).round(4).tolist() for t, p in PALETTES.items()}
json.dump({'mask_texels': int(skin.sum()), 'source_linear_luminance': round(src_lum, 4), 'skin_gain': SKIN_GAIN,
           'tints': tints}, open(OUT / 'tints.json', 'w'), indent=1)
print('TINTS', tints)

preview = np.zeros(base.shape, np.float32)
for m, c in ((skin, (0.7, 0.3, 0.7)), (dark, (0.25, 0.25, 0.25)), (bone, (1, 1, 0.85)), (eyes, (0.2, 0.5, 1))):
    preview[m] = c
(ROOT / 'review').mkdir(exist_ok=True)
Image.fromarray((preview * 255).astype(np.uint8)).resize((1024, 1024), Image.NEAREST).save(
    ROOT / 'review' / 'texture_classes.png')
