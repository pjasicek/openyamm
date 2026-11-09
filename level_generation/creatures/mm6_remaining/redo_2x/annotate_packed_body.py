"""Record candidate complete-sheet body measurements for native-size visual review."""
import argparse
import hashlib
import json

import numpy as np
from PIL import Image

from prepare_packed_outline import REPO, native_2x


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def points(image, scale):
    mask = np.array(image.getchannel('A')) >= 128
    ys, xs = np.where(mask)
    assert len(xs), 'Expected a visible body or effect'
    top, bottom = ys.min(), ys.max()
    span = max(1, bottom - top)
    band = mask[top + round(span * .3):top + round(span * .65) + 1]
    profile = band.sum(axis=0).astype(float)
    radius = max(2, round(span * .035))
    axis = int(np.convolve(profile, np.ones(radius * 2 + 1), mode='same').argmax())
    window = max(round(8 * scale), round(span * .12))
    center = mask[:, max(0, axis - window):min(mask.shape[1], axis + window + 1)]
    cap_y = np.where(center)[0].min()
    cap_yx = np.where(center[cap_y:cap_y + max(1, round(2 * scale))])
    cap_x = float(np.median(cap_yx[1])) + max(0, axis - window)
    floor_y, floor_x = np.where(mask[max(top, bottom - round(3 * scale)):bottom + 1])
    waist_y = cap_y + round((bottom - cap_y) * .53)
    waist_x = np.where(mask[waist_y])[0]
    return dict(body_cap=[cap_x, float(cap_y)], contact_plane=[float(np.median(floor_x)), float(bottom)],
                torso_left=[float(waist_x.min()), float(waist_y)],
                torso_right=[float(waist_x.max()), float(waist_y)])


def annotate(project, translate_poses=True, job_ids=None):
    root = REPO / project
    out = root / 'redo_2x'
    sources = json.loads((root / 'sources.json').read_text())
    run = json.loads((out / 'run.json').read_text())
    policy = json.loads((out / 'processing.json').read_text())
    selected = set(job_ids) if job_ids is not None else None
    if selected is not None:
        assert selected <= {job['id'] for job in run['jobs']}, 'Unknown calibration job'
    calibrations = dict(policy.get('anatomical_sheet_calibration', {})) if selected is not None else {}
    translations = dict(policy.get('frame_translation_calibration', {})) if selected is not None else {}
    if selected is not None:
        owners = {}
        for job in run['jobs']:
            if job.get('selected_raw'):
                for name in job['frames']:
                    owners.setdefault(name, job['id'])
        translations = {name: row for name, row in translations.items() if owners.get(name) not in selected}
    overrides = policy.get('anatomical_point_overrides', {})
    for job in run['jobs']:
        if selected is not None and job['id'] not in selected:
            continue
        if not job.get('selected_raw'):
            continue
        path = out / 'review' / (job['id'] + '_extraction.json')
        if not path.exists():
            continue
        report = json.loads(path.read_text())
        assert report['raw'] == job['selected_raw']
        first = report['frames'][0]
        cw, ch = job['cell_native_size']
        width, height = report['raw_size']
        nominal = min(width / (job['columns'] * cw), height / (job['rows'] * ch))
        landmarks = {}
        for side in ['native', 'clean']:
            image = native_2x(sources['sources'][first['frame']], sources, sources['base_palette'])[0] if side == 'native' else Image.open(REPO / first['clean_path']).convert('RGBA')
            detected = points(image, 2 if side == 'native' else nominal)
            for label, point in detected.items():
                landmarks.setdefault(label, {})[side] = [v / 2 for v in point] if side == 'native' else point
        for label, pair in overrides.get(job['id'], {}).items():
            landmarks[label] = pair
        sampling = (landmarks['contact_plane']['clean'][1] - landmarks['body_cap']['clean'][1]) / (landmarks['contact_plane']['native'][1] - landmarks['body_cap']['native'][1])
        assert sampling > 0
        calibration = dict(frame=first['frame'], raw_sha256=report['raw_sha256'],
            clean_sha256=digest(REPO / first['clean_path']), landmarks=landmarks,
            scale_pair=['body_cap', 'contact_plane'], axes=[1], anchor='body_cap',
            method='Candidate first-pose central body/head cap to visible contact-plane scale, shared uniformly by every pose in this complete sheet. Torso width and native limb/prop sequence require independent visual review; these measurements do not certify anatomy.')
        calibrations[job['id']] = calibration
        if translate_poses:
            for frame in report['frames']:
                name = frame['frame']
                if name in translations:
                    continue
                native = native_2x(sources['sources'][name], sources, sources['base_palette'])[0]
                clean_path = REPO / frame['clean_path']
                clean = Image.open(clean_path).convert('RGBA')
                npnt = [v / 2 for v in points(native, 2)['body_cap']]
                cpnt = points(clean, sampling)['body_cap']
                manual = policy.get('pose_point_overrides', {}).get(name)
                if manual:
                    npnt, cpnt = manual['native'], manual['clean']
                translations[name] = dict(raw_sha256=report['raw_sha256'], clean_sha256=digest(clean_path),
                    axes=[0, 1], landmark='candidate_corresponding_body_cap', native=npnt, clean=cpnt,
                    method='Translate the complete pose using the corresponding body cap; retain the one common animation scale. Candidate detector identity must be checked on every native/restored pose before acceptance.')
    policy['anatomical_sheet_calibration'] = calibrations
    policy['frame_translation_calibration'] = translations
    (out / 'processing.json').write_text(json.dumps(policy, indent=2) + '\n')
    print(json.dumps(dict(project=project, candidate_calibrations=len(calibrations), candidate_translations=len(translations))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project')
    parser.add_argument('--shared-placement', action='store_true', help='Retain within-sheet effect/fragment positions')
    parser.add_argument('--jobs', nargs='+', help='Recalibrate only these complete sheets; retain other calibrations')
    args = parser.parse_args()
    annotate(args.project, not args.shared_placement, args.jobs)
