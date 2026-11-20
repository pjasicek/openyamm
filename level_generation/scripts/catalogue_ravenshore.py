"""Extract Ravenshore's native building/face/event/service graph and measured texture/scale evidence.

Read-only static analysis, no game scenarios. Render with blender_building_catalogue.py through MCP,
then run this script again to regenerate Markdown/HTML around the completed images.
"""
from collections import Counter, defaultdict
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import re
import sys

import numpy as np
from PIL import Image, ImageDraw
import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'level_generation/catalogues/mm8_ravenshore'
sys.path.insert(0, str(ROOT / 'util'))
from map_export import parse_odm_file


def source(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def table(name):
    with (ROOT / 'assets_dev/engine/data_tables' / name).open(encoding='cp1252', newline='') as f:
        return {int(r[0]): dict(row=r, line=i) for i, r in enumerate(csv.reader(f, delimiter='\t'), 1)
                if r and r[0].isdigit()}


def events(path):
    text = path.read_text(encoding='cp1252')
    starts = list(re.finditer(r'^Register(?:NoOp)?Event\((\d+),', text, re.M))
    result = {}
    for i, match in enumerate(starts):
        block = text[match.start():starts[i + 1].start() if i + 1 < len(starts) else len(text)]
        title = re.match(r'RegisterEvent\(\d+,\s*"([^"\n]*)"', block)
        result[int(match[1])] = dict(id=int(match[1]), title=title[1] if title else '',
            line=text.count('\n', 0, match.start()) + 1,
            houses=sorted(set(map(int, re.findall(r'evt\.EnterHouse\((\d+)\)', block)))),
            destinations=sorted(set(re.findall(r'evt\.MoveToMap\([^\n]*"([^"\n]+\.(?:blv|odm))"', block))),
            hint_only=bool(re.match(r'RegisterEvent\(\d+,\s*"[^"\n]*",\s*nil', block)),
            conditional=('if ' in block), qbits=sorted(set(map(int, re.findall(r'QBit\((\d+)\)', block)))))
    # Validate a paired label-only registration against its preceding action and exact title.
    # It supplies semantic association, never an additional active entrance.
    for number, event in result.items():
        prior = result.get(number - 1, {})
        if event['hint_only'] and event['title'] == prior.get('title') and (prior.get('houses') or prior.get('destinations')):
            event['label_for_event'] = number - 1
    return result


def points(model, face=None):
    vertices = model['vertices']
    return np.array([[vertices[i][k] for k in 'xyz'] for i in
                     (face['vertex_indices'] if face else range(len(vertices)))], dtype=float)


def bounds(p):
    return dict(min=p.min(axis=0).tolist(), max=p.max(axis=0).tolist(), size=np.ptp(p, axis=0).tolist())


def face_measure(model, face, paths):
    p = points(model, face)
    uv = np.array(list(zip(face['texture_us'], face['texture_vs'])), dtype=float)
    delta = np.array([face['texture_delta_u'], face['texture_delta_v']])
    path = paths.get(face['texture_name'].lower())
    size = list(Image.open(path).size) if path else None
    lengths = []
    for a in range(len(p)):
        b = (a + 1) % len(p)
        texels = float(np.linalg.norm(uv[a] - uv[b]))
        if texels > .01:
            lengths.append(float(np.linalg.norm(p[a] - p[b])) / texels)
    normal = np.cross(p[1] - p[0], p[2] - p[0])
    if np.linalg.norm(normal):
        normal /= np.linalg.norm(normal)
    return dict(index=face['index'], texture=face['texture_name'], event=face['cog_triggered_number'],
        attributes=face['attributes'], invisible=bool(face['attributes'] & 0x2000),
        vertex_count=len(p), bounds=bounds(p), center=p.mean(axis=0).tolist(), normal=normal.tolist(),
        texture_dimensions=size, texture_delta=delta.tolist(),
        uv_texel_bounds=[(uv + delta).min(axis=0).tolist(), (uv + delta).max(axis=0).tolist()],
        edge_units_per_texel_median=round(float(np.median(lengths)), 4) if lengths else None)


def family(name):
    for tag in ['delf_poor1', 'delf_poor2', 'delf_poor3', 'delf_med1', 'delf_med2', 'delf_rich1',
                'delf_rich2', 'hcleric_poor1', 'hcleric_med1', 'hcleric_rich1', 'ogre_poor1', 'ogre_med1']:
        if tag in name.lower(): return tag
    if 'temple' in name.lower(): return 'temple'
    if 'inn_' in name.lower(): return 'adventurers_inn'
    if 'corner' in name.lower(): return 'town_service_block'
    if 'boat' in name.lower(): return 'boat'
    return 'special_or_other'


FAMILY_NOTES = {
 'delf_rich1': 'Low chamfered main volume with a narrow polygonal tower and pointed cap. The tower changes the silhouette; the door remains ordinary size. Luodrin is this family. Baked wall/window/door panels align their stone lower bands; a thin cornice finishes the flat main roof.',
 'delf_rich2': 'Extended, articulated footprint and hipped roof planes; repeated window and corner-post panels keep the larger envelope coherent. Hostel uses this source family too: the raw rich label is not proof of its current resident’s wealth.',
 'hcleric_poor1': 'Compact rectangular one-level house. A few large facade panels, a low roof and a 128×256 entrance carry the appearance; preserve continuous lower masonry and framed windows.',
 'delf_poor2': 'Very compact rectangular mass with restrained upper trim and a low roof. Use facade panels with matched lower/upper bands, rather than oversized window decals.',
 'delf_poor1': 'Compact gabled house with shingled upper wall panels, stone base, projecting roof and shallow entry step. Read the exact native texture variants before substituting a wall or roof.',
 'delf_med1': 'Chamfered rectangular footprint with a low hipped shingle roof, stone wall panels and vertical corner posts. Window panels, plain panels and trim belong to one material family; role names need not follow the source asset’s medium label.',
 'delf_med2': 'Larger intermediate residence with repeated modular wall and roof treatment. Preserve door size while expanding the body and roof, not every dimension together.',
 'delf_poor3': 'Compact alternative with changed mass/roof treatment. Use the isolated views to distinguish this silhouette from the other poor-labelled variants; do not infer poverty from texture alone.',
 'hcleric_med1': 'Intermediate house with stronger trim and roof articulation. Vary footprint/roof composition within the measured module sizes instead of inflating doors and windows.',
 'hcleric_rich1': 'Larger named residence family with layered massing, richer facade variants and trim. Source rich label describes an art archetype; actual house/NPC binding is listed separately.',
 'ogre_poor1': 'Low rubble-stone cottage with a blue-grey pitched roof and large exposed ridge/end beams. The visible timber braces and rough masonry define this family; do not substitute the smooth t14 facade kit.',
 'ogre_med1': 'Wider, stepped rubble-stone footprint with intersecting blue-grey roofs. Low masonry volumes and roof intersections create variation without oversized doors; inspect the native stone/roof texture kit.',
 'temple': 'Large religious landmark: broad roof and tall polygonal towers around a modest entrance. Its prominence comes from the whole composition and raised site, not a giant door. Keep its road approach connected and empty.',
 'adventurers_inn': 'Large multi-part, multi-level inn. Models 81 and 82 form one establishment; the two active entry faces belong to model 82. Expanded body, roof levels and window rhythm communicate a larger service.',
 'town_service_block': 'One piece of a joined urban block. Roofs, wings, upper masses and posts may span several BModels; assign each actual door its own event/service. Consult the assembly views before treating this piece as a complete building.',
 'boat': 'Transport vessel using boat material families. Keep it in the service catalogue for provenance, but do not use its door/wall textures as the default for a Ravenshore town house.',
 'special_or_other': 'Special-purpose structure or auxiliary piece. Use its measured face/event records and isolated render; distinguish visible construction from invisible transition planes.'}


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'models').mkdir(exist_ok=True)
    (OUT / 'images').mkdir(exist_ok=True)
    map_path = ROOT / 'assets_dev/worlds/mm8/maps/out02.odm'
    scene_path = map_path.with_suffix('.scene.yml')
    lua_path = ROOT / 'assets_dev/worlds/mm8/events/maps/out02.lua'
    native = parse_odm_file(map_path)['payload']
    scene = yaml.safe_load(scene_path.read_text())
    event_map = events(lua_path)
    source_paths = [map_path, scene_path, lua_path, ROOT / 'assets_dev/worlds/mm8/events/maps/out02_mmmerge.lua']
    for name in ['house_data.txt', 'npc.txt', 'npc_topic.txt']:
        source_paths.append(ROOT / 'assets_dev/engine/data_tables' / name)
    house_table, npcs, topics = table('house_data.txt'), table('npc.txt'), table('npc_topic.txt')
    paths = {}
    for package in [ROOT / 'assets_dev/worlds/mm8', ROOT / 'assets_dev/engine']:
        for category in ['textures', 'terrain']:
            for path in sorted((package / category).glob('*.bmp')):
                paths.setdefault(path.stem.lower(), path)
    for override in scene['bmodel_faces']['interactive_faces']:
        f = native['bmodels'][override['bmodel_index']]['faces'][override['face_index']]
        for key in ['cog_number', 'cog_triggered_number', 'cog_trigger']:
            f[key] = override[key]
        f['attributes'] = override['legacy_attributes']
    assert not scene['initial_state']['face_attribute_overrides'], 'Review initial attribute changes explicitly'
    records = []
    for i, model in enumerate(native['bmodels']):
        face_records = [face_measure(model, f, paths) for f in model['faces']]
        direct, labels = defaultdict(list), defaultdict(list)
        for face in face_records:
            e = event_map.get(face['event'], {})
            if e.get('houses') or e.get('destinations'):
                direct[e['id']].append(face['index'])
            elif e.get('label_for_event') is not None:
                labels[e['label_for_event']].append(face['index'])
        services = []
        for number in sorted(set(direct) | set(labels)):
            e = event_map[number]
            houses = []
            for house_id in e['houses']:
                h = house_table[house_id]; row = h['row']
                residents = []
                for npc_id, npc in npcs.items():
                    r = npc['row']
                    if len(r) > 15 and r[6].isdigit() and int(r[6]) == house_id:
                        residents.append(dict(id=npc_id, name=r[1], portrait=r[2], line=npc['line'],
                            topics=[dict(id=int(v), title=topics.get(int(v), {}).get('row', ['', ''])[1])
                                    for v in r[10:16] if v.isdigit() and int(v)]))
                houses.append(dict(id=house_id, type=row[2], name=row[5], proprietor=row[6],
                    proprietor_title=row[7], line=h['line'], resident_candidates=residents))
            services.append(dict(event=number, title=e['title'], line=e['line'], active_faces=direct[number],
                label_only_faces=labels[number], houses=houses, destinations=e['destinations'],
                conditional=e['conditional'], qbits=e['qbits']))
        record = dict(index=i, name=model['name'], family=family(model['name']),
            bounds=bounds(points(model)), vertices=len(model['vertices']), faces=len(face_records),
            polygon_vertex_counts=dict(Counter(f['vertex_count'] for f in face_records)),
            materials=dict(Counter(f['texture'] for f in face_records)), services=services,
            has_active_entry=any(direct.values()), catalogue_building=bool(services) or i == 56, face_records=face_records,
            geometric_association='Merchant House south-west block: unlabelled adjoining tower' if i == 56 else None,
            interpretation=FAMILY_NOTES[family(model['name'])])
        records.append(record)
    stats = []
    for world, stem in [('mm6', 'oute3'), ('mm7', '7out02'), ('mm8', 'out02')]:
        path = ROOT / 'assets_dev/worlds' / world / 'maps' / (stem + '.odm')
        script = ROOT / 'assets_dev/worlds' / world / 'events/maps' / (stem + '.lua')
        es = events(script); data = parse_odm_file(path)['payload']; doors = []
        for mi, m in enumerate(data['bmodels']):
            for f in m['faces']:
                if es.get(f['cog_triggered_number'], {}).get('houses') and not f['attributes'] & 0x2000:
                    q = points(m, f); dims = np.ptp(q, axis=0)
                    # Positive-height, approximately vertical, door-textured faces only. Broad event-bound
                    # facades are excluded; transport doors matching this rule remain in the sample.
                    if dims[2] > 0 and re.search(r'(?:door|dr|^t\d+[a-z]03$)', f['texture_name'], re.I):
                        doors.append(dict(model=mi, face=f['index'], texture=f['texture_name'],
                            width=round(math.hypot(dims[0], dims[1]), 2), height=float(dims[2])))
        stats.append(dict(world=world, map=stem, selection='Direct EnterHouse faces with door-like texture keys; not every facade or all games',
            samples=doors, median_width=float(np.median([d['width'] for d in doors])) if doors else None,
            median_height=float(np.median([d['height'] for d in doors])) if doors else None))
        source_paths += [path, script]
    generated_path = ROOT / 'level_generation/projects/brackenford_greywatch/review/facade_revision/before/lg01.odm'
    generated = parse_odm_file(generated_path)['payload']
    semantics_path = ROOT / 'level_generation/projects/brackenford_greywatch/review/facade_revision/before/lg01.semantic.json'
    semantics = json.loads(semantics_path.read_text()); generated_buildings = []
    for b in semantics['buildings']:
        model_info = next(m for m in semantics['bmodels'] if m['id'] == b['id'])
        door_info = next(m for m in semantics['bmodels'] if m['id'] == b['id'] + '_door')
        door = generated['bmodels'][door_info['index']]
        generated_buildings.append(dict(id=b['id'], form=b['form'], model=model_info['index'],
            bounds=bounds(points(generated['bmodels'][model_info['index']])),
            door=face_measure(door, door['faces'][0], paths)))
    source_paths += [generated_path, semantics_path]
    catalogue = dict(format_version=1, map='mm8/out02.odm', sources=[source(p) for p in dict.fromkeys(source_paths)],
        coverage=dict(all_bmodels=len(records), building_or_entry_parts=sum(r['catalogue_building'] for r in records),
                      directly_enterable_parts=sum(r['has_active_entry'] for r in records)),
        eye_height=dict(units=176, source='game/app/GameApplication.cpp default outdoor eye height; mm8/world.yml has no movement override'),
        events=event_map, models=records, scale_comparison=stats, generated_buildings=generated_buildings,
        assembly_views=[dict(id='luodrin', models=[42], purpose='Luodrin House, user ravenshore_1/2'),
                        dict(id='sanctum', models=[107,108,109,110], purpose='Sanctum temple: four BModels, one entrance'),
                        dict(id='armor_bank_guild', models=[78,79,80], purpose='South-east block: Polished Shield / Steele’s Vault / Self Guild / Guild Caravans'),
                        dict(id='adventurers_inn', models=[81,82], purpose='One inn spans two BModels'),
                        dict(id='kessels_block', models=[46,47,48,49], focus_event=191, purpose='North-east block: Gymnasium / Kessel’s Kantina / Apothecary'),
                        dict(id='northwest_shops', models=[50,51,52,53,54], purpose='North-west shops: Keen Edge / Vexation’s Hexes / Needful Things / Caori’s Curios'),
                        dict(id='merchant_house', models=[55,56,57], purpose='Merchant House of Alvar: two entrances and unlabelled tower'),
                        dict(id='dancing_ogre', models=[71,72], purpose='The Dancing Ogre: two native parts'),
                        dict(id='wind', models=[111,112,113,114,115], purpose='Wind: transport vessel, five parts'),
                        dict(id='dauntless', models=[116,117,118,119,120], purpose='The Dauntless: transport vessel, five parts')],
        limits=['Static bindings with scene face overrides; Lua conditions and NPC candidates are not executed.',
                'Hint-only registrations label surfaces/auxiliary parts; they are not clickable house entrances.',
                'Source rich/med/poor labels describe art families, not verified resident wealth or historical intent.',
                'Bounds are derived from native vertices; old diagnostic header bounds have interleaved axes.',
                'Blender renders use native UVs and neutral study lighting; no actors/terrain or game lighting.',
                'Overlay out02_mmmerge.lua changes event504’s condition, retaining its d10 destination.'])
    (OUT / 'catalogue.json').write_text(json.dumps(catalogue, indent=2) + '\n')
    used = {f['texture'].lower() for r in records if r['catalogue_building'] for f in r['face_records']}
    (OUT / 'textures.json').write_text(json.dumps({key:source(paths[key]) for key in sorted(used) if key in paths}, indent=2)+'\n')
    assert not (used - paths.keys()), used - paths.keys()
    write_docs(catalogue)
    print(json.dumps(catalogue['coverage']))


