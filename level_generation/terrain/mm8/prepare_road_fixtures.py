"""Compile flat road networks and native-context pads for every used MM8 road tile."""
import csv
import json
import subprocess
import yaml
from common import P, ROOT, T, sha
from inventory import descriptor_index


def main():
    inventory = json.loads((P / 'effective_inventory.json').read_text())
    grids = json.loads((P / 'effective_grids.json').read_text())
    table = list(csv.DictReader((ROOT / 'assets_dev/engine/data_tables/terrain_tile_data.txt').open(), delimiter='\t'))
    roads = json.loads((P / 'roads/v3/build.json').read_text())['tiles']
    stepping = json.loads((P / 'roads/stepping_v1/build.json').read_text())['tiles']
    report = dict(fixtures={}, inventory_sha256=sha(P / 'effective_inventory.json'))
    for family, map_id, base in [('roads_dirt', 'out02', 'dirttyl'), ('roads_grey', 'out06', 'gdtyl'),
                                 ('roads_plains', 'out04', 'plntyl')]:
        config = next(r for r in inventory['maps'] if r['id'] == map_id)
        master, lookup = config['master_tile'], config['lookup']
        names = {}
        for raw in range(234):
            names.setdefault(table[descriptor_index(raw, master, lookup)]['texture_name'].lower(), raw)
        records = stepping if family == 'roads_plains' else [r for r in roads if r['family'] == family]
        wanted = {r['name'] for r in records}
        grid = [[base] * 128 for _ in range(128)]
        poses, placements = {}, []
        if family != 'roads_plains':
            by_topology = {}
            for r in sorted(records, key=lambda r: r['name']):
                by_topology.setdefault(tuple(r['topology'][s] for s in 'NSEW'), r['name'])
            cross = {(56 + i, 59) for i in range(7)} | {(59, 56 + i) for i in range(7)}
            has_cross = (True, True, True, True) in by_topology
            if not has_cross:
                cross = {(56 + i, 56 + j) for i in range(7) for j in range(7) if i in (0, 6) or j in (0, 6)}
            loop = {(56 + i, 70 + j) for i in range(7) for j in range(7) if i in (0, 6) or j in (0, 6)}
            for cells in (cross, loop):
                for y, x in sorted(cells):
                    topology = tuple((y + dy, x + dx) in cells for dy, dx in [(-1, 0), (1, 0), (0, 1), (0, -1)])
                    grid[y][x] = by_topology[topology]
            poses.update(west=[-4864, 2304, 0, 0, -.3], east=[256, 2304, 0, 3.1415926536, -.3],
                         south=[-2304, -256, 0, 1.5707963268, -.3],
                         north=[-2304, 4864, 0, 4.7123889804, -.3],
                         overview=[-2304, -512, 3000, 1.5707963268, -.96],
                         loop=[4864, -512, 3000, 1.5707963268, -.96])
            if not has_cross:
                poses['west'][1] = poses['east'][1] = 768
                poses['south'][0] = poses['north'][0] = -3840
        # Preserve actual local arrangements for diagonal variants and separate stepping stones.
        for index, name in enumerate(sorted(wanted)):
            candidates = [(source_map, y, x) for source_map, native in grids.items()
                          for y in range(127) for x in range(127)
                          if native[y][x] == name and
                          all(n in names for line in native[max(0,y-2):y+3] for n in line[max(0,x-2):x+3])]
            assert candidates, (map_id, name)
            source_map, y, x = candidates[len(candidates) // 2]
            native = grids[source_map]
            top, left = 76 + index // 5 * 9, 38 + index % 5 * 9
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    if 0 <= y + dy < 127 and 0 <= x + dx < 127:
                        grid[top + dy][left + dx] = native[y + dy][x + dx]
            placements.append(dict(tile=name, native_map=source_map, native_row=y, native_col=x, row=top, col=left,
                                   outside_native_grid='plain substrate padding'))
            poses[name] = [(left + .5 - 64) * 512, (64 - top - 4) * 512, 2400, 1.5707963268, -.96]
        assert wanted <= {n for row in grid for n in row}
        folder = P / 'fixtures/roads_v1' / family
        folder.mkdir(parents=True, exist_ok=True)
        for kind in ('map', 'scene', 'terrain', 'geometry'):
            template = T / 'mm6_new_sorpigal_transitions/fixture' / ('oute3.' + kind + '.yml')
            data = yaml.safe_load(template.read_text())
            data = json.loads(json.dumps(data).replace('oute3', 'out01').replace('mm6:', 'mm8:'))
            if kind == 'terrain':
                data['tile_map_hex'] = bytes(names[n] for row in grid for n in row).hex()
            elif kind == 'scene':
                data['environment'].update(master_tile=master, tile_set_lookup_indices=lookup)
            elif kind == 'map':
                data.update(package_id='mm8:flat_' + family, display_name='MM8 flat ' + family)
                data.pop('source_fingerprint', None)
                data.pop('built_source_fingerprint', None)
            (folder / ('out01.' + kind + '.yml')).write_text(json.dumps(data, indent=2) + '\n')
        with (folder / 'build.log').open('w') as stream:
            subprocess.run([str(ROOT / 'build/editor/openyamm-editor'), '--asset-root', str(ROOT / 'assets_dev'),
                            '--headless-build-map', str(folder / 'out01.map.yml')],
                           stdout=stream, stderr=subprocess.STDOUT, check=True)
        report['fixtures'][family] = dict(folder=str(folder.relative_to(P)), map_id=map_id, master_tile=master,
                                         lookup=lookup, poses=poses, placements=placements, road_names=sorted(wanted),
                                         odm_sha256=sha(folder / 'out01.odm'))
        print('Compiled', family, len(wanted), 'road tiles', flush=True)
    report['script_sha256'] = sha(P / 'prepare_road_fixtures.py')
    (P / 'reports/road_fixtures.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
