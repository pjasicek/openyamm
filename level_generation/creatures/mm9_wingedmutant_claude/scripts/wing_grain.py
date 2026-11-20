#!/usr/bin/env python3
"""Wing grade of the texture pass (coordinator request 2026-10-30): the 4K paint and the approved wing have the same
luminance spread, but the approved wing holds it in broad soft tone and the new paint in a fine light/dark pebble
pattern. On wing-region texels the log-luminance detail finer than SIGMA texels is scaled so its amplitude is KEEP x the
approved wing's at the same surface scale (the layout is 2.51x denser); edges stay where they are, only their
amplitude drops. Hue is untouched. Reads textures/wmut_basecolor_graded.png, writes wmut_basecolor_graded_wing.png
(compose_head.py input), so re-running never compounds; then re-fit the ramps with wing_tone.py --write.
Usage: wing_grain.py [--keep 1.25] [--sigma 12]"""
import argparse, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV

W = np.array([0.2126, 0.7152, 0.0722])
SCALE = 2.51


def detail(path, mask_path, sigma):
    rgb = RV.load_srgb(path)
    lin = RV.srgb_to_linear(rgb)
    m = np.asarray(Image.open(mask_path).convert('RGBA').getchannel('B').resize(rgb.shape[1::-1], Image.BILINEAR),
                   np.float32) / 255
    log = np.log(np.maximum(lin @ W, 0.003))
    core = (m > 0.5).astype(np.float32)
    low = ndimage.gaussian_filter(log * core, sigma) / np.maximum(ndimage.gaussian_filter(core, sigma), 1e-3)
    return lin, m, log - low, m > 0.9


ap = argparse.ArgumentParser()
ap.add_argument('--keep', type=float, default=1.25)
ap.add_argument('--sigma', type=float, default=12.0)
args = ap.parse_args()
T = HERE / 'textures'
B = HERE / 'work' / 'before_texpass' / 'textures'
_, _, da, ca = detail(B / 'wmut_basecolor_graded_v2.png', B / 'wmut_region_mask_v2.png', args.sigma / SCALE)
lin, m, db, cb = detail(T / 'wmut_basecolor_graded.png', T / 'wmut_region_mask.png', args.sigma)
sa, sb = float(da[ca].std()), float(db[cb].std())
gain = min(1.0, args.keep * sa / sb)
out = lin * np.exp((gain - 1) * db * m)[..., None]
srgb = np.where(out <= 0.0031308, out * 12.92, 1.055 * np.clip(out, 0, 1) ** (1 / 2.4) - 0.055)
Image.fromarray((np.clip(srgb, 0, 1) * 255).round().astype(np.uint8)).save(T / 'wmut_basecolor_graded_wing.png')
print(f'WING_GRAIN detail sd approved {sa:.3f} current {sb:.3f} gain {gain:.3f}')
