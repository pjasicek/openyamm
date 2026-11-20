"""Record an inspected crop-failure artifact; never remove connected visible pixels."""
import argparse, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from process import ROOT, save

p = argparse.ArgumentParser()
p.add_argument('name')
p.add_argument('--accept', action='store_true')
args = p.parse_args()
name = args.name
report = json.loads((ROOT / f'review/{name}_crop_failure.json').read_text())
im = Image.open(ROOT / f'review/{name}_crop_failure.png')
a = np.asarray(im)[:, :, 3]
labels, _ = ndi.label(a > 0)
padding = report['padding']
outside = np.ones(a.shape, dtype=bool)
outside[padding:padding + 576, padding:padding + 576] = False
regions, count = [], 0
for k in np.unique(labels[outside]):
    if not k:
        continue
    selected = labels == k
    assert a[selected].max() == 1, 'Visible component must be retained'
    ys, xs = np.where(selected)
    dx, dy = report['shift']
    regions.append([int(xs.min()) - dx - padding, int(ys.min()) - dy - padding,
                    int(xs.max() + 1) - dx - padding, int(ys.max() + 1) - dy - padding])
    count += int(selected.sum())
bg = Image.new('RGBA', im.size, 'white')
bg.alpha_composite(im)
evidence = f'review/{name}_padded_light.png'
bg.convert('RGB').save(ROOT / evidence)
record = {'regions_before_contact': regions, 'alpha_max': 1, 'pixel_count': count,
          'evidence': evidence, 'reason': 'Inspected detached alpha1-only components outside aligned canvas. Each entire component is retained in the checkpoint and raw; only these quantization specks are removed, with no connected anatomy or anti-aliasing affected.'}
save(ROOT / f'review/{name}_residue_candidate.json', record)
if args.accept:
    data = json.loads((ROOT / 'compact_jobs.json').read_text())
    matching = [(key, j) for key, j in data['jobs'].items() if name in j['frames'] and j['status'] == 'processing']
    assert len(matching) == 1
    matching[0][1].setdefault('reviewed_isolated_residue', {})[name] = record
    save(ROOT / 'compact_jobs.json', data)
print(name, len(regions), 'components;', count, 'pixels;', 'accepted' if args.accept else 'awaiting visual inspection')
