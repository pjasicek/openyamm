#!/usr/bin/env python3
"""Margin x fill study: the same Meshy paint carried onto re-packed layouts, then leak per mip level.

    margin_study.py <src layout glb> <src image 4K png> <out json> <name=layout.npz | name=orig> ... [--fills ...]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import leak  # noqa: E402
import transfer  # noqa: E402
import uvlib  # noqa: E402
from leak_fills import FILLS  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument('src_layout')
parser.add_argument('src_image')
parser.add_argument('out')
parser.add_argument('layouts', nargs='+')
parser.add_argument('--fills', default='black,nearest,pushpull_owned')
parser.add_argument('--save-dir')
args = parser.parse_args()
src = np.asarray(Image.open(args.src_image).convert('RGB'), np.float64)
pos, src_uv = uvlib.lod0_uv(args.src_layout)
results = {}
for item in args.layouts:
    name, path = item.split('=', 1)
    t = time.time()
    if path == 'orig':
        dst_uv, margin = src_uv, 2
    else:
        d = np.load(path)
        dst_uv, margin = d['uv'], int(d['margin'])
        assert np.allclose(d['pos'], pos)
    img = transfer.transfer(src, src_uv, dst_uv)
    ctx = leak.context(dst_uv, pos, 2048)
    entry = {'margin_px': margin, 'atlas_pct': round(100 * float((ctx['labels'] >= 0).mean()), 2), **leak.gaps(ctx),
             'fills': {}}
    cache, cache_sharp = {}, {}
    entry['fills_sharpened'] = {}
    for fill in args.fills.split(','):
        filled = FILLS[fill](img, ctx)
        if args.save_dir:
            Path(args.save_dir).mkdir(parents=True, exist_ok=True)
            Image.fromarray(np.clip(np.round(filled), 0, 255).astype(np.uint8)).save(
                f'{args.save_dir}/{name}_{fill}.png')
        entry['fills'][fill] = leak.leak(filled, ctx, pure_cache=cache)
        entry['fills_sharpened'][fill] = leak.leak(filled, ctx, pure_cache=cache_sharp, sharpen=0.75)
    results[name] = entry
    print(name, f'{time.time() - t:.0f}s', json.dumps({k: v for k, v in entry.items() if not k.startswith('fills')}),
          json.dumps({f: [r['leak_mean'] for r in v] for f, v in entry['fills'].items()}), flush=True)
    Path(args.out).write_text(json.dumps(results, indent=1))
