#!/usr/bin/env python3
"""Leak per mip level for one layout + one 2K map under different gutter fills.

    leak_fills.py <layout glb> <map png | glb:path:image> <uv image name> <out json> [--fills as_is,black,...]
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
import uvlib  # noqa: E402

FILLS = {'as_is': lambda img, ctx: img.astype(np.float64), 'black': leak.fill_black, 'nearest': leak.fill_nearest,
         'pushpull_global': leak.fill_pushpull_global, 'pushpull_owned': leak.fill_pushpull_owned}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('layout')
    parser.add_argument('image')
    parser.add_argument('uv_image')
    parser.add_argument('out')
    parser.add_argument('--fills', default='as_is,black,nearest,pushpull_global,pushpull_owned')
    parser.add_argument('--save-dir')
    args = parser.parse_args()
    if args.image.startswith('glb:'):
        _, path, name = args.image.split(':', 2)
        img = np.asarray(uvlib.glb_image(path, name), np.float64)
    else:
        img = np.asarray(Image.open(args.image).convert('RGB'), np.float64)
    pos, uv = uvlib.lod0_uv(args.layout, args.uv_image)
    ctx = leak.context(uv, pos, img.shape[0])
    result = {'layout': args.layout, 'image': args.image, 'islands': ctx['n'],
              'atlas_pct': round(100 * float((ctx['labels'] >= 0).mean()), 1), **leak.gaps(ctx), 'fills': {}}
    cache = {}
    for name in args.fills.split(','):
        t = time.time()
        filled = FILLS[name](img, ctx)
        if args.save_dir:
            Path(args.save_dir).mkdir(parents=True, exist_ok=True)
            Image.fromarray(np.clip(np.round(filled), 0, 255).astype(np.uint8)).save(f'{args.save_dir}/{name}.png')
        result['fills'][name] = leak.leak(filled, ctx, pure_cache=cache)
        print(name, f'{time.time() - t:.0f}s', json.dumps(result['fills'][name]), flush=True)
    Path(args.out).write_text(json.dumps(result, indent=1))
