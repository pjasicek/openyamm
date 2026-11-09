"""Inventory rendered MM8 terrain, including direct-master remapping and liquid frames."""
import collections
import csv
import hashlib
import html
import json
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file

# Separate visually/semantically different transition substrates, even for shared liquids.
GROUPS = {
    'dirt': ('dirttyl', ['dirt']),
    'grass': ('grastyl', ['gras', 'grdrt']),
    'volcano': ('voltyl', ['vol']),
    'red_dirt': ('rdtyl', ['rdnw']),
    'rock': ('rktyl', ['rk']),
    'sandstone': ('rctyl', ['rc']),
    'roads_dirt': (None, ['drsr']),
    'plains': ('plntyl', ['plntyl']),
    'plains_sand': ('plsatyl', ['plsa']),
    'roads_plains': (None, ['plrd']),
    'grey_dirt': ('gdtyl', ['gdtyl']),
    'grey_stone': ('gstyl', ['gs']),
    'roads_grey': (None, ['gdrd']),
    'shore_dirt': (None, ['wtrdr']),
    'shore_grey': (None, ['wa']),
    'lava_dirt': (None, ['lvdr']),
    'lava_plains': (None, ['lv']),
    'tar_grey': (None, ['tr']),
    'water': ('wtrtyl', ['hdwtr']),
    'lava': ('lavtyl', ['hdlav']),
    'tar': ('tartyl', ['hwoil']),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def family(name):
    for group, (base, prefixes) in GROUPS.items():
        if name == base or any(name.startswith(prefix) for prefix in prefixes):
            return group
    raise ValueError('Unclassified terrain: ' + name)


def descriptor_index(raw, master, lookup):
    if raw < 90:
        return ([0, 450, 630][master] + raw) if raw and master < 3 else raw
    if raw >= 234:
        raise ValueError('Invalid rendered terrain id: ' + str(raw))
    return raw if master >= 3 else lookup[(raw - 90) // 36] + (raw - 90) % 36


def main():
    table_path = ROOT / 'assets_dev/engine/data_tables/terrain_tile_data.txt'
    table = list(csv.DictReader(table_path.open(), delimiter='\t'))
    titles = {r[2].lower(): r[1] for r in csv.reader(
        (ROOT / 'assets_dev/engine/data_tables/map_stats.txt').open(), delimiter='\t') if len(r) > 2}
    used = collections.defaultdict(dict)
    descriptors = collections.defaultdict(dict)
    maps, grids = [], {}
    for path in sorted((ROOT / 'assets_dev/worlds/mm8/maps').glob('*.odm')):
        data = parse_odm_file(path)['payload']
        assert len(data['tile_map']) == 16384
        grid, resolutions = [], {}
        for y in range(127):
            row = []
            for raw in data['tile_map'][y * 128:y * 128 + 127]:
                index = descriptor_index(raw, data['master_tile'], data['tile_set_lookup_indices'])
                record = table[index]
                name = record['texture_name'].lower()
                assert name and name != 'pending', (path, raw, index)
                row.append(name)
                descriptors[name][index] = record
                resolutions[raw] = dict(descriptor=index, texture=name)
            grid.append(row)
        grids[path.stem] = grid
        counts = collections.Counter(n for row in grid for n in row)
        for name, count in counts.items():
            used[name][path.stem] = count
        maps.append(dict(id=path.stem, title=titles.get(path.name, path.stem),
                         source=str(path.relative_to(ROOT)), sha256=sha(path),
                         master_tile=data['master_tile'], lookup=data['tile_set_lookup_indices'],
                         resolution=resolutions, tiles=dict(sorted(counts.items()))))
    surface_path = ROOT / 'assets_dev/engine/rendering/surface_materials.yml'
    surfaces = yaml.safe_load(surface_path.read_text())
    materials = surfaces['materials']
    # Select unprefixed MM8 water by frame names; material IDs need not equal semantics.
    animations = {r['id']: r['animation'] for r in materials if r.get('animation', {}).get('frames')
                  and r['animation']['frames'][0]['texture'] in ('hdwtr000', 'hdlav000', 'hwoil000')}
    frame_names = {f['texture'] for a in animations.values() for f in a['frames']}
    dependencies = {base for base, _ in GROUPS.values() if base} - set(used) - frame_names
    sources = {p.stem.lower(): p for p in (ROOT / 'assets_dev/worlds/mm8/textures').glob('*.bmp')}
    sources.update({p.stem.lower(): p for p in (ROOT / 'assets_dev/engine/terrain').glob('*.bmp')})
    reuse = collections.defaultdict(list)
    for world in ('mm6', 'mm7'):
        for path in (ROOT / f'assets_dev/worlds/{world}/textures').glob('*.bmp'):
            image = Image.open(path).convert('RGB')
            reuse[(image.size, hashlib.sha256(image.tobytes()).hexdigest())].append(
                str(path.relative_to(ROOT)))
    records = []
    for folder in ('references', 'sheets', 'reports'):
        (P / folder).mkdir(exist_ok=True)
    for name in sorted(set(used) | frame_names | dependencies):
        path = sources[name]
        image = Image.open(path)
        rgb = image.convert('RGB')
        rgb.save(P / 'references' / f'{name}.png')
        group = family(name)
        kind = ('animation' if name in frame_names else 'dependency' if name in dependencies else
                'base' if name == GROUPS[group][0] else 'road' if group.startswith('roads') else
                'variant' if name in ('dirt1', 'dirt2', 'grastyl2') or name.endswith('tylx') else
                'transition')
        examples = []
        for map_id in used.get(name, {}):
            grid = grids[map_id]
            y, x = next((y, x) for y, row in enumerate(grid) for x, n in enumerate(row) if n == name)
            examples.append(dict(map=map_id, row=y, column=x))
        records.append(dict(name=name, family=group, kind=kind, source=str(path.relative_to(ROOT)),
                            sha256=sha(path), size=list(image.size), mode=image.mode,
                            palette_zero=image.getpalette()[:3] if image.mode == 'P' else None,
                            maps=used.get(name, {}), examples=examples,
                            descriptors=list(descriptors[name].values()),
                            identical_native_sources=reuse.get((rgb.size, hashlib.sha256(rgb.tobytes()).hexdigest()), [])))
    for group in GROUPS:
        members = [r for r in records if r['family'] == group]
        sheet = Image.new('RGB', (4 * 192, ((len(members) + 3) // 4) * 216), '#202933')
        draw = ImageDraw.Draw(sheet)
        for i, record in enumerate(members):
            x, y = i % 4 * 192, i // 4 * 216
            sheet.paste(Image.open(P / 'references' / (record['name'] + '.png')).resize((192, 192)), (x, y + 24))
            draw.text((x + 4, y + 5), record['name'], fill='white')
        sheet.save(P / 'sheets' / (group + '.png'))
    report = dict(table=str(table_path.relative_to(ROOT)), table_sha256=sha(table_path),
                  runtime_lookup_source_sha256=sha(ROOT / 'game/maps/TerrainTileData.cpp'),
                  rendered_size=[127, 127], groups=GROUPS, maps=maps, tiles=records,
                  static_count=len(used), animation_count=len(frame_names),
                  dependency_only=sorted(dependencies), animations=animations,
                  surface_materials_sha256=sha(surface_path))
    (P / 'inventory.json').write_text(json.dumps(report, indent=2) + '\n')
    (P / 'grids.json').write_text(json.dumps(grids) + '\n')
    page = '<!doctype html><meta charset="utf-8"><title>MM8 original terrain inventory</title>'
    page += '<style>body{background:#202933;color:white;font:16px system-ui;margin:32px}img{max-width:100%}a{color:#9cf}</style>'
    page += f'<h1>MM8 original terrain inventory</h1><p>{len(maps)} maps; {len(used)} used static names; {len(frame_names)} animation frames. Restoration pending.</p>'
    page += '<p><a href="inventory.json">Exact inventory and sources</a></p>'
    for group in GROUPS:
        page += f'<h2>{html.escape(group)}</h2><img src="sheets/{group}.png">'
    (P / 'index.html').write_text(page)
    print(json.dumps(dict(maps=len(maps), static=len(used), animation=len(frame_names),
                         dependencies=sorted(dependencies), groups=dict(collections.Counter(r['family'] for r in records))), indent=2))


if __name__ == '__main__':
    main()
