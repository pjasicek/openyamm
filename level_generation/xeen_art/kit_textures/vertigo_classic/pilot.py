#!/usr/bin/env python3
"""The Vertigo classic pilot in scratch: X1 built with the classic kits, captured beside today's X1, compared on a page.

Nothing here touches assets_dev or the X1 project: each variant is a copy of devdocs/xeen/briefs/x1/L4 whose
half-timbered houses (parts of the MM7 kits plaster, timber, grey, rich and poor) take the variant's textures,
built and installed into a hard-link copy of assets_dev with the variant's textures installed (xtex.py install).

  python3 pilot.py roots            make output/xeen_classic_pilot/root_<v> (cp -al assets_dev)
  python3 pilot.py textures         install the variants' textures into their roots (worlds/xeen)
  python3 pilot.py build [v...]     copy the project, swap the kits, oymap build, install into the root
  python3 pilot.py tour             write the camera tour (Vertigo's town shots of x1/gen_tour.py, today's heights)
  python3 pilot.py shoot [v...]     run the tour in the game: base (assets_dev), a, b
  python3 pilot.py page             write output/xeen_classic_pilot/page/ (index.html, the shots, the textures)

Variants: a (the original's colours) and b (weathered, beside MM7); each with shingle roofs and thatch on the poor
kit's houses (as the original's straw hut).
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
ROOT = HERE.parents[3]
OUT = ROOT / 'output/xeen_classic_pilot'
OYMAP = ROOT / 'openyamm-studio/build-xeen/oymap'
PROJECT = ROOT / 'devdocs/xeen/briefs/x1/L4'
VARIANTS = ('a', 'b', 's')       # s: the chosen A kit composed for seamless bays (compose.py), names xv*
SHOWN = ('base', 'a', 's')        # what the page compares (B was set aside on 2026-11-24)
CLASSIC_KITS = {'plaster', 'timber', 'grey', 'rich', 'poor'}
HH_ROOFS = {'hhm1rf', 'hhm2rf', 'hhm3rf', 'hhp2rf', '7hhr1rf'}
DEFAULT_KIT = 'plaster'           # the first MM7 kit: what a part that names none gets


def kit_textures(v):
    if v == 's':
        # The composed kit: the gable is the wall itself (its posts and beams continue up the gable end).
        return {'wall': 'xvwall', 'window': 'xvwin', 'door': 'xvdoor', 'post_left': 'xvcornl',
                'post_right': 'xvcornr', 'trim': 'xvbeam', 'gable': 'xvwall', 'ridge': 'xvridge'}
    p = 'xv' + v
    return {'wall': p + 'wall', 'window': p + 'win', 'door': p + 'door', 'post_left': p + 'corn',
            'post_right': p + 'cornr', 'trim': p + 'beam', 'gable': p + 'gable', 'ridge': p + 'ridge'}


def roof_name(v, thatch):
    return ('xv' if v == 's' else 'xv' + v) + ('that' if thatch else 'shgl')


def names(v):
    if v == 's':
        return ['xvwall', 'xvwin', 'xvdoor', 'xvcornl', 'xvcornr', 'xvbeam', 'xvridge', 'xvshgl', 'xvthat']
    p = 'xv' + v
    return [p + n for n in ('wall', 'win', 'door', 'corn', 'cornr', 'shgl', 'that', 'beam', 'gable', 'ridge')]


def run(command, **kwargs):
    print('+', ' '.join(str(c) for c in command), flush=True)
    return subprocess.run([str(c) for c in command], check=True, **kwargs)


def root(v):
    return OUT / f'root_{v}'


def cmd_roots(_):
    OUT.mkdir(parents=True, exist_ok=True)
    for v in VARIANTS:
        if not root(v).exists():
            run(['cp', '-al', ROOT / 'assets_dev', root(v)])


def cmd_textures(_):
    for v in VARIANTS:
        run([sys.executable, ROOT / 'level_generation/textures_xeen/xtex.py', '--project', HERE, 'install',
             '--root', root(v), '--world', 'xeen', *names(v)])


def swap(sketch, v):
    """The classic kit's textures on every part of an MM7 half-timber kit; counts of what changed."""
    textures = kit_textures(v)
    counts = {'parts': 0, 'roofs': 0, 'thatch': 0}
    # The houses are district plots (most of them) and building structures (stalls, sheds, the warehouse ...).
    buildings = [s for s in sketch.get('structures') or [] if s.get('kind') == 'building']
    for district in sketch.get('districts') or []:
        buildings += district.get('plots') or []
    for structure in buildings:
        for part in structure.get('parts') or []:
            kit = part.get('kit') or structure.get('kit') or DEFAULT_KIT
            if kit not in CLASSIC_KITS:
                continue
            own = dict(part.get('textures') or {})
            for role, name in textures.items():
                # A part's own wall or door that is not of its kit (a stone base, a special door) stays.
                if role in own and role in ('wall', 'door', 'window'):
                    continue
                own[role] = name
            roof = own.get('roof') or (structure.get('textures') or {}).get('roof')
            if roof is None or roof in HH_ROOFS:
                thatch = kit == 'poor' or roof == 'hhp2rf'
                own['roof'] = roof_name(v, thatch)
                counts['thatch' if thatch else 'roofs'] += 1
            part['textures'] = own
            counts['parts'] += 1
    return counts


