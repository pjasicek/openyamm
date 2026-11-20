"""Audit installed terrain and publish decoration authoring settings; never install runtime content."""
import collections
import hashlib
import json
from pathlib import Path

import yaml
from PIL import Image

HERE = Path(__file__).resolve().parent
TERRAIN = HERE.parent
ROOT = TERRAIN.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mm6_family(name):
    prefixes = {
        '6dirt': 'dirt', '6drsr': 'roads', '6gras': 'grass', '6grdrt': 'grass',
        '6sand': 'sand', '6sndrt': 'sand', 'sno': 'snow', 'crk': 'cracked',
        'swm': 'swamp', 'trop': 'tropical', '6vol': 'volcano', 'voldrt': 'volcano',
        '6wtrdr': 'shore', '6wtrtyl': 'water', '6hdwtr': 'water',
    }
    for prefix, family in prefixes.items():
        if name.startswith(prefix):
            return family
    raise ValueError('Unclassified MM6 terrain: ' + name)


def main():
    design = yaml.safe_load((HERE / 'map_design.yml').read_text())
    families = yaml.safe_load((HERE / 'families.yml').read_text())
    result = {
        'status': 'authoring_catalogue_see_WORK_STATE_for_validation',
        'date': '2026-09-13',
        'allowed_materials': design['allowed_materials'],
        'inputs': {},
        'defaults': families['defaults'],
        'families': families['families'],
        'maps': [],
    }
    tile_audit = {}
    lines = [
        '# Decoration settings for all 42 outdoor maps', '',
        'These authoring settings are installed; see WORK_STATE.json for validation evidence. '
        'New Sorpigal remains the accepted calibration.', '',
        'Density is a multiplier on each family baseline in [families.yml](families.yml): '
        'meadow/coastal/woodland/dry meadow 50 candidates per cell, dry/dead tufts 8, '
        'reeds 18, tropical cover 24, earth stones 10, snow stones 3, volcanic stones 6, other chips 4. '
        'Candidate counts precede masks, slope/building checks and patchiness; they are not instance predictions.', '',
        'New version-2 maps use 4096-unit foliage distance and conservative short silhouettes; '
        'New Sorpigal retains its current settings including 6144-unit grass distance. '
        'Stones retain the renderer\'s shorter range. Missing materials do not receive speculative rules.', '',
    ]
    sources = [
        ('mm6', 'mm6_remaining', 'mm6_remaining/transitions/runtime_x2'),
        ('mm7', 'mm7', 'mm7/runtime_x2'),
        ('mm8', 'mm8', 'mm8/complete_runtime_x2'),
    ]
    for world, inventory_dir, export_dir in sources:
        inventory_path = TERRAIN / inventory_dir / 'inventory.json'
        inventory = json.loads(inventory_path.read_text())
        manifest_path = TERRAIN / export_dir / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        for path in (inventory_path, manifest_path):
            result['inputs'][str(path.relative_to(ROOT))] = sha(path)
        table = ROOT / inventory['table']
        assert sha(table) == inventory['table_sha256'], table
        result['inputs'][inventory['table']] = sha(table)
        for record in inventory['maps']:
            assert sha(ROOT / record['source']) == record.get('source_sha256', record.get('sha256'))
        raw_maps = {m['id']: m for m in inventory['maps']}
        assert set(raw_maps) == {p.stem for p in (ROOT / 'assets_dev/worlds' / world / 'maps').glob('*.odm')}
        assert set(raw_maps) == set(design['maps'][world])
        maps = inventory['maps']
        if world == 'mm8':
            effective_path = TERRAIN / 'mm8/effective_inventory.json'
            effective = json.loads(effective_path.read_text())
            result['inputs'][str(effective_path.relative_to(ROOT))] = sha(effective_path)
            assert effective['table_sha256'] == sha(table)
            maps = effective['maps']
            for record in maps:
                for path, digest in record['sources'].items():
                    assert sha(ROOT / path) == digest, path
            acceptance = json.loads((TERRAIN / 'mm8/reports/acceptance.json').read_text())
            assert acceptance['manifest_sha256'] == sha(manifest_path)
            assert 'v13' in acceptance['road_edge_revision']
        expected = {
            Path(name).stem: value if isinstance(value, str) else value['sha256']
            for name, value in manifest['files'].items()
        }
        installed = ROOT / 'assets_dev/worlds' / world / 'terrain_x2'
        assert set(expected) == {p.stem for p in installed.glob('*.png')}
        lookup = {t['name']: t['family'] for t in inventory['tiles']}
        if world == 'mm6':
            lookup = {name: mm6_family(name) for name in expected}
        tile_audit[world] = {}
        for name, digest in expected.items():
            path = installed / (name + '.png')
            assert sha(path) == digest, path
            with Image.open(path) as image:
                assert image.size == (256, 256)
                tile_audit[world][name] = {
                    'material_family': lookup[name], 'size': list(image.size),
                    'mode': image.mode, 'sha256': digest,
                    'installed_file': str(path.relative_to(ROOT)),
                    'map_cells': {},
                }
        lines += [f'## {world.upper()}', '',
                  '| Map | Actual tile families (cell counts) | Decoration family × density | Placement intent |',
                  '| --- | --- | --- | --- |']
        for record in maps:
            map_id = record['id']
            raw = raw_maps[map_id]
            title = raw.get('name', raw.get('title'))
            tiles = record.get('used_tiles', record.get('tiles'))
            counts = collections.Counter()
            for name, count in tiles.items():
                assert name in expected, (world, map_id, name)
                counts[lookup[name]] += count
                tile_audit[world][name]['map_cells'][map_id] = count
            assert sum(counts.values()) == 127 * 127
            requested = design['maps'][world][map_id]
            settings = []
            for material, (family, density) in requested['settings'].items():
                assert family in families['families'] and 0 < density <= 1
                if counts[material] == 0:
                    continue
                base = families['families'][family]
                settings.append({
                    'material': material, 'family': family, 'density': density,
                    'candidates_per_cell_before_exclusions': round(base['candidates'] * density, 2),
                    'width': base['width'], 'height': base['height'],
                    'readiness': base['readiness'],
                })
            output = {
                'world': world, 'map': map_id + '.odm', 'title': title,
                'seed': int(hashlib.sha256((world + ':' + map_id).encode()).hexdigest()[:8], 16),
                'material_cells': dict(counts.most_common()), 'settings': settings,
                'note': requested['note'], 'status': 'configured',
                'distance': families['defaults']['distance'],
            }
            if requested.get('preserve_existing'):
                existing = ROOT / 'assets_dev/worlds/mm6/terrain_decorations/oute3.yml'
                active = yaml.safe_load(existing.read_text())
                output.update(status='preserve_accepted_existing', seed=active['seed'], distance=active['distance'],
                              existing_config=str(existing.relative_to(ROOT)), existing_sha256=sha(existing))
            if requested.get('defer'):
                output.update(status='intentionally_disabled_pending_specialized_review', reason=requested['defer'])
            result['maps'].append(output)
            material_text = ', '.join(f'{name} {count}' for name, count in counts.most_common())
            rule_text = '; '.join(f"{s['material']}: {s['family']} ×{s['density']:g}" for s in settings) or 'Disabled'
            lines.append(f"| {title} (`{map_id}`) | {material_text} | {rule_text} | {requested['note']} |")
        lines.append('')
    assert len(result['maps']) == 42
    assert sum(len(tiles) for tiles in tile_audit.values()) == 489
    for path in (HERE / 'families.yml', HERE / 'map_design.yml'):
        result['inputs'][str(path.relative_to(ROOT))] = sha(path)
    (HERE / 'catalogue.yml').write_text(yaml.safe_dump(result, sort_keys=False))
    (HERE / 'tiles.json').write_text(json.dumps(tile_audit, indent=2) + '\n')
    (HERE / 'MAPS.md').write_text('\n'.join(lines) + '\n')
    print('Verified 489 accepted installed tiles and inventoried all 42 maps; wrote authoring catalogue and map table.')


if __name__ == '__main__':
    main()
