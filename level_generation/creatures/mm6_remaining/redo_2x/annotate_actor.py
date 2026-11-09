"""Measure candidate body/base registration points for a restored actor.

This records reproducible silhouette measurements for review. It does not approve
anatomy or animation: native-size placement contacts must still be inspected.
"""
import argparse
import hashlib
import json

import numpy as np
from PIL import Image

from prepare_run import REPO, native


BASE_ACTORS = {'hyd', 'seas', 'rea'}


def silhouette(image):
    alpha = np.array(image.convert('RGBA'))[:, :, 3]
    y, x = np.where(alpha >= 32)
    assert len(x), 'Expected a visible creature pose'
    return alpha >= 32, (int(x.min()), int(y.min()), int(x.max()) + 1, int(y.max()) + 1)


def band_center(mask, box, low, high):
    x0, y0, x1, y1 = box
    first = y0 + round((y1 - y0) * low)
    last = y0 + round((y1 - y0) * high)
    y, x = np.where(mask[first:max(first + 1, last)])
    assert len(x)
    return float(np.median(x))


def lower_mass_center(mask, box):
    x0, y0, x1, y1 = box
    first = y0 + round((y1 - y0) * .5)
    last = y0 + round((y1 - y0) * .98)
    y, x = np.where(mask[first:max(first + 1, last)])
    assert len(x)
    return float(x.mean())


def body_axis(mask, box):
    """Find the densest torso/coil column, ignoring wings and held weapons."""
    x0, y0, x1, y1 = box
    first = y0 + round((y1 - y0) * .36)
    last = y0 + round((y1 - y0) * .72)
    profile = mask[first:max(first + 1, last)].sum(axis=0).astype(float)
    radius = max(2, round((y1 - y0) * .035))
    smoothed = np.convolve(profile, np.ones(2 * radius + 1), mode='same')
    center = int(smoothed.argmax())
    neighborhood = max(2, round((y1 - y0) * .07))
    left, right = max(0, center - neighborhood), min(mask.shape[1], center + neighborhood + 1)
    weights = profile[left:right]
    return float(np.average(np.arange(left, right), weights=weights))


def points(mask, box, mode):
    x0, y0, x1, y1 = box
    floor = float(y1 - 1)
    if mode == 'base':
        axis = lower_mass_center(mask, box)
    else:
        axis = body_axis(mask, box)
    top = [band_center(mask, box, 0, .04), float(y0)]
    center = [body_axis(mask, box), float(y0 + (y1 - y0) * .54)]
    bottom = [band_center(mask, box, .93, 1), floor]
    return [[axis, floor], top, center, bottom]


def annotate(project):
    root = REPO / project
    out = root / 'redo_2x'
    run = json.loads((out / 'run.json').read_text())
    sources = json.loads((root / 'sources.json').read_text())
    mode = 'base' if root.name.removeprefix('mm6_') in BASE_ACTORS else 'upright'
    if not (out / 'processing.json').exists():
        (out / 'processing.json').write_text('{}\n')
    policy = json.loads((out / 'processing.json').read_text())
    assigned = {}
    reports = {}
    for job in run['jobs']:
        if not job.get('selected_raw'):
            continue
        path = out / 'review' / (job['id'] + '_extraction.json')
        if not path.exists():
            continue
        report = json.loads(path.read_text())
        assert report['raw'] == job['selected_raw'], job['id']
        reports[job['id']] = report
        for frame in report['frames']:
            name = frame['frame']
            if name not in sources.get('pixel_aliases', {}):
                clean = Image.open(REPO / frame['clean_path'])
                _, box = silhouette(clean)
                clipped = box[0] == 0 or box[1] == 0 or box[2] == clean.width or box[3] == clean.height
                previous = assigned.get(name)
                if previous is None or (previous[2] and not clipped):
                    # Overlap poses are generated twice. Prefer the complete crop when an earlier sheet
                    # let a meaningful limb or prop reach the edge of its cell.
                    assigned[name] = (job['id'], frame, clipped)
    for name, job_id in policy.get('frame_job_overrides', {}).items():
        report = reports[job_id]
        frame = next(frame for frame in report['frames'] if frame['frame'] == name)
        clean = Image.open(REPO / frame['clean_path'])
        _, box = silhouette(clean)
        clipped = box[0] == 0 or box[1] == 0 or box[2] == clean.width or box[3] == clean.height
        assert not clipped, (name, job_id)
        assigned[name] = (job_id, frame, False)
    output = dict(scale_policy='One measured silhouette-height scale per generated sheet; '
                  'the body or base axis and lowest contact register translation. '
                  'Top and center measurements are independent review diagnostics.',
                  calibration={}, frames={})
    for job in run['jobs']:
        report = reports.get(job['id'])
        if report is None:
            continue
        ratios = []
        for frame in report['frames']:
            name = frame['frame']
            _, native_box = silhouette(native(root, name))
            _, clean_box = silhouette(Image.open(REPO / frame['clean_path']))
            ratios.append((clean_box[3] - clean_box[1]) / (native_box[3] - native_box[1]))
        ratio = float(np.median(ratios))
        assert ratio > 2, (job['id'], ratio)
        output['calibration'][job['id']] = dict(native=[[0, 0], [0, 100]],
            raw=[[0, 0], [0, 100 * ratio]], pair=[0, 1], axes=[1],
            measurement='Median alpha>=32 native-to-new-art silhouette height within this generated sheet.')
    for name, (job_id, frame, _) in assigned.items():
        clean_path = REPO / frame['clean_path']
        native_mask, native_box = silhouette(native(root, name))
        raw_mask, raw_box = silhouette(Image.open(clean_path))
        output['frames'][name] = dict(job=job_id,
            native=points(native_mask, native_box, mode),
            raw=points(raw_mask, raw_box, mode),
            landmarks=['body_axis_floor_projection', 'top_silhouette', 'body_center', 'floor_contact'],
            clean_sha256=hashlib.sha256(clean_path.read_bytes()).hexdigest())
    path = out / 'review/anatomy_points.json'
    path.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(dict(annotated=len(output['frames']), calibrations=len(output['calibration']),
        minimum_calibration=min(v['raw'][1][1] / 100 for v in output['calibration'].values()),
        mode=mode, path=str(path))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project')
    annotate(parser.parse_args().project)
