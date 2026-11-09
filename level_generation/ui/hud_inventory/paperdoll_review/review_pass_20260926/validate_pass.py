"""Validate preservation, coverage, dimensions and alpha of the staged review pass."""
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote

import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path(__file__).resolve().parent
HERE = OUT.parent


def read(name):
    return json.loads((OUT / name).read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    baseline = read('baseline.json')
    review = read('review.original.json')
    stage = read('stage_manifest.json')
    repairs = read('repairs.json')['results']
    placements = read('placements.json')
    queue = read('repair_queue.json')
    assert digest(OUT / 'review.original.json') == baseline['review_sha256']
    assert digest(HERE.parent / 'checkpoint/state.json') == baseline['checkpoint_sha256']
    assert set(queue) <= set(repairs)
    approved = 0
    for target, record in stage['records'].items():
        assert record['decision'] == review['decisions'][target], target
        assert digest(HERE / unquote(record['reviewed_path'])) == record['reviewed_sha256'], target
        if record['decision']['decision'] == 'approve':
            assert digest(HERE / record['staged_path']) == record['reviewed_sha256'], target
            approved += 1
    for key, value in review['placements'].items():
        assert placements['placements'][key] == value, key
    inherited = 0
    for key, value in placements['placements'].items():
        if key not in review['placements']:
            donor = review['placements'][value['inherited_from']]
            assert value['delta'] == donor['delta'], key
            assert value['doll_type'] == donor['doll_type'], key
            assert value['slot'] == donor['slot'], key
            inherited += 1
    residue = {}
    saturated_fringe = {}
    for target, record in repairs.items():
        path = HERE / record['path']
        assert digest(path) == record['sha256'], target
        assert not record['unresolved'], (target, record['unresolved'])
        native = Image.open(HERE / 'native' / (target + '.png')).convert('RGBA')
        image = Image.open(path).convert('RGBA')
        assert image.size == (native.width * 2, native.height * 2), target
        pixels = np.asarray(image)
        assert (pixels[:, :, 3] > 0).any(), target
        assert not pixels[pixels[:, :, 3] == 0, :3].any(), target
        n = np.asarray(native.resize(image.size, Image.Resampling.NEAREST)).astype(float)
        nr, ng, nb = n[:, :, :3].transpose(2, 0, 1)
        protected = ndimage.binary_dilation((np.minimum(nr, nb) - ng > 22) & (n[:, :, 3] > 96), iterations=3)
        r, g, b, a = pixels.astype(float).transpose(2, 0, 1)
        bad = (np.minimum(r, b) - g > 20) & (r > 40) & (b > 35) & (a > 8) & ~protected
        if bad.any():
            residue[target] = int(bad.sum())
        native_chroma = ndimage.maximum_filter(np.where(n[:, :, 3] > 96, np.minimum(nr, nb) - ng, 0), size=7)
        distance = ndimage.distance_transform_edt(np.pad(a > 8, 1))[1:-1, 1:-1]
        fringe = (a > 8) & (distance <= 4) & (np.minimum(r, b) - g > 65) & (np.minimum(r, b) - g > native_chroma + 45)
        if fringe.any():
            saturated_fringe[target] = int(fringe.sum())
    with (OUT / 'placement_proposals.csv').open() as stream:
        assert len(list(csv.DictReader(stream))) == len(placements['placements'])
    report = {
        'result': 'PASS', 'immutable_export_sha256': baseline['review_sha256'],
        'checkpoint_unchanged': True, 'preserved_decisions': len(review['decisions']),
        'staged_approved_images_hash_verified': approved,
        'original_placements_preserved_exactly': len(review['placements']),
        'inherited_wand_placements': inherited,
        'explicit_wand_conflicts_preserved': len(placements['inheritance_conflicts']),
        'repair_queue_covered': len(queue), 'repaired_candidates': len(repairs),
        'all_dimensions_native_2x': True, 'transparent_rgb_zero': True,
        'remaining_non_native_pink_pixels': residue,
        'remaining_high_chroma_edge_screen': saturated_fringe,
        'color_scan_limit': 'Native purple detail is protected; this scan is not a substitute for visual review.'
    }
    (OUT / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