def write_docs(catalogue):
    records = catalogue['models']; cards = []; index = []
    index += ['# Ravenshore building and entrance catalogue', '',
        '[Visual generation calibration](../../VISUAL_CALIBRATION.md) · [Searchable image catalogue](index.html) · [All face/UV/event measurements](catalogue.json)', '',
        'Static native evidence, with isolated textured Blender views. Every one of the 121 BModels is inventoried;',
        'house/dungeon/transport parts, including label-only annexes, receive individual cards. Hint-only surface events',
        'are separated from active entrance faces. Multi-service BModels and multi-part establishments are retained.', '',
        'Resident rows are initial global-table candidates; scripts/quest state may alter actual occupancy. Source',
        '`rich/med/poor` names classify art assets, not proven NPC wealth. Explanations of design intent are inferences.', '',
        'Coverage: **84 textured part cards** (83 event-associated parts plus the unlabelled Merchant House tower),',
        '**67 parts with actual entrance faces**, and **10 assembly views**. All remaining native parts stay in the inventory.', '',
        '[Texture roles](images/texture_roles.png) · [Equal-scale doors](images/door_scale.png) · [Quick validation](validation.json)', '',
        '## Buildings and entrance parts', '', '| BModel | Native name | Actual doors / associated labels | Dimensions XYZ |', '| --- | --- | --- | --- |']
    for r in records:
        if not r['catalogue_building']: continue
        i = r['index']; title = '; '.join(s['title'] for s in r['services']) or r['geometric_association']
        dims = ' × '.join(f'{v:g}' for v in r['bounds']['size'])
        index.append(f'| [{i:03d}](models/{i:03d}.md) | `{r["name"]}` | {title} | {dims} |')
        lines = [f'# BModel {i}: {r["name"]}', '', '[Catalogue](../README.md) · [Raw face and UV records](../catalogue.json)', '',
                 f'![Isolated native textured BModel {i}](../images/{i:03d}.png)', '',
                 f'**Purpose/association:** {title}. **Source art family:** `{r["family"]}`.', '',
                 f'**Measured geometry:** {r["vertices"]} vertices, {r["faces"]} faces; XYZ extent {dims} game units.',
                 f'Native vertex bounds: `{r["bounds"]["min"]}` to `{r["bounds"]["max"]}`. Polygon vertex counts: `{r["polygon_vertex_counts"]}`.', '',
                 '**Construction reading / generation advice:** '+r['interpretation'], '',
                 'Related assembly views (when listed): '+', '.join('[{}](../images/assembly_{}.png)'.format(a['purpose'], a['id']) for a in catalogue['assembly_views'] if i in a['models'])+'.', '', '## Face → event → service/resident', '']
        for s in r['services']:
            lines += [f'- Event **{s["event"]}**, {s["title"]}: active entrance faces **{s["active_faces"]}**; label-only faces `{s["label_only_faces"]}`.',
                f'  Source: [out02.lua:{s["line"]}](../../../../assets_dev/worlds/mm8/events/maps/out02.lua#L{s["line"]}). Conditional: {s["conditional"]}; QBits referenced: `{s["qbits"]}`.']
            for h in s['houses']:
                lines.append(f'  House **{h["id"]}**, **{h["type"]}**, {h["name"]}; proprietor field: {h["proprietor"]} ({h["proprietor_title"]}).')
                for n in h['resident_candidates']:
                    lines.append(f'  Initial resident candidate **{n["name"]}** (NPC {n["id"]}); topics: '+', '.join(f'{t["id"]} {t["title"]}' for t in n['topics'])+'.')
            if s['destinations']:lines.append('  Dungeon destinations: '+', '.join(s['destinations'])+'.')
        lines += ['', 'A label-only face identifies a surface/annex; it does not open the house. Separate doors retain separate events.', '',
                  '## Entrance scale', '', '| Native face | Texture | Width × height | Units/texel | UV texel bounds after deltas |', '| --- | --- | --- | --- | --- |']
        for f in r['face_records']:
            if any(f['index'] in s['active_faces'] for s in r['services']):
                d=f['bounds']['size'];width=math.hypot(d[0],d[1])
                lines.append(f'| {f["index"]} | `{f["texture"]}` | {width:g} × {d[2]:g} | {f["edge_units_per_texel_median"]} | `{f["uv_texel_bounds"]}` |')
        lines += ['', '## Texture inventory', '', '| Key | Native bitmap dimensions | Count | Native face IDs |', '| --- | --- | --- | --- |']
        for key,count in sorted(r['materials'].items()):
            f=next(f for f in r['face_records'] if f['texture']==key)
            ids = [f['index'] for f in r['face_records'] if f['texture'] == key]
            lines.append(f'| `{key}` | {f["texture_dimensions"]} | {count} | `{ids}` |')
        lines += ['', 'Use the recorded per-face UV offsets/spans to align facade bands, windows, corners and trim. A shared texture',
                  'key alone does not reproduce its scale or placement. Invisible native faces are excluded from the beauty render;',
                  'the raw records retain them. Automatic camera fitting is per building, so use measured units—not image size—to compare scale.']
        (OUT/'models'/f'{i:03d}.md').write_text('\n'.join(lines)+'\n')
        cards.append(f'<article data-search="{html.escape(str(i)+" "+r["name"]+" "+title+" "+r["family"]+" "+" ".join(n["name"] for s in r["services"] for h in s["houses"] for n in h["resident_candidates"]),quote=True)}"><a href="models/{i:03d}.md"><img loading="lazy" src="images/{i:03d}.png"><h2>{i:03d} · {html.escape(title)}</h2></a><p>{html.escape(r["name"])} · {dims} units</p><p>{html.escape(r["interpretation"])}</p></article>')
    index += ['', '## Whole-establishment views', '']
    for a in catalogue['assembly_views']:
        index += [f'### {a["purpose"]}', '',f'Models `{a["models"]}`; association inferred from physical assembly and face labels.', '',
                  f'![{a["purpose"]}](images/assembly_{a["id"]}.png)', '']
    index += ['## Other native BModels', '', 'These records remain in the JSON with all faces/materials. They have no resolved house/dungeon/transport association.', '',
              '| BModel | Native name | Faces |', '| --- | --- | --- |']
    for r in records:
        if not r['catalogue_building']:index.append(f'| {r["index"]} | `{r["name"]}` | {r["faces"]} |')
    index += ['', '## Reproduce', '', 'Run `python3 level_generation/scripts/catalogue_ravenshore.py`, then the Blender MCP render script',
              '`level_generation/scripts/blender_building_catalogue.py` in batches; rerun the extractor to refresh these pages.',
              'See [visual calibration](../../VISUAL_CALIBRATION.md) for exact usage, screenshot matching and scale guidance.', '', '## Limits', '']
    index += ['- '+v for v in catalogue['limits']]
    (OUT/'README.md').write_text('\n'.join(index)+'\n')
    (OUT/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Ravenshore native building catalogue</title>
<style>body{background:#202329;color:#eee;font:16px system-ui;margin:2rem}a{color:#e5cc96}input{font:inherit;padding:.8rem;width:80%;margin:1rem 0}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:1rem}article{background:#30343b;padding:1rem}img{width:100%;background:#262b33}h2{font-size:1.1rem}p{line-height:1.45}</style>
<h1>Ravenshore: buildings, entrances and services</h1><p>Native textured BModels with original UVs. Search by model ID, resident, service or art family. Images fit each model independently; compare measured dimensions for scale.</p><p><a href="README.md">Full mapping and assemblies</a> · <a href="../../VISUAL_CALIBRATION.md">Generation calibration</a></p><input id="filter" placeholder="Search: Luodrin, temple, bank, 78…" aria-label="Search catalogue"><main>'''+''.join(cards)+'''</main><script>document.querySelector('#filter').addEventListener('input',e=>{const q=e.target.value.toLowerCase();document.querySelectorAll('article').forEach(a=>a.hidden=!a.dataset.search.toLowerCase().includes(q));});</script>''')


if __name__ == '__main__':
    build()
