#!/usr/bin/env python3
"""Native shading transfer for the skull pile (after ../../../creatures/NATIVE_SHADING_TRANSFER.md, adapted to a heap:
the sprite's light sits on each skull, not on one body coordinate). Per texel, from the baked ambient occlusion and
object-space normal (bake_pile_maps.py): light = AO x (0.2 + 0.8 max(0, n . L)) with L from above and outward at every
azimuth (the sprite is lit from above and the camera side; the model is seen from all sides). The light values are histogram-matched to the native sprite's luminance distribution (its ~30 % near
black gaps, grey-blue mid tones and cream-yellow crowns) and coloured through the sprite's luminance-to-colour table,
then times the Meshy texture's own local detail (sockets, teeth, sutures).
Writes textures/<prefix>_basecolor.png (and copies the normal / metallic-roughness of skullpile2k), at <size>.
Usage: shade_pile.py <prefix> <size> [detail strength] [exposed AO threshold]"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LUMA = np.array([0.2126, 0.7152, 0.0722])
UP, OUT = 0.8, 0.6                  # light direction: elevation about 53 degrees
EXPOSED = float(sys.argv[4]) if len(sys.argv) > 4 else 0.6
prefix, size = sys.argv[1], int(sys.argv[2])
detail_strength = float(sys.argv[3]) if len(sys.argv) > 3 else 0.9


def load(path, mode='RGB'):
    return np.asarray(Image.open(path).convert(mode), np.float64) / 255


base = load(os.path.join(HERE, 'textures', 'skullpile2k_basecolor.png'))
ao = load(os.path.join(HERE, 'work', 'skullpile_ao.png'))[..., 0]
normal = load(os.path.join(HERE, 'work', 'skullpile_nrm.png')) * 2 - 1
covered = np.linalg.norm(normal, axis=-1) < 1.3
# The pile is seen from every side, so the light comes from above and outward at every azimuth: L leans toward each
# texel's own horizontal normal direction (inward-facing texels sit in the gaps and are dark through AO anyway).
horizontal = np.linalg.norm(normal[..., :2], axis=-1)
light = ao * (0.2 + 0.8 * np.clip(UP * normal[..., 2] + OUT * horizontal, 0, 1))

native = np.asarray(Image.open(os.path.join(HERE, 'native', 'sklplrev_native_embedded.png')).convert('RGBA'),
                    np.float64)
pixels = native[native[..., 3] > 0][:, :3] / 255
native_lum = np.sort(pixels @ LUMA)
# Luminance -> colour table of the sprite (mean colour per luminance bin, interpolated over empty bins).
bins = np.linspace(0, 1, 33)
index = np.clip(np.digitize(pixels @ LUMA, bins) - 1, 0, 31)
table = np.array([pixels[index == k].mean(0) if (index == k).any() else [np.nan] * 3 for k in range(32)])
centres = (bins[:-1] + bins[1:]) / 2
for c in range(3):
    good = ~np.isnan(table[:, c])
    table[:, c] = np.interp(centres, centres[good], table[good, c])

values = light[covered]
# The mapping light -> native luminance is fitted on the exposed texels only (those the sprite's view would show:
# AO above EXPOSED); hidden texels fall below the exposed minimum and come out near black, as the sprite's gaps.
exposed = values[ao[covered] > EXPOSED]
quantiles = np.linspace(0, 1, 257)
target = np.interp(values, np.quantile(exposed, quantiles), np.quantile(native_lum, quantiles))
lum = base @ LUMA
detail = np.clip(lum / np.maximum(ndimage.gaussian_filter(lum, 6.0), 1e-3), 0.5, 1.6) ** detail_strength
shaded_lum = np.clip(target * detail[covered], 0, 1)
colour = np.stack([np.interp(shaded_lum, centres, table[:, c]) for c in range(3)], axis=-1)
# Keep the luminance exact (the table's colour at that luminance carries the hue).
colour *= (shaded_lum / np.maximum(colour @ LUMA, 1e-4))[:, None]
out = base.copy()
out[covered] = np.clip(colour, 0, 1)
image = Image.fromarray(np.round(out * 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)
image.save(os.path.join(HERE, 'textures', f'{prefix}_basecolor.png'))
for kind in ('normal', 'mr'):
    Image.open(os.path.join(HERE, 'textures', f'skullpile2k_{kind}.png')).resize((size, size), Image.LANCZOS).save(
        os.path.join(HERE, 'textures', f'{prefix}_{kind}.png'))
print('SHADED', prefix, size, 'covered', round(float(covered.mean()), 3), 'mean',
      np.round(np.asarray(image).reshape(-1, 3).mean(0)).tolist(), 'native mean',
      np.round(pixels.mean(0) * 255).tolist())
