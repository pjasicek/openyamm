from pathlib import Path
import json
import numpy as np
from PIL import Image

p = Path(__file__).resolve().parent
root = p.parents[2]
report = {}
for key in json.loads((p / 'checks.json').read_text())['frames']:
    a = np.array(Image.open(p / f'{key}.before_tone.png').convert('RGBA'))
    n = np.array(Image.open(root / 'native' / f'{key}.png').convert('RGBA'))
    rgb = a[:, :, :3].astype(float) / 255
    native = n[:, :, :3].astype(float) / 255
    green = (rgb[:, :, 1] > rgb[:, :, 0] * 1.05) & (rgb[:, :, 1] > rgb[:, :, 2])
    native_green = (native[:, :, 1] > native[:, :, 0] * 1.05) & (native[:, :, 1] > native[:, :, 2])
    result = rgb.copy()
    for name, mask, native_mask in [('foliage', green, native_green)]:
        sample = rgb[mask & (a[:, :, 3] >= 192)]
        target = native[native_mask & (n[:, :, 3] >= 192)].mean(axis=0)
        gamma = []
        for channel in range(3):
            lo, hi = .1, 5.
            for _ in range(40):
                mid = (lo + hi) / 2
                if (sample[:, channel] ** mid).mean() > target[channel]:
                    lo = mid
                else:
                    hi = mid
            gamma.append((lo + hi) / 2)
        result[mask] = rgb[mask] ** np.array(gamma)
        report[name] = {'gamma': gamma, 'native_target_rgb': (target * 255).tolist()}
    a[:, :, :3] = np.rint(result * 255).astype(np.uint8)
    Image.fromarray(a).save(p / f'{key}.png')
report['alpha'] = 'unchanged'
(p / 'tone.json').write_text(json.dumps(report, indent=2) + '\n')
