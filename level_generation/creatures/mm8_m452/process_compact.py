"""Process compact Wererat Rat Form grids with shared scale, native contacts and frozen tone."""
import argparse
import json
import shutil
import numpy as np
from PIL import Image, ImageDraw
from scipy.optimize import minimize
from scipy import ndimage as ndi

import calibrate
import materials
from process import ROOT, queue, save, extract, fix, spill, mean_luma


def contact(image, body_only=False):
    alpha = np.array(image)[:, :, 3] >= 128
    if body_only:
        labels, _ = ndi.label(alpha)
        sizes = np.bincount(labels.ravel())
        sizes[0] = 0
        alpha = labels == int(np.argmax(sizes))
    ys, xs = np.where(alpha)
    bottom = int(ys.max()) + 1
    ys, xs = np.where(alpha[max(0, bottom - 24):bottom])
    return [(float(xs.min()) + float(xs.max()) + 1) / 2, bottom]


def translate(image, shift):
    result = Image.new(image.mode, image.size)
    result.paste(image, tuple(shift))
    back = Image.new(image.mode, image.size)
    back.paste(result, tuple(-x for x in shift))
    assert np.array_equal(image, back), ('translation clips', shift)
    return result


def grade(image, multiplier, name):
    a = np.array(image)
    a[:, :, :3] = np.round(a[:, :, :3].astype(float) * multiplier).clip(0, 255).astype(np.uint8)
    return fix(Image.fromarray(a), name)


def variants(name, image, settings):
    assert settings['base_palette'] == 452
    mask = np.zeros((image.height, image.width), dtype=np.uint8)
    Image.fromarray(mask).save(ROOT / 'masks_2x' / (name + '.png'))
    image.save(ROOT / 'previews' / (name + '_452.png'))
    queue.native(ROOT, name, 452).save(ROOT / 'native_variants' / (name + '_452.png'))


