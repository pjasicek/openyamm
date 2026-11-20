"""Session-local orchestration of the existing packed restoration tools; never accepts artwork automatically."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

REPO = Path.cwd().resolve()
SESSION = REPO / 'level_generation/creatures/mm7_mm8_packed_outline/session_mm7_03'
sys.path.insert(0, str(REPO / 'level_generation/creatures/mm6_remaining/redo_2x'))
from extract_run import extract
from annotate_packed_body import annotate
from register_packed_outline import register
from review_complete_sheets import contacts
from prepare_packed_outline import native_2x
from scipy import ndimage


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def head_feature(image, family):
    """Candidates with explicit feature identity, for drawn correspondence review on every pose."""
    rgba = np.array(image.convert('RGBA'))
    r, g, b = rgba[:, :, :3].astype(float).transpose(2, 0, 1)
    visible = rgba[:, :, 3] >= 128
    ys, xs = np.where(visible)
    top, bottom = ys.min(), ys.max()
    yy = np.indices(visible.shape)[0]
    if family == 'mm7_m234':
        selected = visible & (r > 80) & (r > g * 1.8) & (r > b * 1.8)
        label = 'red_eye_midpoint'
        y, x = np.where(selected)
        assert len(x), 'Visible native/restored eyes require a manual correspondence'
        return label, [float(np.mean(x)), float(np.mean(y))]
    if family == 'mm7_m242':
        selected = visible & (r > 80) & (g > r * .8) & (b > r * .55) & (b < g * 1.04)
        selected &= yy < top + (bottom - top) * .25
        labels, count = ndimage.label(selected)
        sizes = np.bincount(labels.ravel()); sizes[0] = 0
        assert count and sizes.max() > 0, 'Skull requires a manual correspondence'
        selected = labels == sizes.argmax()
        label = 'skull_bone_crown'
    else:
        fraction = .24 if family == 'mm7_m218' else .45
        selected = visible & (r > 90) & (g > 50) & (b > 35) & (r > g * 1.06) & (g > b * 1.08)
        selected &= yy < top + (bottom - top) * fraction
        if family == 'mm7_m218':
            # An isolated brown crown stem was mistaken for the forehead in view 1.
            # Select the substantial connected face region before taking its upper skin boundary.
            labels, count = ndimage.label(ndimage.binary_closing(selected, iterations=1))
            sizes = np.bincount(labels.ravel()); sizes[0] = 0
            assert count and sizes.max() > 0, 'Visible face requires a manual correspondence'
            selected &= labels == sizes.argmax()
        label = 'forehead_skin_cap'
    profile = selected.sum(axis=1)
    valid = np.flatnonzero(profile >= 3)
    assert len(valid), 'Forehead/skull requires a manual correspondence'
    cap = int(valid[0])
    y, x = np.where(selected[cap:cap + 2])
    return label, [float(np.median(x)), float(cap)]


def nominate_head_points(root, job):
    family = root.name
    if family not in ('mm7_m218', 'mm7_m226', 'mm7_m234', 'mm7_m242') or not job['id'].startswith('walk_'):
        return
    if int(job['id'].split('_')[1]) > 2:
        # Rear views have no corresponding visible forehead/eyes/skull; inspect their head silhouettes separately.
        return
    out = root / 'redo_2x'
    sources = read(root / 'sources.json')
    report = read(out / 'review' / (job['id'] + '_extraction.json'))
    settings = read(out / 'processing.json')
    pairs = {}
    for frame in report['frames']:
        name = frame['frame']
        native = native_2x(sources['sources'][name], sources, sources['base_palette'])[0]
        clean = Image.open(REPO / frame['clean_path']).convert('RGBA')
        label, npnt = head_feature(native, family)
        clean_label, cpnt = head_feature(clean, family)
        assert label == clean_label
        pairs[name] = dict(native=[v / 2 for v in npnt], clean=cpnt,
            feature=label, candidate=True, reason='Replace demonstrated leaf/weapon/wing/hand detector confusion; drawn correspondence and independent anatomical review remain required.')
    first = report['frames'][0]['frame']
    pair = pairs[first]
    settings.setdefault('anatomical_point_overrides', {}).setdefault(job['id'], {})['body_cap'] = dict(
        native=pair['native'], clean=pair['clean'])
    settings.setdefault('pose_point_overrides', {}).update(pairs)
    settings.setdefault('candidate_corresponding_features', {})[job['id']] = dict(
        raw_sha256=report['raw_sha256'], feature=pair['feature'], frames=list(pairs), accepted=False)
    write(out / 'processing.json', settings)


def process(family, jobs):
    root = SESSION / family
    out = root / 'redo_2x'
    project = str(root.relative_to(REPO))
    run = read(out / 'run.json')
    selected = [job for job in run['jobs'] if job.get('selected_raw') and (not jobs or job['id'] in jobs)]
    settings = read(out / 'processing.json')
    # Solid actors: inspected exterior alpha-1..3 scatter. Genie retains alpha-2..3 mist feathering.
    settings['supplied_alpha_noise_floor'] = 1 if family == 'mm7_m238' else 3
    body_jobs = set(settings.get('connected_body_extraction_jobs', []))
    notes = settings.setdefault('supplied_alpha_noise_review_by_job', {})
    seeds = settings.setdefault('component_seed_alpha_threshold_by_job', {})
    for job in selected:
        raw = REPO / job['selected_raw']
        digest = hashlib.sha256(raw.read_bytes()).hexdigest()
        pixels = np.array(Image.open(raw).convert('RGBA'))
        alpha = pixels[:, :, 3]
        notes[job['id']] = dict(raw_sha256=digest, floor=settings['supplied_alpha_noise_floor'],
            pixels_removed=int(((alpha > 0) & (alpha <= settings['supplied_alpha_noise_floor'])).sum()),
            reason='Inspected near-transparent exterior scatter; preserve supplied material RGB and all alpha above the recorded floor. Genie alpha-2..3 feathering is retained.')
        body_jobs.add(job['id'])
        gutter_review = settings.get('reviewed_gutter_extraction_jobs', {}).get(job['id'])
        if gutter_review:
            assert gutter_review['raw_sha256'] == digest and gutter_review['reason']
            body_jobs.discard(job['id'])
        if job['id'] not in seeds or seeds[job['id']]['raw_sha256'] != digest:
            seeds[job['id']] = dict(raw_sha256=digest, threshold=32,
                reason='Use substantial supplied-alpha bodies to separate complete sheet poses. All foreground above the recorded noise floor is retained exactly once, including thin props and mist.')
    settings['connected_body_extraction_jobs'] = sorted(body_jobs)
    write(out / 'processing.json', settings)
    good = []
    failures = settings.setdefault('processing_failures', {})
    for job in selected:
        try:
            extract(project, [job['id']])
            nominate_head_points(root, job)
            annotate(project, translate_poses=True, job_ids=[job['id']])
            good.append(job['id'])
            failures.pop(job['id'], None)
        except Exception as error:
            failures[job['id']] = str(error)
            print(json.dumps(dict(family=family, job=job['id'], processing_failure=str(error))), flush=True)
    # annotate saves updated calibrations; retain those when persisting failure notes.
    settings = read(out / 'processing.json')
    settings['processing_failures'] = failures
    write(out / 'processing.json', settings)
    if good:
        register(project)
        contacts(project)
    records = read(out / 'registration.json') if (out / 'registration.json').exists() else {}
    print(json.dumps(dict(family=family, processed=good, registered=len(records),
        clipped=[name for name, record in records.items() if record['raw_clip']],
        accepted=False)), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('families', nargs='+')
    parser.add_argument('--jobs', nargs='+')
    args = parser.parse_args()
    for family in args.families:
        process(family, args.jobs)
