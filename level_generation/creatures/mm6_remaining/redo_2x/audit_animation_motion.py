"""Rank MM6 browser captures for manual motion review; never grant visual acceptance."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ACCEPTED = HERE.parent / 'ground_anchor_review' / 'accepted'
BACKGROUND = np.array([52, 58, 54], dtype=np.int16)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def silhouette_metrics(image, side):
    """Measure both actors in the same fixed capture window, excluding labels and ground guides."""
    left = side * 700 + 35
    pixels = np.asarray(image.convert('RGB'), dtype=np.int16)[50:528, left:left + 630]
    foreground = np.max(np.abs(pixels - BACKGROUND), axis=2) > 18
    y, x = np.nonzero(foreground)
    if len(x) < 20:
        return None
    return {
        'center': [float(np.mean(x) + 35), float(np.mean(y) + 50)],
        'bounds': [int(np.min(x) + 35), int(np.min(y) + 50),
                   int(np.max(x) + 35), int(np.max(y) + 50)],
        'area': int(len(x)),
    }


def temporal_residual(native, restored, first, second):
    """Compare movement between two poses; a stable art offset cancels out."""
    a = native[first]['center']
    b = native[second]['center']
    c = restored[first]['center']
    d = restored[second]['center']
    return [round((d[axis] - c[axis]) - (b[axis] - a[axis]), 2) for axis in range(2)]


def inspect_capture(path):
    image = Image.open(path)
    native = []
    restored = []
    for frame in range(image.n_frames):
        image.seek(frame)
        native.append(silhouette_metrics(image, 0))
        restored.append(silhouette_metrics(image, 1))
    if any(value is None for value in native + restored):
        return {'status': 'unmeasurable', 'encoded_frames': image.n_frames}
    pairs = []
    for second in range(1, image.n_frames):
        first = second - 1
        delta = temporal_residual(native, restored, first, second)
        pairs.append({'frames': [first, second], 'center_delta_residual_px': delta,
                      'center_score_px': round(float(np.hypot(*delta)), 2),
                      'top_delta_residual_px':
                          (restored[second]['bounds'][1] - restored[first]['bounds'][1]) -
                          (native[second]['bounds'][1] - native[first]['bounds'][1]),
                      'bottom_delta_residual_px':
                          (restored[second]['bounds'][3] - restored[first]['bounds'][3]) -
                          (native[second]['bounds'][3] - native[first]['bounds'][3])})
    peak = max(pairs, key=lambda pair: pair['center_score_px'], default=None)
    return {
        'status': 'measured',
        'encoded_frames': image.n_frames,
        'max_center_score_px': peak['center_score_px'] if peak else 0,
        'peak_pair': peak,
        'max_top_delta_residual_px': max((abs(pair['top_delta_residual_px']) for pair in pairs), default=0),
        'max_bottom_delta_residual_px': max((abs(pair['bottom_delta_residual_px']) for pair in pairs), default=0),
    }


def audit(inventory_path, output_path):
    inventory = json.loads(inventory_path.read_text())
    previous = json.loads(output_path.read_text()) if output_path.exists() else {}
    cached = {(family['family'], capture['action'], capture['view'], capture['webp_sha256']): capture
              for family in previous.get('families', []) for capture in family['captures']}
    reused = 0
    families = []
    for family in inventory['families']:
        index_path = REPO / family['index']
        assert digest(index_path) == family['index_sha256'], family['family']
        index = json.loads(index_path.read_text())
        assert len(index['captures']) == family['distinct_captures']
        captures = []
        for capture in index['captures']:
            path = REPO / capture['webp']
            assert digest(path) == capture['webp_sha256'], path
            key = (family['family'], capture['action'], capture['view'], capture['webp_sha256'])
            if key in cached:
                measurement = {field: value for field, value in cached[key].items()
                               if field not in ('action', 'view', 'webp', 'webp_sha256')}
                reused += 1
            else:
                measurement = inspect_capture(path)
            captures.append({
                'action': capture['action'],
                'view': capture['view'],
                'webp': capture['webp'],
                'webp_sha256': capture['webp_sha256'],
                **measurement,
            })
        families.append({'family': family['family'], 'manifest_sha256': family['manifest_sha256'],
                         'capture_index_sha256': family['index_sha256'], 'captures': captures})
    assert len(families) == inventory['family_count']
    assert sum(len(family['captures']) for family in families) == inventory['distinct_capture_count']
    ranked = sorted(((capture['max_center_score_px'], family['family'], capture['action'],
                      capture['view'], capture['webp'])
                     for family in families for capture in family['captures']
                     if capture['status'] == 'measured'), reverse=True)
    report = {
        'method': 'Fixed native/restored 700x600 browser captures; 18-RGB-distance silhouette threshold '
                  'from verified #343a36 background, excluding labels and ground guide. Consecutive-frame '
                  'centroid movement residual; art-shape and effect changes can cause false positives. '
                  'This ranks manual review and never proves visual acceptance.',
        'inventory_sha256': digest(inventory_path),
        'family_count': len(families),
        'capture_count': inventory['distinct_capture_count'],
        'measured_count': len(ranked),
        'unmeasurable_count': inventory['distinct_capture_count'] - len(ranked),
        'cached_measurements_reused': reused,
        'top_center_residuals': [dict(score_px=score, family=name, action=action, view=view, webp=webp)
                                 for score, name, action, view, webp in ranked[:100]],
        'families': families,
        'visual_acceptance': False,
    }
    output_path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'families': len(families), 'captures': report['capture_count'],
                      'measured': report['measured_count'], 'reused': reused, 'output': str(output_path)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--inventory', type=Path, default=ACCEPTED / 'animation_capture_inventory.json')
    parser.add_argument('--output', type=Path, default=ACCEPTED / 'animation_motion_triage.json')
    arguments = parser.parse_args()
    audit(arguments.inventory, arguments.output)
