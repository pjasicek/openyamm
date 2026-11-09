"""Compile visually annotated anatomy into an isolated reviewer checkpoint.

No detection, source resampling, acceptance, checkpoint replacement or installation.
See ../../ANATOMICAL_PLACEMENT_WORKFLOW.md for the landmark-selection procedure.
"""

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

from checkpoints import Checkpoints
from serve import load_family


REPO = Path(__file__).resolve().parents[4]
POLICIES = {'humanoid_walk', 'humanoid_planted', 'flying', 'grounded_beast', 'collapse', 'other'}


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def compile_frame(manifest, bounds, name, annotation, previous):
    """Coordinates are untransformed actor-canvas logical pixels, before mirrors."""
    if annotation.get('policy') not in POLICIES:
        raise ValueError('Choose a documented action policy')
    reason = annotation.get('reason')
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError('Record the landmark and scale rationale')
    points = annotation.get('points')
    if not isinstance(points, dict):
        raise ValueError('points must contain native/restored landmark pairs')
    for pair in points.values():
        if not isinstance(pair, dict):
            raise ValueError('Invalid point pair')
        for side in ('native', 'restored'):
            xy = pair.get(side)
            if not isinstance(xy, list) or len(xy) != 2 or any(
                    v is not None and (not finite(v) or abs(v) > 16384) for v in xy):
                raise ValueError('Use logical [x,y] points; null means an unavailable axis')
    align = annotation.get('align')
    if not isinstance(align, dict) or set(align) != {'x', 'y'} or any(v not in points for v in align.values()):
        raise ValueError('Choose the X and Y landmarks explicitly')
    used = set(align.values())
    if ('scale_factor' in annotation) == ('scale_from' in annotation):
        raise ValueError('Supply either a calibrated scale_factor or a two-point scale_from')
    scale = annotation.get('scale_factor')
    if 'scale_from' in annotation:
        reference = annotation['scale_from']
        if not isinstance(reference, dict) or set(reference) != {'points', 'axis'}:
            raise ValueError('scale_from requires points:[first,second] and axis:x/y/distance')
        names = reference['points']
        axis = reference['axis']
        if not isinstance(names, list) or len(names) != 2 or names[0] == names[1] or any(n not in points for n in names):
            raise ValueError('Size needs two distinct, visible body landmarks')
        if axis not in ('x', 'y', 'distance'):
            raise ValueError('Unknown scale measurement axis')
        spans = []
        axes = [0, 1] if axis == 'distance' else [0 if axis == 'x' else 1]
        for side in ('native', 'restored'):
            a, b = [points[n][side] for n in names]
            if any(a[i] is None or b[i] is None for i in axes):
                raise ValueError('An occluded point cannot calibrate size')
            spans.append(math.dist(a, b) if axis == 'distance' else abs(a[axes[0]] - b[axes[0]]))
        if min(spans) <= 4:
            raise ValueError('Size span is too short; use separated body landmarks')
        scale = spans[0] / spans[1]
        used.update(names)
    if not finite(scale) or not .5 <= scale <= 1.5:
        raise ValueError('Scale must be within the existing reviewer range 0.5..1.5')
    checks = annotation.get('checks')
    if not isinstance(checks, list) or not checks or len(set(checks)) != len(checks) or any(
            n not in points or n in used for n in checks):
        raise ValueError('Provide independent check landmarks not used for fitting')
    if any(points[n] == points[u] for n in checks for u in used):
        raise ValueError('Renaming a fit point does not make it an independent check')
    tolerance = annotation.get('check_tolerance_native_px')
    if not isinstance(tolerance, list) or len(tolerance) != 2 or any(not finite(v) or v <= 0 for v in tolerance):
        raise ValueError('Record positive family-specific X/Y check tolerances in native pixels')
    k = manifest['pixels_per_logical_pixel']
    crop = manifest['frames'][name]['crop_origin_px']
    if bounds is None:
        raise ValueError('Empty art has no anatomical fit; preserve its existing record')
    anchor = [crop[0] + (bounds[0] + bounds[2]) / 2, crop[1] + bounds[3]]
    offset = []
    for i, axis in enumerate(('x', 'y')):
        pair = points[align[axis]]
        n, r = pair['native'][i], pair['restored'][i]
        if n is None or r is None:
            raise ValueError('Alignment landmark is unavailable on its selected axis')
        required = k * n - (anchor[i] + scale * (k * r - anchor[i]))
        offset.append(math.floor(required + .5))  # JavaScript Math.round, including negative ties.
    if any(abs(v) > 16384 for v in offset):
        raise ValueError('Offset exceeds existing reviewer range')
    residuals = {}
    for check in checks:
        pair = points[check]
        if any(v is None for side in ('native', 'restored') for v in pair[side]):
            raise ValueError('An independent check must have visible X and Y coordinates')
        error = [(anchor[i] + scale * (k * pair['restored'][i] - anchor[i]) + offset[i]) / k
                 - pair['native'][i] for i in range(2)]
        residuals[check] = error
        if any(abs(v) > tolerance[i] for i, v in enumerate(error)):
            raise ValueError(f'{check}: independent anatomical residual {error} exceeds {tolerance}')
    result = deepcopy(previous)
    result.update(offset_px=offset, scale_factor=scale, scale_anchor='bottom')
    result.setdefault('regenerate', False)
    old_note = result.get('note', '').strip()
    note = f'Anatomical proposal ({annotation["policy"]}); {reason.strip()}'
    result['note'] = '\n'.join(n for n in (old_note, note) if n)
    if len(result['note']) > 2000:
        raise ValueError('Preserved note plus rationale exceeds reviewer note limit')
    return result, {'scale_factor': scale, 'offset_px': offset, 'independent_residuals_native_px': residuals,
                    'check_tolerance_native_px': tolerance, 'annotation': annotation}


