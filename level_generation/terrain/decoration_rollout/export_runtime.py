"""Build reviewed plant families and exact-tile map rules, then optionally install the staged files."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
TERRAIN = HERE.parent
ROOT = TERRAIN.parents[1]
RUNTIME = HERE / 'runtime'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def coverage(world, name):
    if world == 'mm6':
        old = TERRAIN / 'mm6_new_sorpigal_dirt_fidelity/transitions/masks/connected_v4' / (name + '.png')
        field = TERRAIN / 'mm6_remaining/transitions/fields' / (name + '.npz')
        if old.exists():
            return np.asarray(Image.open(old).convert('L').resize((256, 256), Image.Resampling.BOX)) / 255, old
    else:
        field = TERRAIN / world / 'transitions/fields' / (name + '.npz')
    if field.exists():
        array = np.load(field)['coverage']
        return np.clip(np.asarray(Image.fromarray(array).resize((256, 256), Image.Resampling.BOX)), 0, 1), field
    bases = {
        'mm6': '6grastyl 6dirttyl 6sandtyl snotyl crktyl swmtyl troptyl 6voltyl',
        'mm7': '7grastyl 7dirttyl 7dirt1 7dirt2 7sand 7snow 7swtyl 7swtylv1 7swtylv2 7wastetile',
        'mm8': 'grastyl dirttyl dirt1 dirt2 gdtyl gstyl voltyl rktyl rctyl plntyl plsatyl',
    }
    assert name in bases[world].split(), (world, name, 'missing authoritative material coverage')
    return np.ones((256, 256)), None


def tint(world, material, family):
    grass = {'mm6': [0.82, 0.98, 0.78], 'mm7': [0.72, 0.86, 0.62], 'mm8': [0.72, 0.85, 0.64]}
    if family in ('meadow', 'coastal_grass', 'woodland_grass', 'dry_meadow'):
        return grass[world]
    if family == 'marsh_reed':
        return [0.64, 0.78, 0.48]
    if family == 'tropical_low':
        return [0.78, 0.95, 0.58] if world == 'mm6' else [0.65, 0.80, 0.52]
    if family == 'dead_tuft':
        return [0.44, 0.45, 0.43] if material == 'grey_dirt' else [0.60, 0.58, 0.50]
    if family == 'dry_tuft':
        return [0.87, 0.78, 0.53]
    if family == 'snow_stone':
        return [0.45, 0.46, 0.48]
    if family == 'volcanic_stone':
        return [0.16, 0.16, 0.16]
    if family == 'grey_stone_chip':
        return [0.21, 0.22, 0.22]
    if material in ('red_dirt', 'sandstone'):
        return [0.61, 0.33, 0.18]
    if material == 'rock':
        return [0.40, 0.39, 0.36]
    return {'mm6': [0.65, 0.43, 0.29], 'mm7': [0.57, 0.37, 0.26], 'mm8': [0.41, 0.30, 0.21]}[world]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    catalogue = yaml.safe_load((HERE / 'catalogue.yml').read_text())
    tiles = json.loads((HERE / 'tiles.json').read_text())
    settings_hash = sha(ROOT / 'settings.ini')
    baseline = HERE / 'baseline'
    baseline.mkdir(exist_ok=True)
    original = ROOT / 'assets_dev/worlds/mm6/terrain_decorations'
    if not (baseline / 'oute3.yml').exists():
        shutil.copy2(original / 'oute3.yml', baseline / 'oute3.yml')
    # The original baseline remains authoritative for New Sorpigal's retained grass placements.
    allowed_materials = set(catalogue['allowed_materials'])
    atlas = Image.new('RGBA', (1024, 576))
    old = Image.open(original / 'grass_variants.png').convert('RGBA')
    for layer in range(4):
        cell = old.crop((layer % 2 * 256, layer // 2 * 192, layer % 2 * 256 + 256, layer // 2 * 192 + 192))
        atlas.paste(cell, (layer * 256, 0))
    for family_index, family in enumerate(['marsh_reed', 'tropical_low', 'dead_tuft']):
        for variant in range(2):
            layer = 4 + family_index * 2 + variant
            cell = Image.open(HERE / 'art/processed' / f'{family}_{variant}.png')
            atlas.paste(cell, (layer % 4 * 256, layer // 4 * 192))
    evidence = {'status': 'prepared_pending_runtime_review', 'sources': {}, 'maps': {}, 'masks': {}}
    masks_review = []
    excluded = {'water', 'lava', 'tar', 'shore', 'shore_dirt', 'shore_grey', 'roads', 'roads_dirt',
                'roads_grey', 'roads_plains', 'lava_dirt', 'lava_plains', 'tar_grey'}
    files = {}
    for world in ['mm6', 'mm7', 'mm8']:
        grass_scale = {'mm6': 2, 'mm7': 3, 'mm8': 3}[world]
        dest = RUNTIME / 'worlds' / world / 'terrain_decorations'
        (dest / 'masks').mkdir(parents=True, exist_ok=True)
        atlas.save(dest / 'plants_v2.png')
        library = {'version': 2, 'tuft_texture': 'plants_v2.png', 'tuft_atlas_grid': [4, 3], 'families': {}}
        for name, definition in catalogue['families'].items():
            family = {k: definition[k] for k in ['kind', 'candidates', 'width', 'height']}
            if family['kind'] == 'grass' and name != 'marsh_reed':
                family['width'] *= grass_scale
                family['height'] *= grass_scale
            elif name == 'marsh_reed' and world == 'mm7':
                family['width'] *= 1.5
                family['height'] *= 1.5
            family['tint'] = tint(world, '', name)
            if family['kind'] == 'grass':
                weights = definition.get('weights')
                if weights:
                    family['variants'] = [dict(layer=i, weight=w, width_scale=[1, 1, 1, .85][i],
                                                height_scale=[1, .9, 1.35, .85][i]) for i, w in enumerate(weights)]
                else:
                    layers = {'dry_tuft': [2, 3], 'marsh_reed': [4, 5],
                              'tropical_low': [6, 7, 0], 'dead_tuft': [8, 9]}[name]
                    family['variants'] = [dict(layer=i, weight=1) for i in layers]
                family['full_footprint'] = name in ('marsh_reed', 'tropical_low', 'dead_tuft', 'dry_tuft')
                family['wind_strength'] = {'marsh_reed': 1.2, 'tropical_low': .7, 'dead_tuft': .25}.get(name, 2.5)
            library['families'][name] = family
        (dest / 'families_v2.yml').write_text(yaml.safe_dump(library, sort_keys=False))

        def mask_file(name, field, purpose, source):
            filename = name + '_' + purpose + '.png'
            image = Image.fromarray(np.uint8(np.clip(np.rint(field * 255), 0, 255)))
            image = image.resize((128, 128), Image.Resampling.BOX)
            image.save(dest / 'masks' / filename)
            key = world + '/' + filename
            evidence['masks'][key] = {'mean_coverage': float(np.asarray(image).mean() / 255), 'purpose': purpose,
                                      'source': str(source.relative_to(ROOT)) if source else 'base material',
                                      'sha256': sha(dest / 'masks' / filename)}
            if source:
                evidence['sources'][str(source.relative_to(ROOT))] = sha(source)
            if purpose == 'swamp' and not any(w == world and n == name for w, n, _ in masks_review):
                masks_review.append((world, name, image.copy()))
            return 'masks/' + filename

        for record in [m for m in catalogue['maps'] if m['world'] == world]:
            map_id = Path(record['map']).stem
            if record['status'] == 'preserve_accepted_existing':
                accepted = yaml.safe_load((baseline / 'oute3.yml').read_text())
                accepted['rules'] = [rule for rule in accepted['rules']
                                     if rule['kind'] == 'grass' and
                                     tiles[world][rule['texture']]['material_family'] in allowed_materials]
                for rule in accepted['rules']:
                    rule['width'] *= grass_scale
                    rule['height'] *= grass_scale
                preserved = {'grass_variants.png', 'grass_tuft.png'}
                preserved.update(rule['mask'] for rule in accepted['rules'] if 'mask' in rule)
                for name in sorted(preserved):
                    target = dest / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(original / name, target)
                (dest / 'oute3.yml').write_text(yaml.safe_dump(accepted, sort_keys=False))
                evidence['maps'][world + '/' + map_id] = {'status': 'preserved_grass',
                                                         'rules': len(accepted['rules'])}
                continue
            if record['status'].startswith('intentionally_disabled'):
                config = dict(version=2, enabled=False, reason=record['reason'])
            elif not record['settings']:
                config = dict(version=2, enabled=False,
                              reason='Only grass, tropical and swamp terrain receive decorations.')
            else:
                config = {key: catalogue['defaults'][key] for key in ['minimum_normal_z', 'density_variation',
                          'patch_size', 'tall_grass_chance', 'tall_grass_scale']}
                # The grass range comes from the engine's level-of-detail defaults (GRASS_LOD.md).
                config.update(version=2, families_file='families_v2.yml', seed=record['seed'], rules=[])
                selections = {s['material']: s for s in record['settings']}
                for name, tile in sorted(tiles[world].items()):
                    if map_id not in tile['map_cells'] or tile['material_family'] in excluded:
                        continue
                    material = tile['material_family']
                    field, source = coverage(world, name)
                    backgrounds = {'plains_sand': 'plains', 'grey_stone': 'grey_dirt'}
                    background = backgrounds.get(material, 'dirt')
                    layers = [(material, field, False)]
                    if source and background != material:
                        layers.append((background, 1 - field, True))
                    for selected_material, alpha, inverse in layers:
                        if selected_material not in allowed_materials or selected_material not in selections:
                            continue
                        selected = selections[selected_material]
                        family = selected['family']
                        # Snow remains bare away from exposed material transitions.
                        if family == 'snow_stone' and source is None:
                            continue
                        rule = dict(texture=name, family=family, density=selected['density'],
                                    tint=tint(world, selected_material, family))
                        if selected_material == 'swamp':
                            tile_path = ROOT / tile['installed_file']
                            rgb = np.asarray(Image.open(tile_path).convert('RGB'), dtype=float)
                            water = (rgb[..., 2] > rgb[..., 0] * 1.2) & (rgb[..., 2] > rgb[..., 1] * .95)
                            dry = ~ndimage.binary_dilation(water, iterations=2)
                            alpha = np.minimum(alpha, dry)
                            purpose = 'swamp'
                            evidence['sources'][str(tile_path.relative_to(ROOT))] = sha(tile_path)
                        else:
                            purpose = 'background' if inverse else 'foreground'
                        if not np.any(alpha > .95):
                            continue
                        if source or selected_material == 'swamp':
                            rule['mask'] = mask_file(name, alpha, purpose, source)
                        config['rules'].append(rule)
                assert len(config['rules']) <= 256
            (dest / (map_id + '.yml')).write_text(yaml.safe_dump(config, sort_keys=False))
            evidence['maps'][world + '/' + map_id] = {'status': 'disabled' if config.get('enabled') is False else 'prepared',
                                                     'rules': len(config.get('rules', []))}
        for p in dest.rglob('*'):
            if p.is_file():
                files[str(p.relative_to(RUNTIME))] = sha(p)
    # Inspect each distinct swamp base/transition, including internal opaque blue channels.
    review = Image.new('RGB', (768, max(1, ((len(masks_review) + 1) // 2) * 208)), '#24242a')
    draw = ImageDraw.Draw(review)
    for i, (world, name, mask) in enumerate(masks_review):
        x, y = i % 2 * 384, i // 2 * 208
        draw.text((x + 4, y + 4), world + ' ' + name, fill='white')
        rgb = Image.open(ROOT / tiles[world][name]['installed_file']).convert('RGB').resize((192, 192))
        review.paste(rgb, (x, y + 16))
        review.paste(mask.resize((192, 192)), (x + 192, y + 16))
    if masks_review:
        review.save(HERE / 'swamp_masks_review.png')
    evidence['files'] = files
    evidence['settings_unchanged'] = sha(ROOT / 'settings.ini') == settings_hash
    assert evidence['settings_unchanged']
    if args.install:
        previous_file = HERE / 'installation.json'
        owned = json.loads(previous_file.read_text())['files'] if previous_file.exists() else {}
        for name, digest in files.items():
            target = ROOT / 'assets_dev' / name
            assert not target.exists() or sha(target) in (digest, owned.get(name)), 'Unowned modification: ' + name
        for name, digest in files.items():
            target = ROOT / 'assets_dev' / name
            if target.exists() and sha(target) == digest:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(RUNTIME / name, target)
            target.chmod(0o644)
            assert sha(target) == digest
        evidence['status'] = 'installed_for_runtime_review'
        previous_file.write_text(json.dumps(evidence, indent=2) + '\n')
    (HERE / 'export.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print('Prepared', len(evidence['maps']), 'map decisions and', len(files), 'files;', evidence['status'])


if __name__ == '__main__':
    main()
