"""Inventory actual MM6 outdoor tile use against the accepted New Sorpigal pack."""
import collections
import csv
import hashlib
import html
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file

FAMILIES = {
    'sand': ('Sand', '6sandtyl', '6sndrt'),
    'snow': ('Snow', 'snotyl', 'snodr'),
    'cracked': ('Cracked ground', 'crktyl', 'crkdrt'),
    'swamp': ('Swamp', 'swmtyl', 'swmdr'),
    'tropical': ('Tropical vegetation', 'troptyl', 'trop'),
    'roads': ('Additional cobbles on dirt', None, '6drsr'),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def family(name):
    for key, (_, base, prefix) in FAMILIES.items():
        if name == base or name.startswith(prefix): return key
    raise ValueError('Unclassified missing texture: ' + name)


def main():
    table_path = ROOT / 'assets_dev/engine/data_tables/terrain_tile_data_3.txt'
    table = list(csv.DictReader(table_path.open(), delimiter='\t'))
    map_names = {}
    for line in (ROOT / 'assets_dev/engine/data_tables/map_stats.txt').read_text().splitlines():
        row = line.split('\t')
        if len(row) > 2: map_names[row[2].lower()] = row[1]
    pack = ROOT / 'level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/transitions/shorelines/runtime_x2'
    manifest = json.loads((pack / 'manifest.json').read_text())
    known = {Path(n).stem for n in manifest['files']}
    for n, digest in manifest['files'].items(): assert sha(pack / n) == digest
    counts = collections.Counter()
    uses = collections.defaultdict(dict)
    descriptors = collections.defaultdict(dict)
    maps, grids = [], {}
    for path in sorted((ROOT / 'assets_dev/worlds/mm6/maps').glob('*.odm')):
        data = parse_odm_file(path)['payload']
        lookup = data['tile_set_lookup_indices']
        assert len(data['tile_map']) == 128 * 128
        names = []
        for raw in data['tile_map']:
            assert 0 <= raw < 234
            index = raw if raw < 90 else lookup[(raw - 90) // 36] + (raw - 90) % 36
            descriptor = table[index]
            name = descriptor['texture_name'].lower()
            assert name != 'pending'
            names.append(name)
            descriptors[name][index] = descriptor
        grid = [names[y * 128:y * 128 + 127] for y in range(127)]
        grids[path.stem] = grid
        used = collections.Counter(n for row in grid for n in row)
        counts.update(used)
        for n, count in used.items(): uses[n][path.stem] = count
        maps.append(dict(id=path.stem, name=map_names[path.name], source=str(path.relative_to(ROOT)),
                         source_sha256=sha(path), tile_lookup_bases=lookup,
                         used_tiles=dict(sorted(used.items())), missing_tiles=sorted(set(used) - known)))
    missing = sorted(set(counts) - known)
    (P / 'references').mkdir(exist_ok=True)
    (P / 'sheets').mkdir(exist_ok=True)
    records = []
    for name in missing:
        group = family(name)
        _, base, prefix = FAMILIES[group]
        source = ROOT / 'assets_dev/worlds/mm6/textures' / (name + '.bmp')
        image = Image.open(source)
        assert image.size == (128, 128)
        image.convert('RGB').save(P / 'references' / (name + '.png'))
        example_map = max(uses[name], key=uses[name].get)
        grid = grids[example_map]
        positions = [(y, x) for y in range(1, 126) for x in range(1, 126) if grid[y][x] == name]
        assert positions
        y, x = max(positions, key=lambda pos: len({n for row in grid[pos[0]-1:pos[0]+2] for n in row[pos[1]-1:pos[1]+2]}))
        records.append(dict(name=name, family=group, kind='base' if name == base else 'road' if group == 'roads' else 'transition',
                            suffix=None if name == base else name[len(prefix):], related_materials=[base, '6dirttyl'] if base else ['accepted cobbles', '6dirttyl'],
                            source=str(source.relative_to(ROOT)), source_sha256=sha(source),
                            reference='references/' + name + '.png', source_size=list(image.size),
                            descriptors=list(descriptors[name].values()), maps=uses[name], rendered_cells=counts[name],
                            example=dict(map=example_map, column=x, row=y, context=[row[x-1:x+2] for row in grid[y-1:y+2]]),
                            alpha='Opaque material composite; no separate source material mask'))
    groups = []
    for key, (label, base, prefix) in FAMILIES.items():
        members = [r for r in records if r['family'] == key]
        used_maps = sorted({m for r in members for m in r['maps']})
        groups.append(dict(id=key, label=label, base=base, prefix=prefix, count=len(members),
                           tiles=[r['name'] for r in members], maps=used_maps))
        sheet = Image.new('RGB', (4 * 200, ((len(members) + 3) // 4) * 220), '#202933')
        draw = ImageDraw.Draw(sheet)
        for i, r in enumerate(members):
            x, y = i % 4 * 200, i // 4 * 220
            sheet.paste(Image.open(P / r['reference']).resize((192, 192), Image.Resampling.NEAREST), (x, y + 24))
            draw.text((x + 3, y + 5), r['name'], fill='white')
        sheet.save(P / 'sheets' / (key + '.png'))
    report = dict(scope='All 15 MM6 outdoor ODM maps in assets_dev; actual rendered 127x127 cells, not all table entries. Indoor/bmodel textures excluded.',
                  descriptor_resolution='Matches MM6 TerrainTileData.cpp: raw<90 direct; otherwise map lookup base + 36-slot offset.',
                  table=str(table_path.relative_to(ROOT)), table_sha256=sha(table_path),
                  restored_manifest=str((pack / 'manifest.json').relative_to(ROOT)), restored_manifest_sha256=sha(pack / 'manifest.json'),
                  outdoor_maps=len(maps), used_static_textures=len(counts), restored_used_static_textures=len(set(counts) & known),
                  missing_static_textures=len(missing), additional_water_animation_frames=14,
                  notes=['All five new material families transition to the existing dirt.',
                         'Swamp blue channels are baked opaque artwork, not keyed animated water.',
                         'No additional animated-water or shore-overlay texture names are used outside the restored families.',
                         'Missing means absent from the accepted restored pack; originals exist. Unreviewed ESRGAN/bmodel experiments are not accepted terrain.'],
                  groups=groups, maps=maps, tiles=records)
    (P / 'inventory.json').write_text(json.dumps(report, indent=2) + '\n')
    with (P / 'missing_tiles.csv').open('w') as f:
        writer = csv.writer(f); writer.writerow(['texture', 'family', 'kind', 'maps', 'rendered_cells', 'source'])
        for r in records: writer.writerow([r['name'],r['family'],r['kind'],'; '.join(r['maps']),r['rendered_cells'],r['source']])
    lines = ['# Remaining MM6 outdoor terrain', '', 'Scanned all 15 outdoor maps: **120 distinct static tile textures**, of which **49 are restored** and **71 remain**. The restored pack also contains the 14 water animation frames.', '',
             '| Family | Missing | Maps |', '| --- | ---: | --- |']
    for g in groups:
        labels = [next(m['name'] for m in maps if m['id']==mid) for mid in g['maps']]
        lines.append(f"| {g['label']} | {g['count']} | {', '.join(labels)} |")
    lines += ['', 'Five new masters + 60 directional material→dirt transitions + six additional cobblestone-road tiles.', '',
              'Each new material family uses the twelve suffixes `e,n,ne,nw,s,se,sw,w,xne,xnw,xse,xsw` (edges, corners and inward corners). These are opaque composites; the material masks still need extraction and connected-edge validation.', '',
              'Additional roads: ' + ', '.join('`'+n+'`' for n in groups[-1]['tiles']) + '.', '',
              'Existing dirt, grass, volcano, animated water and dirt shoreline assets can be reused. Swamp channels are baked into its opaque material, not a new water animation. Sand and snow do not introduce separate water-overlay families in the shipped maps.', '',
              '[Visual catalogue](index.html) · [Exact per-map inventory and source hashes](inventory.json) · [71 missing filenames](missing_tiles.csv)', '',
              'This inventory reads repository ODMs, retaining their source hashes; it does not modify maps, artwork or the enhanced playtest. The New Sorpigal test correction changes placements but adds no texture family.', '',
              'Rebuild: `python3 level_generation/terrain/mm6_remaining/inventory.py`']
    (P / 'README.md').write_text('\n'.join(lines)+'\n')
    page = '<!doctype html><meta charset="utf-8"><title>Missing MM6 terrain</title><style>body{background:#202933;color:#eee;font:16px/1.5 system-ui;max-width:1000px;margin:24px auto}img{max-width:100%}a{color:#9cf}</style><h1>Remaining MM6 terrain</h1><p>15 outdoor maps · 71 missing static textures · 5 new material masters. Originals shown below.</p><p><a href="README.md">Summary and map coverage</a> · <a href="inventory.json">Inventory</a> · <a href="missing_tiles.csv">Filenames CSV</a></p>'
    for g in groups:
        page += '<h2>'+html.escape(g['label'])+f' — {g["count"]}</h2><img src="sheets/{g["id"]}.png">'
    (P / 'index.html').write_text(page)
    print(json.dumps({k:report[k] for k in ['outdoor_maps','used_static_textures','restored_used_static_textures','missing_static_textures']},indent=2))

if __name__ == '__main__': main()
