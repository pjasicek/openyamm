"""Delegate shared extraction, assigning detached props by their reviewed native grid cell.

The shared nearest-body assignment can attach a thrown prop to a different row.
This session-only operation retains each entire connected component exactly once.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'mm6_remaining/redo_2x'))
import extract_run


def grid_components(delivered, job, grid_groups=False, seed_alpha_threshold=0):
    pixels = np.array(delivered)
    labels, count = ndimage.label(pixels[:, :, 3] > 0)
    groups = [[] for _ in job['frames']]
    centers = {}
    owners = {}
    for label, region in enumerate(ndimage.find_objects(labels), 1):
        if region is None:
            continue
        y, x = ndimage.center_of_mass(labels[region] == label)
        y += region[0].start
        x += region[1].start
        owner = min(job['rows'] - 1, int(y * job['rows'] / delivered.height)) * job['columns']
        owner += min(job['columns'] - 1, int(x * job['columns'] / delivered.width))
        centers[label] = (y, x)
        if owner < len(groups) and int((labels[region] == label).sum()) >= 32:
            owners[label] = owner
    assert set(owners.values()) == set(range(len(groups)))
    for label, center in centers.items():
        owner = owners.get(label)
        if owner is None:
            nearest = min(owners, key=lambda value: sum((a-b)**2 for a, b in zip(center, centers[value])))
            owner = owners[nearest]
        groups[owner].append(label)
    output = []
    assigned = 0
    for group in groups:
        assert group, 'Every native pose must have returned artwork'
        part = pixels.copy()
        part[~np.isin(labels, group)] = 0
        assigned += int((part[:, :, 3] > 0).sum())
        image = Image.fromarray(part)
        x0, y0, x1, y1 = image.getbbox()
        rect = [max(0, x0 - 12), max(0, y0 - 12), min(image.width, x1 + 12), min(image.height, y1 + 12)]
        output.append((rect, image.crop(rect)))
    assert assigned == int((pixels[:, :, 3] > 0).sum())
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project')
    parser.add_argument('--jobs', nargs='+', required=True)
    args = parser.parse_args()
    out = Path(args.project) / 'redo_2x'
    run = json.loads((out / 'run.json').read_text())
    policy_path = out / 'processing.json'
    policy = json.loads(policy_path.read_text())
    policy['whole_component_grid_ownership'] = dict(
        module=str(Path(__file__).resolve()),
        sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        jobs={job['id']: dict(raw_sha256=hashlib.sha256(Path(job['selected_raw']).read_bytes()).hexdigest(),
                             reason='A detached thrown mace was assigned across rows by nearest-body extraction; '
                                    'visual inspection confirms whole-component native grid ownership.')
              for job in run['jobs'] if job['id'] in args.jobs})
    policy_path.write_text(json.dumps(policy, indent=2) + '\n')
    extract_run.connected_cells = grid_components
    extract_run.extract(args.project, args.jobs)
