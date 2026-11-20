"""Archer-specific common-scale registration and placement review; no automatic art acceptance."""
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from prepare_run import REPO, native
sys.path.insert(0, str(REPO / 'level_generation/creatures/mm6_peasants'))
import process_family as processing

ROOT = REPO / 'level_generation/creatures/mm6_arc1'
OUT = ROOT / 'redo_2x'


def contact(image, band):
    alpha = np.array(image)[:, :, 3] >= 128
    y, x = np.where(alpha)
    bottom = int(y.max()) + 1
    xx = np.where(alpha[max(0, bottom - band):bottom])[1]
    return [(int(xx.min()) + int(xx.max()) + 1) / 2, bottom]


def crown_x(image, scale):
    """Archer-specific red-hair crown landmark, excluding quiver and warm gold equipment."""
    rgba = np.array(image)
    r, g, b = rgba[:, :, :3].astype(float).transpose(2, 0, 1)
    bounds = image.getbbox()
    yy = np.arange(image.height)[:, None]
    hair = (r > g * 1.7) & (r > b * 1.8) & (r > 25) & (rgba[:, :, 3] >= 128)
    hair &= yy < bounds[1] + (bounds[3] - bounds[1]) * .25
    y, x = np.where(hair)
    assert len(x), 'No Archer crown landmark'
    cap = hair & (yy < y.min() + max(2, round(8 * scale)))
    labels, _ = ndimage.label(cap)
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    cy, cx = np.where(labels == sizes.argmax())
    return (int(cx.min()) + int(cx.max()) + 1) / 2


def main():
    config = json.loads((ROOT / 'config.json').read_text())
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    records, calibrations = {}, {}
    for folder in ['aligned_2x', 'masks_2x']:
        (OUT / folder).mkdir(exist_ok=True)
    # The first pose in each Archer batch has a visible crown above the quiver and an unobstructed sole.
    # These explicit first-pose crown-to-sole measurements calibrate one anatomical scale for the entire batch.
    # Attack's first pose reaches behind the head; its hand remains below the crown.
    for path in sorted((OUT / 'review').glob('*_extraction.json')):
        report = json.loads(path.read_text())
        first = report['frames'][0]
        nb, gb = first['native_bounds'], first['clean_bounds']
        sampling = (gb[3] - gb[1]) / (nb[3] - nb[1])
        assert sampling > 2, (report['job'], sampling)
        factor = 2 / sampling
        calibrations[report['job']] = dict(frame=first['frame'], native_crown_y=nb[1], native_sole_y=nb[3],
            raw_crown_y=gb[1], raw_sole_y=gb[3], generated_sampling=sampling,
            method='Reviewed first-pose crown-to-sole anatomical calibration; one uniform scale for all poses',
            raw_sha256=report['raw_sha256'])
        previews = []
        for f in report['frames']:
            name = f['frame']
            # Choose the initial profile as the retained overlap; do not duplicate it in playback.
            if name in records:
                continue
            clean = Image.open(REPO / f['clean_path']).convert('RGBA')
            im = processing.resize_base(clean, (round(clean.width * factor), round(clean.height * factor)), config)
            rgba = np.array(im)
            color = rgba[:, :, :3].astype(float) / 255
            luminance = color @ np.array([.2126, .7152, .0722])
            # One family-wide grade against the accepted old standing art; preserve hue and alpha.
            color *= (.85 * np.maximum(luminance, 1 / 255) ** .10)[:, :, None]
            rgba[:, :, :3] = np.round(np.clip(color * 255, 0, 255)).astype(np.uint8)
            im = Image.fromarray(rgba)
            source = native(ROOT, name)
            nc, rc = contact(source, 6), contact(im, 12)
            nx, rx = crown_x(source, 1), crown_x(im, 2)
            tx, ty = round(nx * 2 - rx), round(nc[1] * 2 - rc[1])
            box = im.getbbox()
            origin = [min(0, tx + box[0] - 4), min(0, ty + box[1] - 4)]
            end = [max(manifest['logical_canvas'][0] * 2, tx + box[2] + 4),
                   max(manifest['logical_canvas'][1] * 2, ty + box[3] + 4)]
            aligned = Image.new('RGBA', (end[0] - origin[0], end[1] - origin[1]))
            aligned.paste(im, (tx - origin[0], ty - origin[1]))
            aligned.save(OUT / 'aligned_2x' / (name + '.png'))
            processing.mask(aligned, config).save(OUT / 'masks_2x' / (name + '.png'))
            effective_sampling = [2 * clean.width / im.width, 2 * clean.height / im.height]
            assert min(effective_sampling) > 2, name
            records[name] = dict(batch=report['job'], raw_path=report['raw'], raw_sha256=report['raw_sha256'],
                raw_size=report['raw_size'], raw_rect=f['raw_rect'], native_crop=report['native_crop'],
                scale=factor, effective_sampling_xy=effective_sampling,
                translate=[tx, ty], canvas_origin_px=origin, native_bounds=f['native_bounds'],
                placement_landmarks=dict(native_contact=nc, restored_contact_before_translation=rc,
                    native_crown_x=nx, restored_crown_x_before_translation=rx,
                    physical_residual=[rx + tx - nx * 2, rc[1] + ty - nc[1] * 2],
                    stance_center_x_residual=rc[0] + tx - nc[0] * 2),
                contact_method='Archer red-hair crown X and per-native-pose contact Y; inspect prone endpoint separately',
                tone_grade={'luminance_gamma': 1.10, 'gain': .85, 'reference': 'previous accepted standing art'},
                raw_clip=f['clean_bounds'][0] <= 0 or f['clean_bounds'][1] <= 0
                    or f['clean_bounds'][2] >= clean.width or f['clean_bounds'][3] >= clean.height,
                matte=f['matte'], review_status='pending_animation_and_landmark_review')
            previews.append((name, source, aligned, origin))
        crop = report['native_crop']
        w, h = crop[2] - crop[0], crop[3] - crop[1]
        if previews:
            contact_sheet = Image.new('RGB', (w * len(previews), h * 2 + 44), (42, 44, 43))
            draw = ImageDraw.Draw(contact_sheet)
            for i, (name, source, aligned, origin) in enumerate(previews):
                src = source.crop(crop)
                restore = aligned.crop((crop[0] * 2 - origin[0], crop[1] * 2 - origin[1],
                                        crop[2] * 2 - origin[0], crop[3] * 2 - origin[1]))
                restore = restore.convert('RGBa').resize((w, h), Image.Resampling.LANCZOS).convert('RGBA')
                contact_sheet.paste(src, (i * w, 20), src)
                contact_sheet.paste(restore, (i * w, h + 40), restore)
                draw.text((i * w + 2, 3), name, fill='white')
            contact_sheet.save(OUT / 'review' / (report['job'] + '_registered_contact.png'))
    assert set(records) == set(manifest['frames']), set(manifest['frames']) - set(records)
    (OUT / 'registration.json').write_text(json.dumps(records, indent=2) + '\n')
    (OUT / 'calibration.json').write_text(json.dumps(calibrations, indent=2) + '\n')
    print(json.dumps(dict(frames=len(records), minimum_sampling=min(min(r['effective_sampling_xy']) for r in records.values()),
                          maximum_anchor_residual=max(max(abs(v) for v in r['placement_landmarks']['physical_residual']) for r in records.values()),
                          status='registered; full animation/variant review pending')))


if __name__ == '__main__':
    main()
