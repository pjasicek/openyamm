"""Remove confirmed residual magenta from the hand charm's narrow contour only."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

P = Path(__file__).resolve().parent
OUT = P / 'hand_final'
OUT.mkdir(exist_ok=True)
source = P / '7item132.png'
rgba = np.array(Image.open(source).convert('RGBA'))
original = rgba.copy()
mask = rgba[:, :, 3] >= 128
band = (rgba[:, :, 3] > 0) & ~ndimage.binary_erosion(mask, iterations=4)
rgb = rgba[:, :, :3].astype(int)
excess = np.maximum(0, np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1] - 2)
correction = np.where(band, excess, 0)
for c in (0, 2):
    rgba[:, :, c] = np.maximum(0, rgb[:, :, c] - correction)
assert np.array_equal(rgba[:, :, 3], original[:, :, 3])
assert np.array_equal(rgba[~band], original[~band])
im = Image.fromarray(rgba)
im.save(OUT / '7item132.png')
edge = Image.new('RGB', (80, 132))
for j, bg in enumerate(('#eeeeee', '#171717')):
    tile = Image.new('RGBA', im.size, bg)
    tile.alpha_composite(im)
    edge.paste(tile.convert('RGB'), (j * 40, 24))
edge.save(OUT / '7item132-light-dark.png')
edge.resize((400, 660), Image.Resampling.NEAREST).save(OUT / '7item132-enlarged-edges.png')
sheet = Image.open(P / 'eye_final/complete-sheet.png').convert('RGB')
tile = Image.new('RGBA', im.size, '#292929')
tile.alpha_composite(im)
sheet.paste(tile.convert('RGB'), (208, 224))
sheet.save(OUT / 'complete-sheet.png')
(OUT / 'cleanup.json').write_text(json.dumps(dict(
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    artifact_sha256=hashlib.sha256((OUT / '7item132.png').read_bytes()).hexdigest(),
    corrected_pixels=int((correction > 0).sum()), contour_width_x2=4, retained_excess=2,
    alpha_unchanged=True, interior_unchanged=True,
    reason='Native silver hand contour has zero magenta excess; enlarged candidate audit confirms residual dark spill.',
    algorithm='Subtract excess beyond2 equally from R and B in visible four-pixel contour only.'), indent=2) + '\n')
