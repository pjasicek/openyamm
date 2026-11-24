#!/usr/bin/env python3
"""Screenshots of the classic kit on installed maps: per map three door fronts of kit houses (the largest buildings
whose door wall is known) and one view over the houses, captured in the game from assets_dev.

  python3 check_maps.py tour x2 x3 ...     write output/xeen_classic_pilot/check/<map>/tour.yml
  (CHECK_ROOT=<asset root> and CHECK_OUT=<folder>: shoot from a scratch root into another folder)
  python3 check_maps.py shoot x2 x3 ...    run each tour (tools/run_game.sh --isolated, minimised, through heavy.sh 6)
  python3 check_maps.py sheet x2 x3 ...    output/xeen_classic_pilot/check/sheet.jpg (one row per map)
"""
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import yaml
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = Path(os.environ.get('CHECK_OUT') or ROOT / 'output/xeen_classic_pilot/check')
ASSETS = Path(os.environ.get('CHECK_ROOT') or ROOT / 'assets_dev')
OYMAP = ROOT / 'openyamm-studio/build-xeen/oymap'
KIT_WALLS = ('xvwall', 'xvswall', 'xvtwall')     # the house, stone and tower kits


def kit_doors(key):
    """(area, centre cell, door side cell) of the kit buildings with a known door wall, largest first."""
    sketch = yaml.safe_load((ROOT / f'devdocs/xeen/briefs/{key}/L4/sketch.yml').read_text())
    found = []
    for district in sketch.get('districts') or []:
        for plot in district.get('plots') or []:
            door = plot.get('door') if isinstance(plot.get('door'), dict) else None
            if not door or door.get('wall') not in ('n', 's', 'e', 'w') or plot.get('turn'):
                continue
            body = next((p for p in plot.get('parts') or [] if p.get('id') == door.get('part')), None)
            if not body or (body.get('textures') or {}).get('wall') not in KIT_WALLS or 'size' not in body:
                continue
            ax, ay = body.get('at', [0, 0])
            w, h = body['size']
            x0, y0 = plot['at'][0] + ax / 512, plot['at'][1] + ay / 512
            x1, y1 = x0 + w / 512, y0 + h / 512
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            face = {'s': (cx, y1), 'n': (cx, y0), 'e': (x1, cy), 'w': (x0, cy)}[door['wall']]
            out = {'s': (0, 1), 'n': (0, -1), 'e': (1, 0), 'w': (-1, 0)}[door['wall']]
            found.append((w * h, (cx, cy), face, out, plot.get('title') or plot.get('building')))
    return sorted(found, key=lambda f: -f[0])


def cmd_tour(keys):
    for key in keys:
        stem = f'xeen_{key}'
        folder = OUT / key
        folder.mkdir(parents=True, exist_ok=True)
        export = folder / 'export.json'
        subprocess.run([str(OYMAP), 'export', str(ASSETS / f'worlds/xeen/maps/{stem}.odm'), '--world',
                        'xeen', '--assets', str(ASSETS), '--out', str(export)], check=True,
                       stdout=subprocess.DEVNULL)
        heights = json.loads(export.read_text())['map']['terrain']['height_map']

        def ground(x, y):
            return heights[int(min(127, max(0, round(y)))) * 128 + int(min(127, max(0, round(x))))] * 32

        doors = kit_doors(key)
        shots = []
        for index, (_, centre, face, out, title) in enumerate(doors[:3]):
            cam = (face[0] + out[0] * 2.2, face[1] + out[1] * 2.2)
            shots.append((f'door_{index + 1}', cam, face, 140, f'{title}, the door front'))
            # Three-quarter, from the door side and one end: the roof's edges over the gable and the eaves.
            side = (out[1], -out[0])
            cam = (centre[0] + (out[0] + side[0]) * 2.6, centre[1] + (out[1] + side[1]) * 2.6)
            shots.append((f'corner_{index + 1}', cam, centre, 220, f'{title}, three-quarter'))
        if doors:
            xs = [d[1][0] for d in doors]
            ys = [d[1][1] for d in doors]
            mid = (sum(xs) / len(xs), sum(ys) / len(ys))
            shots.append(('over_houses', (mid[0], mid[1] + 7), mid, 900, 'Over the kit houses'))
        lines = ['output_dir: "%s"' % (folder / 'shots'), 'exit: true', 'settle_seconds: 3.0', 'shots:']
        captions = {}
        for index, (name, cam, look, height, caption) in enumerate(shots):
            x, y = (cam[0] - 64) * 512, (64 - cam[1]) * 512
            z = ground(*cam) + height
            dx, dy = (look[0] - cam[0]) * 512, (cam[1] - look[1]) * 512
            yaw = math.atan2(dy, dx)
            pitch = math.atan2(ground(*look) + 150 - z, math.hypot(dx, dy))
            lines.append('  - {name: %s, position: [%d, %d, %d], yaw: %.4f, pitch: %.4f, commands: ["render hud off"]}'
                         % (name, x, y, z, yaw, pitch))
            captions['%02d-%s.png' % (index + 1, name)] = caption
        (folder / 'tour.yml').write_text('\n'.join(lines) + '\n')
        (folder / 'captions.yml').write_text(yaml.safe_dump(captions, sort_keys=False, allow_unicode=True))
        print(key, len(shots), 'shots,', len(doors), 'kit houses with a door wall')


def cmd_shoot(keys):
    env = dict(os.environ, SDL_AUDIODRIVER='dummy', OPENYAMM_START_MINIMIZED='1')
    for key in keys:
        (OUT / key / 'shots').mkdir(parents=True, exist_ok=True)
        subprocess.run([str(ROOT / 'tools/heavy.sh'), '6', str(ROOT / 'tools/run_game.sh'), '--isolated',
                        f'xclassic_check_{key}', '--world', 'xeen', '--map', f'xeen_{key}.odm', '--assets', str(ASSETS),
                        '--warmup', '5',
                        '--seconds', '90', '--set', f'debug.screenshot_tour_path={OUT / key / "tour.yml"}'],
                       env=env, cwd=ROOT, check=True)


def cmd_sheet(keys):
    w, h = 480, 270
    rows = []
    for key in keys:
        shots = sorted((OUT / key / 'shots').glob('*.png'))
        rows.append(shots[:6])
    sheet = Image.new('RGB', (w * 6, h * len(rows)))
    for r, shots in enumerate(rows):
        for c, path in enumerate(shots):
            sheet.paste(Image.open(path).convert('RGB').resize((w, h)), (c * w, r * h))
    sheet.save(OUT / 'sheet.jpg', quality=85)
    print(OUT / 'sheet.jpg')


if __name__ == '__main__':
    {'tour': cmd_tour, 'shoot': cmd_shoot, 'sheet': cmd_sheet}[sys.argv[1]](sys.argv[2:])
