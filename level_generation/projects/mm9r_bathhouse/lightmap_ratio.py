#!/usr/bin/env python3
"""Per zone: texel luminance ours / MM9's DAT lightmaps and the chroma factor, from hue_vs_lightmaps.py output.
python3 lightmap_ratio.py work/hue_final.txt"""
import re
import sys

rows, factor = {}, {}
last = None
for line in open(sys.argv[1]):
    m = re.match(r"^(.*?)\s+(MM9|ours)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s", line)
    if m:
        last = m.group(1).strip()
        r, g, b = map(float, m.group(3, 4, 5))
        rows.setdefault(last, {})[m.group(2)] = 0.2126 * r + 0.7152 * g + 0.0722 * b
    elif "->" in line and last:
        factor[last] = line.split("->")[1].strip().split(";")[0]
for zone, v in rows.items():
    if "MM9" in v and "ours" in v:
        print(f"{zone:26s} lum MM9 {v['MM9']:.3f} ours {v['ours']:.3f} ratio {v['ours'] / v['MM9']:.2f}  {factor.get(zone, '')}")
