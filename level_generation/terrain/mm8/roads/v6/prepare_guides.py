"""Plan diagonal road bands from their fixed openings, removing internal concave bites."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from common import *
from PIL import ImageDraw
from scipy.ndimage import distance_transform_edt, gaussian_filter
import json

old = HERE.parent / 'v5'
yy, xx = np.mgrid[:512, :512]
border = np.minimum.reduce([xx, yy, 511 - xx, 511 - yy])
records = []
for name in ('drsrne1', 'drsrne2'):
    alpha = np.load(old / 'fields' / (name + '.npz'))['alpha']
    def bounds(values):
        indexes = np.where(values > .5)[0]
        return int(indexes[0]), int(indexes[-1])
    if name.endswith('1'):
        top, bottom = bounds(alpha[:, 0]); left, right = bounds(alpha[-1])
        points = [(0, top), (right, 511), (left, 511), (0, bottom)]
    else:
        left, right = bounds(alpha[0]); top, bottom = bounds(alpha[:, -1])
        points = [(left, 0), (right, 0), (511, top), (511, bottom)]
    im = Image.new('L', (512, 512)); ImageDraw.Draw(im).polygon(points, fill=255)
    mask = np.asarray(im) > 127
    signed = distance_transform_edt(mask) - distance_transform_edt(~mask)
    rng = np.random.RandomState(42 if name.endswith('1') else 43)
    noise = gaussian_filter(rng.normal(size=(512, 512)), 6)
    noise = noise / noise.std() * 1.8
    weight = np.clip((border - 12) / 24, 0, 1)
    planned = signed + noise * weight > 0
    # Keep the existing openings and their small stone-edge variation, but stop
    # carrying their folded donor art into the interior of diagonal tiles.
    signed_old = distance_transform_edt(alpha > .5) - distance_transform_edt(alpha <= .5)
    signed_planned = distance_transform_edt(planned) - distance_transform_edt(~planned)
    guide = signed_old * (1 - weight) + signed_planned * weight > 0
    save(HERE / 'inputs' / (name + '_coverage.png'), guide[:, :, None].repeat(3, 2) * 255)
    records.append(dict(name=name, polygon=points, input_alpha_sha256=sha(old / 'fields' / (name + '.npz')),
                        guide_sha256=sha(HERE / 'inputs' / (name + '_coverage.png'))))
(HERE / 'inputs/guides.json').write_text(json.dumps(records, indent=2) + '\n')
