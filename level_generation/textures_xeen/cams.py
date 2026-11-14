#!/usr/bin/env python3
"""Tour cameras framing the faces of given textures in a built indoor map (oymap export JSON).

    cams.py <export.json> <spec.yml> --out <tour.yml> --dir <screenshot dir>

spec.yml: a list of {name, texture, [box: [x0, y0, x1, y1]], [distance], [index], [pose: {position, yaw, pitch}]}.
For each entry the largest matching face (or the index-th largest) is framed from in front along its normal, at the
party's floor height there, facing the face's centre; a `pose` is used as given. The same tour is run on the root
before and after a texture change, so both pictures share each camera."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import yaml

EYE = 168.0


def polygon_area(points):
    a = np.asarray(points, float)
    n = np.cross(a[1:-1] - a[0], a[2:] - a[0]).sum(axis=0)
    return 0.5 * float(np.linalg.norm(n))


def inside(point, polygon):
    x, y = point
    hit = False
    for (x0, y0), (x1, y1) in zip(polygon, polygon[1:] + polygon[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            hit = not hit
    return hit


def floor_at(faces, vertices, x, y, below):
    best = None
    for face in faces:
        if face['is_portal'] or face['plane_normal'][2] <= 30000:
            continue
        points = [vertices[i] for i in face['vertices']]
        if not inside((x, y), [p[:2] for p in points]):
            continue
        z = sum(p[2] for p in points) / len(points)
        if z <= below + 1 and (best is None or z > best):
            best = z
    return best


def camera(face, vertices, faces, distance):
    points = np.asarray([vertices[i] for i in face['vertices']], float)
    centre = points.mean(axis=0)
    normal = np.asarray(face['plane_normal'], float) / 65536.0
    horizontal = normal[:2]
    if np.linalg.norm(horizontal) < 0.3:   # floor or ceiling face: look down/up at it from beside
        offset = np.array([distance * 0.7, 0.0])
        position = centre[:2] + offset
        floor = floor_at(faces, vertices, *position, centre[2] + 400) or centre[2]
        eye = floor + EYE
        yaw = math.atan2(centre[1] - position[1], centre[0] - position[0])
        pitch = math.atan2(centre[2] - eye, distance * 0.7)
        return [float(position[0]), float(position[1]), float(floor)], yaw, pitch
    horizontal = horizontal / np.linalg.norm(horizontal)
    for scale in (1.0, 0.8, 0.6, 0.45, 0.3, 0.2):
        position = centre[:2] + horizontal * distance * scale
        floor = floor_at(faces, vertices, *position, points[:, 2].min() + 8)
        if floor is not None:
            break
    else:
        floor = points[:, 2].min()
        position = centre[:2] + horizontal * 64
    eye = floor + EYE
    dist = float(np.linalg.norm(centre[:2] - position))
    yaw = math.atan2(centre[1] - position[1], centre[0] - position[0])
    pitch = math.atan2(centre[2] - eye, max(dist, 1.0))
    return [round(float(position[0])), round(float(position[1])), round(float(floor))], yaw, pitch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('export')
    parser.add_argument('spec')
    parser.add_argument('--out', required=True)
    parser.add_argument('--dir', required=True)
    parser.add_argument('--settle', type=float, default=1.3)
    args = parser.parse_args()
    data = json.loads(Path(args.export).read_text())['map']
    vertices, faces = data['vertices'], data['faces']
    shots = []
    for entry in yaml.safe_load(Path(args.spec).read_text()):
        if 'pose' in entry:
            pose = entry['pose']
            position, yaw, pitch = pose['position'], pose['yaw'], pose['pitch']
        else:
            matches = []
            for face in faces:
                if face['is_portal'] or face['texture'].lower() != entry['texture'].lower():
                    continue
                points = [vertices[i] for i in face['vertices']]
                cx = sum(p[0] for p in points) / len(points)
                cy = sum(p[1] for p in points) / len(points)
                box = entry.get('box')
                if box and not (box[0] <= cx <= box[2] and box[1] <= cy <= box[3]):
                    continue
                upright = abs(face['plane_normal'][2]) < 30000
                if entry.get('upright') is not None and upright != entry['upright']:
                    continue
                matches.append((polygon_area(points), face))
            if not matches:
                print('no face for', entry['name'], entry['texture'])
                continue
            matches.sort(key=lambda m: -m[0])
            face = matches[min(entry.get('index', 0), len(matches) - 1)][1]
            position, yaw, pitch = camera(face, vertices, faces, entry.get('distance', 320))
            pitch = max(-1.2, min(1.2, pitch + entry.get('pitch_add', 0.0)))
        shot = {'name': entry['name'], 'position': position, 'yaw': round(yaw, 4), 'pitch': round(pitch, 4),
                'commands': ['render hud off'] + entry.get('commands', [])}
        if 'settle' in entry:
            shot['settle_seconds'] = entry['settle']
        shots.append(shot)
    tour = {'output_dir': str(Path(args.dir).resolve()), 'exit': True, 'settle_seconds': args.settle, 'shots': shots}
    Path(args.out).write_text(yaml.safe_dump(tour, sort_keys=False, default_flow_style=None, width=200))
    print(len(shots), 'shots ->', args.out)


if __name__ == '__main__':
    main()
