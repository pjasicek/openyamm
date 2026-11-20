"""MM7 Troll tier ramps on the shared MM8 Troll Peasant skin (same render at 1/1.515 raster, MM7 palettes 499/505/509).

The m480 method (mm8_m480_claude/scripts/compose_textures.py) samples native palette indices of each region in a
box on the standing frames (belly skin, loin wrap, crest, mottled back), sorts them by tier-A luminance, keeps the
15-95 % slice and gives each tier a luminance-neutral tone: ramp = stop * mean(tier colour) / lum(mean(tier-A colour))
* (1, 1, .7, .85)[region] over the full range 0..1.
The MM7 palettes order their indices differently (MM7 skin 0-126 is the same in every tier; the crest and the hair
on the back use 133-157, the wrap 165-198, while MM8 recolours its skin too), so the MM7 index ranges are read from
the MM7 palettes and the same boxes, mapped onto the smaller MM7 raster by the frames' bounding boxes. Tier A of MM7
(palette 499) is the luminance reference, as 481 is for MM8.
The method is checked first by rebuilding the installed MM8 ramps from the MM8 frames.
Writes textures/m461_ramps.json.
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parents[1]
REPO = P.parents[2]
sys.path.insert(0, str(P.parent / 'claude_shared'))
import region_variants as RV  # noqa: E402

SOURCE = REPO / 'assets_source/worlds/mm8/models/mm8_m480.glb'
MM8_SPRITES = REPO / 'assets_legacy/sprites_mm8_monsters_20261019/assets_dev/engine/sprites'
MM7_SPRITES = REPO / 'assets_dev/engine/sprites'
FACTORS = (1., 1., .7, .85)
NAMES = ('skin', 'loin wrap', 'crest', 'mottled back')
# MM8 boxes (x0, y0, x1, y1 on the 256 px m480 canvas) and index ranges, as in the m480 script.
MM8_REGIONS = [('sa0', (110, 110, 139, 149), range(40, 132)), ('sa0', (111, 157, 141, 181), range(170, 195)),
               ('sa0', (110, 51, 143, 78), range(139, 156)), ('sa4', (109, 93, 147, 135), range(211, 240))]
# MM7: the same boxes, MM7 index ranges (skin is palette-invariant; back hair shares the crest indices).
MM7_RANGES = [range(40, 127), range(165, 199), range(133, 158), range(133, 158)]
VARIANTS = {'m461_a': 499, 'm461_b': 505, 'm461_c': 509}
encode = lambda x: np.where(x <= .0031308, x * 12.92, 1.055 * np.maximum(x, 0) ** (1 / 2.4) - .055)


def palette(world, pid):
    directory = REPO / f'assets_dev/worlds/{world}/textures'
    name = next(e for e in os.listdir(directory) if e.lower() == f'pal{pid}.act')
    return np.frombuffer((directory / name).read_bytes()[:768], np.uint8).reshape(256, 3) / 255


def bitmap(directory, name):
    entry = next(e for e in os.listdir(directory) if e.lower() == name + '.bmp')
    return np.asarray(Image.open(directory / entry))


def bounds(ids):
    rows, cols = np.nonzero(ids)
    return rows.min(), rows.max(), cols.min(), cols.max()


def samples(stem, regions, reference, mapping=None):
    out = []
    for view, (x0, y0, x1, y1), indices in regions:
        ids = bitmap(MM8_SPRITES if mapping is None else MM7_SPRITES, stem + view)
        if mapping is not None:
            x0, y0, x1, y1 = mapping(view, (x0, y0, x1, y1))
        picked = ids[y0:y1, x0:x1].ravel()
        picked = picked[np.isin(picked, list(indices))]
        assert len(picked) > 100, (view, len(picked))
        out.append(picked[np.argsort(RV.luminance(reference[picked]))])
    return out


def ramps_for(native, palettes, reference):
    ramps = {name: [] for name in palettes}
    for region, picked in enumerate(native):
        selected = picked[int(len(picked) * .15):max(int(len(picked) * .95), 1)]
        luminance = float(RV.srgb_to_linear(reference[selected]).mean(0) @ RV.LUMA)
        for name, pal in palettes.items():
            tone = RV.srgb_to_linear(pal[selected]).mean(0) / max(luminance, 1e-5)
            ramps[name].append({'range': [0.0, 1.0], 'colors': [np.clip(stop * tone * FACTORS[region], 0, 1).tolist()
                                                                for stop in np.linspace(0, 1, 16)]})
    return ramps


def mm7_box(view, box):
    """Map an m480 box onto the MM7 frame: same render, scaled about the bounding boxes' bottom centres."""
    b8, b7 = bounds(bitmap(MM8_SPRITES, 'm480' + view)), bounds(bitmap(MM7_SPRITES, 'm461' + view))
    factor = (b7[1] - b7[0]) / (b8[1] - b8[0])
    cx8, cx7 = (b8[2] + b8[3]) / 2, (b7[2] + b7[3]) / 2
    x0, y0, x1, y1 = box
    return (round(cx7 + (x0 - cx8) * factor), round(b7[1] - (b8[1] - y0) * factor),
            round(cx7 + (x1 - cx8) * factor), round(b7[1] - (b8[1] - y1) * factor))


doc, _ = RV.read_glb(SOURCE)
installed = {m['name'].split('_')[-1].lower(): m['extras']['openyamm_region_ramps'] for m in doc['materials']}
mm8_pal = {tier: palette('mm8', pid) for tier, pid in zip('abc', (481, 482, 483))}
rebuilt = ramps_for(samples('m480', MM8_REGIONS, mm8_pal['a']), mm8_pal, mm8_pal['a'])
check = [{'tier': tier, 'region': r,
          'max_abs_linear': round(float(np.abs(np.subtract(rebuilt[tier][r]['colors'],
                                                           installed[tier][r]['colors'])).max()), 6)}
         for tier in 'abc' for r in range(4)]
mm7_pal = {name: palette('mm7', pid) for name, pid in VARIANTS.items()}
regions7 = [(view, box, indices) for (view, box, _), indices in zip(MM8_REGIONS, MM7_RANGES)]
native7 = samples('m461', regions7, mm7_pal['m461_a'], mm7_box)
ramps = ramps_for(native7, mm7_pal, mm7_pal['m461_a'])
report = {'method_check_mm8_rebuild': check,
          'mm7_boxes': {NAMES[r]: [regions7[r][0], list(map(int, mm7_box(regions7[r][0], regions7[r][1])))]
                        for r in range(4)},
          'mm7_index_ranges': {NAMES[r]: [MM7_RANGES[r].start, MM7_RANGES[r].stop - 1] for r in range(4)},
          'mm7_samples': {NAMES[r]: int(len(native7[r])) for r in range(4)},
          'srgb_at_mid_stop': {name: [np.round(encode(np.asarray(ramps[name][r]['colors'][8])), 3).tolist()
                                      for r in range(4)] for name in VARIANTS}}
config = dict(variants=list(VARIANTS), palettes=VARIANTS, regions=list(NAMES),
              materials=[dict(base='TrollPeasant_A', prefix='Troll', mask='(installed m480 atlas mask)', ramps=ramps)],
              report=report)
(P / 'textures/m461_ramps.json').write_text(json.dumps(config, indent=2) + '\n')
print(json.dumps(report, indent=1))
