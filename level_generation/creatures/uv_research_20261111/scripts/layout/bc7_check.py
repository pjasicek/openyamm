#!/usr/bin/env python3
"""BC7 4x4 blocks across island borders, through the engine's own cooker (openyamm_model_texture_cook: box mips in
linear sRGB, colour_mip_sharpening 0.75 as the creature class, BC7 like colour_hero).

Level 0: encoding error (mean |decoded - source| over RGB, 8-bit levels) of island texels in blocks that hold only
their own island's texels and fill, versus blocks shared with another island's texels or fill, versus blocks
that hold gutter texels at all. Levels 1-5: leak of the cooked chain (BC7 + sharpening) against the island-alone
reference of leak.py, next to the plain box chain of the same image.

    bc7_check.py <layout glb | npz> <filled 2K png>... --out json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import leak  # noqa: E402
import uvlib  # noqa: E402
from repack import load_layout  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument('layout')
parser.add_argument('images', nargs='+')
parser.add_argument('--out', required=True)
parser.add_argument('--work', default='/tmp')
args = parser.parse_args()
pos, uv = load_layout(args.layout)
ctx = leak.context(uv, pos, 2048)
labels, owner = ctx['labels'], ctx['owner']
blocks_owner = owner.reshape(512, 4, 512, 4).transpose(0, 2, 1, 3).reshape(512, 512, 16)
mixed_block = blocks_owner.min(2) != blocks_owner.max(2)
gutter_block = (labels.reshape(512, 4, 512, 4).transpose(0, 2, 1, 3).reshape(512, 512, 16) < 0).any(2)
mixed = np.repeat(np.repeat(mixed_block, 4, 0), 4, 1)
gutter = np.repeat(np.repeat(gutter_block, 4, 0), 4, 1)
inside = labels >= 0
result = {'layout': args.layout, 'blocks_mixed_pct_of_island_texels': round(100 * float(mixed[inside].mean()), 2),
          'blocks_with_gutter_pct_of_island_texels': round(100 * float(gutter[inside].mean()), 2), 'images': {}}
for path in args.images:
    img = np.asarray(Image.open(path).convert('RGB'), np.float64)
    chain = uvlib.cook_mips(path, args.work, levels=6, sharpen=0.75)
    err = np.abs(chain[0] - img).mean(2)
    entry = {'bc7_l0_clean_block': round(float(err[inside & ~gutter].mean()), 2),
             'bc7_l0_gutter_block_same_island': round(float(err[inside & gutter & ~mixed].mean()), 2),
             'bc7_l0_mixed_block': round(float(err[inside & mixed].mean()), 2),
             'bc7_l0_p99_mixed': round(float(np.percentile(err[inside & mixed], 99)), 1),
             'bc7_l0_p99_clean': round(float(np.percentile(err[inside & ~gutter], 99)), 1)}
    # leak of the cooked chain: swap the box chain for the decoded one
    lin_chain = [uvlib.srgb_to_linear(c) for c in chain]
    cooked = leak.leak(img, ctx, chain=lin_chain, sharpen=0.75)
    sharp = leak.leak(img, ctx, sharpen=0.75)
    plain = leak.leak(img, ctx)
    entry['leak_cooked'] = [r['leak_mean'] for r in cooked]
    entry['leak_cooked_over4'] = [r['over_limit_pct'] for r in cooked]
    entry['leak_box_sharpened'] = [r['leak_mean'] for r in sharp]
    entry['leak_box_sharpened_over4'] = [r['over_limit_pct'] for r in sharp]
    entry['leak_box'] = [r['leak_mean'] for r in plain]
    entry['leak_box_over4'] = [r['over_limit_pct'] for r in plain]
    result['images'][Path(path).name] = entry
    print(Path(path).name, json.dumps(entry), flush=True)
Path(args.out).write_text(json.dumps(result, indent=1))