def cmd_build(args):
    for v in args or VARIANTS:
        project = OUT / f'x1_{v}' / 'L4'
        if project.exists():
            shutil.rmtree(project)
        shutil.copytree(PROJECT, project)
        sketch = yaml.safe_load((project / 'sketch.yml').read_text())
        counts = swap(sketch, v)
        (project / 'sketch.yml').write_text(yaml.safe_dump(sketch, sort_keys=False, width=120, allow_unicode=True))
        print(v, counts)
        build = OUT / f'build_{v}'
        run([ROOT / 'tools/heavy.sh', 8, OYMAP, 'build', project, '--assets', root(v), '--out', build],
            stdout=open(OUT / f'build_{v}.log', 'w'), stderr=subprocess.STDOUT)
        run([OYMAP, 'install', project, '--build', build, '--root', root(v)], stdout=subprocess.DEVNULL)
        restamp(root(v))


def fnv1a(data):
    value = 14695981039346656037
    for byte in data:
        value = ((value ^ byte) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return value


def restamp(asset_root):
    """Scratch roots only: the variant's ODM differs from today's in face texture names alone (same faces, same
    order), so today's lighting bake fits it; its header's geometry hash (FNV-1a of the ODM bytes, offset 16) is
    set to the new ODM's. A real install re-bakes (tools/lighting/baked_outdoors). Written as a new file renamed
    into place: the root's .lighting is a hard link into assets_dev."""
    maps = asset_root / 'worlds/xeen/maps'
    lighting = bytearray((maps / 'xeen_x1.lighting').read_bytes())
    lighting[16:24] = fnv1a((maps / 'xeen_x1.odm').read_bytes()).to_bytes(8, 'little')
    temporary = maps / '.xeen_x1.lighting.tmp'
    temporary.write_bytes(bytes(lighting))
    temporary.replace(maps / 'xeen_x1.lighting')
    print('restamped', maps / 'xeen_x1.lighting')


# Vertigo's town shots of level_generation/projects/xeen/x1/gen_tour.py (camera cell, look-at cell, height, caption),
# and a few closer looks at the houses.
SHOTS = [
    ('square_start', (54, 47.6), (54, 40), 170, 'Arrival in Vertigo square: the north street, the town hall, shops'),
    ('square_south', (54, 45), (54, 52), 170, 'From the square south: the south gate, the bridge, the guild row'),
    ('main_street_west', (60, 44), (43, 44), 170, 'Main street looking west to the west gate'),
    ('main_street_east', (44, 44), (62, 44), 170, 'Main street looking east to the east gate'),
    ('north_row', (51, 43.5), (47, 40.5), 170, 'North row: armoury, ironworks, town hall'),
    ('temple', (55, 43.5), (58, 47), 170, 'The temple and its neighbours'),
    ('tavern_inn', (47, 43.4), (45, 46.5), 170, "Lady Geraldine's Tavern and the Adventurer's Inn"),
    ('north_row_close', (49.5, 43.2), (48.6, 41.6), 150, 'Close to a house front on the north row'),
    ('tavern_close', (46.4, 44.6), (45.8, 46.2), 150, 'Close to the tavern front'),
    ('roofs', (54, 50), (50, 42), 900, 'Over the roofs of the old town'),
    ('wall_aerial', (52, 64), (52, 44), 2600, 'Vertigo from the air'),
    ('joes_yard', (58, 59), (61.5, 58.3), 170, "Joe's yard on the south bank"),
    ('guild_row', (50, 54.4), (44, 57), 170, 'The guild row on the south bank'),
    # Straight at a door (the door wall's middle, 1.8 cells out): the door bay against the wall bays beside it.
    ('door_hexes', (53.25, 45.21), (53.25, 43.41), 140, "Gilbert's Hexes, the door front"),
    ('door_tavern', (55.25, 44.99), (55.25, 43.19), 140, "Lady Geraldine's Tavern, the door front"),
    ('door_inn', (43.75, 43.29), (43.75, 45.09), 140, "The Adventurer's Inn, the door front"),
    ('door_cobb', (61.0, 44.83), (61.0, 46.62), 140, 'Cobb Residence, the door front'),
    ('door_fenwick', (44.79, 48.0), (46.59, 48.0), 140, 'Fenwick Residence, the door front'),
]


def cmd_tour(_):
    export = OUT / 'export_x1.json'
    if not export.exists():
        run([OYMAP, 'export', ROOT / 'assets_dev/worlds/xeen/maps/xeen_x1.odm', '--world', 'xeen', '--assets',
             ROOT / 'assets_dev', '--out', export])
    heights = json.loads(export.read_text())['map']['terrain']['height_map']

    def ground(x, y):
        return heights[int(min(127, max(0, round(y)))) * 128 + int(min(127, max(0, round(x))))] * 32

    for label in ('base',) + VARIANTS:
        shots = OUT / 'shots' / label
        shots.mkdir(parents=True, exist_ok=True)
        lines = ['output_dir: "%s"' % shots, 'exit: true', 'settle_seconds: 3.0', 'shots:']
        for name, cam, look, height, _ in SHOTS:
            x, y = (cam[0] - 64) * 512, (64 - cam[1]) * 512
            z = ground(*cam) + height
            dx, dy = (look[0] - cam[0]) * 512, (cam[1] - look[1]) * 512
            yaw = math.atan2(dy, dx)
            pitch = math.atan2(ground(*look) + 150 - z, math.hypot(dx, dy))
            lines.append('  - {name: %s, position: [%d, %d, %d], yaw: %.4f, pitch: %.4f, commands: ["render hud off"]}'
                         % (name, x, y, z, yaw, pitch))
        (OUT / f'tour_{label}.yml').write_text('\n'.join(lines) + '\n')
    print(len(SHOTS), 'shots')


def cmd_shoot(args):
    env = dict(os.environ, SDL_AUDIODRIVER='dummy', OPENYAMM_START_MINIMIZED='1')
    for label in args or SHOWN:
        assets = ROOT / 'assets_dev' if label == 'base' else root(label)
        run([ROOT / 'tools/heavy.sh', 6, ROOT / 'tools/run_game.sh', '--isolated', f'xclassic_{label}',
             '--world', 'xeen', '--map', 'xeen_x1.odm', '--assets', assets, '--warmup', 5, '--seconds', 150,
             '--set', f'debug.screenshot_tour_path={OUT / f"tour_{label}.yml"}'], env=env, cwd=ROOT)


def cmd_page(_):
    page = OUT / 'page'
    (page / 'shots').mkdir(parents=True, exist_ok=True)
    (page / 'tex').mkdir(parents=True, exist_ok=True)
    shots = []
    for index, (name, _, _, _, caption) in enumerate(SHOTS):
        file = '%02d-%s.png' % (index + 1, name)
        row = {'name': name, 'caption': caption, 'images': {}}
        for label in SHOWN:
            source = OUT / 'shots' / label / file
            if source.exists():
                target = page / 'shots' / f'{label}_{name}.jpg'
                Image.open(source).convert('RGB').save(target, quality=88)
                row['images'][label] = f'shots/{label}_{name}.jpg'
        shots.append(row)
    textures = {}
    for v in ('a', 's'):
        textures[v] = []
        for name in names(v):
            source = HERE / 'finished' / f'{name}.png'
            if source.exists():
                image = Image.open(source).convert('RGB')
                image.thumbnail((512, 512), Image.LANCZOS)
                image.save(page / 'tex' / f'{name}.jpg', quality=90)
                textures[v].append(name)
    facade = Image.open(HERE / 'sheets' / 'compose_facade.png').convert('RGB')
    facade.save(page / 'tex' / 'facade.jpg', quality=90)
    natives = []
    for name in ('native_wall', 'native_door', 'native_torch', 'native_hut', 'native_well'):
        shutil.copy(HERE / 'pics' / f'{name}.png', page / 'tex' / f'{name}.png')
        natives.append(name)
    # The installed maps (check_maps.py): door fronts and a view over the houses, per Cloudside map.
    installed = []
    titles = {'doors': 'Double doors: one wing per leaf (D6 Necropolis, D4, D1)',
              'stables': 'Stables (installed on X1, X2, D1; X6 the same way)',
              'stables2': 'X4 stables (installed)', 'square': 'X1 Vertigo square (as installed)',
              'townhall': "X1 Vertigo Town Hall (the mayor's)",
              'x1': 'X1 Vertigo', 'x2': 'X2 Rivercity', 'x3': 'X3 Lifeforce Lagoon', 'x4': 'X4 Asp and Burlock',
              'x5': 'X5 Winterkill', 'x6': 'X6 Desert of the Sphinx', 'halon': "X5 Halon's Workshop",
              'd1': 'D1 Castleview', 'd3': 'D3 Sandcaster', 'd4': 'D4 Lakeside', 'd6': 'D6 Necropolis'}
    (page / 'installed').mkdir(exist_ok=True)
    for key, title in titles.items():
        folder = OUT / 'check' / key
        captions = yaml.safe_load((folder / 'captions.yml').read_text()) if (folder / 'captions.yml').exists() else {}
        for source in sorted((folder / 'shots').glob('*.png')) if (folder / 'shots').exists() else []:
            if 'over_houses' in source.name:
                continue     # the cameras over the houses missed on some maps
            target = page / 'installed' / f'{key}_{source.stem}.jpg'
            Image.open(source).convert('RGB').save(target, quality=86)
            caption = captions.get(source.name) or source.stem.split('-', 1)[-1].replace('halon_', '').replace(
                'front', 'from the south, as in the user\'s screenshot').replace('quarter', 'three-quarter')
            installed.append({'map': title, 'src': f'installed/{target.name}', 'caption': caption})
    # The stone kit's pilot (stone_pilot.py page writes stone.json and page/stone/).
    stone = json.loads((OUT / 'stone.json').read_text()) if (OUT / 'stone.json').exists() else None
    data = json.dumps({'shots': shots, 'textures': textures, 'natives': natives, 'installed': installed,
                       'stone': stone})
    (page / 'index.html').write_text((HERE / 'page_template.html').read_text().replace('/*DATA*/', data))
    print('page:', page / 'index.html', len(shots), 'shots')


def main():
    command, args = sys.argv[1], sys.argv[2:]
    {'roots': cmd_roots, 'textures': cmd_textures, 'build': cmd_build, 'tour': cmd_tour, 'shoot': cmd_shoot,
     'page': cmd_page}[command](args)


if __name__ == '__main__':
    main()
