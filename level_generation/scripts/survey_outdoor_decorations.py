"""Inventory every mounted MM6/MM7/MM8 ODM decoration and its spatial context.

Read-only inputs. Outputs are reference evidence, not scatter rules or runtime content.
The 96x96-cell analytical window is deliberately comparable with measure_landscape.py;
it is not a navigation or traversability boundary. Counts describe initial scene state.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
import yaml

from inspect_decoration_references import load_catalog, terrain_sample

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'level_generation/catalogues/outdoor_decorations'
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file

BIOMES = {
    'mm6': dict(outa1='blighted', outa2='lush highlands', outa3='island', outb1='highlands',
                outb2='dry settlement', outb3='desert', outc1='snow', outc2='temperate city',
                outc3='haunted wetland', outd1='coastal grassland', outd2='tropical coast',
                outd3='wooded highlands', oute1='islands', oute2='island settlement', oute3='coastal village'),
    'mm7': dict(**{'7out01':'island village', '7out02':'temperate highlands', '7out03':'temperate city',
                  '7out04':'forest', '7out05':'necropolis', '7out06':'desert city', '7out13':'wetland coast',
                  '7out15':'underwater'}, out09='ruined island', out10='snow mountains',
                out11='burial landscape', out12='barren highlands', out14='forest coast'),
    'mm8': dict(out01='tropical islands', out02='temperate city', out03='temperate city',
                out04='desert', out05='grass and dirt forts', out06='necropolis', out07='forest',
                out08='dry grassland', out13='tropical island', out15='tutorial',
                elema='air plane', elemf='fire plane', elemw='water plane', pbp='otherworld'),
}
COLORS = {'trees':'#367c43', 'plants':'#91b73c', 'flowers':'#d66ca6', 'dry_plants':'#be9639',
          'aquatic':'#48b6b2', 'rocks':'#82776d', 'deadwood':'#8b6241', 'remains':'#b8a382',
          'ritual':'#9771c4', 'wayfinding':'#ecaa37', 'working_props':'#b55943',
          'fire_lights':'#f17323', 'watercraft':'#4873ad', 'food_plants':'#5da62e',
          'effects':'#aab2b8', 'markers':'#747b86', 'special':'#ee32ab'}
# Explicit visual readings from the native contact sheets: generic "tree"/"plant"
# hints alone conceal leafless variants and container plants. Not botanical claims.
BARE_TREES = {'6tree27','6tree28','7tree06','7tree09','7tree15','7tree18','7tree21',
              '7tree24','7tree30','tree27','tree41','tree42'}
SNOW_TREES = {'snotre01','snotre03','snotre05','tree33','tree36'}
POTTED_PLANTS = {'plant01a','plant01b','plant02a','plant03b','plant04b','plant07b','plant11a'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def flags_value(value):
    bits = dict(MoveThrough=1, DontDraw=2, FlickerSlow=4, FlickerAverage=8, FlickerFast=16,
                Marker=32, SlowLoop=64, EmitFire=128, SoundOnDawn=256, SoundOnDusk=512, EmitSmoke=1024)
    return int(value, 0) if re.fullmatch(r'(?:0x[0-9a-fA-F]+|\d+)', value) else sum(
        bits[part.strip()] for part in value.split(',') if part.strip())


def role(entry):
    name, hint = entry['name'], entry['hint'].lower()
    flags = flags_value(entry['flags'])
    if flags & 2 or (entry['sprite_id'] == 0 and not flags & (128 | 1024)):
        return 'markers'
    if entry['sprite_id'] == 0:
        return 'effects'
    if 'food tree' in hint or name == 'plant34':
        return 'food_plants'
    if any(word in hint for word in ['lily pad', 'seaweed', 'coral']):
        return 'aquatic'
    if any(word in hint for word in ['cactus', 'tumbleweed']):
        return 'dry_plants'
    if any(word in hint for word in ['dead tree', 'stump']) or name == '7dec16' or name in BARE_TREES:
        return 'deadwood'
    if 'tree' in hint or 'tree' in name or name.startswith('snotre'):
        return 'trees'
    if 'flower' in hint:
        return 'flowers'
    if any(word in hint for word in ['plant', 'fern', 'shrub', 'bush', 'weeds']):
        return 'plants'
    if any(word in hint for word in ['rune', 'statue', 'pedastal', 'sword in a stone', 'beacon fire']):
        return 'ritual'
    if any(word in hint for word in ['path marker', 'flag', 'buoy']):
        return 'wayfinding'
    if any(word in hint for word in ['bones', 'skeleton', 'corpse', 'skull', 'carrion']):
        return 'remains'
    if any(word in hint for word in ['fire', 'torch', 'lamp', 'brazier']):
        return 'fire_lights'
    if 'rock' in hint or 'boulder' in hint:
        return 'rocks'
    if hint == 'ship':
        return 'watercraft'
    if name == 'dec03' or any(word in hint for word in ['barrel', 'keg', 'trash', 'cauldron', 'bowl']):
        return 'working_props'
    return 'special'


def sprite_preview(world, entry, frames, image_paths, source_hashes):
    frame = frames.get(entry['sprite_id'])
    if not frame:
        return None
    texture = frame['texture_name'].lower()
    path = image_paths[world].get(texture)
    if path is None and 'Image1' not in frame.get('flags', []):
        path = image_paths[world].get(texture + '0')
    if path is None:
        return {'missing_texture': texture}
    with Image.open(path) as image:
        rgb = np.array(image.convert('RGB'))
        alpha = np.array(image.convert('RGBA'))[:, :, 3]
        alpha[((rgb[:, :, 0] >= 248) & (rgb[:, :, 1] <= 8) & (rgb[:, :, 2] >= 248)) |
              ((rgb[:, :, 0] <= 8) & (rgb[:, :, 1] >= 248) & (rgb[:, :, 2] >= 248))] = 0
        palette_path = None
        if image.mode == 'P':
            indices = np.array(image)
            alpha[indices == 0] = 0
            palette_name = 'pal%03d.act' % frame.get('palette_id', 0)
            palette_path = next((base / 'textures' / palette_name for base in
                                [ROOT / 'assets_dev/worlds' / world, ROOT / 'assets_dev/engine']
                                if (base / 'textures' / palette_name).exists()), None)
            if palette_path:
                palette = np.frombuffer(palette_path.read_bytes()[:768], dtype=np.uint8).reshape(256, 3)
                rgb = palette[indices]
        target = OUT / 'sprites' / f'{world}_{entry["id"]}.png'
        Image.fromarray(np.dstack((rgb, alpha))).save(target)
        source_hashes[str(path.relative_to(ROOT))] = sha(path)
        if palette_path:
            source_hashes[str(palette_path.relative_to(ROOT))] = sha(palette_path)
        return {'path': str(target.relative_to(OUT)), 'source': str(path.relative_to(ROOT)),
                'palette_source': str(palette_path.relative_to(ROOT)) if palette_path else None,
                'pixel_size': list(image.size), 'frame_scale': frame.get('scale', 1),
                'palette_id': frame.get('palette_id'), 'frame_flags': frame.get('flags', [])}


def terrain_data(payload, scene, world, descriptors):
    env = scene['environment']
    raw = np.array(payload['tile_map']).reshape(128, 128)[:127, :127]
    lookup = []
    for tile in range(256):
        index = tile
        if tile < 90 and tile and world == 'mm8' and env['master_tile'] < 3:
            index += [0, 450, 630][env['master_tile']]
        elif 90 <= tile < 234 and env['master_tile'] < 3:
            index = env['tile_set_lookup_indices'][(tile - 90) // 36] + (tile - 90) % 36
        elif tile >= 234:
            index = 0
        lookup.append(descriptors[index])
    flags = np.array([int(d['flags'], 0) for d in lookup])[raw]
    water = (flags & 2) != 0
    # Native road families have crossing/straight/cap/paired-diagonal suffixes;
    # numerical tilesets above 10 also include ordinary terrain in MM8.
    road_suffix = r'(?:cros[0-9]*|ns(?:_[ew])?|ew(?:_[ns])?|[ns]_[ew]|[nsew]cap|(?:ne|nw|se|sw)[12])$'
    roads = np.array([bool(re.search(road_suffix, d['texture_name'].lower())) for d in lookup])[raw]
    cells = np.stack(np.meshgrid(-32768 + (np.arange(127) + .5) * 512,
                                 32768 - (np.arange(127) + .5) * 512), axis=-1)
    heights = np.array(payload['height_map']).reshape(128, 128) * 32
    grade = np.maximum(np.hypot(heights[:127, 1:] - heights[:127, :127],
                                heights[1:, :127] - heights[:127, :127]),
                       np.hypot(heights[1:, 1:] - heights[1:, :127],
                                heights[1:, 1:] - heights[:127, 1:])) / 512
    central = (np.abs(cells[:, :, 0]) < 24576) & (np.abs(cells[:, :, 1]) < 24576)
    land = central & ~water
    return raw, lookup, flags, roads, cells, grade, land


def distance_to(points, target_points):
    return cKDTree(target_points).query(points)[0] if len(target_points) else np.full(len(points), np.inf)


def finite(value):
    return round(float(value), 1) if np.isfinite(value) else None


def background(payload, lookup, raw, target):
    colors = []
    for d in lookup:
        name, flags = d['texture_name'].lower(), int(d['flags'], 0)
        color = [142, 124, 91]
        if 'gr' in name or 'gras' in name: color = [129, 147, 98]
        if any(s in name for s in ['sno', 'ice']): color = [209, 216, 220]
        if any(s in name for s in ['sand', 'dsrt', 'des']): color = [204, 176, 118]
        if any(s in name for s in ['swmp', 'swp']): color = [104, 128, 109]
        if flags & 2: color = [79, 130, 164]
        if flags & 1: color = [183, 102, 71]
        if any(s in name for s in ['drsr', 'grsr', 'snor']): color = [173, 160, 135]
        colors.append(color)
    rgb = np.array(colors, dtype=float)[raw] / 255
    heights = np.array(payload['height_map']).reshape(128, 128)[:127, :127]
    gy, gx = np.gradient(heights.astype(float))
    shade = np.clip(.92 - (gx + gy) / 65, .6, 1.15)
    plt.imsave(target, np.clip(rgb * shade[:, :, None], 0, 1))


def write_readme(maps, validation):
    intro = '''# All-outdoor decoration reference catalogue

Open [the interactive map and asset browser](index.html), or read
[the generation guidelines](../../OUTDOOR_DECORATION_CALIBRATION.md).

## Coverage and provenance

This survey includes every `*.odm` under the mounted MM6, MM7 and MM8 map directories:
15 + 13 + 14 = 42 maps. MM8's tutorial and exceptional planes are retained, not treated
as ordinary countryside density targets. Celeste and The Pit are BLV maps; they and
Plane of Earth are outside this ODM survey. No generated Brackenford/MM5 maps are pooled.

Inputs are the mounted native files plus scene overrides and merged decoration/frame
registries. All 42 entity-count/XYZ-coordinate multisets match the corresponding local
`reference/mmerge_data_forus/Data/mm*.games.lod` ODMs, including duplicate coordinates.
This establishes placement preservation against that reference, not retail event parity.
See each map's `reference_parity`, [source hashes](sources.json) and [validation](validation.json).

## Reading the measurements

- **Total records** include starts, sound markers, hidden entries and effects.
- **Visible** means an initially drawable sprite descriptor: nonzero sprite ID,
  no descriptor `DontDraw`, and no initial instance invisible bit. It is not a
  visibility-culling result or a post-load Lua simulation. Emitter-only effects are separate.
- **Descriptor IDs** are zero-based merged runtime indices. Names/aliases are resolved
  like `DecorationTable::resolveMapDecoration`; original raw indices alone are not reliable.
- **Central land** means nonwater cells in the ±24,576-unit analytical square, 96×96
  native cells. Shores and steep land count. This is neither the travel boundary nor
  proven walkability. Full-map records and buffers remain available in the browser.
- **Rate** is central-land visible anchors divided by central nonwater area, expressed
  per 4,096×4,096 units. It does not include water/outside-window anchors in the numerator.
- **Far %** counts central nonwater cell centres over 2,048 units from any initially
  visible decoration anchor (including anchors outside the window). The gentle-land
  counterpart restricts the sample to maximum native triangle grade ≤0.5.
- **Local counts** use aligned 2,048×2,048 bins. They are counts, not area-normalized
  density at coasts. A tiny flower and a large tree each count once.
- **Near a BModel** is XY distance to the nearest bounding rectangle; that model can
  be a cliff, boat, bridge or wall, not necessarily a house. No automatic town classifier.
- **Road/water proximity** is distance to source cell centres, not a traced path/shoreline.
  Road cells are recognised by native crossing/straight/cap/paired-diagonal texture suffixes;
  a plain-dirt footpath without road artwork is not detected. Read the terrain key too.
- **Roles** are analytical visual/use groups. Explicit appearance tags distinguish
  inspected bare/snow trees and container plants. They are not historical author metadata.
- **Previews** decode the first frame with palette/alpha and preserve frame scale in
  metadata. They do not simulate animation, lighting, seasons or quest changes.
- **Event 0** does not prove a decoration is inert. Native rules can supply behavior.
  `script_visual_change_calls` is a list of source references, not evaluated reachability.

The sprite inventory excludes actors, loose items, modeled props and embedded texture
detail. A zero-sprite map can still contain substantial architecture, landform and effects.
The schematic terrain backdrop is not an exact textured minimap or a water-depth model.

## Complete map inventory

| World | Map / source records | Context | Total | Visible | Types | Rate | Far % |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
'''
    rows = []
    for m in maps:
        c, d = m['counts'], m['density']
        rows.append(f'| {m["world"]} | [{m["name"]}](maps/{m["key"]}.json) `{m["map"]}` | '
                    f'{m["biome"]} | {c["records"]} | {c["visible"]} | {c["visible_types"]} | '
                    f'{d["per_4096_square"]} | {d["land_farther_than_2048_pct"]} |')
    tail = f'''

Totals: **{validation['records']:,} records**, **{validation['visible']:,} initially visible sprites**,
**{validation['types']} resolved descriptor identities**; all referenced sprite previews resolved.

## Files and regeneration

- [Map summary CSV](map_summary.csv): counts, rates, coverage and role totals.
- [Decoration × map CSV](decoration_usage.csv): every used descriptor and all its maps/counts.
- [Full inventory JSON](inventory.json): every placement, type and analytical measurement.
- `maps/`: individual reports with coordinates, geometry envelopes and event references.
- `sprites/`: palette-correct first-frame previews; `contacts/`: role contact sheets.
- `data.js`: local-file browser data, regenerated alongside the JSON.

Run from the repository root:

```sh
python3 level_generation/scripts/survey_outdoor_decorations.py
```

Requires PyYAML, NumPy, SciPy, Pillow and Matplotlib. This only writes reference evidence
under this catalogue. It does not edit maps, art, events or gameplay tables. Routine
generation should reuse the evidence rather than rerun the complete survey.
'''
    (OUT / 'README.md').write_text(intro + '\n'.join(rows) + tail)


def main():
    for folder in ['maps', 'terrain', 'sprites', 'contacts']:
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    catalog, names, aliases, frames = load_catalog()
    sources = {}
    for relative in ['assets_dev/engine/data_tables/decoration_data.txt',
                     'assets_dev/engine/rendering/sprite_frame_data_common.yml',
                     'assets_dev/engine/data_tables/map_stats.txt',
                     'assets_dev/engine/data_tables/map_navigation.txt']:
        sources[relative] = sha(ROOT / relative)
    table_rows = list(csv.reader((ROOT / 'assets_dev/engine/data_tables/map_stats.txt').open(), delimiter='\t'))
    map_names = {row[2].lower(): row[1] for row in table_rows if len(row) > 2 and row[0].isdigit()}
    image_paths = {}
    for world in BIOMES:
        paths = {}
        for base in [ROOT / 'assets_dev/worlds' / world, ROOT / 'assets_dev/engine']:
            for path in sorted((base / 'sprites').glob('*')):
                if path.suffix.lower() in {'.png', '.bmp'}:
                    paths.setdefault(path.stem.lower(), path)
        image_paths[world] = paths
    maps, types, previews = [], {}, {}
    for world, biomes in BIOMES.items():
        table = ROOT / 'assets_dev/engine/data_tables' / {
            'mm6':'terrain_tile_data_3.txt', 'mm7':'terrain_tile_data_2.txt', 'mm8':'terrain_tile_data.txt'}[world]
        sources[str(table.relative_to(ROOT))] = sha(table)
        descriptors = list(csv.DictReader(table.open(), delimiter='\t'))
        paths = sorted((ROOT / 'assets_dev/worlds' / world / 'maps').glob('*.odm'))
        assert set(p.stem for p in paths) == set(biomes), 'Update explicit coverage/biome inventory'
        for path in paths:
            key = world + '_' + path.stem
            payload = parse_odm_file(path)['payload']
            scene_path = path.with_suffix('.scene.yml')
            scene = yaml.load(scene_path.read_text(), Loader=yaml.CSafeLoader)
            for source in [path, scene_path]:
                sources[str(source.relative_to(ROOT))] = sha(source)
            overrides = {e['entity_index']: e for e in scene.get('entities', [])}
            raw, lookup, flags, roads, cells, grade, land = terrain_data(payload, scene, world, descriptors)
            models = []
            for model in payload['bmodels']:
                vertices = np.array([[v[a] for a in 'xyz'] for v in model['vertices']])
                if not len(vertices): continue
                models.append({'index':model['index'], 'name':model['name'],
                               'bounds':[vertices.min(0).tolist(), vertices.max(0).tolist()]})
            records = []
            for source in payload['entities']:
                e = dict(source); e.update(overrides.get(e['index'], {}))
                name = e['name'].strip().lower(); raw_entry = catalog.get(e['decoration_list_id'])
                entry = names.get(name) if name else catalog[0]
                if entry is None:
                    entry = (aliases.get(name) if raw_entry is None or raw_entry['name'] == 'pending' else None) or raw_entry
                if entry is None: raise ValueError((key, e))
                desc_flags = flags_value(entry['flags'])
                hidden = bool(e.get('initial_decoration_flag', e['ai_attributes']) & 32)
                visible = bool(entry['sprite_id']) and not bool(desc_flags & 2) and not hidden
                emitter = bool(desc_flags & (128 | 1024)) and not hidden
                group = role(entry)
                preview_key = (world, entry['id'])
                if entry['sprite_id'] and preview_key not in previews:
                    previews[preview_key] = sprite_preview(world, entry, frames, image_paths, sources)
                x, y, z = [e['position'][a] for a in 'xyz']
                col, row = int(np.floor(x / 512 + 64)), int(np.floor(64 - y / 512))
                inside_grid = 0 <= col < 127 and 0 <= row < 127
                ground, slope = terrain_sample(payload, x, y)
                record = {'index':e['index'], 'descriptor_id':entry['id'], 'name':entry['name'],
                          'source_name':e['name'], 'hint':entry['hint'], 'role':group, 'position':[x,y,z],
                          'visible':visible, 'hidden':hidden, 'emitter':emitter,
                          'event_primary':e['event_id_primary'], 'event_secondary':e['event_id_secondary'],
                          'initial_flags':e.get('initial_decoration_flag', e['ai_attributes']),
                          'terrain_texture':lookup[int(raw[row,col])]['texture_name'] if inside_grid else None,
                          'central_land':bool(land[row,col]) if inside_grid else False,
                          'central_window':abs(x) < 24576 and abs(y) < 24576,
                          'grade':slope, 'ground_offset':round(z-ground, 1), 'nearest_model':None,
                          'nearest_model_xy':None}
                if models:
                    distances = [np.hypot(max(m['bounds'][0][0]-x, 0, x-m['bounds'][1][0]),
                                          max(m['bounds'][0][1]-y, 0, y-m['bounds'][1][1])) for m in models]
                    closest = int(np.argmin(distances)); record['nearest_model'] = models[closest]['index']
                    record['nearest_model_xy'] = finite(distances[closest])
                records.append(record)
                if entry['id'] not in types:
                    tags = []
                    if entry['name'] in BARE_TREES: tags.append('bare tree')
                    if entry['name'] in SNOW_TREES: tags.append('snow-covered tree')
                    if entry['name'] in POTTED_PLANTS: tags.append('container plant / fixture')
                    types[entry['id']] = dict(entry, role=group, appearance_tags=tags, maps={}, previews={})
                type_entry = types[entry['id']]
                usage = type_entry['maps'].setdefault(key, {'total':0, 'visible':0, 'hidden':0, 'emitters':0})
                for field, value in [('total',1), ('visible',visible), ('hidden',hidden), ('emitters',emitter)]:
                    usage[field] += int(value)
                if preview_key in previews:
                    type_entry['previews'][world] = previews[preview_key]
            points = np.array([r['position'][:2] for r in records]).reshape(-1, 2)
            for field, mask in [('road_cell_distance', roads), ('water_cell_distance', (flags & 2) != 0)]:
                distances = distance_to(points, cells[mask])
                for record, distance in zip(records, distances): record[field] = finite(distance)
            visible = [r for r in records if r['visible']]
            land_records = [r for r in visible if r['central_land']]
            all_visible_points = np.array([r['position'][:2] for r in visible]).reshape(-1, 2)
            nearest = distance_to(cells[land], all_visible_points)
            gentle = land & (grade <= .5)
            nearest_gentle = distance_to(cells[gentle], all_visible_points)
            local_counts = np.zeros((24,24), dtype=int)
            for record in land_records:
                x,y = record['position'][:2]
                local_counts[min(23,int((24576-y)/2048)), min(23,int((x+24576)/2048))] += 1
            role_stats = {}
            for group in COLORS:
                members = [r for r in visible if r['role'] == group]
                if not members: continue
                role_stats[group] = {'count':len(members),
                    'central_land':sum(r['central_land'] for r in members),
                    'near_model_1024':sum(r['nearest_model_xy'] is not None and r['nearest_model_xy']<=1024 for r in members),
                    'near_road_cells_768':sum(r['road_cell_distance'] is not None and r['road_cell_distance']<=768 for r in members),
                    'near_water_cells_768':sum(r['water_cell_distance'] is not None and r['water_cell_distance']<=768 for r in members),
                    'steep_grade_gt_05':sum(r['grade']>.5 for r in members)}
            script_paths = sorted((path.parents[1] / 'events/maps').glob(path.stem + '*.lua'))
            script_changes = []
            for script in script_paths:
                lines = script.read_text(errors='replace').splitlines()
                matches = [{'line':i+1, 'text':line.strip()} for i,line in enumerate(lines)
                           if re.search(r'evt\.(?:SetSprite|SetDecoration|SetLight)\(', line)]
                if matches:
                    sources[str(script.relative_to(ROOT))] = sha(script)
                    script_changes.append({'path':str(script.relative_to(ROOT)), 'calls':matches})
            report = {'key':key, 'world':world, 'map':path.name, 'name':map_names[path.name.lower()],
                      'biome':biomes[path.stem], 'special_comparison':path.stem in ['out15','7out15','elema','elemf','elemw','pbp'],
                      'native_source':str(path.relative_to(ROOT)), 'scene_source':str(scene_path.relative_to(ROOT)),
                      'counts':{'records':len(records), 'visible':len(visible), 'hidden':sum(r['hidden'] for r in records),
                                'emitters':sum(r['emitter'] for r in records), 'visible_types':len({r['descriptor_id'] for r in visible}),
                                'bmodels':len(models), 'outside_central_window':sum(not r['central_window'] for r in visible)},
                      'density':{'central_nonwater_cells':int(land.sum()), 'central_land_decorations':len(land_records),
                                 'per_4096_square':round(len(land_records)/int(land.sum())*64,2) if land.any() else None,
                                 'land_farther_than_2048_pct':round(float(np.mean(nearest>2048))*100,1) if len(nearest) else None,
                                 'gentle_land_farther_than_2048_pct':round(float(np.mean(nearest_gentle>2048))*100,1) if len(nearest_gentle) else None,
                                 'gentle_land_cells':int(gentle.sum()), 'max_in_2048_square':int(local_counts.max()),
                                 'local_counts_2048':local_counts.tolist()},
                      'roles':role_stats, 'palette':dict(Counter(r['name'] for r in visible).most_common()),
                      'terrain_palette':dict(Counter(lookup[int(i)]['texture_name'] for i in raw.flat).most_common()),
                      'script_visual_change_calls':script_changes, 'models':models, 'records':records}
            reference = ROOT / 'reference/mmerge_data_forus/Data' / (world + '.games.lod') / path.name
            if reference.exists():
                original = parse_odm_file(reference)['payload']['entities']
                old_positions = Counter(tuple(e['position'][a] for a in 'xyz') for e in original)
                current_positions = Counter(tuple(e['position']) for e in records)
                sources[str(reference.relative_to(ROOT))] = sha(reference)
                report['reference_parity'] = {'path':str(reference.relative_to(ROOT)),
                    'reference_count':len(original), 'coordinate_multiset_matches':old_positions == current_positions}
            background(payload, lookup, raw, OUT / 'terrain' / (key + '.png'))
            write_json(OUT / 'maps' / (key + '.json'), report)
            maps.append(report)
            print(key, report['counts']['visible'], report['density']['per_4096_square'], flush=True)
    type_list = sorted(types.values(), key=lambda t:(t['role'], t['name']))
    write_json(OUT / 'inventory.json', {'maps':maps, 'types':type_list})
    write_json(OUT / 'sources.json', sources)
    with (OUT / 'map_summary.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['world','map','name','biome','records','visible','types','hidden','emitters',
                         'central_land_count','per_4096_square','land_far_2048_pct','gentle_land_far_2048_pct'] + list(COLORS))
        for m in maps:
            writer.writerow([m['world'],m['map'],m['name'],m['biome'],m['counts']['records'],m['counts']['visible'],
                             m['counts']['visible_types'],m['counts']['hidden'],m['counts']['emitters'],
                             m['density']['central_land_decorations'],m['density']['per_4096_square'],
                             m['density']['land_farther_than_2048_pct'],m['density']['gentle_land_farther_than_2048_pct']]+
                            [m['roles'].get(c,{}).get('count',0) for c in COLORS])
    with (OUT / 'decoration_usage.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['id','name','hint','role','world_map','total','visible','hidden','event_indices'])
        for t in type_list:
            for key, counts in t['maps'].items():
                m = next(m for m in maps if m['key']==key)
                events = [f'{r["index"]}:p{r["event_primary"]}/s{r["event_secondary"]}' for r in m['records']
                          if r['descriptor_id']==t['id'] and (r['event_primary'] or r['event_secondary'])]
                writer.writerow([t['id'],t['name'],t['hint'],t['role'],key,counts['total'],counts['visible'],
                                 counts['hidden'],' '.join(events)])
    compact_maps = [{**{k:v for k,v in m.items() if k not in ['script_visual_change_calls','terrain_palette']},
                     'records':[{k:r[k] for k in ['index','descriptor_id','position','visible','hidden','emitter',
                                                 'role','event_secondary','terrain_texture','nearest_model']} for r in m['records']]}
                    for m in maps]
    (OUT / 'data.js').write_text('const survey = ' + json.dumps({'maps':compact_maps,'types':type_list,'colors':COLORS},
                                separators=(',', ':')) + ';\n')
    for group in COLORS:
        entries = [t for t in type_list if t['role']==group and any(t['previews'].values())]
        for page in range((len(entries)+47)//48):
            chunk = entries[page*48:(page+1)*48]
            fig, axes = plt.subplots((len(chunk)+7)//8, 8, figsize=(18, max(3,((len(chunk)+7)//8)*2.4)), squeeze=False)
            for ax in axes.flat: ax.axis('off')
            for ax, entry in zip(axes.flat, chunk):
                preview = next(p for p in entry['previews'].values() if p and 'path' in p)
                ax.imshow(Image.open(OUT / preview['path']))
                count = sum(m['visible'] for m in entry['maps'].values())
                ax.set_title(f'{entry["name"]} · {count}\n{entry["hint"]}', fontsize=8)
            fig.suptitle(group + ' — first frames, independently fitted; labels are descriptor names / visible counts')
            fig.tight_layout(rect=(0,0,1,.94)); fig.savefig(OUT / 'contacts' / f'{group}_{page+1}.png', dpi=120); plt.close(fig)
    validation = {'maps':len(maps), 'maps_by_world':dict(Counter(m['world'] for m in maps)),
                  'records':sum(m['counts']['records'] for m in maps), 'types':len(types),
                  'visible':sum(m['counts']['visible'] for m in maps),
                  'reference_coordinate_matches':sum(m.get('reference_parity',{}).get('coordinate_multiset_matches',False) for m in maps),
                  'unclassified_types':[t['name'] for t in type_list if t['role']=='special'],
                  'missing_previews':[f'{w}:{i}' for (w,i),p in previews.items() if not p or 'missing_texture' in p],
                  'checks':'all ODM stems inventoried; every entity resolved; map/type totals reconcile; source hashes recorded'}
    assert validation['records'] == sum(sum(u['total'] for u in t['maps'].values()) for t in type_list)
    assert validation['visible'] == sum(sum(u['visible'] for u in t['maps'].values()) for t in type_list)
    write_json(OUT / 'validation.json', validation)
    write_readme(maps, validation)
    print(json.dumps(validation, indent=2))


if __name__ == '__main__':
    main()
