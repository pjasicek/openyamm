#!/usr/bin/env python3
"""LOD0 bounds of finished models (the engine scales a decoration by its LOD0 height): height, width (x) and depth
(z) in metres and the width / height ratio next to the sprite's. Usage: bounds.py <id> ..."""
import glob, os, sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools'))
import link_static_model_lods as link
for sid in sys.argv[1:]:
    doc, _ = link.read_glb(HERE / 'work' / f'mm6_deco_{sid}.glb')
    mesh = doc['meshes'][doc['nodes'][0]['mesh']]
    lo = [min(doc['accessors'][p['attributes']['POSITION']]['min'][a] for p in mesh['primitives']) for a in range(3)]
    hi = [max(doc['accessors'][p['attributes']['POSITION']]['max'][a] for p in mesh['primitives']) for a in range(3)]
    sprite = Image.open(sorted(glob.glob(str(REPO / 'assets_dev/engine/decorations_x2' / f'{sid}_p*.png')))[0])
    x0, y0, x1, y1 = sprite.getchannel('A').point(lambda v: 255 if v > 128 else 0).getbbox()
    h = hi[1] - lo[1]
    print(sid, 'height', round(h, 2), 'width', round(hi[0] - lo[0], 2), 'depth', round(hi[2] - lo[2], 2),
          'w/h', round((hi[0] - lo[0]) / h, 2), 'sprite w/h', round((x1 - x0) / (y1 - y0), 2))