def checked_json(path, expected):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f'Stale pinned input: {path}')
    return json.loads(raw)


def build_proposal(plan, output):
    if plan.get('schema_version') != 1:
        raise ValueError('Unsupported landmark plan schema')
    checkpoint = (REPO / plan['checkpoint']).resolve()
    manifest_path = (REPO / plan['manifest']).resolve()
    evidence_path = output.with_suffix('.evidence.json')
    if output.resolve() in (checkpoint, manifest_path) or output.exists() or evidence_path.exists():
        raise ValueError('Use new isolated output paths; existing checkpoints and evidence are immutable inputs')
    data = checked_json(checkpoint, plan['checkpoint_sha256'])
    manifest = checked_json(manifest_path, plan['manifest_sha256'])
    if manifest['creature'].replace(':', '_') != plan['family']:
        raise ValueError('Family ID does not match the pinned manifest')
    family = load_family(plan['family'], manifest_path, 'anatomical proposal', 'proposal only')
    if family.artifact_sha256 != plan['artifact_sha256']:
        raise ValueError('Selected art changed; landmark plan requires remeasurement')
    current = data['families'].get(family.id, {}).get(family.artifact_sha256)
    if current is None or current.get('manifest_sha256') != family.manifest_sha256:
        raise ValueError('Checkpoint does not contain this exact selected art and manifest')
    annotations = plan.get('frames')
    if not isinstance(annotations, dict) or not annotations:
        raise ValueError('Plan must contain annotated frame names')
    request = deepcopy(current)
    accepted, blocked = {}, {}
    for name, annotation in annotations.items():
        if name not in manifest['frames']:
            raise ValueError(f'Unknown frame {name}; use authoritative names, including aliases')
        try:
            result, evidence = compile_frame(manifest, family.restored_bounds[name], name, annotation,
                                            request['frames'].get(name, {}))
            request['frames'][name] = result
            accepted[name] = evidence
        except (ValueError, TypeError, KeyError) as error:
            blocked[name] = str(error)
    report = {'schema_version': 1, 'status': 'proposal only; visual sequence review and acceptance remain pending',
              'family': family.id, 'manifest_sha256': family.manifest_sha256,
              'artifact_sha256': family.artifact_sha256, 'checkpoint_sha256': plan['checkpoint_sha256'],
              'compiled_frames': accepted, 'blocked_frames_preserved': blocked,
              'coverage': {'annotated': len(annotations), 'compiled': len(accepted), 'family_frames': len(manifest['frames'])}}
    if accepted:
        output.parent.mkdir(parents=True, exist_ok=True)
        # Save through the viewer's schema/revision validation on a copied checkpoint.
        created = False
        try:
            with output.open('x') as stream:
                created = True
                json.dump(data, stream, indent=2)
            Checkpoints(output).save(family, request)
        except Exception:
            if created:
                output.unlink(missing_ok=True)  # Only the new candidate created by this operation.
            raise
    else:
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
    with evidence_path.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New isolated frame_fixups.json candidate')
    args = parser.parse_args()
    try:
        report = build_proposal(json.loads(args.plan.read_text()), args.output.resolve())
    except (ValueError, KeyError, RuntimeError) as error:
        parser.error(str(error))
    print(json.dumps({'family': report['family'], **report['coverage'],
                      'blocked': len(report['blocked_frames_preserved']), 'status': report['status']}))


if __name__ == '__main__':
    main()
