"""Detect historical normalization/affine clipping using a padded reconstruction."""
import json
import numpy as np
from PIL import Image
from process import ROOT, save


def outside(image, padding=224):
    alpha = np.array(image)[:, :, 3]
    alpha[padding:padding + 576, padding:padding + 576] = 0
    return {'pixels': int((alpha > 0).sum()), 'alpha_max': int(alpha.max())}


def run():
    jobs = json.loads((ROOT / 'compact_jobs.json').read_text())['jobs']
    records = json.loads((ROOT / 'registration.json').read_text())
    results = {}
    for name, record in records.items():
        if record.get('working_padding_px'):
            continue
        job = jobs[record['batch']]
        raw = Image.open(ROOT / record['raw'])
        index = job['frames'].index(name)
        cw, ch = raw.width / job['columns'], raw.height / job['rows']
        nominal = [round(index % job['columns'] * cw), round(index // job['columns'] * ch)]
        rect = record['raw_cell']
        ratio = record['normalization_scale']
        clean = Image.open(ROOT / 'cleaned' / (name + '.png'))
        resized = clean.convert('RGBa').resize(tuple(round(v * ratio) for v in clean.size), Image.Resampling.LANCZOS).convert('RGBA')
        art = Image.new('RGBA', (1024, 1024))
        offset = [256 + job['crop_native'][k] * 2 + round((rect[k] - nominal[k]) * ratio) for k in range(2)]
        art.paste(resized, tuple(offset))
        normalization = outside(art)
        values = record['shared_calibration']
        scale = values[0]
        row = index // job['columns']
        dx, dy = values[1 + row * 2], values[2 + row * 2]
        out = art.convert('RGBa').transform((1024, 1024), Image.Transform.AFFINE,
            (1 / scale, 0, 512 - (512 + 4.5 * dx) / scale,
             0, 1 / scale, 512 - (512 + 4.5 * dy) / scale), Image.Resampling.BICUBIC).convert('RGBA')
        affine = outside(out)
        if normalization['pixels'] or affine['pixels']:
            results[name] = {'batch': record['batch'], 'normalization': normalization, 'affine': affine}
    save(ROOT / 'review/historical_transform_extent.json', results)
    print(json.dumps(results))


if __name__ == '__main__':
    run()
