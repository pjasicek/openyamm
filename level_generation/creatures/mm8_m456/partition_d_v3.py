"""Separate interleaving pose bounds without cutting any visible foreground."""
import json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from process import ROOT, queue, save

data = json.loads((ROOT / 'compact_jobs.json').read_text())
job = data['jobs']['d_v3']
raw = Image.open(ROOT / job['selected_raw']).convert('RGBA')
a = np.array(raw)
labels, _ = ndi.label(a[:, :, 3] > 4)
sizes = np.bincount(labels.ravel())
sizes[0] = 0
components = []
for label in np.argsort(sizes)[-5:]:
    ys, xs = np.where(labels == label)
    components.append((int(ys.min()) >= 588, int(xs.min()), int(label)))
components.sort()
seeds = np.zeros(labels.shape, dtype=np.uint8)
for index, (_, _, label) in enumerate(components):
    seeds[labels == label] = index + 1
_, nearest = ndi.distance_transform_edt(seeds == 0, return_indices=True)
owner = seeds[tuple(nearest)]
assert set(np.unique(owner)) == {1, 2, 3, 4, 5}
folder = ROOT / 'extraction_masks'
folder.mkdir(exist_ok=True)
rectangles, masks, evidence = {}, {}, {}
coverage = np.zeros(owner.shape, dtype=np.uint8)
for index, name in enumerate(job['frames']):
    selected = owner == index + 1
    occupied = selected & (a[:, :, 3] > 0)
    ys, xs = np.where(occupied)
    box = [max(0, int(xs.min()) - 4), max(0, int(ys.min()) - 4),
           min(raw.width, int(xs.max()) + 5), min(raw.height, int(ys.max()) + 5)]
    x0, y0, x1, y1 = box
    path = folder / (name + '.png')
    Image.fromarray(selected[y0:y1, x0:x1].astype(np.uint8) * 255).save(path)
    rectangles[name] = box
    masks[name] = {'path': str(path.relative_to(ROOT)), 'sha256': queue.sha(path)}
    coverage[occupied] += 1
    evidence[name] = {'pixels': int(occupied.sum()), 'box': box, 'main_component': components[index][2]}
assert np.all(coverage[a[:, :, 3] > 0] == 1)
# Ownership borders cross quantization residue only, never visible anatomy.
border = np.zeros(owner.shape, dtype=bool)
border[:, 1:] |= owner[:, 1:] != owner[:, :-1]
border[1:, :] |= owner[1:, :] != owner[:-1, :]
assert int(a[:, :, 3][border].max()) <= 4
job.update(extraction_overrides=rectangles, extraction_masks=masks,
           extraction_review='Reviewed disjoint complete poses have interleaving bounding rectangles. Five alpha>4 body components define deterministic nearest-component ownership. All supplied nonzero-alpha pixels are assigned exactly once; no visible pixels are cut or recolored.')
save(ROOT / 'review/d_v3_partition.json', {'raw_sha256': queue.sha(ROOT / job['selected_raw']),
    'status': 'lossless_partition', 'foreground_coverage_exactly_once': True,
    'ownership_border_alpha_max': int(a[:, :, 3][border].max()), 'frames': evidence})
save(ROOT / 'compact_jobs.json', data)
print(evidence)
