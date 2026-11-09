"""Measure drop-in registration; geometry checks complement, never replace, visual review."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from finalize_classification import ROOT, digest
from freeze_targets import rendered


PROMPT = (
    'Drop-in fitting requirement: double the artwork coordinates as well as the canvas. Preserve the original '
    'occupied footprint, margins, internal spacing and attachment landmarks. Do not shrink the subject to add '
    'padding, enlarge it to fill native margins, recenter it or invent filler. For opaque portraits/pages/buttons '
    'preserve internal feature positions and scale, not merely the outer rectangle. Acceptance compares the '
    'native and restored images at the same logical size and checks landmarks and rendered silhouettes.'
)


def footprint(alpha, threshold):
    mask = alpha >= threshold
    ys, xs = np.nonzero(mask)
    return dict(pixels=int(mask.sum()),
                bounds=[int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if len(xs) else None,
                centroid=[float(xs.mean()), float(ys.mean())] if len(xs) else None)


def compare(source, restored):
    """Both inputs are rendered RGBA on the same x2 canvas. Never auto-fit either image."""
    expected = np.array(source.getchannel('A'))
    actual = np.array(restored.getchannel('A'))
    assert expected.shape == actual.shape, 'Incorrect exact x2 region size'
    results, failures = [], []
    for threshold in (16, 128):
        native, output = footprint(expected, threshold), footprint(actual, threshold)
        a, b = expected >= threshold, actual >= threshold
        union = int((a | b).sum())
        iou = float((a & b).sum() / union) if union else 1.0
        result = dict(alpha_threshold=threshold, expected=native, restored=output, silhouette_iou=iou)
        if bool(native['pixels']) != bool(output['pixels']):
            failures.append(f'alpha {threshold}: occupied/empty footprint changed')
        elif native['pixels']:
            bounds_error = max(abs(x - y) for x, y in zip(native['bounds'], output['bounds']))
            shift = max(abs(x - y) for x, y in zip(native['centroid'], output['centroid']))
            ratio = output['pixels'] / native['pixels']
            result.update(max_bounds_error_x2=bounds_error, centroid_shift_x2=shift, occupied_area_ratio=ratio)
            if bounds_error > 2 or shift > 2 or not 0.90 <= ratio <= 1.10 or iou < 0.85:
                failures.append(f'alpha {threshold}: footprint/margins changed beyond registration tolerance')
        results.append(result)
    return dict(thresholds=results, failures=failures,
                interior_visual_review_required=True,
                limits=dict(bounds_and_centroid_pixels_x2=2, occupied_area_ratio=[0.90, 1.10], minimum_iou=0.85))


def images(member, target, artifact):
    x, y, w, h = member['source_rect']
    with Image.open(ROOT / member['source_path']) as source, Image.open(artifact) as output:
        assert digest(ROOT / member['source_path']) == member['source_sha256'], 'Registration source changed'
        assert list(output.size) == member['export_region'][2:], 'Incorrect exact x2 region size'
        for profile in target['compositing']['profiles']:
            # PNG menu exports use the PNG loader's keys, not the original BMP/PCX-only extra keys.
            output_profile = 'menu_png' if profile.startswith('menu_') and artifact.suffix.lower() == '.png' else profile
            native = rendered(source, profile).crop((x, y, x + w, y + h))
            yield profile, native.resize((w * 2, h * 2), Image.Resampling.NEAREST), rendered(output, output_profile)


def measurements(member, target, artifact):
    return dict(schema_version=1, cell=member['id'], source_sha256=member['source_sha256'],
                artifact_sha256=digest(artifact), source_rect=member['source_rect'],
                profiles={profile: compare(native, output) for profile, native, output in images(member, target, artifact)})


def evidence(member, target, artifact, directory):
    record_path = directory / f'{member["id"]}-registration.json'
    assert not record_path.exists(), 'Preserve existing review notes; choose a new comparison directory'
    directory.mkdir(parents=True, exist_ok=True)
    report = measurements(member, target, artifact)
    paths = []
    for profile, native, output in images(member, target, artifact):
        w, h = native.size
        sheet = Image.new('RGB', (3 * w + 32, h + h // 2 + 72), (45, 45, 45))
        draw = ImageDraw.Draw(sheet)
        for index, (label, picture) in enumerate([
                ('Native x2 reference', native), ('Restored x2', output),
                ('50% overlay', Image.blend(native, output, 0.5))]):
            x = index * (w + 8)
            draw.text((x, 0), label, fill='white')
            sheet.paste(picture, (x, 24), picture)
            logical = picture.resize((w // 2, h // 2), Image.Resampling.LANCZOS)
            sheet.paste(logical, (x, h + 56), logical)
        path = directory / f'{member["id"]}-{profile}.png'
        sheet.save(path)
        paths.append(str(path.resolve()))
    record = dict(measurements=report, comparison_images={p: digest(Path(p)) for p in paths},
                  landmarks=[], visual_fit_notes='',
                  instructions='Inspect all comparison images. Record at least three named, spatially separated '
                               'features with source_xy in native region-local pixels and restored_xy in x2 '
                               'region-local pixels, measured from the actual artwork. Do not fill in expected '
                               'coordinates without inspecting the result. Check internal scale and every component. '
                               'Uniform deterministic regions need notes but no invented landmarks.')
    record_path.write_text(json.dumps(record, indent=2) + '\n')
    return dict(registration_record=str(record_path.resolve()), review_images=paths,
                failures={p: v['failures'] for p, v in report['profiles'].items() if v['failures']})


def validate(member, target, artifact, record_path):
    record = json.loads(record_path.read_text())
    current = measurements(member, target, artifact)
    assert record.get('measurements') == current, 'Missing or stale measured registration; run compare first'
    assert all(not p['failures'] for p in current['profiles'].values()), 'Artwork footprint does not fit native canvas'
    assert record.get('comparison_images'), 'Missing same-scale visual comparison'
    for name, sha in record['comparison_images'].items():
        assert Path(name).is_file() and digest(Path(name)) == sha, 'Registration comparison changed'
    assert record.get('visual_fit_notes', '').strip(), 'Record actual visual review of internal scale and placement'
    landmarks = record.get('landmarks', [])
    if member['method'] != 'deterministic_uniform_regions':
        assert len(landmarks) >= 3, 'Review at least three named registration landmarks'
        assert len({p['name'] for p in landmarks}) == len(landmarks), 'Use distinct landmarks'
        assert len({tuple(p['source_xy']) for p in landmarks}) == len(landmarks), 'Use spatially distinct landmarks'
        w, h = member['source_rect'][2:]
        for point in landmarks:
            assert point['name'].strip()
            a, b = point['source_xy'], point['restored_xy']
            assert len(a) == len(b) == 2
            assert all(np.isfinite(v) for v in [*a, *b]), 'Landmarks must be finite'
            assert 0 <= a[0] <= w and 0 <= a[1] <= h and 0 <= b[0] <= w * 2 and 0 <= b[1] <= h * 2
            assert max(abs(y - x * 2) for x, y in zip(a, b)) <= 2, 'Internal landmark scale/position changed'
    return list(record['comparison_images'])
