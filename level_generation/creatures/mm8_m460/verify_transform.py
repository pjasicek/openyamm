"""Replay selected transformations on padded canvases and check lossless pose partitioning."""
import json
import numpy as np
from PIL import Image
from process import ROOT, queue, save
from process_compact import translate


def run():
    jobs = json.loads((ROOT / 'compact_jobs.json').read_text())['jobs']
    records = json.loads((ROOT / 'registration.json').read_text())
    count = 0
    for name, record in records.items():
        job = jobs[record['batch']]
        raw = Image.open(ROOT / record['raw'])
        clean = Image.open(ROOT / 'cleaned' / (name + '.png'))
        index = job['frames'].index(name)
        columns = job['columns']
        origin = [round(index % columns * raw.width / columns),
                  round(index // columns * raw.height / job['rows'])]
        ratio = record['normalization_scale']
        resized = clean.convert('RGBa').resize(tuple(round(v * ratio) for v in clean.size),
                    Image.Resampling.LANCZOS).convert('RGBA')
        padding = record.get('working_padding_px', 0)
        size = 576 + padding * 2
        offset = [32 + padding + job['crop_native'][k] * 2 +
                  round((record['raw_cell'][k] - origin[k]) * ratio) for k in range(2)]
        art = Image.new('RGBA', (size, size))
        art.paste(resized, tuple(offset))
        assert np.array_equal(resized, art.crop((*offset, offset[0] + resized.width, offset[1] + resized.height))), (name, 'normalization')
        values = record['shared_calibration']; scale = values[0]
        row = index // columns
        dx, dy = values[1 + row * 2:3 + row * 2]
        center = size / 2
        out = art.convert('RGBa').transform((size, size), Image.Transform.AFFINE,
            (1 / scale, 0, center - (center + 4.5 * dx) / scale,
             0, 1 / scale, center - (center + 4.5 * dy) / scale), Image.Resampling.BICUBIC).convert('RGBA')
        if record.get('reviewed_isolated_residue'):
            before = Image.open(ROOT / 'checkpoints/residue' / (name + '_before.png'))
            assert np.array_equal(out, before), (name, 'residue checkpoint replay')
            a = np.array(out)
            mask = np.asarray(Image.open(ROOT / 'checkpoints/residue' / (name + '_mask.png'))) > 0
            a[mask] = 0; out = Image.fromarray(a)
        out = translate(out, record['integer_translation_2x'])
        crop = out.crop((padding, padding, padding + 576, padding + 576))
        reconstruction = Image.new('RGBA', out.size); reconstruction.paste(crop, (padding, padding))
        assert np.array_equal(reconstruction, out), (name, 'final crop')
        assert np.array_equal(crop, Image.open(ROOT / 'registered_2x' / (name + '.png'))), (name, 'selected master replay')
        count += 1
    historical = json.loads((ROOT / 'review/historical_transform_extent.json').read_text())
    assert not historical, historical
    partitions = {}
    for key, job in jobs.items():
        if not job.get('extraction_masks'):
            continue
        raw = np.asarray(Image.open(ROOT / job['selected_raw']))
        coverage = np.zeros(raw.shape[:2], dtype=np.uint8)
        reconstructed = np.zeros_like(raw)
        for name, item in job['extraction_masks'].items():
            assert queue.sha(ROOT / item['path']) == item['sha256']
            mask = np.asarray(Image.open(ROOT / item['path'])) > 0
            x0, y0, x1, y1 = job['extraction_overrides'][name]
            coverage[y0:y1, x0:x1] += mask
            reconstructed[y0:y1, x0:x1][mask] = raw[y0:y1, x0:x1][mask]
        assert np.all(coverage[raw[:, :, 3] > 0] == 1)
        assert np.array_equal(raw[raw[:, :, 3] > 0], reconstructed[raw[:, :, 3] > 0])
        partitions[key] = {'nonzero_alpha_owned_exactly_once': True, 'visible_rgba_exact': True}
    save(ROOT / 'review/transform_checks.json', {'status': 'passed', 'frames': count,
        'selected_transforms_replayed_exactly': True, 'historical_affine_extent_clean': True,
        'normalization_and_final_crop_lossless': True, 'pose_partitions': partitions})
    print(count, 'exact transformation replays;', len(partitions), 'lossless pose partitions')


if __name__ == '__main__':
    run()
