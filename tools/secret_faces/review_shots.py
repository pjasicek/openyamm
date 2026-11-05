#!/usr/bin/env python3
"""Screenshots of wall faces for reviewing secret-face candidates, one isolated game run per map (at most six at
once), plus a contact sheet.

    python3 tools/secret_faces/review_shots.py --world mm6 --out /abs/dir 6d08:652 cd2:314,4521 [--distance 600]

The camera stands on a floor in front of each face (either side; the nearest of a few distances that has floor under
it), at that floor's height, looking at the face's centre. Shots are <out>/<map>/NN-f<face>.png; the sheet is
<out>/sheet.jpg. A one-shot tour closes the game before the launcher's warmup ends, so "Game closed during warmup"
in a run's log is expected. Faces flagged secret pulse red when the party's Perception is high enough.
"""

import argparse
import math
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from util.map_export import parse_blv_file  # noqa: E402

MAX_RUNS = 6
SHEET_WIDTH = 480


def write_tour(world, map_name, face_ids, out_dir, distance):
    payload = parse_blv_file(REPO / 'assets_dev' / 'worlds' / world / 'maps' / f'{map_name}.blv')['payload']
    faces, vertices = payload['faces'], payload['vertices']

    def point(index):
        v = vertices[index]
        return (v['x'], v['y'], v['z']) if isinstance(v, dict) else tuple(v)

    floors = []
    for face in faces:
        if face['facet_type'] in (3, 4) and not face['is_portal']:
            points = [point(i) for i in face['vertex_indices']]
            floors.append(([(p[0], p[1]) for p in points], min(p[2] for p in points), max(p[2] for p in points)))

    def floor_at(x, y, z):
        best = None
        for polygon, low, high in floors:
            if low > z + 96 or high < z - 160:
                continue
            inside = False
            for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
                if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                    inside = not inside
            if inside and (best is None or abs(high - z) < abs(best - z)):
                best = high
        return best

    shots = []
    for face_index in face_ids:
        points = [point(i) for i in faces[face_index]['vertex_indices']]
        cx, cy, cz = (sum(p[k] for p in points) / len(points) for k in range(3))
        nx = ny = 0.0
        for a, b in zip(points, points[1:] + points[:1]):
            nx += (a[1] - b[1]) * (a[2] + b[2])
            ny += (a[2] - b[2]) * (a[0] + b[0])
        length = math.hypot(nx, ny) or 1.0
        nx, ny = nx / length, ny / length
        bottom = min(p[2] for p in points)
        placed = None
        for step in (distance, distance * 0.7, distance * 0.5, distance * 0.33, 140.0):
            for sign in (1.0, -1.0):
                x, y = cx + sign * nx * step, cy + sign * ny * step
                z = floor_at(x, y, bottom)
                if z is not None:
                    placed = (x, y, z, step)
                    break
            if placed:
                break
        if placed is None:
            print(f'{map_name}: no floor in front of face {face_index}', file=sys.stderr)
            continue
        x, y, z, used = placed
        yaw = math.atan2(cy - y, cx - x)
        pitch = max(-0.6, min(0.6, math.atan2(cz - (z + 160), used)))
        shots.append(f'  - name: f{face_index}\n    position: [{x:.0f}, {y:.0f}, {z:.0f}]\n'
                     f'    yaw: {yaw:.4f}\n    pitch: {pitch:.4f}\n')
    out_dir.mkdir(parents=True, exist_ok=True)
    tour = out_dir / 'tour.yml'
    tour.write_text(f'output_dir: {out_dir.resolve()}\nexit: true\nsettle_seconds: 1.5\nshots:\n' + ''.join(shots))
    return tour


def contact_sheet(paths, out):
    images = []
    for path in paths:
        image = Image.open(path).convert('RGB')
        image = image.resize((SHEET_WIDTH, int(image.height * SHEET_WIDTH / image.width)))
        ImageDraw.Draw(image).text((6, 6), f'{path.parent.name}/{path.stem}', fill=(255, 255, 0))
        images.append(image)
    columns = 3
    height = images[0].height
    sheet = Image.new('RGB', (columns * SHEET_WIDTH, (len(images) + columns - 1) // columns * height))
    for index, image in enumerate(images):
        sheet.paste(image, ((index % columns) * SHEET_WIDTH, (index // columns) * height))
    sheet.save(out, quality=85)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--world', default='mm6')
    parser.add_argument('--out', type=Path, required=True, help='absolute output directory')
    parser.add_argument('--distance', type=float, default=600.0)
    parser.add_argument('items', nargs='+', help='map:face[,face...]')
    args = parser.parse_args()
    out = args.out.resolve()
    running = []
    for item in args.items:
        map_name, faces = item.split(':')
        tour = write_tour(args.world, map_name, [int(f) for f in faces.split(',')], out / map_name, args.distance)
        log = open(out / f'{map_name}.log', 'w')
        command = [str(REPO / 'tools' / 'run_game.sh'), '--isolated', f'secret_{map_name}', '--world', args.world,
                   '--map', f'{map_name}.blv', '--warmup', '3', '--seconds', '45',
                   '--set', f'debug.screenshot_tour_path={tour}']
        running.append(subprocess.Popen(command, cwd=REPO, stdout=log, stderr=subprocess.STDOUT))
        while len(running) >= MAX_RUNS:
            running = [process for process in running if process.poll() is None]
            time.sleep(1)
    for process in running:
        process.wait()
    shots = sorted(out.glob('*/*.png'))
    if shots:
        contact_sheet(shots, out / 'sheet.jpg')
    print(f'{len(shots)} shots, sheet {out / "sheet.jpg"}')


if __name__ == '__main__':
    main()
