import json
import sys
from pathlib import Path
from PIL import Image
import numpy as np
from scipy import ndimage
p = Path(__file__).resolve().parent
root = p.parents[2]
sys.path.insert(0, str(root))
from finish import clean_solid, register_cell, check_existing
job = json.loads((root / 'jobs/g08166_v0_s0.json').read_text())
sources = json.loads((root / 'sources.json').read_text())
raw = Image.open(p / 'raw.png')
# Reviewed pink petals with yellow centers and green leaves on yellow.
# Old mask cuts into petals and adds pale outlines.
clean, stats = clean_solid(raw, [255, 255, 0])
# Preserve enclosed yellow centers whose immediate surroundings are pink petals.
rgb = np.array(raw.convert('RGB'))
yellow = (rgb[:,:,0].astype(int) > rgb[:,:,2].astype(int) + 45) & (rgb[:,:,1].astype(int) > rgb[:,:,2].astype(int) + 45)
labels, count = ndimage.label(yellow)
pixels = np.array(clean)
restored = 0
for label in range(1, count + 1):
    region = labels == label
    area = int(region.sum())
    if area < 8 or area > 2500:
        continue
    ring = ndimage.binary_dilation(region, iterations=3) & ~region
    colors = rgb[ring].astype(int)
    pink = (colors[:,0] > colors[:,1] * 1.2) & (colors[:,2] > colors[:,1] * 1.1)
    if pink.mean() < .15:
        continue
    pixels[region,:3] = rgb[region]
    pixels[region,3] = 255
    restored += 1
clean = Image.fromarray(pixels)
stats['enclosed_yellow_centers_restored'] = restored
cell = job['cells'][0]
cell['native_bounds'] = sources[cell['asset']]['native_bounds']
clean.save(p / (cell['asset'] + '.master.png'))
output, registration = register_cell(clean, job, cell, raw.size)
output.save(p / (cell['asset'] + '.png'))
(p / 'extraction_correction.json').write_text(json.dumps({'cleanup': stats, 'registration': registration, 'reason': 'Direct yellow extraction restores opaque foliage; enclosed yellow components adjacent to pink petals preserve flower centers without retaining exterior background.'}, indent=2) + '\n')
check_existing(job, sources, p)
