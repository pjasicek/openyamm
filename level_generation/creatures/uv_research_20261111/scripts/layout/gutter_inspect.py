#!/usr/bin/env python3
"""What fills the space between UV islands in a colour map: per distance band from the nearest island texel, the mean
absolute difference to that nearest island texel (0 = nearest-texel dilation), the share of near-black texels and of
texels closer in colour to a different island than to the nearest one.

    gutter_inspect.py <layout glb> <image png | glb:image-name> <label> [--json out.json]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import uvlib  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument('layout')
parser.add_argument('image')
parser.add_argument('label')
parser.add_argument('--json')
parser.add_argument('--uv-image', help='base-colour image name of the layout mesh (LOD0 pick)')
args = parser.parse_args()

if args.image.startswith('glb:'):
    _, path, name = args.image.split(':', 2)
    img = np.asarray(uvlib.glb_image(path, name), np.float64)
else:
    img = np.asarray(Image.open(args.image).convert('RGB'), np.float64)
size = img.shape[0]
pos, uv = uvlib.lod0_uv(args.layout, args.uv_image)
isl = uvlib.island_ids(uv, pos)
labels = uvlib.raster_labels(uv, isl, size)
covered = labels >= 0
dist, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
nearest = img[iy, ix]
diff = np.abs(img - nearest).mean(2)
black = img.max(2) < 8
bands = [(0.5, 1.5, '1'), (1.5, 2.5, '2'), (2.5, 4.5, '3-4'), (4.5, 8.5, '5-8'), (8.5, 16.5, '9-16'),
         (16.5, 1e9, '>16')]
rows = []
for lo, hi, name in bands:
    m = (~covered) & (dist >= lo) & (dist < hi)
    if not m.any():
        continue
    rows.append({'band_px': name, 'share_of_atlas_pct': round(100 * m.mean(), 2),
                 'mean_abs_diff_to_nearest_island': round(float(diff[m].mean()), 1),
                 'p90_abs_diff': round(float(np.percentile(diff[m], 90)), 1),
                 'black_pct': round(100 * float(black[m].mean()), 1)})
# inside islands for scale: mean abs difference between 4-neighbours inside one island (texture "busyness")
inside = covered[:, 1:] & covered[:, :-1] & (labels[:, 1:] == labels[:, :-1])
busy = float(np.abs(img[:, 1:] - img[:, :-1]).mean(2)[inside].mean())
result = {'label': args.label, 'image_px': size, 'islands': int(isl.max() + 1),
          'gutter_pct': round(100 * float((~covered).mean()), 1), 'neighbour_diff_inside_islands': round(busy, 1),
          'bands': rows}
print(json.dumps(result, indent=1))
if args.json:
    Path(args.json).write_text(json.dumps(result, indent=1))
