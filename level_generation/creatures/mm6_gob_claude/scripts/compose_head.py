#!/usr/bin/env python3
"""Head texture set, step 2: goblin head maps from the head-only Meshy retexture (meshy/head_retexture_v1).

- Base colour: graded like the body (local 0.4, contrast 1.08, saturation 1.12, no AO), then the skin's luminance is
  scaled so its median matches the body's tier-A skin; 1K.
- Normal and metal/roughness (R 1, G roughness, B metallic) from Meshy's PBR maps; 1K.
- Tiers: skin weight from HSV hue/saturation (olive skin, brown ears; yellow eyes, gold hoops, teeth excluded). The
  head reuses the body's skin ramps (same luminance range), so the neck seam matches in every tier; written as the
  GoblinHead entry of textures/gob_ramps.json with mask textures/gob_head_region_mask.png.
Run after scripts/tier_ramps.py (which writes the body entry)."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared'))
import region_variants as R

ROOT = HERE.parent
T = ROOT / 'textures'
SRC = ROOT / 'meshy/head_retexture_v1/texture_urls_0'
SIZE = 1024


def save(array, path, mode='RGB'):
    Image.fromarray(np.clip(array * 255 + 0.5, 0, 255).astype(np.uint8), mode).save(path, optimize=True)


def hsv(rgb):
    high, low = rgb.max(-1), rgb.min(-1)
    delta = np.maximum(high - low, 1e-6)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    hue = np.where(high == r, (g - b) / delta % 6, np.where(high == g, (b - r) / delta + 2, (r - g) / delta + 4)) * 60
    return hue, (high - low) / np.maximum(high, 1e-6), high


def skin_weight(rgb):
    """Olive skin and brown ears (HSV hue 15-120); bright saturated eyes/hoops and pale teeth excluded."""
    hue, saturation, value = hsv(rgb)
    weight = (np.clip((hue - 10) / 5, 0, 1) * np.clip((125 - hue) / 5, 0, 1)
              * np.clip((saturation - 0.12) / 0.08, 0, 1) * np.clip((value - 0.04) / 0.06, 0, 1))
    weight *= 1 - np.clip((value - 0.55) / 0.08, 0, 1) * np.clip((saturation - 0.55) / 0.08, 0, 1)
    weight *= 1 - np.clip((value - 0.6) / 0.08, 0, 1) * np.clip((0.4 - saturation) / 0.08, 0, 1)
    return ndimage.gaussian_filter(weight, 0.8)


def main():
    # Grade the head like the body (no AO), then match its skin luminance distribution to the body's tier-A skin.
    raw = T / 'gob_head_basecolor.png'
    save(R.load_srgb(str(SRC) + '_base_color.png', SIZE), raw)
    white = T / 'gob_head_no_ao.png'
    Image.new('L', (SIZE, SIZE), 255).save(white)
    subprocess.run([sys.executable, str(HERE.parents[1] / 'claude_shared/grade_basecolor.py'), '--ao', str(white),
                    '--ao-strength', '0', '--local', '0.4', '--contrast', '1.08', '--saturation', '1.12', str(raw)],
                   check=True)
    white.unlink()
    graded_path = T / 'gob_head_basecolor_graded.png'
    graded = R.load_srgb(graded_path)
    weight = skin_weight(graded)

    config_path = T / 'gob_ramps.json'
    config = json.loads(config_path.read_text())
    body_entry = next(entry for entry in config['materials'] if entry['prefix'] == 'Goblin')
    body = R.load_srgb(T / 'gob_a_basecolor_graded.png')
    body_mask = np.asarray(Image.open(T / 'gob_region_mask.png').getchannel('R').resize(body.shape[1::-1]),
                           np.float64) / 255
    body_lum = R.luminance(body)[body_mask > 0.9]
    head_linear = R.srgb_to_linear(graded)
    head_lum = head_linear @ R.LUMA
    gain = float(np.median(body_lum) / max(np.median(head_lum[weight > 0.9]), 1e-4))
    matched = head_linear * (1 + (gain - 1) * weight[..., None])
    encode = lambda v: np.where(v <= 0.0031308, v * 12.92, 1.055 * np.maximum(v, 0) ** (1 / 2.4) - 0.055)
    save(encode(np.clip(matched, 0, 1)), graded_path)

    normal = R.load_srgb(str(SRC) + '_normal.png', SIZE)
    save(normal, T / 'gob_head_normal_1k.png')
    rough = np.asarray(Image.open(str(SRC) + '_roughness.png').convert('L').resize((SIZE, SIZE), Image.LANCZOS),
                       np.float64) / 255
    metal = np.asarray(Image.open(str(SRC) + '_metallic.png').convert('L').resize((SIZE, SIZE), Image.LANCZOS),
                       np.float64) / 255
    save(np.stack([np.ones_like(rough), rough, metal], -1), T / 'gob_head_metal_rough_1k.png')

    # The head skin uses the body's skin ramps, so head and neck take the same colours in every tier.
    R.write_mask([weight], T / 'gob_head_region_mask.png', size=SIZE)
    config['materials'] = [entry for entry in config['materials'] if entry['prefix'] != 'GoblinHead']
    config['materials'].append({'base': 'GoblinHead_A', 'prefix': 'GoblinHead', 'mask': 'gob_head_region_mask.png',
                                'regions': ['skin'], 'palettes': body_entry['palettes'],
                                'ramps': body_entry['ramps'], 'luminance_gain': round(gain, 4)})
    config_path.write_text(json.dumps(config, indent=1) + '\n')
    print(json.dumps({'luminance_gain': round(gain, 3), 'skin_texels': int((weight > 0.5).sum()),
                      'head_skin_lum_median': round(float(np.median((R.srgb_to_linear(R.load_srgb(graded_path)) @ R.LUMA)[weight > 0.9])), 4),
                      'body_skin_lum_median': round(float(np.median(body_lum)), 4)}))


if __name__ == '__main__':
    main()
