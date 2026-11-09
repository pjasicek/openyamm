"""MM7 Roc tier ramps on the shared MM8 Thunderbird skin (same render, same palettes 553-555).

The MM7 frames draw the flight feathers with palette indices 187-249, which each palette colours differently
(Roc grey-olive, Greater Roc red-brown, Thunderbird near-black); MM8 uses the palette-invariant greens 128-186.
So the body and texture are the MM8 model's, and only the ramps are fitted again from the MM7 standing frames,
with the m552 compose method (mm8_m552_claude/scripts/compose_thunderbird.py): the region's texels ranked by
luminance take the native colours of that region in the same rank, albedo gains 1.45 body / 1.10 feathers.
Writes textures/m390_ramps.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
REPO = P.parents[2]
sys.path[:0] = [str(P.parent / 'mm6_gob_claude/scripts'), str(P.parent / 'claude_shared')]
import compose_textures_v2 as C  # noqa: E402
import region_variants as RV  # noqa: E402

M552 = P.parent / 'mm8_m552_claude/textures'
GAIN = (1.45, 1.10)
palettes = {pid: np.frombuffer((REPO / f'assets_dev/worlds/mm8/textures/pal{pid}.act').read_bytes()[:768],
                               np.uint8).reshape(256, 3) / 255 for pid in (553, 554, 555)}
indices = np.concatenate([np.asarray(Image.open(REPO / f'assets_dev/worlds/mm7/sprites/m390sa{view}.bmp')).ravel()
                          for view in range(5)])
indices = indices[indices != 0]
ph, ps, pv = C.hsv(palettes[553])
pg = (ph >= 55).astype(int)
graded = RV.load_srgb(M552 / 'm552_basecolor.png', 1024)
lum = RV.luminance(graded)
mask = np.stack([np.asarray(ch, np.float32) / 255 for ch in Image.open(M552 / 'm552_region_mask.png').split()], -1)
variants = {'m390_a': 553, 'm390_b': 554, 'm390_c': 555}
ramps = {name: [] for name in variants}
reports = []
encode = lambda x: np.where(x <= .0031308, x * 12.92, 1.055 * np.maximum(x, 0) ** (1 / 2.4) - .055)
for channel in range(2):
    core = mask[..., channel] >= .9
    order = np.argsort(lum[core])
    rank = np.empty(order.size)
    rank[order] = (np.arange(order.size) + .5) / order.size
    ids = indices[(pg[indices] == channel) & (ps[indices] > .12) & (pv[indices] > .08)
                  & ((channel == 1) | (ps[indices] < .75))]
    assert len(ids) > 100, (channel, len(ids))
    targets = {}
    for name, pid in variants.items():
        colors = RV.srgb_to_linear(np.clip(palettes[pid][ids] * GAIN[channel], 0, 1))
        colors = colors[np.argsort(colors @ RV.LUMA)]
        q = .06 + .91 * rank
        target = graded.copy()
        target[core] = encode(np.clip(colors[np.minimum((q * len(colors)).astype(int), len(colors) - 1)], 0, 1))
        targets[name] = target
    fitted, report = RV.fit_ramps(graded, targets, mask[..., channel])
    for name in variants:
        ramps[name].append(fitted[name])
    reports.append({'region': channel, 'native_samples': int(len(ids)),
                    'index_range': [int(ids.min()), int(ids.max())], 'fit': report})
config = dict(variants=list(variants), palettes=variants, regions=['brown body plumage', 'flight feathers'],
              materials=[dict(base='Thunderbird_A', prefix='Roc', mask='m390_region_mask.png', ramps=ramps)],
              gains=GAIN, report=reports)
(P / 'textures/m390_ramps.json').write_text(json.dumps(config, indent=2) + '\n')
print(json.dumps(reports))
