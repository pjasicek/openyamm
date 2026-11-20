#!/usr/bin/env python3
"""Head material tiers: the helmet is armour and trim like the body, the crest is its own region (red in 828/829,
cyan in 830). Rasterizes the head UV layout (work/head_uv_layout.json from dump_head_uv.py): armour = helmet and dome
texels that are not gold or red, trim = gold texels, crest = the crest faces. Ramps per region from the aligned native
pixels: armour and trim reuse the body's ramps, the crest ramp is fitted on the head's crest. Writes
textures/ttn_head_region_mask.png and appends a 'TitanHead' material to textures/ttn_ramps.json."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
sys.path.insert(0, str(HERE / 'scripts'))
import native_shading as NS
import region_variants as R
from prepare_textures import TIERS, hsv_of

T = HERE / 'textures'
N = 1024
GAIN = {'armour': 1.35, 'trim': 1.0, 'crest': 1.2}
layout = json.loads((HERE / 'work' / 'head_uv_layout.json').read_text())


def raster(parts):
    img = Image.new('L', (N, N), 0)
    d = ImageDraw.Draw(img)
    for part, pts in layout['faces']:
        if part in parts:
            d.polygon([(u * N, (1 - v) * N) for u, v in pts], fill=255, outline=255)
    return ndimage.binary_dilation(np.asarray(img) > 0, iterations=2)


head = R.load_srgb(T / 'ttn_head_basecolor_graded.png', N)
h, s, v = hsv_of(head)
gold = (h > 28) & (h < 70) & (s >= 0.35) & (v >= 0.3)
red = ((h < 15) | (h > 340)) & (s >= 0.5)
crest_faces = raster({'Crest'})
shell = raster({'Helmet', 'Dome', 'Nape'})
soft = lambda m: np.clip(ndimage.gaussian_filter(m.astype(np.float64), 1.0), 0, 1)
w_crest = soft(crest_faces & ~gold)
w_trim = soft(gold & (shell | crest_faces))
w_arm = soft(shell & ~gold & ~red & ~crest_faces) * (1 - w_trim) * (1 - w_crest)
weights = {'armour': w_arm, 'trim': w_trim, 'crest': w_crest}
pixels = np.load(HERE / 'work' / 'native_shading' / 'pixels.npz')
# one shared set of ramps (merge_head_material.py merges the head into the body material and requires them equal):
# armour and trim keep the body's ramps, the crest ramp is fitted on the head's crest and appended to both (the body
# mask has no crest channel)
crest = NS.transfer_ramps(head, {'crest': w_crest}, pixels, {'crest': 'crest'}, TIERS, reference=828, gain=GAIN)
R.write_mask(list(weights.values()), T / 'ttn_head_region_mask.png', size=N)
cfg = json.loads((T / 'ttn_ramps.json').read_text())
body = cfg['materials'][0]
body['regions'] = ['armour', 'trim', 'crest']
for t in TIERS:
    body['ramps'][t] = body['ramps'][t][:2] + crest[t]
cfg['materials'] = [body, {'base': 'TitanHead_A', 'prefix': 'TitanHead', 'mask': 'ttn_head_region_mask.png',
                           'regions': body['regions'], 'palettes': TIERS, 'ramps': body['ramps']}]
(T / 'ttn_ramps.json').write_text(json.dumps(cfg, indent=1) + '\n')
print('HEAD regions', {k: int((w > 0.5).sum()) for k, w in weights.items()})
