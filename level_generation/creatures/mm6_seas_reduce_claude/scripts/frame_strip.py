#!/usr/bin/env python3
"""Join clip_frames.py renders: one row per prefix, one column per frame -> <out>.png.
Usage: frame_strip.py <out.png> <view> <frames,...> <prefix> [<prefix> ...]"""
import sys
from PIL import Image
out, view, frames, prefixes = sys.argv[1], sys.argv[2], sys.argv[3].split(','), sys.argv[4:]
s = Image.new('RGB', (360 * len(frames), 360 * len(prefixes)))
for j, p in enumerate(prefixes):
    for i, f in enumerate(frames):
        s.paste(Image.open(f'{p}_{view}_{int(f):02d}.png').convert('RGB'), (i * 360, j * 360))
s.save(out)
