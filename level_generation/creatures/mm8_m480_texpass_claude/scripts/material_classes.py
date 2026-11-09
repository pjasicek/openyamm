"""Material class map on the texture-pass layout (CLAUDE_CREATURE_TEXTURES.md labels), carried from the approved
per-set class maps of mm8_m480_claude/textures (body set at x 0..1023 and head set at x 1056..2079 of the installed
2080x1024 atlas), nearest, at the same surface points. Usage: material_classes.py <layout npz> <raster npz> <out png>"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import texlib  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
T = HERE.parent / 'mm8_m480_claude' / 'textures'
layout, raster, out = sys.argv[1:4]
before = np.load(HERE / 'work' / 'lod0_before.npz')
atlas = np.zeros((1024, 2080), np.uint8)
atlas[:, :1024] = np.asarray(Image.open(T / 'm480_material_classes.png'))
atlas[:, 1056:] = np.asarray(Image.open(T / 'm480_head_material_classes.png'))
r = np.load(raster)
cov, uv = texlib.corresponding_uv(r['tri_id'], r['bary'], before['uv'][before['tri']])
size = r['tri_id'].shape[0]
classes = np.zeros((size, size), np.uint8)
classes[cov] = texlib.nearest(atlas[..., None], uv)[:, 0]
hole = cov & (classes == 0)                 # points in the approved sets' gutters: nearest labelled texel
classes[hole] = texlib.pad(classes, classes > 0)[hole]
Image.fromarray(classes).save(out)
print('CLASSES', out, np.bincount(classes[cov], minlength=12).tolist())
