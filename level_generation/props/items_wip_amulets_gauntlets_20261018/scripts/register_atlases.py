"""Calibrate independent generated painting frames onto the fixed mesh guide frames; keep raw art intact.

Only texture projection coordinates change. Shape agreement after registration must pass before baking.
"""
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

P = Path(__file__).resolve().parents[1]
VIEWS = ['front', 'back', 'left', 'right', 'top', 'bottom']


def bounds(image):
    y, x = np.nonzero(np.asarray(image)[..., 3] > 127)
    assert len(x), 'Empty projection view'
    return int(x.min()), int(y.min()), int(x.max()) + 1, int(y.max()) + 1


def register(name):
    folder = P / 'codex_tex' / name
    output = folder / 'aligned'
    output.mkdir(exist_ok=True)
    reports = {}
    for kind in ['paint', 'mask']:
        raw = Image.open(folder / f'{kind}_atlas.png').convert('RGBA')
        assert abs(raw.width / raw.height - 1.5) < .01, raw.size
        atlas = Image.new('RGBA', (1536, 1024))
        for i, view in enumerate(VIEWS[:4]):
            tile = raw.crop((i % 3 * raw.width // 3, i // 3 * raw.height // 2,
                             (i % 3 + 1) * raw.width // 3, (i // 3 + 1) * raw.height // 2))
            guide = Image.open(folder / f'guide_{view}.png').convert('RGBA').resize((512, 512))
            a, b = bounds(tile), bounds(guide)
            width, height = a[2] - a[0], a[3] - a[1]
            sx, sy = width / (b[2] - b[0]), height / (b[3] - b[1])
            assert .4 < sx < 2.8 and .4 < sy < 2.8, (name, kind, view, sx, sy)
            aligned = Image.new('RGBA', (512, 512))
            aligned.paste(tile.crop(a).resize((b[2] - b[0], b[3] - b[1]),
                                             Image.Resampling.NEAREST if kind == 'mask'
                                             else Image.Resampling.LANCZOS), (b[0], b[1]))
            p, g = np.asarray(aligned)[..., 3] > 127, np.asarray(guide)[..., 3] > 127
            iou = float((p & g).sum() / (p | g).sum())
            reports[kind + '_' + view] = {'raw_frame_scale': [sx, sy], 'registered_iou': iou}
            assert iou >= .78, (name, kind, view, 'Silhouette changed beyond framing', iou)
            if kind == 'mask':
                missing = g & ~p
                fraction = float(missing.sum() / max(g.sum(), 1))
                assert fraction < .12, (name, view, 'Too much material mask missing', fraction)
                pixels = np.array(aligned)
                nearest = distance_transform_edt(~p, return_distances=False, return_indices=True)
                pixels[missing, :3] = pixels[tuple(nearest[:, missing])][:, :3]
                pixels[..., 3] = np.asarray(guide)[..., 3]
                aligned = Image.fromarray(pixels)
                reports[kind + '_' + view]['guide_edge_fill_fraction'] = fraction
            atlas.alpha_composite(aligned, (i % 3 * 512, i // 3 * 512))
        atlas.save(output / f'{kind}_atlas.png')
    (folder / 'registration.json').write_text(json.dumps(reports, indent=2) + '\n')
    print('REGISTERED', name, min(r['registered_iou'] for r in reports.values()))


if __name__ == '__main__':
    for name in sys.argv[1:]:
        register(name)
