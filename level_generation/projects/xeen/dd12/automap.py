#!/usr/bin/env python3
"""automap.py <map.blv> <out.jpg> [party_z] [x0 y0 x1 y1]: the indoor automap as the game draws it with every outline
revealed (game/indoor/IndoorWorldRuntime.cpp: each BLV outline a line, grey 200 - min(100, |z - party z| / 8)), from
`oymap export`. Black ground, north up."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json, subprocess, sys
from PIL import Image, ImageDraw
R = _REPO_ROOT
blv, out = sys.argv[1], sys.argv[2]
pz = float(sys.argv[3]) if len(sys.argv) > 3 else -2560
tmp = R + '/output/studio_cal/dd12/tex/automap_export.json'
subprocess.run([R + '/openyamm-studio/build-xeen/oymap', 'export', blv, '--out', tmp], check=True,
               stdout=subprocess.DEVNULL)
m = json.load(open(tmp))['map']
V = m['vertices']
if len(sys.argv) > 7:
    x0, y0, x1, y1 = map(float, sys.argv[4:8])
else:
    (x0, y0, _), (x1, y1, _) = m['bounds']['min'], m['bounds']['max']
W = 2000
s = W / (x1 - x0)
Hh = int((y1 - y0) * s) + 1
im = Image.new('RGB', (W, Hh), (0, 0, 0))
d = ImageDraw.Draw(im)
lines = sorted(m['outlines'], key=lambda o: -abs(o[4] - pz))
for a, b, f1, f2, z, fl in lines:
    g = max(0, 200 - min(100, int(abs(z - pz) / 8)))
    pa, pb = V[a], V[b]
    d.line([((pa[0] - x0) * s, (y1 - pa[1]) * s), ((pb[0] - x0) * s, (y1 - pb[1]) * s)], fill=(g, g, g), width=2)
im.save(out, quality=88)
print(out, im.size)
