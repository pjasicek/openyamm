"""Match shared road boundary colours without changing stone contours or interior artwork.

The old directional contracts preserve different endpoint colours. A small,
smooth correction of the road-only border neighbourhood removes the resulting
line for every combination of straight, diagonal and junction road tiles.
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from common import *
import json
from scipy.ndimage import gaussian_filter1d, maximum_filter1d

build = json.loads((HERE / 'build.json').read_text())
profiles = {}
for prefix in ('drsr', 'gdrd'):
    for axis, suffix in [('vertical', 'ns'), ('horizontal', 'ew')]:
        im = read(HERE / 'runtime' / (prefix + suffix + '.png'))
        alpha = np.asarray(Image.open(HERE / 'masks' / (prefix + suffix + '.png')).resize((256, 256)), float) / 255
        if axis == 'horizontal': im, alpha = im.transpose(1, 0, 2), alpha.T
        profile = (im[0] + im[-1]) / 2
        coverage = maximum_filter1d(np.maximum(alpha[0], alpha[-1]), 7)
        coverage = gaussian_filter1d(coverage, .65)
        profiles[prefix, axis] = profile, coverage

records = []
for record in build['tiles']:
    name = record['name']
    im = read(HERE / 'runtime' / (name + '.png'))
    original = im.copy()
    for side, opened in record['topology'].items():
        if not opened: continue
        horizontal = side in ('E', 'W')
        view = im.transpose(1, 0, 2) if horizontal else im
        if side in ('E', 'S'): view = view[::-1]
        profile, coverage = profiles[name[:4], 'horizontal' if horizontal else 'vertical']
        delta = (profile - view[0]) * coverage[:, None]
        for distance in range(8):
            t = distance / 8
            weight = 1 - t * t * (3 - 2 * t)
            view[distance] += delta * weight
    save(HERE / 'runtime' / (name + '.png'), im)
    record['runtime_sha256'] = sha(HERE / 'runtime' / (name + '.png'))
    records.append(dict(name=name, max_delta=float(abs(im - original).max()),
                        changed_pixels=int(np.any(seams.byte(im) != seams.byte(original), axis=2).sum())))
previous = HERE.parent / 'v6/runtime'
build['changed'] = [r['name'] for r in build['tiles'] if sha(previous / (r['name'] + '.png')) != r['runtime_sha256']]
build['port_correction'] = dict(width_runtime_pixels=8, records=records,
                                script_sha256=sha(Path(__file__).resolve()))
(HERE / 'build.json').write_text(json.dumps(build, indent=2) + '\n')
print('Matched shared colour profiles on', len(build['changed']), 'road textures')
