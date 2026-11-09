"""Protect the opaque pink lacquer inside the generated brass charm's closed body."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

BASE = Path(__file__).resolve().parent
OUT = BASE / 'brass_matte_repair'
OUT.mkdir(exist_ok=True)
HUD = BASE.parents[2]
sys.path.insert(0, str(HUD))
import matte
import registration
from finalize_classification import read

spec = importlib.util.spec_from_file_location('fitting', HUD / 'pilots/boots/process.py')
fitting = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fitting)
previous = json.loads((BASE / 'processing.json').read_text())
record = next(c for c in previous['cells'] if c['cell'] == 'engine--icons--item147.bmp')
raw_path = HUD / 'checkpoint/attempts' / previous['attempt'] / 'raw.png'
assert hashlib.sha256(raw_path.read_bytes()).hexdigest() == previous['raw_sha256']
raw = Image.open(raw_path).convert('RGB').crop(record['raw_crop_xyxy'])
clean, stats = matte.extract(raw)
rgba = np.array(clean)
generated_mask = rgba[:, :, 3] >= 128
# The raw visibly encloses solid pink lacquer inside its gold rim. Its only genuine opening is the top ring.
# Derive protection from this generated outline; no native alpha or native RGB is substituted.
body = ndimage.binary_erosion(ndimage.binary_fill_holes(generated_mask), iterations=3)
body[:round(raw.height * .16)] = False
changed_alpha = int((body & (rgba[:, :, 3] < 255)).sum())
rgba[body, :3] = np.array(raw)[body]
rgba[body, 3] = 255
protected = Image.fromarray(rgba)
protected.save(OUT / 'clean-master.png')
candidate = fitting.transform(protected.convert('RGBa'), (72, 102),
                              record['uniform_scale_translate_xy']).convert('RGBA')
candidate.save(OUT / 'item147-before-contour.png')
rgba = np.array(candidate)
original = rgba.copy()
mask = rgba[:, :, 3] >= 128
# External contour only: enclosed lacquer is excluded even if an antialias sample falls below128.
filled = ndimage.binary_fill_holes(mask)
band = (rgba[:, :, 3] > 0) & ~ndimage.binary_erosion(filled, iterations=3)
rgb = rgba[:, :, :3].astype(int)
excess = np.maximum(0, np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1] - 2)
correction = np.where(band, excess, 0)
for channel in (0, 2):
    rgba[:, :, channel] = np.maximum(0, rgb[:, :, channel] - correction)
assert np.array_equal(rgba[:, :, 3], original[:, :, 3])
assert np.array_equal(rgba[~band], original[~band])
candidate = Image.fromarray(rgba)
artifact = OUT / 'item147.png'
candidate.save(artifact)
job = next(j for j in read('jobs.json')['jobs'] if j['id'] == 'inventory_items-9ce057f0fa21')
member = next(m for m in job['members'] if m['id'] == record['cell'])
target = next(t for t in read('expected_targets.json')['targets'] if t['id'] == member['target'])
evidence = registration.evidence(member, target, artifact, OUT / 'registration')
edge = Image.new('RGB', (144, 126))
for j, bg in enumerate(('#eeeeee', '#171717')):
    tile = Image.new('RGBA', candidate.size, bg)
    tile.alpha_composite(candidate)
    edge.paste(tile.convert('RGB'), (72 * j, 24))
edge.resize((576, 504), Image.Resampling.NEAREST).save(OUT / 'enlarged-edges.png')
sheet = Image.open(BASE / 'complete-sheet.png').convert('RGB')
tile = Image.new('RGBA', candidate.size, '#292929')
tile.alpha_composite(candidate)
sheet.paste(tile.convert('RGB'), (8, 224))
sheet.save(OUT / 'complete-sheet.png')
report = dict(attempt=previous['attempt'], raw_sha256=previous['raw_sha256'],
              raw_crop_xyxy=record['raw_crop_xyxy'], cleanup=stats,
              protected_region='Generated filled alpha128 body eroded3 raw pixels, excluding top16% ring area',
              protected_pixels=int(body.sum()), protected_alpha_pixels=changed_alpha,
              uniform_scale_translate_xy=record['uniform_scale_translate_xy'],
              contour_corrected_pixels=int((correction > 0).sum()), contour_width_x2=3,
              script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              matte_sha256=hashlib.sha256(Path(matte.__file__).read_bytes()).hexdigest(),
              fitting_sha256=hashlib.sha256(Path(fitting.__file__).read_bytes()).hexdigest(),
              artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(), **evidence)
(OUT / 'processing.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
