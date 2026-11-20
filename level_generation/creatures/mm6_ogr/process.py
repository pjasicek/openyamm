"""Rebuild Ogre cutouts and apply one fixed, reviewed family tonal grade."""
import json
import hashlib
import shutil
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'mm6_peasants'))
import process_family


def suppress_green_fringe(image):
    pixels = np.array(image)
    rgb = pixels[:, :, :3].astype(np.int16)
    edge = ndimage.distance_transform_edt(pixels[:, :, 3] >= 250) <= 3
    excess = np.maximum(0, rgb[:, :, 1] - np.maximum(rgb[:, :, 0], rgb[:, :, 2]) - 2)
    rgb[:, :, 1] -= np.where(edge, excess, 0)
    pixels[:, :, :3] = rgb.astype(np.uint8)
    return Image.fromarray(pixels)


def spike_mask(image):
    pixels = np.array(image)
    rgb = pixels[:, :, :3].astype(float) / 255
    red, green, blue = rgb.transpose(2, 0, 1)
    dominance = (blue - red) / np.maximum(blue, .01)
    weight = np.clip((dominance - .12) / .18, 0, 1) * np.clip((blue - green * .85) / .04, 0, 1)
    labels, _ = ndimage.label((weight > .5) & (pixels[:, :, 3] > 200))
    sizes = np.bincount(labels.ravel())
    keep = sizes >= 12
    keep[0] = False
    region = ndimage.binary_dilation(keep[labels], iterations=3)
    weight *= region & (pixels[:, :, 3] > 0)
    return Image.fromarray(np.round(weight * 255).astype(np.uint8), 'L')


def rebuild_masks():
    for path in (ROOT / 'aligned_2x').glob('*.png'):
        spike_mask(Image.open(path)).save(ROOT / 'masks_2x' / path.name)


def main():
    process_family.run('ogr')
    for folder in ('cleaned', 'aligned_2x'):
        for path in (ROOT / folder).glob('*.png'):
            pixels = np.array(Image.open(path))
            pixels[:, :, :3] = np.round(pixels[:, :, :3].astype(float) * .90).astype(np.uint8)
            suppress_green_fringe(Image.fromarray(pixels)).save(path)
    rebuild_masks()
    (ROOT / 'tone.json').write_text(json.dumps({
        'rgb_gain': .90,
        'reason': 'Fixed correction for brighter generated skin, silver plates and leather; native comparisons reviewed.',
        'alpha': 'unchanged',
        'comparisons': 'Extraction comparisons precede grade; final packaged reviews include grade.'
    }, indent=2) + '\n')


def crown(image, frame=None):
    """Locate the broad brown crown above neutral steel and blue spikes."""
    pixels = np.array(image)
    r, g, b = pixels[:, :, :3].astype(float).transpose(2, 0, 1)
    box = process_family.bounds(image)
    height = box[3] - box[1]
    yy = np.arange(image.height)[:, None]
    skin = (pixels[:, :, 3] >= 128) & (r > b + 7) & (g > b + 3) & (r < g * 1.6)
    skin &= yy < box[1] + height * .45
    if frame in ('ogratkc0', 'ogratkd0'):
        # Rust on the raised blade otherwise resembles brown skin above the actual head.
        skin &= yy >= box[1] + height * .24
    broad = ndimage.binary_opening(skin, structure=np.ones((1, max(3, round(height * .055))), bool))
    ys, xs = np.where(broad)
    assert len(xs), 'No broad Ogre crown landmark'
    top = int(ys.min())
    cap = broad & (yy < top + max(2, round(height * .045)))
    return [float(np.median(np.where(cap)[1])), top]


def planted_foot_x(image, scale):
    """Viewer-right planted foot for the reviewed front attack and hit sequences."""
    solid = np.array(image)[:, :, 3] >= 128
    bottom = int(np.where(solid)[0].max()) + 1
    band = solid[bottom - round(18 * scale):bottom - round(5 * scale)]
    labels, count = ndimage.label(band.any(axis=0))
    feet = [label for label in range(1, count + 1) if (labels == label).sum() >= 3 * scale]
    assert feet, 'Missing planted-foot landmark'
    xs = np.where(labels == feet[-1])[0]
    return (int(xs[0]) + int(xs[-1]) + 1) / 2


