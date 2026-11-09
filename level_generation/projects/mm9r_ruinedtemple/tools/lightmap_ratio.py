"""Per-zone texel luminance ours / MM9's DAT lightmaps and B/R, G/R, from hue_vs_lightmaps.py's output (stdin)."""
import re
import sys
rows = {}
for line in sys.stdin:
    m = re.match(r"(.+?)\s+(MM9|ours)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", line)
    if m:
        r, g, b = map(float, m.group(3, 4, 5))
        rows.setdefault(m.group(1).strip(), {})[m.group(2)] = (0.2126 * r + 0.7152 * g + 0.0722 * b, b / r, g / r)
for zone, v in rows.items():
    if "MM9" in v and "ours" in v:
        (lm, bm, gm), (lo, bo, go) = v["MM9"], v["ours"]
        print(f"{zone:20} luma MM9 {lm:.3f} ours {lo:.3f} ratio {lo / lm:.2f}  B/R {bm:.2f}/{bo:.2f}  G/R {gm:.2f}/{go:.2f}")
