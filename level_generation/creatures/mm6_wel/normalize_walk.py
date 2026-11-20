"""Normalize the five oversized MM6 Water Elemental walk endings.

The source is the accepted, registered 2x art. Transform every material-mask
channel with the same inverse map as premultiplied color. Native frame timing,
logical canvas and pivot remain the authority; only the documented anatomy and
silhouette scale exception changes. The b3 torso expansion is instead recorded
in processing.json and applied to the higher-resolution clean image by
register_landmarks.py. Preview first, then apply after visual review.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import map_coordinates


ROOT = Path(__file__).resolve().parent
STAGE = ROOT / 'redo_2x'
SOURCE = STAGE / 'walk_normalization_source'
BOTTOM = 335.0
HORIZONTAL_CENTER = 320.0

# Targets bridge the final crouch and first rising pose in each six-frame loop.
# Native f poses contain a one-frame whole-body scale jump; these targets are
# deliberately normalized rather than native-coordinate matches.
TARGETS = {
    'welwkf0': ('waist_calibration', 173.0, 266.0, 0.0),
    'welwkf1': ('waist_calibration', 174.0, 268.0, -14.0),
    'welwkf2': ('elbow_calibration', 176.0, 267.0, -25.0),
    'welwkf3': ('waist_calibration', 178.0, 256.0, -15.0),
    'welwkf4': ('waist_calibration', 177.0, 254.0, 0.0),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def anchors(record, body_label):
    points = record['review_landmarks']
    def logical(label):
        return np.array(points[label]['restored_before_translation'], dtype=float) / 2 + np.array(
            record['translate'], dtype=float) / 2
    return logical('head_anchor'), logical(body_label)


def transform_spec(name, record):
    body_label, target_head, target_body, head_shift = TARGETS[name]
    head, body = anchors(record, body_label)
    scale_x = 0.75
    upper = (target_body - target_head) / (body[1] - head[1])
    lower = (BOTTOM - target_body) / (BOTTOM - body[1])
    assert 0.5 < upper < 1.2 and 0.5 < lower < 1.2
    derivative = -head_shift / (body[1] - head[1])
    expansion = max(np.linalg.svd([[scale_x, derivative], [0, upper]], compute_uv=False).max(),
                    np.linalg.svd([[scale_x, 0], [0, lower]], compute_uv=False).max(), 1.0)
    assert min(record['effective_sampling_xy']) / expansion > 2, name
    return dict(source_head=head.tolist(), source_body=body.tolist(), target_head_y=target_head,
                target_body_y=target_body, head_x_shift=head_shift, horizontal_scale=scale_x,
                waterline_y=BOTTOM, preserve_above_head=False,
                maximum_occupied_expansion=float(expansion))


def map_logical(x, y, spec):
    source_head = spec['source_head'][1]
    source_body = spec['source_body'][1]
    target_head = spec['target_head_y']
    target_body = spec['target_body_y']
    upper = (target_body - target_head) / (source_body - source_head)
    lower = (BOTTOM - target_body) / (BOTTOM - source_body)
    output_y = np.where(y <= source_body, target_body + (y - source_body) * upper,
                        target_body + (y - source_body) * lower)
    if spec['preserve_above_head']:
        output_y = np.where(y <= source_head, y, output_y)
    shift = np.where(y <= source_head, spec['head_x_shift'],
                     np.where(y >= source_body, 0.0,
                              spec['head_x_shift'] * (source_body - y) / (source_body - source_head)))
    output_x = HORIZONTAL_CENTER + (x - HORIZONTAL_CENTER) * spec['horizontal_scale'] + shift
    return output_x, output_y


def inverse_grid(size, spec):
    width, height = size
    yy, xx = np.mgrid[:height, :width].astype(np.float32) / 2
    source_head = spec['source_head'][1]
    source_body = spec['source_body'][1]
    target_head = spec['target_head_y']
    target_body = spec['target_body_y']
    upper = (target_body - target_head) / (source_body - source_head)
    lower = (BOTTOM - target_body) / (BOTTOM - source_body)
    source_y = np.where(yy <= target_body, source_body + (yy - target_body) / upper,
                        source_body + (yy - target_body) / lower)
    if spec['preserve_above_head']:
        source_y = np.where(yy <= target_head, yy, source_y)
    shift = np.where(source_y <= source_head, spec['head_x_shift'],
                     np.where(source_y >= source_body, 0.0,
                              spec['head_x_shift'] * (source_body - source_y) / (source_body - source_head)))
    source_x = HORIZONTAL_CENTER + (xx - HORIZONTAL_CENTER - shift) / spec['horizontal_scale']
    return np.array([source_y * 2, source_x * 2])


def warp(image, mask, spec):
    assert image.mode == 'RGBA' and image.size == mask.size
    coordinates = inverse_grid(image.size, spec)
    def sample(values):
        return map_coordinates(values.astype(np.float32), coordinates, order=1,
                               mode='constant', cval=0, prefilter=False)
    pixels = np.asarray(image, dtype=np.float32)
    alpha = pixels[:, :, 3] / 255
    warped_alpha = sample(alpha)
    result = np.zeros_like(pixels)
    for channel in range(3):
        result[:, :, channel] = sample(pixels[:, :, channel] * alpha) / np.maximum(warped_alpha, 1e-8)
    result[:, :, 3] = warped_alpha * 255
    color = np.clip(np.round(result), 0, 255).astype(np.uint8)
    weights = np.asarray(mask)
    bands = [sample(weights)] if weights.ndim == 2 else [sample(weights[:, :, i])
        for i in range(weights.shape[2])]
    warped_mask = np.clip(np.stack(bands, axis=-1), 0, 255)
    if weights.ndim == 3:
        warped_mask *= np.minimum(1, 255 / np.maximum(1, warped_mask.sum(axis=-1, keepdims=True)))
    warped_mask = np.floor(warped_mask).astype(np.uint8)
    warped_mask[color[:, :, 3] == 0] = 0
    if weights.ndim == 2:
        warped_mask = warped_mask[:, :, 0]
    return Image.fromarray(color), Image.fromarray(warped_mask)


def source_path(name, folder, preview):
    saved = SOURCE / folder / (name + '.png')
    if saved.exists():
        return saved
    assert preview, 'Accepted normalization source missing: ' + str(saved)
    return STAGE / folder / (name + '.png')


def make_contact(output, images):
    for view in range(5):
        names = [f'welwke{view}', f'welwkf{view}', f'welwka{view}']
        panel = Image.new('RGB', (480 * 3, 410), '#252827')
        draw = ImageDraw.Draw(panel)
        for index, name in enumerate(names):
            sprite = images.get(name) or Image.open(STAGE / 'aligned_2x' / (name + '.png'))
            sprite = sprite.crop((160, 0, 1120, 670)).convert('RGBa').resize(
                (480, 335), Image.Resampling.LANCZOS).convert('RGBA')
            panel.paste(sprite, (480 * index, 35), sprite)
            draw.text((480 * index + 8, 8), name + (' normalized' if name in images else ' accepted'), fill='white')
            draw.line((480 * index, 370, 480 * (index + 1), 370), fill='#a34b4b')
        panel.save(output / f'walk_{view}_seam.png')
    names = ['welwka3', 'welwkb3', 'welwkc3']
    panel = Image.new('RGB', (480 * 3, 410), '#252827')
    draw = ImageDraw.Draw(panel)
    for index, name in enumerate(names):
        sprite = images.get(name) or Image.open(STAGE / 'aligned_2x' / (name + '.png'))
        sprite = sprite.crop((160, 0, 1120, 670)).convert('RGBa').resize(
            (480, 335), Image.Resampling.LANCZOS).convert('RGBA')
        panel.paste(sprite, (480 * index, 35), sprite)
        draw.text((480 * index + 8, 8), name + (' raw-source torso repair' if name == 'welwkb3'
                  else ' accepted'), fill='white')
        draw.line((480 * index, 370, 480 * (index + 1), 370), fill='#a34b4b')
    panel.save(output / 'walk_3_torso.png')


def main(preview):
    registration = json.loads((STAGE / 'registration.json').read_text())
    source_registration = SOURCE / 'registration.json'
    baseline = json.loads(source_registration.read_text()) if source_registration.exists() else registration
    output = STAGE / 'review' / 'walk_normalization_preview' if preview else STAGE / 'review' / 'walk_normalization'
    output.mkdir(parents=True, exist_ok=True)
    results = {}
    edited = {}
    if not preview:
        SOURCE.mkdir(parents=True, exist_ok=True)
        if not source_registration.exists():
            shutil.copy2(STAGE / 'registration.json', source_registration)
        for folder in ('aligned_2x', 'masks_2x'):
            (SOURCE / folder).mkdir(parents=True, exist_ok=True)
            for name in TARGETS:
                saved = SOURCE / folder / (name + '.png')
                if not saved.exists():
                    shutil.copy2(STAGE / folder / (name + '.png'), saved)
    for name in TARGETS:
        record = baseline[name]
        assert record['canvas_origin_px'] == [0, 0], name
        spec = transform_spec(name, record)
        art_path = source_path(name, 'aligned_2x', preview)
        mask_path = source_path(name, 'masks_2x', preview)
        art, mask = warp(Image.open(art_path).convert('RGBA'), Image.open(mask_path), spec)
        edited[name] = art
        target_art = output / (name + '.png')
        target_mask = output / (name + '_mask.png')
        art.save(target_art)
        mask.save(target_mask)
        if not preview:
            shutil.copy2(target_art, STAGE / 'aligned_2x' / (name + '.png'))
            shutil.copy2(target_mask, STAGE / 'masks_2x' / (name + '.png'))
        results[name] = dict(spec, source_art_sha256=sha(art_path), source_mask_sha256=sha(mask_path),
                             pre_export_art_sha256=sha(target_art), pre_export_mask_sha256=sha(target_mask))
        if not preview:
            registration[name] = json.loads(json.dumps(record))
            record = registration[name]
            before = record['review_landmarks']
            for point in before.values():
                old = np.array(point['restored_before_translation']) / 2 + np.array(record['translate']) / 2
                x, y = map_logical(old[0], old[1], spec)
                point['restored_before_translation'] = (np.array([x, y]) * 2 - record['translate']).tolist()
            record['independent_residual_logical'] = {
                label: (np.array(point['restored_before_translation']) / 2 + np.array(record['translate']) / 2
                        - point['native']).tolist() for label, point in before.items() if label != 'head_anchor'
                and label not in record.get('diagnostic_landmarks', [])}
            record['post_registration_normalization'] = results[name]
            record['effective_sampling_xy'] = (np.array(record['effective_sampling_xy'])
                / spec['maximum_occupied_expansion']).tolist()
            record['review_status'] = 'candidate_requires_visual_review'
    make_contact(output, edited)
    (output / 'transform.json').write_text(json.dumps(results, indent=2) + '\n')
    if not preview:
        (STAGE / 'registration.json').write_text(json.dumps(registration, indent=2) + '\n')
    print(json.dumps(dict(mode='preview' if preview else 'applied', output=str(output),
                          minimum_sampling=min(min(r['effective_sampling_xy']) for r in registration.values()),
                          frames=list(TARGETS))))


def finalize_export():
    registration = json.loads((STAGE / 'registration.json').read_text())
    for name in TARGETS:
        record = registration[name]['post_registration_normalization']
        for folder, label in [('aligned_2x', 'art'), ('masks_2x', 'mask')]:
            assert sha(SOURCE / folder / (name + '.png')) == record[f'source_{label}_sha256']
            expected = STAGE / 'review' / 'walk_normalization' / (
                name + ('_mask.png' if label == 'mask' else '.png'))
            old_key = f'output_{label}_sha256'
            if old_key in record:
                record[f'pre_export_{label}_sha256'] = record.pop(old_key)
            assert sha(expected) == record[f'pre_export_{label}_sha256']
            packaged = STAGE / folder / (name + '.png')
            before, after = np.asarray(Image.open(expected)), np.asarray(Image.open(packaged))
            if label == 'art':
                assert np.array_equal(before[:, :, 3], after[:, :, 3])
            else:
                visible = np.asarray(Image.open(STAGE / 'aligned_2x' / (name + '.png')).getchannel('A')) > 0
                assert np.array_equal(before[visible], after[visible])
            record[f'packaged_{label}_sha256'] = sha(packaged)
    (STAGE / 'registration.json').write_text(json.dumps(registration, indent=2) + '\n')
    print(json.dumps(dict(status='packaged_art_and_masks_hash_bound', frames=list(TARGETS))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', action='store_true', help='Write independent review candidates only')
    parser.add_argument('--finalize', action='store_true', help='Bind exporter output to the source and repair preview')
    args = parser.parse_args()
    assert not (args.preview and args.finalize)
    finalize_export() if args.finalize else main(args.preview)
