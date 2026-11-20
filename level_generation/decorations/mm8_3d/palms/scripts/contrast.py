#!/usr/bin/env python3
"""Luminance spread of a palm's LOD0 front review render (work/<id>/rv_Plant_front.png, Eevee with sun shadows) against
its native x2 sprite: 10th / 50th / 90th percentile of Rec. 709 luma (sRGB 0-255) over opaque pixels, and the mean
colour. Usage: contrast.py <id> [...]  (prints one line per palm)"""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palm_common as pc


def stats(path):
    x = np.asarray(Image.open(path).convert('RGBA')).astype(float)
    m = x[..., 3] > 128
    rgb = x[m][:, :3]
    y = rgb @ np.array([0.2126, 0.7152, 0.0722])
    p10, p50, p90 = np.percentile(y, [10, 50, 90])
    return {'p10': p10, 'p50': p50, 'p90': p90, 'spread': p90 - p10, 'mean': rgb.mean(0)}


def compare(sid, render='rv_Plant_front.png'):
    s = stats(os.path.join(pc.SPRITES, pc.SPECIES[sid]['sprite']))
    m = stats(os.path.join(pc.work(sid), render))
    return s, m


if __name__ == '__main__':
    render = os.environ.get('RENDER', 'rv_Plant_front.png')
    for sid in sys.argv[1:]:
        s, m = compare(sid, render)
        print(f"CONTRAST {sid} sprite p10/p50/p90 {s['p10']:.0f}/{s['p50']:.0f}/{s['p90']:.0f} spread {s['spread']:.0f} | "
              f"model {m['p10']:.0f}/{m['p50']:.0f}/{m['p90']:.0f} spread {m['spread']:.0f} | mean delta "
              f"{np.round(m['mean'] - s['mean'], 1).tolist()}")
