"""Resumable MM6 restoration inventory and native archer preparation. No AI calls."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw
import yaml

HERE = Path(__file__).resolve().parent
CREATURES = HERE.parent
REPO = CREATURES.parents[1]
ASSETS = REPO / 'assets_dev'
sys.path.insert(0, str(CREATURES.parent / 'sprites'))
sys.path.insert(0, str(CREATURES))
from inventory import frame_images
from mm6_sampling_audit import audit as audit_sampling

ACTIONS = ['standing', 'walk', 'attack', 'attack2', 'hit', 'death', 'corpse', 'fidget']


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_native_tables():
    descriptors_path = ASSETS / 'engine/data_tables/monster_descriptors.txt'
    descriptors = {int(c[0]): c for line in descriptors_path.read_text().splitlines()
                   for c in [line.split('\t')] if c[0].isdigit()}
    groups = {}
    paths = [ASSETS / 'engine/rendering/sprite_frame_data_common.yml']
    paths.extend(sorted((ASSETS / 'engine/rendering/sprite_frames/monsters').glob('*.yml')))
    for path in paths:
        for group in yaml.load(path.read_text(), Loader=yaml.CSafeLoader)['sprites']:
            groups[group['sprite_name'].lower()] = group
    return descriptors, groups


def ledger():
    inventory = json.loads((CREATURES / 'remaining_inventory.json').read_text())
    previous = json.loads((HERE / 'progress.json').read_text()) if (HERE / 'progress.json').exists() else {}
    old = {r['descriptor_id']: r for r in previous.get('families', [])}
    rows = []
    for family in inventory['families']:
        if family['world'] != 'mm6':
            continue
        first = family['descriptors'][0]['id']
        row = old.get(first, dict(descriptor_id=first, label=family['label'], status='pending',
                                 stage='native inventory', package=None, notes=[]))
        row['referenced_images'] = len(family['images'])
        candidates = family.get('package_candidates', [])
        if candidates and any('insufficient generated detail' in issue for issue in candidates[0]['issues']):
            path = REPO / candidates[0]['path']
            sampling = audit_sampling(path.parent)
            row.update(package=candidates[0]['path'], status='insufficient',
                       stage='below 2x generated detail; redo inventory prepared',
                       generated_detail_status='insufficient',
                       insufficient_frames=[f['frame'] for f in sampling['frames'] if f['status']=='below_2x'],
                       redo_inventory='level_generation/creatures/mm6_remaining/redo_2x/inventory.json')
        if family['completed_package']:
            path = REPO / family['completed_package']
            manifest = json.loads(path.read_text())
            missing = sorted(set(family['images']) - set(manifest['frames']))
            validation = json.loads((path.parent / 'validation.json').read_text())
            failures = [key for key, value in validation.items() if value is False]
            row.update(package=family['completed_package'], missing_referenced_frames=missing,
                       generated_detail_status='sufficient', insufficient_frames=[])
            reviewed = row['status'] == 'validated' or validation.get('visual_review_complete', False)
            row['status'] = 'validated' if not missing and not failures and reviewed else 'partial'
            row['stage'] = 'reused accepted package; coverage and recorded validation checked'
            row['prior_validation_failures'] = failures
        rows.append(row)
    installation_path = HERE / 'installation.json'
    installation = json.loads(installation_path.read_text()) if installation_path.exists() else {}
    installed = installation.get('installed', False)
    if installed:
        targets = {p['descriptor_id']: p['package'] for p in installation['packages']}
        for row in rows:
            row['installed_package'] = 'assets_dev/engine/sprites_new/' + targets[row['descriptor_id']]
    installation_text = ('All MM6 families installed in assets_dev; original BMPs preserved; see installation.json'
                         if installed else 'staged only; native assets and gameplay unchanged')
    result = dict(schema_version=1, scope='All remaining MM6 native actor families; preserve existing accepted work',
                  started='2026-09-11', statuses=['pending', 'partial', 'validated', 'blocked', 'insufficient'],
                  installation=installation_text, families=rows,
                  summary={state: sum(r['status'] == state for r in rows)
                           for state in ['pending', 'partial', 'validated', 'blocked', 'insufficient']})
    write(HERE / 'progress.json', result)
    lines = ['# MM6 remaining creature restoration', '',
             'Resumable ledger: [progress.json](progress.json). Status is per family, not per generated sheet.',
             'Current blockers and exact resume steps: [HANDOFF.md](HANDOFF.md).',
             installation_text + '. Reuse all validated MM6 packages.', '',
             '| ID | Family | Status | Stage |', '| --- | --- | --- | --- |']
    lines.extend(f"| {r['descriptor_id']} | {r['label']} | {r['status']} | {r['stage']} |" for r in rows)
    lines += ['', 'Regenerate the native inventory with `python3 level_generation/creatures/inventory_remaining.py`,',
              'then refresh this ledger with `python3 level_generation/creatures/mm6_remaining/prepare.py ledger`.',
              'Only mark new work validated after complete native coverage, variant/animation and visual edge checks.',
              'Preserve raw generations and exact prompts; resume from selected successful sheets.']
    (HERE / 'README.md').write_text('\n'.join(lines) + '\n')
    return result


def archer():
    root = CREATURES / 'mm6_arc1'
    for directory in ['native', 'references', 'prompts', 'raw', 'review']:
        (root / directory).mkdir(parents=True, exist_ok=True)
    descriptors, groups = load_native_tables()
    variants, used = {}, set()
    for mid in [475, 476, 477]:
        d = descriptors[mid]
        actions = {action: groups[name.lower()] for action, name in zip(ACTIONS, d[11:19])}
        palette = actions['standing']['frames'][0]['palette_id']
        variants[str(palette)] = dict(descriptor_id=mid, descriptor_label=d[1], actions=actions)
        used.update(n for g in actions.values() for f in g['frames'] for n in frame_images(f))
    sources, duplicates = {}, defaultdict(list)
    for path in sorted((ASSETS / 'engine/sprites').glob('arc1*.bmp')):
        im = Image.open(path)
        fingerprint = hashlib.sha256(str(im.size).encode() + im.tobytes()).hexdigest()
        sources[path.stem] = dict(path=str(path.relative_to(REPO)), sha256=sha(path), size=im.size,
                                  pixel_hash=fingerprint, referenced=path.stem in used)
        duplicates[fingerprint].append(path.stem)
    assert used <= sources.keys()
    aliases = {name: names[0] for names in duplicates.values() for name in names[1:]}
    canvas = [max(s['size'][0] for s in sources.values()), max(s['size'][1] for s in sources.values())]
    inv = dict(variants=variants, sources=sources, pixel_aliases=aliases,
               unreferenced=sorted(sources.keys() - used), logical_canvas=canvas)
    write(root / 'inventory.json', {'arc1': inv})
    config = dict(family='arc1', title='MM6 Archer', inventory_file='inventory.json', base_palette=660,
                  matte='magenta', mask_kind='blue',
                  description='Adult red-haired female archer; blue puffed elbow sleeves, dark blue short trousers, '
                  'gold/brown leather pointed bodice, long reddish-brown boots, fair skin, golden wooden bow in '
                  'left hand, back quiver and arrows. Preserve native build, face, hand, bow and strap placement.',
                  regions='Blue sleeves and blue trouser panels only; protect skin, hair, bow, leather and quiver.',
                  variant_names={'660': 'Archer A / blue cloth', '661': 'Archer B / red cloth',
                                 '662': 'Archer C / green cloth'})
    write(root / 'config.json', config)
    colors = np.frombuffer((ASSETS / 'worlds/mm6/textures/pal660.act').read_bytes()[:768], np.uint8).reshape(256, 3)
    for name, s in sources.items():
        ix = np.array(Image.open(REPO / s['path']))
        im = Image.fromarray(np.dstack([colors[ix], (ix != 0).astype(np.uint8) * 255]))
        im.save(root / 'native' / (name + '.png'))
        s.update(native_offset=[0, 0], aligned_bounds=im.getbbox())
    batches, seen = {}, set()

    def add(key, names, view):
        names = list(dict.fromkeys(aliases.get(n, n) for n in names))
        names = [n for n in names if n not in seen]
        if not names:
            return
        assert len(names) <= 8
        seen.update(names)
        batches[key] = dict(frames=names, view=view)

    actions = variants['660']['actions']
    add('standing', ['arc1sta' + str(v) for v in range(5)],
        'front, front-oblique, profile, rear-oblique, back')
    for view in range(5):
        add('walk_' + str(view), [f['texture_name'].lower() + str(view) for f in actions['walk']['frames']],
            ['front', 'front-oblique', 'profile', 'rear-oblique', 'back'][view])
    # fidget owns arc1fia0, which is also the first native attack frame.
    add('fidget', [f['texture_name'].lower() for f in actions['fidget']['frames']], 'front')
    for action in ['attack', 'hit', 'death']:
        names = [f['texture_name'].lower() for f in actions[action]['frames']]
        if action == 'attack':
            names += inv['unreferenced']
        if action == 'death':
            names += [f['texture_name'].lower() for f in actions['corpse']['frames']]
        add('death_corpse' if action == 'death' else action, names, 'front')
    assert seen | set(aliases) == set(sources)
    for key, batch in batches.items():
        columns = 3 if len(batch['frames']) > 4 else 2
        rows = (len(batch['frames']) + columns - 1) // columns
        cell = [canvas[0] * 2 + 64, canvas[1] * 2 + 64]
        sheet = Image.new('RGB', (columns * cell[0], rows * cell[1]), (255, 0, 255))
        for i, name in enumerate(batch['frames']):
            im = Image.open(root / 'native' / (name + '.png')).resize(
                (canvas[0] * 2, canvas[1] * 2), Image.Resampling.NEAREST)
            sheet.paste(im, (i % columns * cell[0] + 32, i // columns * cell[1] + 32), im)
        sheet.save(root / 'references' / (key + '.png'))
        batch.update(columns=columns, rows=rows, cell_size=cell)
        if key == 'standing':
            continue
        prompt = f'''Use case: style-transfer. Restore the exact Might and Magic VI archer animation sprites.
Input 1 is POSE AND LAYOUT authority: {columns} columns by {rows} rows, {len(batch['frames'])} occupied cells in row-major order. Action {key}; view {batch['view']}; frame order {', '.join(batch['frames'])}. Leave unused cells empty.
Input 2 is accepted enhanced standing artwork: IDENTITY AND MATERIAL authority only. Preserve the same red-haired adult female archer, face, build, blue sleeves/trouser panels, textured brown-gold leather bodice, reddish-brown tall boots, golden wooden bow and back quiver. Input 1 controls every distinct pose, limb position, bow angle and native camera view. Do not copy standing poses over the animation. Preserve the source's dark tonal weight and restrained baked lighting; clarify material detail without redesigning or adding accessories.
Keep common anatomical scale and native-relative placement. No per-cell zoom, recentering, omitted poses, swapped hands, cropped limbs or bow tips. Same grid and aspect ratio as input 1, with useful per-figure detail, generous empty gutters, no labels or grid lines.
Output background is perfectly flat pure magenta RGB(255,0,255), including gaps around the bowstring and limbs; no checkerboard, gradients, shadows, colored spill, text or watermark. Do not add background color to edges. This explicit flat-matte output replaces the failed transparency request of the earlier standing draft.
'''
        if key == 'death_corpse':
            prompt += 'Preserve each falling/prone pose and foreshortening without enlarging the fallen body. No added gore.\n'
        (root / 'prompts' / (key + '.txt')).write_text(prompt)
    palette_sources = {p: dict(path=f'assets_dev/worlds/mm6/textures/pal{p}.act',
                              sha256=sha(ASSETS / f'worlds/mm6/textures/pal{p}.act')) for p in variants}
    write(root / 'sources.json', dict(inv, base_palette=660, palette_sources=palette_sources,
                                    logical_pivot=[canvas[0] / 2, canvas[1]], anchor='bottom-center'))
    write(root / 'batches.json', batches)
    result = ledger()
    row = next(r for r in result['families'] if r['descriptor_id'] == 475)
    row.update(status='partial', stage='standing generated; action sheets pending',
               project='level_generation/creatures/mm6_arc1', source_files=len(sources),
               unique_source_images=len(duplicates), batches=len(batches),
               notes=['arc1atk is an unreferenced native attack pose retained offline.',
                      'arc1fia0 is shared by native attack and fidget; generate once, reuse with native timings.'])
    write(HERE / 'progress.json', result)
    ledger()
    print(f'Archer: {len(sources)} source files, {len(duplicates)} unique pixels, {len(batches)} batches')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'archer':
        archer()
    else:
        ledger()
