#!/usr/bin/env python3
"""The classic stone kit's pilot on Vertigo (2026-11-24): X1's stone buildings (MM7's `stone` kit: the bank, the
temple, the Fire Guild, a farmhouse) in Clouds of Xeen's castle walls, captured beside today's X1, in scratch.

  python3 stone_pilot.py build     root_t (cp -al assets_dev), the stone textures installed in it, X1 built with the
                                   stone kit on those buildings and installed, today's bake re-stamped (only texture
                                   names change: pilot.restamp)
  python3 stone_pilot.py shoot     the tour in today's game (assets_dev) and in root_t
  python3 stone_pilot.py page      output/xeen_classic_pilot/page/stone/ and stone.json for pilot.py page
"""
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pilot  # noqa: E402

ROOT = HERE.parents[3]
OUT = ROOT / 'output/xeen_classic_pilot'
ROOT_T = OUT / 'root_t'
NAMES = ['xvswall', 'xvswin', 'xvsdoor', 'xvscornl', 'xvscornr']
STONE = {'wall': 'xvswall', 'window': 'xvswin', 'door': 'xvsdoor', 'post_left': 'xvscornl', 'post_right': 'xvscornr',
         'trim': 'xvbeam', 'gable': 'xvswall', 'ridge': 'xvridge'}
MM7_STONE_ROOFS = {'7hhr1rf', 'hhm1rf', 'hhm2rf', 'hhm3rf', 'hhp2rf'}


def stone_swap(sketch):
    """The stone kit on the parts of the district plots built of MM7's stone kit (not the out-of-town structures)."""
    count = 0
    for district in sketch.get('districts') or []:
        for plot in district.get('plots') or []:
            for part in plot.get('parts') or []:
                if (part.get('kit') or plot.get('kit')) != 'stone':
                    continue
                own = dict(part.get('textures') or {})
                if own.get('wall'):
                    continue
                own.update(STONE)
                if own.get('roof') in MM7_STONE_ROOFS or 'roof' not in own:
                    own['roof'] = 'xvshgl'
                part['textures'] = own
                count += 1
    return count


def cmd_build():
    if not ROOT_T.exists():
        pilot.run(['cp', '-al', ROOT / 'assets_dev', ROOT_T])
    pilot.run([sys.executable, ROOT / 'level_generation/textures_xeen/xtex.py', '--project', HERE, 'install', '--root',
               ROOT_T, '--world', 'xeen', *NAMES])
    project = OUT / 'x1_t' / 'L4'
    if project.exists():
        shutil.rmtree(project)
    shutil.copytree(pilot.PROJECT, project)
    sketch = yaml.safe_load((project / 'sketch.yml').read_text())
    print('stone parts:', stone_swap(sketch))
    (project / 'sketch.yml').write_text(yaml.safe_dump(sketch, sort_keys=False, width=120, allow_unicode=True))
    build = OUT / 'build_t'
    pilot.run([ROOT / 'tools/heavy.sh', 8, pilot.OYMAP, 'build', project, '--assets', ROOT_T, '--out', build],
              stdout=open(OUT / 'build_t.log', 'w'), stderr=subprocess.STDOUT)
    for name in ('xeen_x1.odm', 'xeen_x1.scene.yml', 'xeen_x1.studio.yml', 'xeen_x1.lighting', 'xeen_x1.bake.json'):
        target = ROOT_T / 'worlds/xeen/maps' / name
        if target.exists():
            target.unlink()     # unlinked first: never written through a hard link into assets_dev
    (ROOT_T / 'worlds/xeen/events/maps/xeen_x1.lua').unlink()
    pilot.run([pilot.OYMAP, 'install', project, '--build', build, '--root', ROOT_T], stdout=subprocess.DEVNULL)
    for name in ('xeen_x1.lighting', 'xeen_x1.bake.json'):
        shutil.copyfile(ROOT / 'assets_dev/worlds/xeen/maps' / name, ROOT_T / 'worlds/xeen/maps' / name)
    pilot.restamp(ROOT_T)


