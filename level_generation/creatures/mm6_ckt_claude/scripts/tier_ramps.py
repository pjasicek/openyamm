#!/usr/bin/env python3
"""Cockatrice tiers as one shared skin: the wing membrane ramp per tier by palette transfer
(claude_shared/native_shading.py transfer_ramps, ../NATIVE_SHADING_TRANSFER.md). Cockatrice A/B/C = palettes
680 tan / 681 turquoise / 682 red. The base texture's membrane is turquoise (masters in the 681 colouring), so the
membrane pixels of the native standing views (work/native_shading/pixels.npz, region from the restored mask R) are
matched by luminance in palette 681 and read in each tier's palette, times GAIN for the engine's darkening.
Also writes the baked AO into the red channel of the metal/roughness map (glTF ORM packing).
Writes textures/ckt_region_mask.png and textures/ckt_ramps.json."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'claude_shared'))
import region_variants as R
import native_shading as NS

ROOT = HERE.parent
T = ROOT / 'textures'
PALETTES = {'ckt_a': 680, 'ckt_b': 681, 'ckt_c': 682}
GAIN = 1.3
BODY_GAIN = 1.25
CHROMA = 1.1


def main():
    base = R.load_srgb(T / 'ckt_a_basecolor_graded.png')
    weight = np.asarray(np.load(T / 'ckt_region_weights.npz')['membrane'], np.float64)
    body = np.asarray(np.load(T / 'ckt_body_weight.npz')['body'], np.float64)
    body = np.asarray(Image.fromarray((body * 255).astype(np.uint8)).resize(weight.shape[::-1], Image.LANCZOS), np.float64) / 255
    R.write_mask([weight, body], T / 'ckt_region_mask.png')
    pixels = np.load(ROOT / 'work' / 'native_shading' / 'pixels.npz')
    ramps = NS.transfer_ramps(base, {'membrane': weight}, pixels, {'membrane': 'membrane'}, PALETTES,
                              reference=681, gain={'membrane': GAIN}, chroma=CHROMA)
    # body (native_body_shade.py): the sprite's own body pixels, the same brown in every tier
    body_pixels = np.load(ROOT / 'work' / 'native_shading' / 'body_pixels.npz')
    body_ramps = NS.transfer_ramps(base, {'body': body}, body_pixels, {'body': 'body'}, PALETTES,
                                   reference=680, gain={'body': BODY_GAIN})
    for v in ramps:
        ramps[v] += body_ramps[v]
    config = {'variants': list(PALETTES),
              'materials': [{'base': 'Cockatrice_A', 'prefix': 'Cockatrice', 'mask': 'ckt_region_mask.png',
                             'regions': ['membrane', 'body'], 'palettes': PALETTES, 'ramps': ramps}]}
    (T / 'ckt_ramps.json').write_text(json.dumps(config, indent=1) + '\n')
    ao = Image.open(T / 'ckt_ao_2k.png').convert('L').resize((1024, 1024), Image.LANCZOS)
    mr = Image.open(T / 'ckt_metal_rough_1k.png').convert('RGB')
    Image.merge('RGB', (ao, mr.getchannel('G'), mr.getchannel('B'))).save(T / 'ckt_metal_rough_1k.png')
    print(json.dumps({v: r[0]['colors'][8] for v, r in ramps.items()}))


if __name__ == '__main__':
    main()
