"""Compile matching-material land islands, holes, and native variant contexts on empty flat terrain."""
import csv
import json
import subprocess
import yaml
from common import P, ROOT, sha
from inventory import GROUPS, descriptor_index


def main():
    inventory = json.loads((P / 'effective_inventory.json').read_text())
    grids = json.loads((P / 'effective_grids.json').read_text())
    bindings = json.loads((P / 'materials.json').read_text())['land']
    records = json.loads((P / 'transitions/build.json').read_text())['tiles']
    table = list(csv.DictReader((ROOT / 'assets_dev/engine/data_tables/terrain_tile_data.txt').open(), delimiter='\t'))
    report = dict(fixtures={})
    for family, binding in bindings.items():
        members = [r for r in records if not r['overlay'] and r['family'] == family]
        background, foreground = GROUPS[binding['background']][0], GROUPS[binding['foreground']][0]
        wanted = {r['name'] for r in members} | {background, foreground}
        choices = []
        for config in inventory['maps']:
            names = {}
            for raw in range(234):
                names.setdefault(table[descriptor_index(raw, config['master_tile'], config['lookup'])]['texture_name'].lower(), raw)
            if wanted <= set(names):
                choices.append((config, names))
        assert choices, (family, wanted)
        config, names = choices[0]
        grid = [[background] * 128 for _ in range(128)]
        poses, layouts, missing = {}, {}, []
        corner_names = {}
        for r in members:
            if r['name'] == 'voltylx':
                continue
            corner_names.setdefault(r['topology']['N'] + r['topology']['S'], r['name'])
        for kind, left in [('island', 52), ('hole', 64)]:
            vertices = [[int(0 < x < 5 and 0 < y < 5) for x in range(6)] for y in range(6)]
            if kind == 'hole':
                vertices = [[1 - v for v in row] for row in vertices]
            layout = []
            for y in range(5):
                row = []
                for x in range(5):
                    corners = ''.join(str(vertices[yy][xx]) for yy, xx in [(y, x), (y, x+1), (y+1, x), (y+1, x+1)])
                    row.append(background if corners == '0000' else foreground if corners == '1111' else corner_names.get(corners))
                layout.append(row)
            if any(n is None for row in layout for n in row):
                missing.append(kind)
                continue
            for y in range(53, 64):
                for x in range(left-3, left+8):
                    grid[y][x] = background if kind == 'island' else foreground
            for y, row in enumerate(layout):
                for x, n in enumerate(row):
                    grid[56+y][left+x] = n
            poses[kind] = [(left+2.5-64)*512, 512, 3000, 1.5707963268, -.96]
            layouts[kind] = dict(row=56, col=left, grid=layout)
        # Native pads cover variants and every used shape even when a family lacks a full corner set.
        for i, n in enumerate(sorted(wanted)):
            if n in (background, foreground):
                top, left = 32, 50 if n == background else 64
                for y in range(top-3, top+4):
                    for x in range(left-3, left+4):
                        grid[y][x] = n
            else:
                candidates = [(m,y,x) for m,g in grids.items() for y,row in enumerate(g) for x,name in enumerate(row)
                              if name == n and all(v in names for line in g[max(0,y-2):y+3] for v in line[max(0,x-2):x+3])]
                assert candidates, n
                m,y,x = candidates[len(candidates)//2];native = grids[m]
                top,left = 76 + i//5*8, 38+i%5*9
                for dy in range(-2,3):
                    for dx in range(-2,3):
                        if 0 <= y+dy < 127 and 0 <= x+dx < 127:
                            grid[top+dy][left+dx] = native[y+dy][x+dx]
                layouts[n] = dict(native_map=m,native_row=y,native_col=x,row=top,col=left)
            poses[n] = [(left+.5-64)*512,(64-top-4)*512,2400,1.5707963268,-.96]
        assert wanted <= {n for row in grid for n in row}
        folder = P / 'fixtures/land_v1' / family
        folder.mkdir(parents=True, exist_ok=True)
        for kind in ('map','scene','terrain','geometry'):
            data = yaml.safe_load((P/'fixtures/banks_v2/shore_dirt'/('out01.'+kind+'.yml')).read_text())
            if kind == 'terrain':
                data['tile_map_hex'] = bytes(names[n] for row in grid for n in row).hex()
            elif kind == 'scene':
                data['environment'].update(master_tile=config['master_tile'],tile_set_lookup_indices=config['lookup'])
            elif kind == 'map':
                data.update(package_id='mm8:flat_land_'+family,display_name='MM8 flat land '+family)
                data.pop('source_fingerprint',None);data.pop('built_source_fingerprint',None)
            (folder/('out01.'+kind+'.yml')).write_text(json.dumps(data,indent=2)+'\n')
        with (folder/'build.log').open('w') as stream:
            subprocess.run([str(ROOT/'build/editor/openyamm-editor'),'--asset-root',str(ROOT/'assets_dev'),
                            '--headless-build-map',str(folder/'out01.map.yml')],stdout=stream,stderr=subprocess.STDOUT,check=True)
        report['fixtures'][family] = dict(folder=str(folder.relative_to(P)),master_tile=config['master_tile'],
                                         lookup=config['lookup'],poses=poses,layouts=layouts,used_names=sorted(wanted),
                                         unavailable_closed_layouts=missing,odm_sha256=sha(folder/'out01.odm'))
        print('Compiled',family,len(wanted),'names; unavailable closed layouts',missing,flush=True)
    report['script_sha256'] = sha(P/'prepare_land_fixtures.py')
    (P/'reports/land_fixtures.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    main()