def stone_shots():
    """Door fronts and three-quarter views of the stone plots, and two of the town views."""
    sketch = yaml.safe_load((pilot.PROJECT / 'sketch.yml').read_text())
    shots = []
    for district in sketch.get('districts') or []:
        for plot in district.get('plots') or []:
            door = plot.get('door') if isinstance(plot.get('door'), dict) else None
            if plot.get('kit') != 'stone' or not door or door.get('wall') not in ('n', 's', 'e', 'w'):
                continue
            body = next((p for p in plot['parts'] if p.get('id') == door.get('part')), None)
            if not body or 'size' not in body:
                continue
            ax, ay = body.get('at', [0, 0])
            w, h = body['size']
            x0, y0 = plot['at'][0] + ax / 512, plot['at'][1] + ay / 512
            x1, y1 = x0 + w / 512, y0 + h / 512
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            face = {'s': (cx, y1), 'n': (cx, y0), 'e': (x1, cy), 'w': (x0, cy)}[door['wall']]
            out = {'s': (0, 1), 'n': (0, -1), 'e': (1, 0), 'w': (-1, 0)}[door['wall']]
            title = plot.get('title') or 'Stone farmhouse'
            key = (plot.get('building') or 'house').split(':')[-1]
            shots.append((f'{key}_door', (face[0] + out[0] * 2.4, face[1] + out[1] * 2.4), face, 150,
                          f'{title}, the door front'))
            side = (out[1], -out[0])
            shots.append((f'{key}_quarter', (cx + (out[0] + side[0]) * 3.2, cy + (out[1] + side[1]) * 3.2),
                          (cx, cy), 260, f'{title}, three-quarter'))
    shots += [s for s in pilot.SHOTS if s[0] in ('temple', 'guild_row')]
    return shots


def cmd_shoot():
    heights = json.loads((OUT / 'export_x1.json').read_text())['map']['terrain']['height_map']

    def ground(x, y):
        return heights[int(min(127, max(0, round(y)))) * 128 + int(min(127, max(0, round(x))))] * 32

    shots = stone_shots()
    env = dict(os.environ, SDL_AUDIODRIVER='dummy', OPENYAMM_START_MINIMIZED='1')
    for label, assets in (('stone_base', ROOT / 'assets_dev'), ('stone_t', ROOT_T)):
        folder = OUT / 'shots' / label
        folder.mkdir(parents=True, exist_ok=True)
        lines = ['output_dir: "%s"' % folder, 'exit: true', 'settle_seconds: 3.0', 'shots:']
        for name, cam, look, height, _ in shots:
            x, y = (cam[0] - 64) * 512, (64 - cam[1]) * 512
            z = ground(*cam) + height
            dx, dy = (look[0] - cam[0]) * 512, (cam[1] - look[1]) * 512
            pitch = math.atan2(ground(*look) + 200 - z, math.hypot(dx, dy))
            lines.append('  - {name: %s, position: [%d, %d, %d], yaw: %.4f, pitch: %.4f, commands: ["render hud off"]}'
                         % (name, x, y, z, math.atan2(dy, dx), pitch))
        (OUT / f'tour_{label}.yml').write_text('\n'.join(lines) + '\n')
        pilot.run([ROOT / 'tools/heavy.sh', 6, ROOT / 'tools/run_game.sh', '--isolated', f'xclassic_{label}',
                   '--world', 'xeen', '--map', 'xeen_x1.odm', '--assets', assets, '--warmup', 5, '--seconds', 120,
                   '--set', f'debug.screenshot_tour_path={OUT / f"tour_{label}.yml"}'], env=env, cwd=ROOT)


def cmd_page():
    page = OUT / 'page' / 'stone'
    page.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, (name, _, _, _, caption) in enumerate(stone_shots()):
        file = '%02d-%s.png' % (index + 1, name)
        row = {'caption': caption}
        for label, key in (('stone_base', 'before'), ('stone_t', 'after')):
            source = OUT / 'shots' / label / file
            if source.exists():
                target = page / f'{key}_{name}.jpg'
                Image.open(source).convert('RGB').save(target, quality=86)
                row[key] = f'stone/{target.name}'
        rows.append(row)
    Image.open(HERE / 'sheets' / 'stone_facade.png').convert('RGB').save(page / 'facade.jpg', quality=90)
    for name in ('native_cwall', 'native_cdoor'):
        shutil.copyfile(HERE / 'pics' / f'{name}.png', page / f'{name}.png')
    (OUT / 'stone.json').write_text(json.dumps({'rows': rows, 'facade': 'stone/facade.jpg',
                                                'natives': ['stone/native_cwall.png', 'stone/native_cdoor.png']}))
    print(len(rows), 'stone rows')


if __name__ == '__main__':
    {'build': cmd_build, 'shoot': cmd_shoot, 'page': cmd_page}[sys.argv[1]]()
