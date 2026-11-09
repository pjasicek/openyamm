"""Compile empty, flat MM8 bank fixtures from the inspected connected layouts."""
import csv
import json
import subprocess

import yaml

from common import P, ROOT, T, sha


def main():
    contexts_path = P / 'liquids/banks_v2/contexts.json'
    contexts = json.loads(contexts_path.read_text())
    assert contexts['build_sha256'] == sha(P / 'liquids/banks_v2/build.json')
    table = list(csv.DictReader((ROOT / 'assets_dev/engine/data_tables/terrain_tile_data.txt').open(),
                               delimiter='\t'))
    aliases = dict(dirt='dirttyl', grey_dirt='gdtyl', water='wtrtyl', lava='lavtyl', tar='tartyl')
    report = dict(contexts_sha256=sha(contexts_path), fixtures={})
    for family, master, lookup, land, liquid in [
        ('shore_dirt', 0, [126, 378, 90, 414], 'dirttyl', 'wtrtyl'),
        ('lava_dirt', 0, [126, 378, 90, 414], 'dirttyl', 'lavtyl'),
        ('tar_grey', 2, [702, 738, 666, 774], 'gdtyl', 'tartyl'),
    ]:
        names = {}
        for raw in range(234):
            index = 0 if raw == 0 else ([0, 450, 630][master] + raw if raw < 90 else
                                      lookup[(raw - 90) // 36] + (raw - 90) % 36)
            names.setdefault(table[index]['texture_name'].lower(), raw)
        grid = [[land] * 128 for _ in range(128)]
        placements = {}
        for kind, left in [('island', 52), ('hole', 64)]:
            top = 56
            # A full surrounding ring gives boundary tiles their intended neighbour.
            background = liquid if kind == 'island' else land
            for y in range(top - 3, top + 8):
                for x in range(left - 3, left + 8):
                    grid[y][x] = background
            source = contexts['layouts'][family + '_' + kind + '.png']['grid']
            for y, row in enumerate(source):
                for x, name in enumerate(row):
                    grid[top + y][left + x] = aliases.get(name, name)
            placements[kind] = dict(row=top, col=left, grid=source,
                                    pose=[(left + 2.5 - 64) * 512, (64 - top - 7) * 512,
                                          3000, 1.5707963268, -0.96])
        folder = P / 'fixtures/banks_v2' / family
        folder.mkdir(parents=True, exist_ok=True)
        for kind in ('map', 'scene', 'terrain', 'geometry'):
            source = T / 'mm6_new_sorpigal_transitions/fixture' / ('oute3.' + kind + '.yml')
            data = yaml.safe_load(source.read_text())
            data = json.loads(json.dumps(data).replace('oute3', 'out01').replace('mm6:', 'mm8:'))
            if kind == 'terrain':
                data['tile_map_hex'] = bytes(names[n] for row in grid for n in row).hex()
            elif kind == 'scene':
                data['environment'].update(master_tile=master, tile_set_lookup_indices=lookup)
            elif kind == 'map':
                data.update(package_id='mm8:terrain_bank_fixture_' + family,
                            display_name='MM8 flat bank fixture ' + family)
                data.pop('source_fingerprint', None)
                data.pop('built_source_fingerprint', None)
            (folder / ('out01.' + kind + '.yml')).write_text(json.dumps(data, indent=2) + '\n')
        with (folder / 'build.log').open('w') as stream:
            subprocess.run([str(ROOT / 'build/editor/openyamm-editor'), '--asset-root', str(ROOT / 'assets_dev'),
                            '--headless-build-map', str(folder / 'out01.map.yml')],
                           stdout=stream, stderr=subprocess.STDOUT, check=True)
        report['fixtures'][family] = dict(folder=str(folder.relative_to(P)), master_tile=master,
                                         lookup=lookup, placements=placements,
                                         odm_sha256=sha(folder / 'out01.odm'),
                                         used_names=sorted({n for row in grid for n in row}))
        print('Compiled', family, flush=True)
    report['script_sha256'] = sha(P / 'prepare_bank_fixtures.py')
    (P / 'reports/bank_fixtures.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
