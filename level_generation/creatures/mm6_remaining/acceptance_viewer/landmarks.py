"""Conservative, independently located review landmarks, in native logical coordinates.

Suggestions never change placement or acceptance. Template tracking stays in the same
stored view; a missing point means unknown, not invisible. Only a reviewer can record
an explicit null (hidden or inapplicable).
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage, signal


KINDS = ('eye1', 'eye2', 'head', 'head_top', 'groin')
SIDES = ('original', 'restored')
CONTRACT = ('Native logical pixels in the shared actor canvas, before frame scale, mirroring, '
            'placement offsets and size corrections. Head stores X only as [x, null]. '
            'Other points store [x, y]. Missing = unknown; null = explicitly hidden/inapplicable. '
            'Original BMP coordinates subtract manifest.frames[name].native_offset. '
            'Restored atlas-local pixels = logical point * pixels_per_logical_pixel - crop_origin_px.')
HEAD_LABELS = ('head_centre', 'reviewed_head', 'head_or_skull_center', 'head_skull',
               'back_skull', 'queen_face', 'head_crown')
# These selected MM6 families have separately visible legs. Dresses, robes, tails,
# machinery and multi-legged creatures are deliberately not assigned an A-gap point.
BIPEDS = {'arc1', 'bar1', 'dmn', 'ert', 'figc', 'fgt', 'goblin', 'gua', 'jak1',
          'kni', 'lch', 'min1', 'nobl', 'ogr', 'pman', 'pmn2',
          'natm', 'ske', 'thf', 'ttn1', 'wfigt1', 'wdm', 'gar', 'hrp'}


def validate_landmarks(records, manifest):
    if not isinstance(records, dict):
        raise ValueError('landmarks must be a frame-keyed object')
    for name, sides in records.items():
        if name not in manifest['frames'] or not isinstance(sides, dict) or set(sides) - set(SIDES):
            raise ValueError('Unknown landmark frame or side')
        for points in sides.values():
            if not isinstance(points, dict) or set(points) - set(KINDS):
                raise ValueError('Unknown landmark kind')
            for kind, point in points.items():
                if point is None:
                    continue
                if not isinstance(point, list) or len(point) != 2:
                    raise ValueError('A landmark requires [x, y], [head_x, null], or null')
                for axis, value in enumerate(point):
                    if kind == 'head' and axis == 1 and value is None:
                        continue
                    if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 16384:
                        raise ValueError('Landmark coordinates must be finite logical pixels within ±16384')
                if kind == 'head' and point[1] is not None:
                    raise ValueError('Head is an X-only landmark; use [x, null]')
    return records


def source_signature(root, seeds):
    registration = root / 'registration.json'
    digest = hashlib.sha256(registration.read_bytes() if registration.exists() else b'')
    digest.update(json.dumps(seeds, sort_keys=True).encode())
    digest.update(Path(__file__).read_bytes())
    return digest.hexdigest()


def canonical_views(manifest):
    views = defaultdict(set)
    palette = next(k for k, v in manifest['variants'].items() if v.get('exact_base_bypass'))
    for action in manifest['animations_by_palette'][palette].values():
        for view, steps in action['views'].items():
            for step in steps:
                if not step.get('mirrored'):
                    views[step['frame']].add(view)
    return views


def actor_image(root, manifest, name, side):
    """Render both inputs at 1 native pixel per pixel with their exact fractional anchors."""
    frame = manifest['frames'][name]
    width, height = manifest['logical_canvas']
    canvas = Image.new('RGBA', (width, height))
    if side == 'original':
        palette = next(k for k, v in manifest['variants'].items() if v.get('exact_base_bypass'))
        with Image.open(root / 'native_variants' / f'{name}_{palette}.png') as image:
            # Native previews use floor-centred padding. Shift by the fractional
            # remainder exactly as the reviewer does, rather than snapping seeds.
            sw, sh = frame['source_canvas']
            dx = (width - sw) / 2 - math.floor((width - sw) / 2)
            dy = -(height - sh) / 2 if manifest.get('anchor') == 'center' else 0
            canvas = image.convert('RGBA').transform((width, height), Image.Transform.AFFINE,
                    (1, 0, -dx, 0, 1, -dy), Image.Resampling.BILINEAR)
    else:
        tier = manifest['pixels_per_logical_pixel']
        with Image.open(root / 'aligned_2x' / f'{name}.png') as image:
            # aligned masters may start at a negative canvas origin. Recover global
            # actor coordinates before reducing, rather than using the atlas crop.
            ox, oy = frame.get('aligned_canvas_origin_px', [0, 0])
            canvas = image.convert('RGBA').transform((width, height), Image.Transform.AFFINE,
                    (tier, 0, -ox, 0, tier, -oy), Image.Resampling.BILINEAR)
    return np.asarray(canvas).astype(np.float32)


def registration_seeds(root, manifest):
    path = root / 'registration.json'
    records = json.loads(path.read_text()) if path.exists() else {}
    seeds = {}
    tier = manifest['pixels_per_logical_pixel']
    for name, frame in manifest['frames'].items():
        record = records.get(name, {})
        landmarks = record.get('review_landmarks', {})
        translation = record.get('translate')
        correction = frame.get('anchor_correction_px', [0, 0])
        if (not isinstance(translation, list) or len(translation) != 2 or
                record.get('geometry_correction') or record.get('warp')):
            continue
        for kind, labels in [('head', HEAD_LABELS), ('eye1', ('eye',)), ('head_top', ('head_crown',))]:
            measurement = next((landmarks[label] for label in labels if label in landmarks), None)
            if not isinstance(measurement, dict):
                continue
            original = measurement.get('native')
            restored = measurement.get('restored_before_translation')
            if not all(isinstance(p, list) and len(p) == 2 for p in (original, restored)):
                continue
            for side, point in [('original', [(original[i] * tier + correction[i]) / tier for i in range(2)]),
                                ('restored', [(restored[i] + translation[i] + correction[i]) / tier
                                              for i in range(2)])]:
                label = next(label for label in labels if label in landmarks)
                seeds.setdefault(name, {}).setdefault(side, {})[kind] = {
                    'xy': [point[0], None] if kind == 'head' else point,
                    'tracking_xy': point, 'confidence': .95,
                    'source': f'registration.json: {label}'}
    return seeds


def head_top(image, tracking):
    """Find a compact crown contour near a located head, not the highest sprite pixel."""
    if not tracking or tracking[1] is None:
        return None
    alpha = image[:, :, 3] >= 128
    ys, _ = np.nonzero(alpha)
    if not len(ys):
        return None
    height = float(ys.max() - ys.min())
    radius = max(2, min(8, round(height * .025)))
    x = round(tracking[0])
    lo, hi = x-radius, x+radius+1
    start = max(0, math.floor(tracking[1] - max(12, min(45, height*.17))))
    end = min(alpha.shape[0], math.ceil(tracking[1] + max(8, height*.055)))
    if lo < 0 or hi > alpha.shape[1] or end-start < 8:
        return None
    tops = []
    for column in range(lo, hi):
        occupied = np.flatnonzero(alpha[start:end, column])
        if not len(occupied):
            return None
        tops.append(int(occupied[0]) + start)
    # A clipped search or narrow upright projection cannot establish the crown.
    if min(tops) <= start+1 or max(tops)-min(tops) > max(5, height*.03):
        return None
    top = min(tops)
    sample_y = min(end-1, top+max(3, round(height*.015)))
    if np.count_nonzero(alpha[sample_y, lo:hi]) < (hi-lo)*.7:
        return None
    # Require the cap to continue into the head, rather than floating foreground.
    core_end = min(end, max(sample_y+4, math.ceil(tracking[1])+1))
    if (not alpha[sample_y:min(end, sample_y+4), x-1:x+2].all() or
            np.any(alpha[sample_y:core_end, lo:hi].sum(axis=1) < (hi-lo)*.7)):
        return None
    columns = [lo+i for i, y in enumerate(tops) if y <= top+1]
    return [float(np.median(columns)), float(top)]


def template_match(source, target, point, radius=22, patch_radius=8):
    """Require both a close appearance match and a distinct spatial maximum."""
    x, y = (round(v) for v in point)
    h, w = source.shape[:2]
    r = patch_radius
    if not (r <= x < w - r and r <= y < h - r):
        return None
    patch = source[y-r:y+r+1, x-r:x+r+1]
    if np.count_nonzero(patch[:, :, 3] >= 128) < .3 * patch.shape[0] * patch.shape[1]:
        return None
    def features(image):
        alpha = image[:, :, 3:4] / 255
        return np.concatenate((image[:, :, :3] * alpha, alpha * 128), axis=2)
    patch = features(patch)
    patch -= patch.mean(axis=(0, 1))
    energy = np.sum(patch * patch)
    if energy < 1000:
        return None
    left, top = max(0, x-r-radius), max(0, y-r-radius)
    right, bottom = min(w, x+r+radius+1), min(h, y+r+radius+1)
    region = features(target[top:bottom, left:right])
    shape = patch.shape[:2]
    ones = np.ones(shape, dtype=np.float32)
    numerator = sum(signal.correlate2d(region[:, :, c], patch[:, :, c], mode='valid') for c in range(4))
    denominator = sum(signal.correlate2d(region[:, :, c] ** 2, ones, mode='valid') -
                      signal.correlate2d(region[:, :, c], ones, mode='valid') ** 2 / ones.size
                      for c in range(4))
    scores = numerator / np.sqrt(np.maximum(denominator * energy, 1))
    iy, ix = np.unravel_index(np.argmax(scores), scores.shape)
    score = float(scores[iy, ix])
    alternatives = scores.copy()
    alternatives[max(0, iy-3):iy+4, max(0, ix-3):ix+4] = -1
    margin = score - float(alternatives.max())
    if score < .94 or margin < .025:
        return None
    return [float(point[0] + left + ix + r - x), float(point[1] + top + iy + r - y)], score


def leg_gap(image):
    """Locate a visible A-shaped split, not the centre of the pelvis or a skirt hem."""
    alpha = image[:, :, 3] >= 128
    ys, xs = np.nonzero(alpha)
    if not len(xs):
        return None
    top, bottom = ys.min(), ys.max()
    height = bottom - top
    if height < 40:
        return None
    # A lower-torso axis is less vulnerable to helmets, wings and raised weapons.
    rows = alpha[round(top + height*.35):round(top + height*.58)]
    weights = ndimage.uniform_filter1d(rows.sum(axis=0).astype(float), max(3, round(height*.08)))
    axis = int(np.median(np.flatnonzero(weights >= weights.max() * .95)))
    lo, hi = max(0, axis-round(height*.16)), min(alpha.shape[1], axis+round(height*.16)+1)
    start, end = round(top+height*.43), round(top+height*.74)
    def runs(row):
        background = ~alpha[row, lo:hi]
        changes = np.diff(np.r_[False, background, False].astype(int))
        return list(zip(np.flatnonzero(changes == 1), np.flatnonzero(changes == -1)-1))

    def leg_width(row, a, b):
        left = a - 1
        while left >= 0 and alpha[row, lo+left]:
            left -= 1
        right = b + 1
        while right < hi-lo and alpha[row, lo+right]:
            right += 1
        return a-left-1, right-b-1

    def continues_between_legs(y, a, b):
        initial_width = b-a+1
        widened = False
        # Follow this particular gap, not the entire connected background. Gaps
        # alongside an arm/shield can share that background with the leg gap.
        for row in range(y+1, round(top+height*.90)+1):
            candidates = [(c, d) for c, d in runs(row) if c <= b+1 and d >= a-1 and
                          c > 0 and d < hi-lo-1 and abs((c+d)-(a+b)) <= 6]
            if not candidates:
                return False
            a, b = min(candidates, key=lambda run: abs(sum(run)-(a+b)))
            widths = leg_width(row, a, b)
            if min(widths) < max(3, round(height*.02)):
                return False
            if row >= y+round(height*.1) and b-a+1 > initial_width+1:
                widened = True
        return widened

    candidates = []
    for y in range(start, end):
        for a, b in runs(y):
            # Require an enclosed narrow apex and substantial leg material on both
            # sides. Border background and isolated armour holes do not qualify.
            if a < 3 or b >= hi-lo-3 or b-a > max(3, height*.025):
                continue
            if not (alpha[y, lo+a-3:lo+a].all() and alpha[y, lo+b+1:lo+b+4].all()):
                continue
            if not continues_between_legs(y, a, b):
                continue
            x = lo+(a+b)/2
            if abs(x-axis) <= height*.08:
                candidates.append([float(x), float(y)-.5])
        if candidates:
            return min(candidates, key=lambda p: abs(p[0]-axis))
    return None


def suggest(root, manifest, extra_seeds=None):
    seeds = registration_seeds(root, manifest)
    for name, sides in (extra_seeds or {}).items():
        if name not in manifest['frames']:
            continue
        for side, points in sides.items():
            for kind, point in points.items():
                if point is not None:
                    seeds.setdefault(name, {}).setdefault(side, {})[kind] = {
                        'xy': [point[0], None] if kind == 'head' else point,
                        'tracking_xy': point, 'confidence': 1,
                        'source': 'visually located seed'}
    views = canonical_views(manifest)
    images = {}
    def get(name, side):
        key = (name, side)
        if key not in images:
            images[key] = actor_image(root, manifest, name, side)
        return images[key]
    result = json.loads(json.dumps(seeds))
    for name in manifest['frames']:
        for side in SIDES:
            points = result.setdefault(name, {}).setdefault(side, {})
            candidates = [(other, values[side]) for other, values in seeds.items()
                          if side in values and views[name] & views[other]]
            for kind in KINDS:
                if kind in points:
                    continue
                matches = []
                for other, values in candidates:
                    if kind not in values:
                        continue
                    seed = values[kind]
                    tracking = seed['tracking_xy']
                    if tracking[1] is None:
                        continue
                    found = template_match(get(other, side), get(name, side), tracking)
                    if found:
                        point, confidence = found
                        matches.append((point, confidence, other))
                    if len(matches) >= 3:
                        break
                if matches:
                    # Conflicting seed matches are ambiguity, not a reason to pick
                    # the most convenient point or infer it from the opposite art.
                    if any(math.dist(matches[0][0], item[0]) > 3 for item in matches[1:]):
                        continue
                    point, confidence, other = max(matches, key=lambda value: value[1])
                    points[kind] = {'xy': [point[0], None] if kind == 'head' else point,
                                    'tracking_xy': point, 'confidence': round(confidence, 4),
                                    'source': f'same-view appearance match: {other}'}
            if 'head_top' not in points and 'head' in points:
                point = head_top(get(name, side), points['head'].get('tracking_xy'))
                if point:
                    points['head_top'] = {'xy': point, 'confidence': .94,
                                          'source': 'compact crown contour near located head axis'}
    family = manifest['creature'].split(':')[-1]
    if manifest['creature'].startswith('mm6:') and family in BIPEDS:
        for name in manifest['frames']:
            gaps = {side: leg_gap(get(name, side)) for side in SIDES}
            if all(gaps.values()) and math.dist(gaps['original'], gaps['restored']) <= 7:
                for side, point in gaps.items():
                    result[name][side].setdefault('groin', {
                        'xy': point, 'confidence': .94, 'source': 'visible two-leg A-gap; cross-art agreement'})
    result = {name: {side: points for side, points in sides.items() if points}
              for name, sides in result.items() if any(sides.values())}
    counts = Counter(f'{side}:{kind}' for sides in result.values()
                     for side, points in sides.items() for kind in points)
    return {'schema_version': 1, 'coordinate_contract': CONTRACT, 'frames': result,
            'coverage': {'frames_with_points': len(result), 'total_frames': len(manifest['frames']),
                         'points': dict(sorted(counts.items()))}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection', type=Path, required=True)
    parser.add_argument('--family', help='Optional exact creature ID')
    args = parser.parse_args()
    collection = json.loads(args.collection.read_text())
    folder = args.collection.parent / 'landmarks'
    folder.mkdir(exist_ok=True)
    seed_path = folder / 'seeds.json'
    seeds = json.loads(seed_path.read_text()) if seed_path.exists() else {}
    totals = Counter()
    for record in collection['families']:
        if args.family and record['creature'] != args.family:
            continue
        root = (args.collection.parent / record['manifest']).resolve().parent
        raw = (root / 'manifest.json').read_bytes()
        if hashlib.sha256(raw).hexdigest() != record['manifest_sha256']:
            raise ValueError(f'{record["creature"]}: manifest changed')
        family_seeds = seeds.get(record['creature'], {})
        result = suggest(root, json.loads(raw), family_seeds)
        result.update(creature=record['creature'], artifact_sha256=record['artifact_sha256'],
                      manifest_sha256=record['manifest_sha256'],
                      source_signature=source_signature(root, family_seeds))
        target = folder / (record['creature'].replace(':', '_') + '.json')
        temporary = target.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(result, indent=2) + '\n')
        temporary.replace(target)
        totals.update(result['coverage']['points'])
        print(record['creature'], result['coverage']['frames_with_points'], '/', record['frame_count'], flush=True)
    print('Points:', dict(totals))


if __name__ == '__main__':
    main()
