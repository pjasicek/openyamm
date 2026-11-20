"""Compare the actual jade highlight and suspension opening; never auto-accept artwork."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parent
HUD = OUT.parents[2]
ROOT = HUD.parents[2]
sys.path.insert(0, str(HUD))
from freeze_targets import rendered

native = rendered(Image.open(ROOT / 'assets_dev/engine/icons/item148.bmp'), 'item')
native = native.resize((68, 96), Image.Resampling.NEAREST)
candidate = Image.open(OUT / 'item148.png').convert('RGBA')
assert candidate.size == native.size
proof = Image.new('RGB', (136, 96), '#444444')
records = []
for i, im in enumerate((native, candidate)):
    bg = Image.new('RGBA', im.size, '#444444')
    bg.alpha_composite(im)
    proof.paste(bg.convert('RGB'), (68 * i, 0))
    rgba = np.array(im)
    rgb = rgba[:, :, :3].astype(int)
    yy, xx = np.indices(rgba.shape[:2])
    mask = rgba[:, :, 3] >= 128
    stone = ((rgb[:, :, 1] > rgb[:, :, 0] + 10) & mask &
             (xx >= 10) & (xx < 60) & (yy >= 15) & (yy < 90))
    weights = np.maximum(0, np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - 140) * stone
    cy, cx = ndimage.center_of_mass(weights)
    labels, count = ndimage.label(ndimage.binary_fill_holes(mask) & ~mask)
    holes = []
    for j in range(1, count + 1):
        y, x = ndimage.center_of_mass(labels == j)
        holes.append(dict(area=int((labels == j).sum()), center=[x, y]))
    band = (rgba[:, :, 3] > 0) & ~ndimage.binary_erosion(mask, iterations=4)
    spill = np.maximum(0, np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1])
    spill = spill * rgba[:, :, 3] / 255
    records.append(dict(highlight_centroid_x2=[cx, cy], highlight_weight=int(weights.sum()), holes=holes,
                        max_contour_weighted_magenta=float(spill[band].max()),
                        stone_row_bounds={str(y): [int(np.where(stone[y])[0].min()),
                                                  int(np.where(stone[y])[0].max())]
                                          for y in (25, 35, 45, 55, 65, 75) if stone[y].any()}))
proof.resize((544, 384), Image.Resampling.NEAREST).save(OUT / 'item148-enlarged-comparison.png')
Image.open(OUT / 'item148-light-dark.png').resize((544, 480), Image.Resampling.NEAREST).save(
    OUT / 'item148-enlarged-edges.png')
result = dict(method='Bright stone centroid weighted by max(0,min(R,B)-140) within green stone mask; '
                    'diagnostic, not geometry proof alone.',
              script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              artifact_sha256=hashlib.sha256((OUT / 'item148.png').read_bytes()).hexdigest(),
              native_x2=records[0], candidate_x2=records[1])
(OUT / 'highlight-diagnostic.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