def run_redo():
    sys.path.insert(0, str(ROOT.parent / 'mm6_remaining/redo_2x'))
    from prepare_run import REPO, native
    out = ROOT / 'redo_2x'
    config = json.loads((ROOT / 'config.json').read_text())
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    run = json.loads((out / 'run.json').read_text())
    records, calibrations = {}, {}
    for directory in ['aligned_2x', 'masks_2x']:
        (out / directory).mkdir(exist_ok=True)
    for job in run['jobs']:
        report = json.loads((out / 'review' / (job['id'] + '_extraction.json')).read_text())
        first = report['frames'][0]
        source = native(ROOT, first['frame'])
        clean = Image.open(REPO / first['clean_path']).convert('RGBA')
        nb, gb = process_family.bounds(source), process_family.bounds(clean)
        nc, gc = crown(source, first['frame']), crown(clean, first['frame'])
        sampling = (gb[3] - gc[1]) / (nb[3] - nc[1])
        method = 'First-pose crown-to-sole anatomical scale; one uniform scale across the sheet'
        if job['id'] in ['death_corpse_redo_04', 'death_corpse_redo_05']:
            previous = records[first['frame']]
            old = Image.open(out / 'cleaned' / previous['batch'] / (first['frame'] + '.png'))
            ob = process_family.bounds(old)
            sampling = previous['calibrated_sampling'] * (gb[2] - gb[0]) / (ob[2] - ob[0])
            method = 'Shared crouched overlap width transfers preceding anatomical scale; no per-pose fitting'
        assert sampling > 2, (job['id'], sampling)
        factor = 2 / sampling
        calibrations[job['id']] = dict(frame=first['frame'], native_crown=nc, raw_crown=gc,
            native_sole_y=nb[3], raw_sole_y=gb[3], generated_sampling=sampling, method=method,
            raw_sha256=report['raw_sha256'])
        for frame in report['frames']:
            name = frame['frame']
            if name in records:
                continue
            clean = Image.open(REPO / frame['clean_path']).convert('RGBA')
            source = native(ROOT, name)
            im = process_family.resize_base(clean, (round(clean.width * factor), round(clean.height * factor)), config)
            nb, rb = process_family.bounds(source), process_family.bounds(im)
            nc, rc = crown(source, name), crown(im, name)
            tx, ty = round(nc[0] * 2 - rc[0]), nb[3] * 2 - rb[3]
            # A near-zero X residual alone can certify the wrong feature (e.g. a rusty blade).
            crown_y_residual = rc[1] + ty - nc[1] * 2
            assert abs(crown_y_residual) <= max(24, (nb[3] - nc[1]) * .16), (name, crown_y_residual)
            nx, rx = nc[0], rc[0]
            contact_method = 'Brown crown X and per-native-pose alpha>=96 baseline Y'
            if name.startswith(('ogratk', 'ogrwnc')):
                nx, rx = planted_foot_x(source, 1), planted_foot_x(im, 2)
                tx = round(nx * 2 - rx)
                contact_method = 'Reviewed viewer-right planted-foot X and native baseline Y; retain native body motion'
            box = im.getbbox()
            origin = [min(0, tx + box[0] - 4), min(0, ty + box[1] - 4)]
            end = [max(manifest['logical_canvas'][0] * 2, tx + box[2] + 4),
                   max(manifest['logical_canvas'][1] * 2, ty + box[3] + 4)]
            aligned = Image.new('RGBA', (end[0] - origin[0], end[1] - origin[1]))
            aligned.paste(im, (tx - origin[0], ty - origin[1]))
            aligned.save(out / 'aligned_2x' / (name + '.png'))
            spike_mask(aligned).save(out / 'masks_2x' / (name + '.png'))
            effective = [2 * clean.width / im.width, 2 * clean.height / im.height]
            assert min(effective) > 2, (name, effective)
            actual = clean.getbbox()
            records[name] = dict(batch=job['id'], raw_path=report['raw'], raw_sha256=report['raw_sha256'],
                raw_size=report['raw_size'], raw_rect=frame['raw_rect'], native_crop=report['native_crop'],
                scale=factor, calibrated_sampling=sampling, effective_sampling_xy=effective,
                translate=[tx, ty], canvas_origin_px=origin, native_bounds=frame['native_bounds'],
                placement_landmarks=dict(native_crown=nc, restored_crown_before_translation=rc,
                    native_contact_y=nb[3], restored_contact_y_before_translation=rb[3],
                    native_anchor_x=nx, restored_anchor_x_before_translation=rx,
                    crown_y_residual=crown_y_residual,
                    physical_residual=[rx + tx - nx * 2, rb[3] + ty - nb[3] * 2]),
                contact_method=contact_method,
                tone_grade='Native restrained palette and standing identity; no additional grade',
                raw_clip=actual[0] <= 0 or actual[1] <= 0 or actual[2] >= clean.width or actual[3] >= clean.height,
                matte=frame['matte'], review_status='pending_static_sequence_and_variant_review')
    # This unused native pose was already generated above 2x; retain the exact historical checkpoint.
    name = 'ogrdief0'
    previous = json.loads((ROOT / 'registration.json').read_text())[name]
    assets = {}
    for folder in ['aligned_2x', 'masks_2x', 'cleaned']:
        relative = f'{folder}/{name}.png'
        shutil.copy2(ROOT / relative, out / relative)
        assets[relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    records[name] = dict(previous, effective_sampling_xy=[2 / previous['scale']] * 2,
        retained_from=dict(project=str(ROOT.relative_to(REPO)),
            registration_sha256=hashlib.sha256((ROOT / 'registration.json').read_bytes()).hexdigest(), assets=assets))
    assert set(records) == set(manifest['frames']), set(manifest['frames']) - set(records)
    (out / 'registration.json').write_text(json.dumps(records, indent=2) + '\n')
    (out / 'calibration.json').write_text(json.dumps(calibrations, indent=2) + '\n')
    print(json.dumps(dict(frames=len(records), minimum_sampling=min(min(r['effective_sampling_xy']) for r in records.values()),
        clipped=[n for n, r in records.items() if r['raw_clip']],
        status='Registered; visual review pending')))


if __name__ == '__main__':
    if '--redo' in sys.argv:
        run_redo()
    else:
        main()
