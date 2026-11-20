"""Prepare reviewable core/envelope landmarks for a radial sprite family.

The candidate points are measurements, not visual acceptance. Inspect the resulting
registration overlays and animation contacts before freezing a restoration.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from prepare_run import REPO, native


def box_and_alpha(image):
    pixels = np.array(image.convert('RGBA'))
    alpha = pixels[:, :, 3]
    ys, xs = np.where(alpha >= 32)
    if not len(xs):
        return None, pixels
    return [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)], pixels


def core(pixels, box, particle=False):
    alpha = pixels[:, :, 3].astype(float)
    yy, xx = np.indices(alpha.shape)
    if particle:
        weight = alpha
    else:
        x0, y0, x1, y1 = box
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        roi = (abs(xx - cx) < (x1 - x0) * .25) & (abs(yy - cy) < (y1 - y0) * .25)
        darkness = np.clip(170 - pixels[:, :, :3].astype(float).mean(axis=2), 0, 170)
        weight = darkness**2 * roi * (alpha >= 64)
        if weight.sum() < 1:
            weight = alpha
    return [round(float((xx * weight).sum() / weight.sum()), 2),
            round(float((yy * weight).sum() / weight.sum()), 2)]


def envelope(pixels, box, upper):
    alpha = pixels[:, :, 3]
    y = box[1] if upper else box[3] - 1
    band = alpha[max(0, y - 2):min(alpha.shape[0], y + 3)] >= 32
    ys, xs = np.where(band)
    return [round(float(np.median(xs)), 2), float(y)] if len(xs) else [float((box[0] + box[2]) / 2), float(y)]


def annotate(project):
    root = REPO / project
    out = root / 'redo_2x'
    run = json.loads((out / 'run.json').read_text())
    sources = json.loads((root / 'sources.json').read_text())
    policy = json.loads((out / 'processing.json').read_text()).get('radial_registration', {})
    baseline = policy['normal_native_height']
    corrupt = set(policy.get('corrupt_native_frames', []))
    particle = set(policy.get('particle_frames', []))
    overrides = policy.get('calibration_ratios', {})
    assigned = {}
    reports = {}
    for job in run['jobs']:
        if not job.get('selected_raw'):
            continue
        report_path = out / 'review' / (job['id'] + '_extraction.json')
        report = json.loads(report_path.read_text())
        assert report['raw'] == job['selected_raw'], job['id']
        reports[job['id']] = report
        for frame in report['frames']:
            name = frame['frame']
            if name not in sources['pixel_aliases']:
                assigned[name] = (job['id'], frame)
    output = dict(scale_policy='Sheetwise measured silhouette height; radial dark core sets translation; '
                  'upper/lower spine envelopes independently check size and source damage', calibration={}, frames={})
    for job in run['jobs']:
        if job['id'] not in reports:
            continue
        ratios = []
        for frame in reports[job['id']]['frames']:
            name = frame['frame']
            if name in corrupt or name in particle:
                continue
            nb, rb = frame['native_bounds'], frame['clean_bounds']
            if nb and rb:
                ratios.append((rb[3] - rb[1]) / (nb[3] - nb[1]))
        ratio = float(np.median(ratios)) if ratios else None
        if job['id'] in overrides:
            ratio = float(overrides[job['id']])
        elif job['id'] in policy.get('normalize_jobs', []):
            heights = [f['clean_bounds'][3] - f['clean_bounds'][1]
                       for f in reports[job['id']]['frames'] if f['clean_bounds']]
            ratio = float(np.median(heights)) / baseline
        assert ratio and ratio > 2, (job['id'], ratio)
        output['calibration'][job['id']] = dict(native=[[0, 0], [0, baseline]],
            raw=[[0, 0], [0, baseline * ratio]], pair=[0, 1], axes=[1],
            measurement='Median native/generated alpha>=32 envelope height for this action sheet; '
                        'damaged native tiles use the intact family height when configured.')
    for name, (job_id, frame) in assigned.items():
        native_image = native(root, name)
        clean_path = REPO / frame['clean_path']
        restored_image = Image.open(clean_path).convert('RGBA')
        nb, npix = box_and_alpha(native_image)
        rb, rpix = box_and_alpha(restored_image)
        assert nb and rb, name
        nc = policy.get('fixed_native_core', [134.5, 119]) if name in corrupt else core(
            npix, nb, particle=name in particle)
        rc = core(rpix, rb, particle=name in particle)
        points = dict(job=job_id, native=[nc, envelope(npix, nb, True), envelope(npix, nb, False)],
            raw=[rc, envelope(rpix, rb, True), envelope(rpix, rb, False)],
            landmarks=['radial_core', 'upper_spine_envelope', 'lower_spine_envelope'],
            clean_sha256=hashlib.sha256(clean_path.read_bytes()).hexdigest())
        if name in corrupt or name in particle:
            points['diagnostic_landmarks'] = ['upper_spine_envelope', 'lower_spine_envelope']
        output['frames'][name] = points
    path = out / 'review/anatomy_points.json'
    path.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(dict(annotated=len(assigned), calibrations=len(output['calibration']), path=str(path))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project')
    args = parser.parse_args()
    annotate(args.project)
