"""Show delivered detail and true contour patches at 100%; never resize artwork for this review."""
import argparse
import hashlib
import json
import math
import sys

import numpy as np
from PIL import Image, ImageDraw

from prepare_packed_outline import REPO
sys.path.insert(0, str(REPO / 'level_generation/creatures/mm6_peasants'))
from package_family import edge_stats


def review(project):
    root = REPO / project
    out = root / 'redo_2x'
    config = json.loads((root / 'config.json').read_text())
    run = json.loads((out / 'run.json').read_text())
    policy = json.loads((out / 'processing.json').read_text())
    samples = []
    paths = []
    for job in run['jobs']:
        path = out / 'review' / (job['id'] + '_extraction.json')
        if not job.get('selected_raw') or not path.exists():
            continue
        report = json.loads(path.read_text())
        assert report['raw'] == job['selected_raw']
        for frame in report['frames']:
            image_path = REPO / frame['clean_path']
            image = Image.open(image_path).convert('RGBA')
            stat = edge_stats(image, config['matte'])
            paths.append((stat['max_score'], frame['frame'], image_path, stat['position']))
        if job['id'] in ['walk_0_sheet', 'attack_0_sheet', 'death_0_sheet', 'corpse_0_sheet']:
            first = report['frames'][0]
            image_path = REPO / first['clean_path']
            image = Image.open(image_path).convert('RGBA')
            calibration = policy.get('anatomical_sheet_calibration', {}).get(job['id'], {})
            landmarks = calibration.get('landmarks', {})
            cap = landmarks.get('hair_crown', landmarks.get('body_cap', {})).get('clean')
            if cap:
                samples.append((first['frame'] + ' head/body cap', image_path, [cap[0], cap[1] + 48]))
            y, x = np.where(np.array(image.getchannel('A')) >= 128)
            samples.append((first['frame'] + ' material interior', image_path, [float(np.median(x)), float(np.median(y))]))
    registration = json.loads((out / 'registration.json').read_text())
    for name, record in registration.items():
        if 'retained_from' not in record:
            continue
        image_path = out / 'cleaned' / (name + '.png')
        image = Image.open(image_path).convert('RGBA')
        stat = edge_stats(image, config['matte'])
        paths.append((stat['max_score'], name, image_path, stat['position']))
        y, x = np.where(np.array(image.getchannel('A')) >= 128)
        samples.append((name + ' retained material', image_path, [float(np.median(x)), float(np.median(y))]))
    samples.extend((name + ' contour', path, point) for _, name, path, point in sorted(paths, reverse=True)[:6])
    columns = 4
    tile_width, tile_height = 268, 154
    sheet = Image.new('RGB', (columns * tile_width, math.ceil(len(samples) / columns) * tile_height), '#353535')
    draw = ImageDraw.Draw(sheet)
    evidence = []
    for index, (label, path, center) in enumerate(samples):
        image = Image.open(path).convert('RGBA')
        x, y = (index % columns) * tile_width, (index // columns) * tile_height
        draw.text((x + 3, y + 3), label, fill='white')
        cx, cy = (round(v) for v in center)
        rectangle = [cx - 64, cy - 64, cx + 64, cy + 64]
        patch = image.crop(rectangle)
        for side, color in enumerate(['#262a28', '#eee9df']):
            background = Image.new('RGBA', patch.size, color)
            background.alpha_composite(patch)
            sheet.paste(background, (x + side * 134, y + 22))
        evidence.append(dict(label=label, source=str(path.relative_to(out)),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(), source_rect=rectangle))
    sheet.save(out / 'review/detail_alpha_100pct.png')
    (out / 'review/detail_alpha_100pct.json').write_text(json.dumps(dict(
        delivered_pixel_scale=1, method='Unresized cleaned pixels composited with actual alpha on dark and ivory; contour score excludes near-opaque interior alpha 128–254.',
        samples=evidence), indent=2) + '\n')
    print(json.dumps(dict(project=project, samples=len(samples))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project')
    review(parser.parse_args().project)
