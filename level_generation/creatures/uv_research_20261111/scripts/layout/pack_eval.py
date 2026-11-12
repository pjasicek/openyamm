#!/usr/bin/env python3
"""Evaluate packed layouts against a reference layout of the same charts: atlas use (texel-centre union at 2048), UV
sum (overlap check), inside the unit square, gaps between islands (empty texels edge to edge), and whether every
island kept its relative scale (texel density ratio to the reference, p5/p95 across islands; 1.0 = uniform scale).

    pack_eval.py <reference npz|glb> <packed npz>... [--json out]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import leak  # noqa: E402
import uvlib  # noqa: E402
from repack import load_layout  # noqa: E402


def area(uv):
    d1, d2 = uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]
    return np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / 2


def evaluate(ref_uv, pos, uv, seconds=None):
    ctx = leak.context(uv, pos, 2048)
    isl = ctx['isl']
    ra, pa = area(ref_uv), area(uv)
    per = np.array([np.sqrt(pa[isl == i].sum() / max(ra[isl == i].sum(), 1e-18)) for i in range(isl.max() + 1)])
    per /= np.median(per)
    out = {'atlas_pct': round(100 * float((ctx['labels'] >= 0).mean()), 2), 'uv_sum_pct': round(100 * float(pa.sum()), 2),
           'inside_square': bool(uv.min() >= -1e-6 and uv.max() <= 1 + 1e-6), 'islands': ctx['n'],
           'scale_p5': round(float(np.percentile(per, 5)), 3), 'scale_p95': round(float(np.percentile(per, 95)), 3),
           **{k: round(v, 2) for k, v in leak.gaps(ctx).items()}}
    if seconds is not None:
        out['seconds'] = round(float(seconds), 1)
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('reference')
    parser.add_argument('packed', nargs='+')
    parser.add_argument('--json')
    args = parser.parse_args()
    pos, ref = load_layout(args.reference)
    results = {}
    for p in args.packed:
        d = np.load(p)
        assert np.allclose(d['pos'], pos)
        results[Path(p).stem] = evaluate(ref, pos, d['uv'], d['seconds'] if 'seconds' in d else None)
        print(Path(p).stem, json.dumps(results[Path(p).stem]), flush=True)
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=1))
