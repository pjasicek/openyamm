#!/usr/bin/env python3
"""Catalogue existing MM6 New Sorpigal terrain without modifying or generating game artwork."""

import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile
from collections import Counter

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import yaml


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'level_generation/terrain/mm6_new_sorpigal'
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file

GROUPS = {
    'bases': ('Base tiles', ['grass', 'dirt', 'rock', 'water']),
    'grass_dirt': ('Grass / dirt transitions', ['grass', 'dirt']),
    'rock_dirt': ('Rock / dirt transitions', ['rock', 'dirt']),
    'shoreline': ('Shore overlays / water openings', ['dirt', 'water']),
    'roads': ('Roads on dirt', ['road', 'dirt']),
}
BASES = {'grass': '6grastyl', 'dirt': '6dirttyl', 'rock': '6voltyl', 'water': '6wtrtyl'}
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
SMALL = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)


def save_json(relative, value):
    path = OUTPUT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def save_image(relative, image):
    path = OUTPUT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return relative


def copy_source(source, directory):
    target = OUTPUT / directory / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return str(target.relative_to(OUTPUT))


def checkered(image):
    yy, xx = np.indices((image.height, image.width))
    grey = np.where((xx // 8 + yy // 8) % 2, 100, 155).astype(np.uint8)
    background = Image.fromarray(np.stack([grey] * 3, axis=2)).convert('RGBA')
    return Image.alpha_composite(background, image.convert('RGBA')).convert('RGB')


def sheet(relative, title, items, columns=4, size=192):
    cell_width, cell_height = size + 16, size + 60
    rows = (len(items) + columns - 1) // columns
    canvas = Image.new('RGB', (columns * cell_width, 52 + rows * cell_height), '#1c2027')
    draw = ImageDraw.Draw(canvas)
    draw.text((10, 14), title, font=FONT, fill='white')
    for index, (label, subtitle, image) in enumerate(items):
        x, y = (index % columns) * cell_width + 8, (index // columns) * cell_height + 52
        preview = checkered(image).resize((size, size), Image.Resampling.NEAREST)
        canvas.paste(preview, (x, y))
        draw.text((x, y + size + 5), label, font=FONT, fill='white')
        draw.text((x, y + size + 29), subtitle, font=SMALL, fill='#c8d1dd')
    return save_image(relative, canvas)


def classify(name):
    if name in BASES.values():
        return 'bases', 'base', None
    for prefix, family in [('6grdrt', 'grass_dirt'), ('voldrt', 'rock_dirt'), ('6wtrdr', 'shoreline')]:
        if name.startswith(prefix):
            direction = name[len(prefix):].upper()
            kind = 'X-corner' if direction.startswith('X') else 'corner' if len(direction) == 2 else 'edge'
            return family, kind, direction
    assert name.startswith('6drsr'), name
    suffix = name[5:].upper()
    kind = 'end cap' if 'CAP' in suffix else 'junction' if len(suffix) > 3 else 'turn' if '_' in suffix else 'straight'
    return 'roads', kind, suffix


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    native_path = ROOT / 'assets_dev/worlds/mm6/maps/oute3.odm'
    native = parse_odm_file(native_path)['payload']
    table_path = ROOT / 'assets_dev/engine/data_tables/terrain_tile_data_3.txt'
    descriptors = list(csv.DictReader(table_path.open(), delimiter='\t'))
    lookups = native['tile_set_lookup_indices']

    def descriptor_index(raw):
        assert 0 <= raw < 234
        return raw if raw < 90 else lookups[(raw - 90) // 36] + (raw - 90) % 36

    raw_grid = np.array(native['tile_map'], dtype=np.uint8).reshape(128, 128)
    names = np.array([descriptors[descriptor_index(raw)]['texture_name'].lower()
                      for raw in native['tile_map']]).reshape(128, 128)
    rendered = names[:127, :127]
    stored_counts, counts = Counter(names.ravel()), Counter(rendered.ravel())
    assert len(counts) == 49
    surface_path = ROOT / 'assets_dev/engine/rendering/surface_materials.yml'
    water = next(material for material in yaml.safe_load(surface_path.read_text())['materials']
                 if material['id'] == 'water_mm6')
    animation = []
    for frame in water['animation']['frames']:
        name = frame['texture']
        source = ROOT / 'assets_dev/engine/terrain' / (name + '.bmp')
        image = Image.open(source).convert('RGBA')
        assert image.size == (256, 256)
        # Match the runtime's floor-based nearest sampling at terrain=x1.
        runtime_image = Image.fromarray(np.array(image)[::2, ::2])
        animation.append({'name': name, 'ticks': frame['ticks'],
                          'source': str(source.relative_to(ROOT)),
                          'bmp': copy_source(source, 'water_animation/original_bmp'),
                          'png': save_image(f'water_animation/png/{name}.png', image),
                          'source_size': list(image.size),
                          'runtime_x1_png': save_image(f'water_animation/runtime_x1/{name}.png', runtime_image),
                          'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    assert len(animation) == 14
    water_image = Image.open(OUTPUT / animation[0]['runtime_x1_png']).convert('RGBA')

    records, display_images = [], {}
    for name in sorted(counts):
        source = ROOT / 'assets_dev/worlds/mm6/textures' / (name + '.bmp')
        indexed = Image.open(source)
        assert indexed.size == (128, 128) and indexed.mode == 'P'
        rgb = np.array(indexed.convert('RGB'))
        family, kind, direction = classify(name)
        alpha = np.full((128, 128), 255, dtype=np.uint8)
        if family == 'shoreline':
            # Match MapAssetLoader's indexed BMP decoding with applyTransparencyKey=true.
            keyed = ((np.array(indexed) == 0)
                     | ((rgb[:, :, 0] >= 248) & (rgb[:, :, 1] <= 8) & (rgb[:, :, 2] >= 248))
                     | ((rgb[:, :, 0] <= 8) & (rgb[:, :, 1] >= 248) & (rgb[:, :, 2] >= 248)))
            alpha[keyed] = 0
            assert set(np.unique(alpha)) == {0, 255}
            assert indexed.getpalette()[:3] == [0, 252, 252]
        rgba = Image.fromarray(np.dstack([rgb, alpha]))
        display_images[name] = (Image.alpha_composite(water_image, rgba) if family == 'shoreline'
                                else water_image.copy() if name == BASES['water'] else rgba)
        used_raw = sorted(int(raw) for raw in np.unique(raw_grid[names == name]))
        materials = ([next(material for material, base in BASES.items() if base == name)]
                     if family == 'bases' else GROUPS[family][1])
        record = {'name': name, 'family': family, 'kind': kind, 'native_suffix': direction,
                  'materials': materials, 'related_base_tiles': [BASES[m] for m in materials if m in BASES],
                  'rendered_cells': counts[name], 'stored_cells': stored_counts[name],
                  'raw_tile_ids': used_raw,
                  'descriptors': [descriptors[descriptor_index(raw)] for raw in used_raw],
                  'source': str(source.relative_to(ROOT)), 'source_size': [128, 128],
                  'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                  'bmp': copy_source(source, 'original_bmp'),
                  'source_rgb': save_image(f'source_rgb/{name}.png', indexed.convert('RGB')),
                  'rgba': save_image(f'rgba/{name}.png', rgba),
                  'preview': save_image(f'previews/{name}.png', checkered(rgba)),
                  'rendered_preview': save_image(f'composited/{name}.png', display_images[name]),
                  'alpha_status': 'exact source key' if family == 'shoreline' else 'opaque; no material alpha in source'}
        if family == 'shoreline':
            record['shore_alpha'] = save_image(f'alpha/shore_visible/{name}.png', Image.fromarray(alpha))
            record['water_mask'] = save_image(f'alpha/water_opening/{name}.png', Image.fromarray(255 - alpha))
            record['water_fraction'] = float(np.mean(alpha == 0))
            record['alpha_edges'] = {edge: values.tolist() for edge, values in
                                     [('north', alpha[0]), ('south', alpha[-1]),
                                      ('west', alpha[:, 0]), ('east', alpha[:, -1])]}
            assert np.array_equal(np.array(Image.open(OUTPUT / record['shore_alpha'])), alpha)
            composed = np.array(display_images[name])
            assert np.array_equal(composed[alpha == 255, :3], rgb[alpha == 255])
            assert np.array_equal(composed[alpha == 0], np.array(water_image)[alpha == 0])
        records.append(record)

    by_name = {record['name']: record for record in records}
    adjacency = Counter()
    cells = []
    for y in range(127):
        for x in range(127):
            name = str(names[y, x])
            raw = int(raw_grid[y, x])
            cells.append({'column': x, 'row': y, 'world_x': (x - 64) * 512,
                          'world_y': (64 - y) * 512, 'raw_tile_id': raw,
                          'descriptor_index': descriptor_index(raw), 'texture': name})
            if x < 126:
                adjacency[(name, 'east', str(names[y, x + 1]))] += 1
            if y < 126:
                adjacency[(name, 'south', str(names[y + 1, x]))] += 1
    with (OUTPUT / 'map_cells.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(cells[0]))
        writer.writeheader()
        writer.writerows(cells)
    adjacency_records = [{'a': a, 'direction_from_a': direction, 'b': b, 'count': count}
                         for (a, direction, b), count in sorted(adjacency.items())]
    save_json('adjacency.json', adjacency_records)

    # Every tile gets one real 3x3 map neighbourhood. Nothing is fabricated by repeating a transition.
    for record in records:
        ys, xs = np.where(rendered == record['name'])
        candidates = [(int(y), int(x)) for y, x in zip(ys, xs) if 0 < y < 126 and 0 < x < 126]
        assert candidates, record['name']
        y, x = max(candidates, key=lambda point: len(set(
            names[point[0] - 1:point[0] + 2, point[1] - 1:point[1] + 2].ravel())))
        context = Image.new('RGB', (384, 384))
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                context.paste(display_images[names[y + dy, x + dx]].convert('RGB'), ((dx + 1) * 128, (dy + 1) * 128))
        record['context'] = save_image(f'contexts/{record["name"]}.png', context)
        record['context_center'] = {'column': x, 'row': y, 'world_x': (x - 64) * 512, 'world_y': (64 - y) * 512}
        record['context_tiles'] = names[y - 1:y + 2, x - 1:x + 2].tolist()

    group_records = []
    for family, (title, materials) in GROUPS.items():
        members = [record for record in records if record['family'] == family]
        reference = sheet(f'sheets/{family}.png', f'{title} — original 128px art',
                          [(r['name'], f'{r["kind"]} | {r["rendered_cells"]} cells',
                            Image.open(OUTPUT / r['rgba'])) for r in members])
        contexts = sheet(f'sheets/{family}_contexts.png', f'{title} — actual map neighbours; target in centre',
                         [(r['name'], '3 x 3 source tiles', Image.open(OUTPUT / r['context'])) for r in members], size=256)
        group_records.append({'id': family, 'title': title, 'materials': materials,
                              'tiles': [r['name'] for r in members], 'reference_sheet': reference,
                              'context_sheet': contexts})
    shores = [r for r in records if r['family'] == 'shoreline']
    sheet('sheets/shore_alpha.png', 'Exact shoreline alpha — white = visible shore, black = water opening',
          [(r['name'], 'native 128px binary alpha', Image.open(OUTPUT / r['shore_alpha'])) for r in shores])
    sheet('sheets/water_openings.png', 'Exact water masks — white = water opening, black = shore',
          [(r['name'], 'inverse of shore alpha', Image.open(OUTPUT / r['water_mask'])) for r in shores])
    sheet('sheets/water_composites.png', 'Shore overlays composited over first MM6 water animation frame',
          [(r['name'], 'water_mm6 + exact shore alpha', display_images[r['name']]) for r in shores])
    sheet('sheets/water_animation.png', 'water_mm6 — 14 frames, source table order',
          [(r['name'], f'{r["ticks"]} native ticks', Image.open(OUTPUT / r['png'])) for r in animation])
    overview = Image.new('RGB', (127 * 16, 127 * 16))
    thumbs = {name: image.convert('RGB').resize((16, 16), Image.Resampling.LANCZOS)
              for name, image in display_images.items()}
    for cell in cells:
        overview.paste(thumbs[cell['texture']], (cell['column'] * 16, cell['row'] * 16))
    save_image('map/terrain_overview.png', overview)
    family_colors = {'bases': '#929ba6', 'grass_dirt': '#61b669', 'rock_dirt': '#b491d9',
                     'shoreline': '#4ac4d6', 'roads': '#e6b75e'}
    base_colors = {'6grastyl': '#325e30', '6dirttyl': '#75523d', '6voltyl': '#37343e', '6wtrtyl': '#244e81'}
    group_map = Image.new('RGB', overview.size)
    draw = ImageDraw.Draw(group_map)
    for cell in cells:
        color = base_colors.get(cell['texture'], family_colors[by_name[cell['texture']]['family']])
        x, y = cell['column'] * 16, cell['row'] * 16
        draw.rectangle((x, y, x + 15, y + 15), fill=color)
    save_image('map/families.png', group_map)

    materials = []
    for material in ['grass', 'dirt', 'rock', 'road', 'water']:
        base = BASES.get(material)
        members = [r['name'] for r in records if material in r['materials']]
        materials.append({'id': material, 'base_tile': base, 'used_by': members,
                          'note': 'No standalone road base tile; use the road pieces as artwork references.'
                          if material == 'road' else 'Water is animated; 6wtrtyl is the static fallback.'
                          if material == 'water' else 'Restore one shared master before making transitions.'})
    jobs = []
    common = ('Preserve MM6 colour balance, material scale and top-down orthographic orientation. '
              'No perspective, objects, cast shadows, lettering or watermarks. '
              'Do not use the old x4 outputs as quality targets. Output is a draft requiring tiled review. ')
    for material in materials:
        identifier = material['id']
        refs = ([by_name[material['base_tile']]['source_rgb']] if material['base_tile'] else ['sheets/roads.png'])
        if identifier == 'water':
            refs += ['sheets/water_animation.png']
        prompt = (f'Create a seamless 512x512 master texture for MM6 New Sorpigal {identifier}, '
                  f'using the attached native artwork as the reference. {common}'
                  'This master will be shared by all tiles containing this material; it must have repeatable edges. '
                  'Preserve broad colour and value structure while restoring restrained fine surface detail.')
        if identifier == 'road':
            prompt += ' Extract the visual character of the stone road surface; do not draw a road path or dirt border.'
        if identifier == 'water':
            prompt += ' This is a style reference first; a replacement must ultimately preserve coherent motion across 14 frames.'
        relative = f'imagegen_briefs/{identifier}_master.txt'
        (OUTPUT / 'imagegen_briefs').mkdir(exist_ok=True)
        (OUTPUT / relative).write_text(prompt + '\n')
        jobs.append({'id': identifier + '_master', 'status': 'prepared, not run', 'references': refs,
                     'prompt_file': relative, 'suggested_output': f'generated/masters/{identifier}.png',
                     'review': ['material identity and colour', '3x3 seamless repetition', 'scale beside native buildings',
                                'reduced-resolution appearance']})
    save_json('imagegen_briefs/jobs.json', jobs)
    (OUTPUT / 'imagegen_briefs/transitions.md').write_text(
        '# Transition preparation\n\n'
        'Generate/review shared material masters before rebuilding any mixed tiles. The numbered/native suffixes are '
        'identifiers, not permission to rotate or mirror artwork. Inspect each source and its actual-map context.\n\n'
        'Grass/dirt and rock/dirt: the native source is opaque artwork; no true material alpha exists. '
        'A material-coverage mask must be derived and reviewed across the whole family. Match adjoining edge coverage '
        'and shared material texture phase. Preserve intentional islands and silhouette structure unless a later '
        'task explicitly changes them. Do not independently regenerate each mixed tile.\n\n'
        'Roads: nine pieces are actually used. There is no standalone native road material in this map. '
        'Use the road reference sheet for a master, then preserve each road footprint and its edge connections.\n\n'
        'Water: rgba/6wtrdr*.png contains exact visible shoreline overlays. alpha/shore_visible is white for visible '
        'shore; alpha/water_opening is its inverse. These are source masks, not imagegen-specific edit masks. '
        'Check the edit tool mask convention before use. Keep masks separate from generated RGB; reapply them during '
        'composition. Pure 6wtrtyl is a static fallback; the runtime uses the 14 listed water_mm6 frames. '
        'Do not paint cyan key pixels as water or independently animate the land.\n\n'
        'Review complete families at native, target and mip sizes, and in contexts/*.png layouts. '
        'Reference sheets contain labels for humans; individual source_rgb/ and rgba/ images are unlabelled inputs.\n')

    catalogue = {'world': 'mm6', 'map': 'oute3.odm', 'display_name': 'New Sorpigal',
                 'source_map': str(native_path.relative_to(ROOT)),
                 'source_map_sha256': hashlib.sha256(native_path.read_bytes()).hexdigest(),
                 'table': str(table_path.relative_to(ROOT)), 'tile_lookup_bases': lookups,
                 'stored_grid': [128, 128], 'rendered_grid': [127, 127],
                 'orientation': 'north up; image x east, image y south; tile pixels retain source orientation',
                 'counts': {'unique_tiles': len(records), 'rendered_cells': len(cells),
                            'water_animation_frames': len(animation), 'exact_alpha_masks': len(shores)},
                 'group_map_colors': {**family_colors, **base_colors},
                 'materials': materials, 'groups': group_records, 'tiles': records,
                 'water': {'surface_material': 'water_mm6', 'source': str(surface_path.relative_to(ROOT)),
                           'transparency': 'shore only: palette index 0 OR cyan/magenta key thresholds from runtime',
                           'palette_index_zero_rgb': [0, 252, 252], 'animation': animation},
                 'checks': ['49 used terrain sources found at native 128x128',
                            'all 16129 rendered cells resolved through MM6 descriptor table',
                            '12 exact binary alpha masks round-tripped and composited correctly',
                            '14 animation frames found in surface-material order',
                            'one real 3x3 map context for every tile'],
                 'imagegen_jobs': 'imagegen_briefs/jobs.json'}
    assert sum(record['rendered_cells'] for record in records) == 127 * 127
    assert len(shores) == 12
    save_json('catalogue.json', catalogue)
    with (OUTPUT / 'tiles.csv').open('w') as stream:
        fields = ['name', 'family', 'kind', 'native_suffix', 'rendered_cells', 'stored_cells', 'alpha_status', 'source']
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)
    build_readme(catalogue)
    build_html(catalogue)
    files = [p for p in OUTPUT.rglob('*') if p.is_file()]
    checksums = {str(p.relative_to(OUTPUT)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(files) if p.name != 'checksums.json'}
    save_json('checksums.json', checksums)
    archive = OUTPUT.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(OUTPUT.rglob('*')):
            if path.is_file():
                bundle.write(path, str(Path(OUTPUT.name) / path.relative_to(OUTPUT)))
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
    print(json.dumps({'catalogue': str(OUTPUT), 'counts': catalogue['counts'],
                      'archive_bytes': archive.stat().st_size, 'validation': 'passed'}))


def build_readme(catalogue):
    lines = ['# New Sorpigal terrain catalogue', '',
             'Open **index.html** for the searchable, offline visual catalogue. All paths in JSON are relative '
             'to this catalogue unless explicitly identified as source paths in the repository.', '',
             '49 unique native 128×128 terrain textures, 12 exact shoreline alpha masks and 14 additional water '
             'animation frames. Sources are copied unchanged as indexed BMP and also decoded to PNG. '
             'No generation has been run and no runtime assets have been changed.', '',
             '| Group | Used tiles | Related materials |', '|---|---:|---|']
    for group in catalogue['groups']:
        lines.append(f'| {group["title"]} | {len(group["tiles"])} | {", ".join(group["materials"])} |')
    lines += ['', '## Files', '',
              '- `original_bmp/`: byte-identical native tile sources, including palettes.',
              '- `source_rgb/`: unmodified colours; shoreline keys remain cyan.',
              '- `rgba/`: ready-to-reference tiles; shoreline keys converted to exact transparency.',
              '- `alpha/shore_visible/`: white = visible shore; black = water opening.',
              '- `alpha/water_opening/`: white = water opening; black = shore.',
              '- `composited/`: water uses animation frame 0; shore alpha is composited over that frame.',
              '- `contexts/`: one real 3×3 map neighbourhood per tile, target in the centre; no labels in image.',
              '- `sheets/`: labelled family, context, water-frame, alpha and composition reference sheets.',
              '- `map/`: flat source-art overview and family map (colours in catalogue.json).',
              '- `water_animation/`: 14 existing 256px BMP/PNG frame pairs plus runtime-equivalent 128px copies.',
              '- `imagegen_briefs/`: five material-master prompts, input references and transition instructions.',
              '- `catalogue.json`, `tiles.csv`: grouping, descriptors, usage counts, source provenance and paths.',
              '- `map_cells.csv`, `adjacency.json`: all rendered cells and observed east/south neighbour pairs.',
              '- `checksums.json`: SHA-256 of every other catalogue file.', '',
              '## Interpretation', '',
              'The four bases are 6grastyl (grass), 6dirttyl (dirt), 6voltyl (rock) and 6wtrtyl '
              '(static water fallback). The rock/dirt family uses voldrt*, not a grass/rock blend. '
              'Roads also contain dirt and have no standalone native master tile here.', '',
              'Edge/corner/X-corner classifications retain native filename suffixes. The suffix alone does not '
              'define which side is material A; the source image and real-map context are authoritative. '
              'No rotations or mirrors are introduced.', '',
              'Only shoreline masks are exact material-separation data. Grass/dirt, rock/dirt and road tiles '
              'are opaque painted images: they do not carry a material alpha channel. Do not use colour-distance '
              'estimates as authoritative masks without review. Black rock and palette index 0 in opaque road/rock '
              'tiles must remain visible.', '',
              'The map stores 128×128 tile entries; the renderer draws 127×127 cells. Counts distinguish these. '
              'Contexts and overview use rendered cells, north up. World coordinates in map_cells.csv describe '
              'the north-west tile corner. These are flat texture assemblies, not game screenshots.', '',
              'The legacy BMP sources encode shoreline openings as cyan RGB (0,252,252), palette index 0. '
              'Exported shore alpha follows runtime key rules. 6wtrtyl is only the static fallback: water_mm6 '
              'supplies 14 existing 256px animated frames, each with 15 native ticks in the surface table. '
              'Runtime x1 composites use the engine\'s floor-based nearest resize to 128px. '
              'The catalogue does not equate native ticks to milliseconds.', '',
              '## Next generation order', '',
              '1. Review and restore shared grass, dirt, rock and road masters; establish a water style reference.',
              '2. Derive/review opaque transition masks together, constraining neighbour edges and material phase.',
              '3. Rebuild transitions from approved masters; retain exact shoreline coverage.',
              '4. Review full families, actual map contexts and reduced-resolution versions before runtime use.', '',
              'Generation prompts are drafts ready for later tool calls. They do not guarantee seamless output. '
              'Individual inputs are unlabelled; reference sheets include labels that must not appear in generated art.', '',
              'Rebuild from the repository root: `python3 level_generation/terrain/build_new_sorpigal_catalogue.py`.', '',
              'Original artwork remains MM6 game artwork; this catalogue does not grant a new asset licence.', '']
    (OUTPUT / 'README.md').write_text('\n'.join(lines))


def build_html(catalogue):
    groups = []
    for group in catalogue['groups']:
        cards = []
        for record in catalogue['tiles']:
            if record['family'] != group['id']:
                continue
            views = {'source': record['source_rgb'], 'rgba': record['preview'],
                     'composite': record['rendered_preview']}
            if 'shore_alpha' in record:
                views.update(alpha=record['shore_alpha'], opening=record['water_mask'])
            options = ''.join(f'<option value="{path}">{label}</option>' for label, path in views.items())
            links = [('BMP', record['bmp']), ('RGB', record['source_rgb']), ('RGBA', record['rgba']),
                     ('Actual neighbours', record['context'])]
            if 'shore_alpha' in record:
                links += [('Shore alpha', record['shore_alpha']), ('Water mask', record['water_mask'])]
            links_html = ' · '.join(f'<a href="{path}">{label}</a>' for label, path in links)
            cards.append(f'''<article data-search="{record['name']} {record['kind']} {' '.join(record['materials'])}">
<h3>{record['name']}</h3><div class="tile"><img loading="lazy" src="{record['source_rgb']}" alt="{record['name']}"></div>
<select aria-label="Preview for {record['name']}" onchange="this.previousElementSibling.querySelector('img').src=this.value">{options}</select>
<p>{record['kind']} · {record['rendered_cells']} map cells<br>{' + '.join(record['materials'])}</p>
<p class="links">{links_html}</p><details><summary>Actual 3×3 map context</summary>
<a href="{record['context']}"><img class="context" loading="lazy" src="{record['context']}" alt="Map neighbours; target in centre"></a>
</details></article>''')
        groups.append(f'''<section data-family="{group['id']}" id="{group['id']}"><h2>{group['title']} ({len(group['tiles'])})</h2>
<p><a href="{group['reference_sheet']}">Family reference sheet</a> · <a href="{group['context_sheet']}">Context sheet</a></p>
<div class="cards">{''.join(cards)}</div></section>''')
    options = ''.join(f'<option value="{g["id"]}">{g["title"]}</option>' for g in catalogue['groups'])
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>New Sorpigal terrain catalogue</title><style>
body{font:16px/1.5 system-ui,sans-serif;background:#141920;color:#e7edf5;margin:0 auto;padding:30px;max-width:1420px}
a{color:#8cc9ff}h1{margin-bottom:8px}h2{margin-top:42px}h3{margin:0 0 12px}p{max-width:1000px}
.controls{position:sticky;top:0;background:#141920;padding:14px 0;display:flex;gap:12px;z-index:2;flex-wrap:wrap}
input,select{font:inherit;background:#26313f;color:white;border:1px solid #607087;padding:8px;border-radius:5px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(235px,1fr));gap:18px}
article{background:#202934;border:1px solid #354456;border-radius:8px;padding:16px}.tile{text-align:center}
.tile img{width:192px;height:192px;image-rendering:pixelated;max-width:100%;object-fit:contain}article select{width:100%;margin-top:10px}
.links{font-size:14px}.context{width:100%;image-rendering:pixelated}.maps{display:flex;gap:20px;flex-wrap:wrap}
.maps img{width:300px;max-width:100%}.note{background:#283747;border-left:4px solid #85b7df;padding:15px}
[hidden]{display:none!important}summary{cursor:pointer}button{cursor:pointer}
</style><h1>New Sorpigal — terrain reference catalogue</h1>
<p>49 native terrain tiles · 12 exact shoreline alpha masks · 14 water animation frames. Prepared from MM6 oute3.odm for later image generation.</p>
<p><a href="README.md">Readme</a> · <a href="catalogue.json">Full catalogue JSON</a> · <a href="tiles.csv">Tile inventory CSV</a> ·
<a href="imagegen_briefs/jobs.json">Prepared imagegen jobs</a> · <a href="imagegen_briefs/transitions.md">Transition instructions</a></p>
<div class="note">Grass ↔ dirt; rock ↔ dirt; road sits on dirt; shore overlays animated water.
Only shorelines have true alpha. Opaque grass/rock/road mixtures still need reviewed material masks.
Reference sheets are labelled; individual PNG inputs are unlabelled. No images have been regenerated.</div>
<div class="maps"><p><a href="map/terrain_overview.png"><img src="map/terrain_overview.png" alt="Flat native terrain overview"></a><br>Native terrain, north up; no geometry or lighting.</p>
<p><a href="map/families.png"><img src="map/families.png" alt="Terrain families"></a><br>Transitions: green grass/dirt, purple rock/dirt,<br>cyan shores, yellow roads.</p></div>
<p>Water references: <a href="sheets/water_animation.png">14 frames</a> · <a href="sheets/shore_alpha.png">Shore alpha</a> ·
<a href="sheets/water_openings.png">Water openings</a> · <a href="sheets/water_composites.png">Composited shores</a></p>
<div class="controls"><input id="search" type="search" placeholder="Search texture, material or shape" aria-label="Search tiles">
<select id="family" aria-label="Filter by family"><option value="">All families</option>''' + options + '''</select><span id="count"></span></div>'''
    page += ''.join(groups)
    page += '''<script>
const search=document.querySelector('#search'),family=document.querySelector('#family');
function filter(){let count=0;for(const section of document.querySelectorAll('section')){let visible=0;
for(const card of section.querySelectorAll('article')){card.hidden=Boolean((family.value&&section.dataset.family!==family.value)||!card.dataset.search.toLowerCase().includes(search.value.toLowerCase()));if(!card.hidden){visible++;count++;}}
section.hidden=!visible;}document.querySelector('#count').textContent=count+' / 49 tiles';}
search.addEventListener('input',filter);family.addEventListener('change',filter);filter();
</script></html>'''
    (OUTPUT / 'index.html').write_text(page)


if __name__ == '__main__':
    main()
