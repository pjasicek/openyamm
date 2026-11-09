#!/usr/bin/env python3
"""Room screenshot tour of one remade MM9 map for x4 seam/joint review.

    python3 mm9_room_tour.py MAP OUT_DIR [--rooms N] [--append]

Picks the N sectors with the largest floor area that lie at least 600 units apart, stands on the centroid of each
sector's largest floor face and shoots four directions at a slight downward pitch (walls, floor joints, corners) and
one upward view (ceiling). Writes OUT_DIR/tour.yml (with --append, adds to an existing tour, e.g. a door tour).
"""
import argparse
import math
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_blv_file  # noqa: E402

MAPS = ROOT / 'output/mm9_rework/assets_dev/worlds/mm9/maps'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('map')
    parser.add_argument('out_dir')
    parser.add_argument('--rooms', type=int, default=6)
    parser.add_argument('--append', action='store_true')
    args = parser.parse_args()
    stem = Path(args.map).stem
    payload = parse_blv_file(MAPS / f'{stem}.blv')['payload']
    vertices = payload['vertices']
    sectors = {}
    for face in payload['faces']:
        indices = face.get('vertex_indices') or []
        if len(indices) < 3 or face.get('is_portal'):
            continue
        points = np.array([[vertices[i][k] for k in 'xyz'] for i in indices], float)
        normal = np.zeros(3)
        for index in range(1, len(points) - 1):
            normal += np.cross(points[index] - points[0], points[index + 1] - points[0])
        area = np.linalg.norm(normal) / 2
        if area < 1 or normal[2] / (2 * area) < 0.9:
            continue  # floors only (upward normals)
        record = sectors.setdefault(face['room_number'], {'area': 0.0, 'best': (0.0, None)})
        record['area'] += area
        if area > record['best'][0]:
            record['best'] = (area, points.mean(axis=0))
    chosen = []
    for sector, record in sorted(sectors.items(), key=lambda item: -item[1]['area']):
        centre = record['best'][1]
        if centre is None or any(np.linalg.norm(centre[:2] - other[:2]) < 600 for _, other in chosen):
            continue
        chosen.append((sector, centre))
        if len(chosen) >= args.rooms:
            break
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tour_path = out / 'tour.yml'
    if args.append and tour_path.exists():
        tour = yaml.safe_load(tour_path.read_text())
    else:
        tour = {'output_dir': str(out.resolve()), 'settle_seconds': 2.0, 'exit': True, 'shots': []}
    for sector, centre in chosen:
        position = [round(float(centre[0])), round(float(centre[1])), round(float(centre[2]))]
        for label, yaw in (('e', 0.0), ('n', math.pi / 2), ('w', math.pi), ('s', -math.pi / 2)):
            tour['shots'].append({'name': f'room{sector}-{label}', 'position': position, 'yaw': yaw, 'pitch': -0.12})
        tour['shots'].append({'name': f'room{sector}-up', 'position': position, 'yaw': 0.0, 'pitch': 0.9})
    tour_path.write_text(yaml.safe_dump(tour, sort_keys=False))
    print(tour_path, len(chosen), 'rooms')


if __name__ == '__main__':
    main()
