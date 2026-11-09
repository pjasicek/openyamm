"""Check the deliberately normalized Water Elemental walk against its accepted source.

The native f poses are oversized; native-relative residuals therefore do not
measure continuity after this authorized normalization. Check actual exported
head motion, body landmarks, silhouette heights, waterline, provenance and masks.
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image


STAGE = Path(__file__).resolve().parent / 'redo_2x'
SOURCE = STAGE / 'walk_normalization_source'
OUTPUT = STAGE / 'review' / 'walk_normalization'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point(registration, name, label):
    record = registration[name]
    before = record['review_landmarks'][label]['restored_before_translation']
    return [(before[i] + record['translate'][i]) / 2 for i in range(2)]


def bbox(name):
    image = Image.open(STAGE / 'aligned_2x' / (name + '.png')).getchannel('A')
    yy, xx = np.where(np.asarray(image) > 32)
    return [float(xx.min() / 2), float(yy.min() / 2), float(xx.max() / 2), float(yy.max() / 2)]


def main():
    current = read(STAGE / 'registration.json')
    baseline = read(SOURCE / 'registration.json')
    manifest = read(STAGE / 'manifest.json')
    assert set(current) == set(baseline) == set(manifest['frames'])
    assert len(current) == 71
    assert manifest['pixels_per_logical_pixel'] == 2
    assert manifest['logical_pivot'] == [320, 335]
    rows = []
    for view in range(5):
        names = [f'welwk{letter}{view}' for letter in 'abcdef']
        last = names[-1]
        normalization = current[last]['post_registration_normalization']
        for folder, label in [('aligned_2x', 'art'), ('masks_2x', 'mask')]:
            assert sha(SOURCE / folder / (last + '.png')) == normalization[f'source_{label}_sha256']
            assert sha(STAGE / folder / (last + '.png')) == normalization[f'packaged_{label}_sha256']
            candidate = OUTPUT / (last + ('_mask.png' if label == 'mask' else '.png'))
            assert sha(candidate) == normalization[f'pre_export_{label}_sha256']
        old_head = [point(baseline, name, 'head_anchor') for name in names]
        head = [point(current, name, 'head_anchor') for name in names]
        old_seam = [math.dist(old_head[i], old_head[j]) for i, j in ((4, 5), (5, 0))]
        seam = [math.dist(head[i], head[j]) for i, j in ((4, 5), (5, 0))]
        full_loop = [math.dist(head[i], head[(i + 1) % 6]) for i in range(6)]
        assert max(old_seam) > 40, (view, old_seam)
        assert max(seam) < 14, (view, seam)
        assert max(full_loop) < 18, (view, full_loop)
        assert max(seam) < max(old_seam) * 0.3, view
        fbox, ebox, abox = bbox(last), bbox(names[4]), bbox(names[0])
        assert min(ebox[1], abox[1]) - 2 <= fbox[1] <= max(ebox[1], abox[1]) + 2, view
        assert abs(fbox[3] - 335) <= 1.5, view
        body_label = 'elbow_calibration' if view == 2 else 'waist_calibration'
        body = point(current, last, body_label)
        assert min(current[last]['effective_sampling_xy']) > 2
        rows.append(dict(view=view, sequence=names, head_xy=head, head_step_logical=full_loop,
                         previous_seam_step_logical=old_seam, repaired_seam_step_logical=seam,
                         final_body_xy=body, final_bbox_logical=fbox,
                         source_detail_minimum=min(baseline[last]['effective_sampling_xy']),
                         repaired_detail_minimum=min(current[last]['effective_sampling_xy'])))
    b3 = 'welwkb3'
    b3_record = current[b3]
    b3_annotation = read(STAGE / 'review/anatomy_points.json')['frames'][b3]
    assert 'post_registration_normalization' not in b3_record
    assert b3_record['local_geometry']['clean_sha256'] == b3_annotation['clean_sha256']
    assert sha(STAGE / 'cleaned' / (b3 + '.png')) == b3_annotation['clean_sha256']
    assert 'waist_calibration' in b3_record['local_geometry']['control_landmarks']
    assert min(b3_record['effective_sampling_xy']) > 2
    native_head = b3_record['review_landmarks']['head_anchor']['native']
    native_waist = b3_record['review_landmarks']['waist_calibration']['native']
    old_span = point(baseline, b3, 'waist_calibration')[1] - point(baseline, b3, 'head_anchor')[1]
    new_span = point(current, b3, 'waist_calibration')[1] - point(current, b3, 'head_anchor')[1]
    native_span = native_waist[1] - native_head[1]
    assert abs(new_span - native_span) <= 1.5
    assert abs(point(current, b3, 'head_anchor')[1] - point(baseline, b3, 'head_anchor')[1]) < 0.1
    assert abs(bbox(b3)[3] - 335) <= 1.5
    for name in [f'welwkf{view}' for view in range(5)] + [b3]:
        alpha = np.asarray(Image.open(STAGE / 'aligned_2x' / (name + '.png')).getchannel('A'))
        mask = np.asarray(Image.open(STAGE / 'masks_2x' / (name + '.png')))
        assert np.max(mask.astype(int).sum(axis=2)) <= 255
        assert np.count_nonzero(mask[alpha > 0]) > 0
        page = manifest['frames'][name]['page']
        rect = manifest['frames'][name]['atlas_xywh']
        atlas = Image.open(STAGE / manifest['pages'][page]['base']).convert('RGBA')
        cropped = np.asarray(atlas.crop((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3])))
        master = np.asarray(Image.open(STAGE / 'aligned_2x' / (name + '.png')).convert('RGBA').crop(
            manifest['frames'][name]['crop_in_aligned_px']))
        assert np.array_equal(cropped[:, :, 3], master[:, :, 3])
        assert np.array_equal(cropped[cropped[:, :, 3] > 0], master[master[:, :, 3] > 0])
    result = dict(status='passed', intent='Deliberate normalization of oversized native f poses',
                  method='Actual exported atlas/master geometry, generated-source b3 mesh, restored landmarks and exact source/repair hashes',
                  manifest_sha256=sha(STAGE / 'manifest.json'), registration_sha256=sha(STAGE / 'registration.json'),
                  source_registration_sha256=sha(SOURCE / 'registration.json'),
                  head_seam_old_max=max(max(row['previous_seam_step_logical']) for row in rows),
                  head_seam_repaired_max=max(max(row['repaired_seam_step_logical']) for row in rows),
                  full_walk_head_step_max=max(max(row['head_step_logical']) for row in rows),
                  b3_torso_span=dict(previous=old_span, repaired=new_span, native=native_span),
                  minimum_generated_sampling=min(min(row['effective_sampling_xy']) for row in current.values()),
                  frames=rows)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / 'motion_audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'head_seam_old_max', 'head_seam_repaired_max',
                                             'full_walk_head_step_max', 'b3_torso_span',
                                             'minimum_generated_sampling')}))


if __name__ == '__main__':
    main()
