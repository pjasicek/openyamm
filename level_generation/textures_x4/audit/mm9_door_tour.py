#!/usr/bin/env python3
"""Screenshot tour of chosen doors of one remade MM9 map, closed and open, for x4 door review.

    python3 mm9_door_tour.py MAP OUT_DIR TEXTURE [TEXTURE ...] [--per-texture N] [--extra NAME:X,Y,Z,YAW,PITCH ...]

For each texture the first N door pairs (or single leaves) from `mm9_doors.json` that a map Lua handler opens are
shot: from the front (whole doorway), a close-up of the joint at a grazing angle, from the back, then the handler is
run (`event <id>` console command) and the doorway is shot open from the front. The camera stands where a ray from
the door centre along the leaf normal stays clear of other faces. Writes OUT_DIR/tour.yml and prints its path.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_blv_file  # noqa: E402

MAPS = ROOT / 'output/mm9_rework/assets_dev/worlds/mm9/maps'
EVENTS = ROOT / 'output/mm9_rework/assets_dev/worlds/mm9/events/maps'
EYE = 0  # tour positions are party (feet) positions


def door_handlers(map_stem):
    handlers = {}
    text = (EVENTS / f'{map_stem}.lua').read_text(errors='ignore')
    for match in re.finditer(r'^handlers\[(\d+)\]\s*=\s*function\(\)(.*)$', text, re.M):
        for door in re.findall(r'SetDoorState\((\d+)', match.group(2)):
            handlers.setdefault(int(door), int(match.group(1)))
    return handlers


def face_polys(payload):
    polys = []
    for face in payload['faces']:
        indices = face.get('vertex_indices') or []
        if len(indices) < 3 or face.get('is_portal'):
            continue
        points = np.array([[payload['vertices'][i][k] for k in 'xyz'] for i in indices], float)
        normal = np.cross(points[1] - points[0], points[2] - points[0])
        norm = np.linalg.norm(normal)
        if norm < 1e-6:
            continue
        polys.append((face['index'], points, normal / norm))
    return polys


def ray_hit(origin, direction, polys, skip):
    best = math.inf
    for index, points, normal in polys:
        if index in skip:
            continue
        denom = float(normal @ direction)
        if abs(denom) < 1e-6:
            continue
        t = float(normal @ (points[0] - origin)) / denom
        if t <= 1 or t >= best:
            continue
        hit = origin + t * direction
        # Point in polygon (project to the dominant plane).
        axis = int(np.argmax(np.abs(normal)))
        keep = [k for k in range(3) if k != axis]
        p2 = points[:, keep]
        h2 = hit[keep]
        inside = False
        for a in range(len(p2)):
            b = (a + 1) % len(p2)
            if (p2[a][1] > h2[1]) != (p2[b][1] > h2[1]):
                x = p2[a][0] + (h2[1] - p2[a][1]) * (p2[b][0] - p2[a][0]) / (p2[b][1] - p2[a][1])
                if x > h2[0]:
                    inside = not inside
        if inside:
            best = t
    return best


def shot(name, position, look, pitch=0.0, commands=None, settle=None):
    entry = {'name': name, 'position': [round(float(v)) for v in position],
             'yaw': round(math.atan2(look[1], look[0]), 4), 'pitch': pitch}
    if commands:
        entry['commands'] = commands
    if settle is not None:
        entry['settle_seconds'] = settle
    return entry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('map')
    parser.add_argument('out_dir')
    parser.add_argument('textures', nargs='+')
    parser.add_argument('--per-texture', type=int, default=1)
    args = parser.parse_args()
    stem = Path(args.map).stem
    report = json.loads((HERE / 'mm9_doors.json').read_text())['maps'][stem]
    scene = yaml.safe_load((MAPS / f'{stem}.scene.yml').read_text())
    doors = {door['door_id']: door for door in scene['initial_state']['doors']}
    payload = parse_blv_file(MAPS / f'{stem}.blv')['payload']
    polys = face_polys(payload)
    handlers = door_handlers(stem)
    shots = []
    for texture in args.textures:
        groups = [((pair['a'], pair['b']), pair['kind']) for pair in report['pairs']
                  if pair['tex_a'] == texture and pair['tex_b'] == texture]
        groups += [((single['door'],), 'single') for single in report['singles'] if single['texture'] == texture]
        taken = 0
        for ids, kind in groups:
            if taken >= args.per_texture:
                break
            if not all(i in handlers for i in ids) and any(
                    all(i in handlers for i in other) for other, _ in groups):
                continue  # prefer doors a handler opens; otherwise shoot them closed only
            face_ids = [f for i in ids for f in doors[i]['face_ids']]
            leaf_faces = [p for p in polys if p[0] in face_ids and abs(p[2][2]) < 0.7]
            if not leaf_faces:
                continue
            leaf_faces.sort(key=lambda p: -np.linalg.norm(np.cross(p[1][1] - p[1][0], p[1][2] - p[1][0])))
            normal = leaf_faces[0][2]
            points = np.concatenate([p[1] for p in leaf_faces])
            centre = points.mean(axis=0)
            floor = points[:, 2].min()
            height = points[:, 2].max() - floor
            horizontal = np.array([normal[0], normal[1], 0.0])
            horizontal /= np.linalg.norm(horizontal)
            along = np.cross([0.0, 0.0, 1.0], horizontal)
            width = float(np.ptp(points @ along))
            sides = []
            for sign in (1, -1):
                direction = sign * horizontal
                origin = np.array([centre[0], centre[1], floor + 60])
                clear = ray_hit(origin + direction * 20, direction, polys, set(face_ids))
                distance = min(clear - 60, max(1.4 * max(width, height), 300))
                if distance >= 150:
                    sides.append((sign, distance))
            if not sides:
                continue
            taken += 1
            tag = f'{texture}-d{ids[0]}'
            sign, distance = sides[0]
            front = np.array([centre[0], centre[1], floor]) + sign * horizontal * distance
            pitch_front = math.atan2(centre[2] - floor - 100, distance) * 0.6
            shots.append(shot(f'{tag}-closed-front', front, -sign * horizontal, round(pitch_front, 3)))
            # Joint close-up at a grazing angle: stand off to one side, look at the joint.
            near = min(distance, 160)
            side_pos = np.array([centre[0], centre[1], floor]) + sign * horizontal * near + along * 120
            look = np.array([centre[0], centre[1], floor]) - side_pos
            shots.append(shot(f'{tag}-joint-graze', side_pos, look, 0.15))
            if len(sides) > 1:
                sign_b, distance_b = sides[1]
                back = np.array([centre[0], centre[1], floor]) + sign_b * horizontal * distance_b
                shots.append(shot(f'{tag}-closed-back', back, -sign_b * horizontal, round(pitch_front, 3)))
            if ids[0] in handlers:
                shots.append(shot(f'{tag}-open-front', front, -sign * horizontal, round(pitch_front, 3),
                                  commands=[f'event {handlers[ids[0]]}'], settle=5.0))
            print(texture, kind, ids, 'event', handlers.get(ids[0]), 'sides', len(sides), file=sys.stderr)
        if not taken:
            print(texture, 'no door with a handler and a clear view', file=sys.stderr)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tour = {'output_dir': str(out.resolve()), 'settle_seconds': 2.0, 'exit': True, 'shots': shots}
    (out / 'tour.yml').write_text(yaml.safe_dump(tour, sort_keys=False))
    print(out / 'tour.yml')


if __name__ == '__main__':
    main()