def run(key):
    data = json.loads((ROOT / 'compact_jobs.json').read_text())
    job = data['jobs'][key]
    # Keep the previous accepted overlap available for continuity review and selection.
    registration_path = ROOT / 'registration.json'
    previous = json.loads(registration_path.read_text()) if registration_path.exists() else {}
    for name in job.get('overlap_previous', []):
        if name not in previous or previous[name]['batch'] == key:
            continue
        checkpoint = ROOT / 'checkpoints' / 'overlaps' / key / name
        if not checkpoint.exists():
            checkpoint.mkdir(parents=True)
            save(checkpoint / 'registration.json', previous[name])
            for folder in ['cleaned', 'registered_2x', 'toned_2x', 'masks_2x']:
                shutil.copy2(ROOT / folder / (name + '.png'), checkpoint / (folder + '.png'))
            job.setdefault('overlap_checkpoints', {})[name] = str(checkpoint.relative_to(ROOT))
    raw_path = ROOT / job.get('selected_raw', 'raw/' + key + '_v1.png')
    raw = Image.open(raw_path)
    supplied_alpha = 'A' in raw.getbands() and raw.getchannel('A').getextrema()[0] < 255
    columns, rows = job['columns'], job['rows']
    crop = job['crop_native']
    cw, ch = raw.width / columns, raw.height / rows
    rx, ry = 2 * (crop[2] - crop[0]) / cw, 2 * (crop[3] - crop[1]) / ch
    assert abs(rx / ry - 1) < .025, ('changed aspect', key, rx, ry)
    assert min(2 / rx, 2 / ry) >= 2, ('insufficient raw sampling', key)
    ratio = (rx + ry) / 2
    for folder in ['cleaned', 'registered_2x', 'toned_2x', 'masks_2x', 'previews', 'native_variants']:
        (ROOT / folder).mkdir(exist_ok=True)
    arts, natives, records = [], [], []
    for i, name in enumerate(job['frames']):
        rect = [round(i % columns * cw), round(i // columns * ch),
                round((i % columns + 1) * cw), round((i // columns + 1) * ch)]
        origin = rect[:2]
        rect = job.get('extraction_overrides', {}).get(name, rect)
        clean = extract(raw.crop(rect), name)
        bb = clean.getbbox()
        # Supplied alpha can contain one-code-value residue at the sheet boundary.
        # Keep those pixels; verify that all alpha above that residue has a safe margin.
        residue = job.get('boundary_alpha_residue_max', 1)
        visible_bb = clean.getchannel('A').point(lambda a: 255 if a > residue else 0).getbbox()
        assert visible_bb and visible_bb[0] > 0 and visible_bb[1] > 0 and visible_bb[2] < clean.width and visible_bb[3] < clean.height, (name, visible_bb)
        clean.save(ROOT / 'cleaned' / (name + '.png'))
        art = Image.new('RGBA', (576, 576))
        resized = clean.convert('RGBa').resize(tuple(round(v * ratio) for v in clean.size),
                                                Image.Resampling.LANCZOS).convert('RGBA')
        offset = [32 + crop[k] * 2 + round((rect[k] - origin[k]) * ratio) for k in range(2)]
        art.paste(resized, tuple(offset))
        native = Image.new('RGBA', (576, 576))
        native.paste(queue.native(ROOT, name).resize((512, 512), Image.Resampling.NEAREST), (32, 32))
        arts.append(art)
        natives.append(native)
        records.append({'raw_cell': rect, 'raw_bbox': bb, 'visible_bbox': visible_bb,
                        'boundary_alpha_residue_max': residue,
                        'normalization_scale': ratio})
    am, nm = [calibrate.body(im) for im in arts], [calibrate.body(im) for im in natives]

    def objective(values):
        numerator = denominator = 0
        for i, (a, b) in enumerate(zip(am, nm)):
            row = i // columns
            out = calibrate.warp(a, [values[0], values[1 + row * 2], values[2 + row * 2]])
            numerator += 2 * (out * b).sum()
            denominator += (out * out + b * b).sum()
        return 1 - numerator / max(denominator, 1e-6) + .025 * (values[0] - 1) ** 2

    values = job.get('frozen_calibration')
    if values is None:
        values = minimize(objective, [1] + [0] * (rows * 2), method='Powell',
                          bounds=[(.78, 1.08)] + [(-24, 24)] * (rows * 2),
                          options={'maxiter': 50, 'xtol': .0002}).x.tolist()
    scale = values[0]
    sampling = 2 / (ratio * scale)
    assert sampling >= 2
    outputs = []
    for i, (name, art, native, record) in enumerate(zip(job['frames'], arts, natives, records)):
        row = i // columns
        dx, dy = values[1 + row * 2], values[2 + row * 2]
        out = art.convert('RGBa').transform((576, 576), Image.Transform.AFFINE,
            (1 / scale, 0, 288 - (288 + 4.5 * dx) / scale,
             0, 1 / scale, 288 - (288 + 4.5 * dy) / scale), Image.Resampling.BICUBIC).convert('RGBA')
        out = fix(out, name)
        target, actual = contact(native, job['action'] == 'd'), contact(out, job['action'] == 'd')
        shift = [int(np.rint(a - b)) for a, b in zip(target, actual)]
        out = translate(out, shift)
        out.save(ROOT / 'registered_2x' / (name + '.png'))
        record.update(native_landmark=target, generated_landmark_before=actual,
                      integer_translation_2x=shift, inverse_translation_exact=True,
                      landmark_region='largest rat body component' if job['action'] == 'd'
                                      else 'native pose lower 24px contact band')
        outputs.append(out)
    tone_path = ROOT / 'tone_settings.json'
    if tone_path.exists():
        tone = json.loads(tone_path.read_text())
    else:
        assert key == 'identity'
        ratios = [mean_luma(n) / mean_luma(a) for n, a in zip(natives, outputs)]
        tone = {'multiplier': float(np.median(ratios)), 'identity_ratios': ratios,
                'method': 'One native/enhanced median luminance ratio, frozen across all frames; no spatial transfer.'}
        save(tone_path, tone)
    settings = materials.settings()
    save(ROOT / 'material_settings.json', settings)
    registration_path = ROOT / 'registration.json'
    registration = json.loads(registration_path.read_text()) if registration_path.exists() else {}
    contact_sheet = Image.new('RGB', (len(outputs) * 256, 3 * 280), (35, 35, 35))
    draw = ImageDraw.Draw(contact_sheet)
    for i, (name, out, native, record) in enumerate(zip(job['frames'], outputs, natives, records)):
        final = grade(out, tone['multiplier'], name)
        final.save(ROOT / 'toned_2x' / (name + '.png'))
        variants(name, final, settings)
        registration[name] = {**record, 'batch': key, 'raw': str(raw_path.relative_to(ROOT)),
            'shared_calibration': values, 'generated_pixels_per_native_pixel': sampling,
            'raw_sampling_xy': [2 / rx, 2 / ry], 'canvas_origin_px': [-32, -32],
            'aligned_size_px': [576, 576], 'logical_size': [256, 256], 'status': 'processed_unreviewed'}
        mask = np.asarray(Image.open(ROOT / 'masks_2x' / (name + '.png'))) / 255
        overlay = np.array(final)
        overlay[:, :, :3] = np.round(overlay[:, :, :3] * (1 - .65 * mask[:, :, None]) +
                                     np.array([255, 70, 30]) * .65 * mask[:, :, None]).astype(np.uint8)
        pics = [native] + [Image.open(ROOT / 'previews' / (name + '_' + str(p) + '.png'))
                           for p in materials.PALETTES] + [Image.fromarray(overlay)]
        for row, pic in enumerate(pics):
            bg = Image.new('RGBA', pic.size, (35, 35, 35, 255))
            bg.alpha_composite(pic)
            contact_sheet.paste(bg.resize((256, 256)).convert('RGB'), (i * 256, row * 280 + 24))
            draw.text((i * 256 + 3, row * 280 + 4), name + ' ' + str(['native', 452, 'mask'][row]), fill='white')
    contact_sheet.save(ROOT / 'review' / (key + '_combined.png'))
    save(registration_path, registration)
    save(ROOT / 'calibration_registration.json', registration)
    job.update(status='processed_unreviewed', selected_raw=str(raw_path.relative_to(ROOT)),
               actual_size=list(raw.size), sampling=sampling, frozen_calibration=values,
               returned_background={'mode': raw.mode,
                   'handling': 'preserve supplied alpha; local contour RGB audit' if supplied_alpha
                   else 'recover alpha from magenta matte; local RGB unmixing and contour audit'},
               generation={'raw': {'path': str(raw_path.relative_to(ROOT)), 'sha256': queue.sha(raw_path)},
                           'prompt': {'path': job['prompt'], 'sha256': queue.sha(ROOT / job['prompt'])},
                           'references': [{'path': p, 'sha256': queue.sha(ROOT / p)} for p in job['references']]})
    save(ROOT / 'compact_jobs.json', data)
    ledger_path = ROOT.parent / 'mm8_remaining/progress.json'
    ledger = json.loads(ledger_path.read_text())
    ledger['families']['m452'].update(status='partial', processed_frames=len(registration),
        resume='Review compact combined contacts; reuse accepted identity and continue compact_jobs.json pending jobs.')
    save(ledger_path, ledger)
    print(key, len(outputs), 'frames;', round(sampling, 3), 'generated/native;', len(registration), '/160 processed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('jobs', nargs='+')
    for key in parser.parse_args().jobs:
        run(key)
