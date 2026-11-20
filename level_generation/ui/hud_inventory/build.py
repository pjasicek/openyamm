"""Read-only inventory of HUD layouts, related UI screens, and their dynamic asset families.

Run from any directory. Only this catalogue directory is written; no runtime assets are changed.
"""
import collections
import csv
import hashlib
import json
import re
from pathlib import Path

import yaml
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ASSETS = ROOT / 'assets_dev'
EXTENSIONS = {'.png', '.bmp', '.pcx'}
STATES = {'default', 'highlighted', 'pressed', 'selected', 'frame', 'health_bar', 'mana_bar'}


def relative(path):
    return path.relative_to(ROOT).as_posix()


def main():
    by_name = collections.defaultdict(list)
    for directory in [ASSETS / 'engine/icons', *sorted((ASSETS / 'worlds').glob('*/icons'))]:
        for path in sorted(directory.rglob('*')):
            if path.is_file() and path.suffix.lower() in EXTENSIONS:
                by_name[path.stem.lower()].append(path)
    rows = {}
    fonts = collections.defaultdict(list)
    layouts = []
    unknown_states = []

    def add(name, kind, source, line=0, **usage):
        name = str(name).strip()
        if not name or name.lower() in {'none', 'null'}:
            return
        key = name.lower()
        row = rows.setdefault(key, dict(name=name, usages=[]))
        ref = dict(kind=kind, source=relative(source), line=line, **usage)
        if ref not in row['usages']:
            row['usages'].append(ref)

    def walk(node, source, screen, parents=()):
        if isinstance(node, yaml.MappingNode):
            fields = {k.value: v for k, v in node.value}
            element = fields.get('id')
            element = element.value if isinstance(element, yaml.ScalarNode) else ''
            placement = {k: v.value for k, v in fields.items()
                         if k in {'id', 'anchor', 'anchor_space', 'offset_x', 'offset_y', 'width', 'height',
                                  'visible', 'z_index', 'interactive'} and isinstance(v, yaml.ScalarNode)}
            chain = parents + (placement,) if element else parents
            asset = fields.get('asset')
            pairs = asset.value if isinstance(asset, yaml.MappingNode) else []
            if isinstance(asset, yaml.ScalarNode):
                pairs = [(yaml.ScalarNode('tag:yaml.org,2002:str', 'default'), asset)]
            for state, value in pairs:
                if isinstance(value, yaml.ScalarNode):
                    add(value.value, 'yaml', source, value.start_mark.line + 1,
                        screen=screen, element=element, state=state.value, layout_chain=list(chain),
                        logical_size=[fields[k].value if k in fields else None for k in ('width', 'height')])
                    if state.value not in STATES:
                        unknown_states.append(dict(source=relative(source), element=element, state=state.value))
            text = fields.get('text')
            if isinstance(text, yaml.MappingNode):
                for key, value in text.value:
                    if key.value == 'font':
                        fonts[value.value.lower()].append(dict(source=relative(source), element=element,
                                                               line=value.start_mark.line + 1, screen=screen))
            for value in fields.values():
                walk(value, source, screen, chain)
        elif isinstance(node, yaml.SequenceNode):
            for value in node.value:
                walk(value, source, screen, parents)

    ui_roots = [ASSETS / 'engine/ui', *sorted((ASSETS / 'worlds').glob('*/ui'))]
    for source in sorted(p for directory in ui_roots for p in directory.rglob('*.yml')):
        text = source.read_text()
        data = yaml.safe_load(text)
        if not isinstance(data, dict) or 'elements' not in data:
            continue
        screen = data.get('screen', source.stem)
        layouts.append(dict(path=relative(source), screen=screen,
                            sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
        walk(yaml.compose(text), source, screen)

    # Conservative source audit: exact image-name literals are candidates until a use is reviewed.
    # This catches arrays/constants as well as direct loader calls without pretending to parse C++.
    literals = set()
    formats = []
    source_files = sorted(set((ROOT / 'game/ui').rglob('*.cpp')) |
                          set((ROOT / 'game/ui').rglob('*.h')) |
                          set((ROOT / 'game/gameplay').glob('Gameplay*.cpp')) |
                          set((ROOT / 'game/app').glob('*.cpp')) |
                          set((ROOT / 'game/input').glob('*.cpp')))
    font_names = {p.stem.lower() for p in (ASSETS / 'engine/fonts').rglob('*') if p.suffix.lower() == '.fnt'}
    font_names.update({'rudeblack', 'rudered'})
    for source in source_files:
        for number, line in enumerate(source.read_text().splitlines(), 1):
            if line.lstrip().startswith('//'):
                continue
            for name in re.findall(r'"([^"\n]+)"', line):
                literals.add(name.lower())
                stem = Path(name).stem.lower() if Path(name).suffix.lower() in EXTENSIONS else name.lower()
                if Path(name).suffix.lower() in EXTENSIONS and '/' in name:
                    for root in [ASSETS, ASSETS / 'engine', *sorted((ASSETS / 'worlds').glob('*'))]:
                        candidate = root / name
                        if candidate.is_file() and candidate not in by_name[stem]:
                            by_name[stem].append(candidate)
                if stem in by_name:
                    add(stem, 'code_literal_candidate', source, number, requested=name)
                if name.lower() in font_names:
                    fonts[name.lower()].append(dict(source=relative(source), line=number,
                                                    kind='code_font_candidate'))
                if re.fullmatch(r'IRA-[1-4]', name):
                    for match in by_name:
                        if re.fullmatch(re.escape(name.lower()) + r'_\d+', match):
                            add(match, 'journal_animation_family', source, number, prefix=name)
                if re.match(r'^[a-zA-Z][\w-]*%', name) and re.search(r'%0?\d*[du]', name):
                    pattern = re.escape(name.lower())
                    pattern = re.sub(r'%0?(\d*)[du]', lambda m: r'\d{' + m[1] + ',}' if m[1] else r'\d+', pattern)
                    matching = [n for n in by_name if re.fullmatch(pattern, n)]
                    if matching:
                        formats.append(dict(format=name, source=relative(source), line=number, matches=len(matching)))
                        for match in matching:
                            add(match, 'dynamic_format_family', source, number, format=name)

    tables = ASSETS / 'engine/data_tables'
    def table_rows(name):
        candidates = [tables / name, *sorted((ASSETS / 'worlds').glob('*/data_tables/' + name))]
        for source in candidates:
            if source.is_file():
                for number, line in enumerate(source.read_text(errors='replace').splitlines(), 1):
                    yield source, number, line.split('\t')

    # Inventory icons and possible fitted paperdoll variants are data-driven, not layout assets.
    item_names = set()
    for source, number, fields in table_rows('items.txt'):
        if len(fields) > 1 and fields[0].strip().isdigit() and fields[1].strip():
            name = fields[1].strip().lower()
            item_names.add(name)
            add(name, 'item_table', source, number, item_id=fields[0].strip())
    for name in sorted(by_name):
        match = re.fullmatch(r'(.+)v([1-5])a?', name)
        if match and match[1] in item_names:
            add(name, 'equipment_variant_family', ROOT / 'game/gameplay/GameplayScreenRuntime.cpp',
                base_icon=match[1], note='Existing variant candidate; selected by slot, doll type and hand pose.')

    for source, number, fields in table_rows('character_data.txt'):
        if len(fields) < 20 or not fields[0].isdigit():
            continue
        for index in [8, 9, 10, 11, 12, 13, 14, 17, 18]:
            add(fields[index], 'paperdoll_table', source, number, character_id=fields[0], column=index)
        prefix = fields[19].strip().lower()
        if prefix:
            for name in by_name:
                if name.startswith(prefix) and name[len(prefix):].isdigit():
                    add(name, 'portrait_table_family', source, number, character_id=fields[0], prefix=prefix)

    animation_names = literals | {'turn0', 'turn1', 'turn2', 'turn3', 'turn4'}
    for source, number, fields in table_rows('portrait_fx_events.txt'):
        if len(fields) >= 3 and fields[0] != 'Kind' and not fields[0].startswith('//'):
            animation_names.add(fields[2].strip().lower())
    animation = ''
    for source, number, fields in table_rows('icon_frame_data.txt'):
        if len(fields) < 5 or fields[0].startswith('//') or fields[0] == 'AnimationName':
            continue
        animation = fields[0].strip().lower() or animation
        if animation in animation_names:
            add(fields[1], 'hud_animation_table', source, number, animation=animation)

    # Exact table tokens cover maps, chest backgrounds and portal destinations. Keep candidate status,
    # because a static token match alone cannot prove that every row is reachable in a mounted world.
    for table in ['town_portal_switch.txt', 'continent_settings.txt', 'chest_data.txt',
                  'map_stats.txt', 'monster_portraits.txt']:
        for source, number, fields in table_rows(table):
            for value in fields:
                value = value.strip()
                if value.lower() in by_name:
                    add(value, 'presentation_table_candidate', source, number, table=table)

    for name in by_name:
        if re.fullmatch(r'(mapdir|micon)\d+', name):
            add(name, 'minimap_symbol_family', ROOT / 'game/ui/GameplayHudCommon.cpp',
                note='Family identified by HUD transparency rules; candidate coverage.')

    # The map journal/minimap also consumes authored world PCX images outside icons/.
    for catalog in sorted((ASSETS / 'worlds').glob('*/ui/maps/catalog.yml')):
        document = yaml.safe_load(catalog.read_text())
        world_root = catalog.parents[2]
        for map_entry in document.get('maps', []):
            for variant in map_entry.get('variants', []):
                path = world_root / variant['texture']
                if not path.is_file():
                    raise FileNotFoundError(path)
                key = path.stem.lower()
                if path not in by_name[key]:
                    by_name[key].append(path)
                add(key, 'map_presentation_catalog', catalog, map=map_entry['map'],
                    requested=variant['texture'], declared_size=[variant['width'], variant['height']],
                    world_bounds=map_entry.get('world_bounds'), flip_u=map_entry.get('flip_u', False),
                    flip_v=map_entry.get('flip_v', False), minimum_z=variant.get('minimum_z'),
                    maximum_z=variant.get('maximum_z'))

    previews = HERE / 'previews'
    previews.mkdir(exist_ok=True)
    file_cache = {}
    def file_info(path):
        if path in file_cache:
            return file_cache[path]
        payload = path.read_bytes()
        sha = hashlib.sha256(payload).hexdigest()
        info = dict(path=relative(path), bytes=len(payload), sha256=sha)
        try:
            with Image.open(path) as im:
                info.update(size=list(im.size), x2_size=[im.width * 2, im.height * 2], mode=im.mode)
                # Decode the original palette without repainting or applying guessed transparency.
                preview = previews / (sha + '.png')
                if not preview.exists():
                    im = im.convert('RGBA')
                    im.thumbnail((192, 144), Image.Resampling.NEAREST)
                    im.save(preview)
                info['preview'] = 'previews/' + preview.name
        except (OSError, ValueError) as error:
            info['decode_error'] = str(error)
        file_cache[path] = info
        return info

    for key, row in sorted(rows.items()):
        paths = sorted(by_name.get(key, []), key=lambda p: (
            'worlds' in p.parts, ['.png', '.bmp', '.pcx'].index(p.suffix.lower()), relative(p)))
        row['files'] = [file_info(p) for p in paths]
        row['tier_variants'] = []
        for path in paths:
            for tier in ('x2', 'x4'):
                folder = path.parent.with_name(path.parent.name + '_' + tier)
                for ext in ('.png', '.bmp', '.pcx'):
                    variant = folder / (path.stem + ext)
                    if variant.is_file():
                        row['tier_variants'].append(dict(path=relative(variant), tier=tier))
        row['status'] = 'resolved' if paths else ('generated' if key == 'minimap' else 'missing')
        row['groups'] = sorted({ref['kind'] for ref in row['usages']})
        row['screens'] = sorted({ref['screen'] for ref in row['usages'] if 'screen' in ref})
        row['yaml_uses'] = sum(ref['kind'] == 'yaml' for ref in row['usages'])

    font_records = []
    for name, usages in sorted(fonts.items()):
        paths = [p for p in (ASSETS / 'engine/fonts').rglob('*')
                 if p.is_file() and (p.stem.lower() == name or p.name.lower().startswith('openyamm_' + name + '_'))]
        paths += [p for directory in ui_roots for p in directory.rglob('*.pcx') if p.stem.lower() == name]
        font_records.append(dict(name=name, usages=usages, files=[relative(p) for p in sorted(paths)],
                                 treatment='Use the existing faithful font pipeline; do not imagegen glyph sheets.'))

    assets = sorted(rows.values(), key=lambda row: row['name'].lower())
    direct = [row for row in assets if row['yaml_uses']]
    summary = dict(layout_files=len(layouts), yaml_uses=sum(row['yaml_uses'] for row in direct),
                   yaml_asset_names=len(direct), yaml_resolved=sum(row['status'] == 'resolved' for row in direct),
                   core_hud_names=sum(any(u['source'].endswith(('/gameplay.yml', '/gameplay_mobile.yml'))
                                          for u in row['usages']) for row in direct),
                   yaml_generated=[row['name'] for row in direct if row['status'] == 'generated'],
                   yaml_missing=[row['name'] for row in direct if row['status'] == 'missing'],
                   total_names_including_dynamic_candidates=len(assets), distinct_source_files=len(file_cache),
                   unique_source_hashes=len({info['sha256'] for info in file_cache.values()}),
                   font_names=len(font_records), unknown_yaml_states=unknown_states,
                   groups=dict(collections.Counter(g for row in assets for g in row['groups'])),
                   limits='Complete asset/state extraction for the checked-in engine and world UI YAMLs. Dynamic families and '
                          'code/table candidates are a conservative static audit, not proof of runtime reachability '
                          'or exhaustive coverage of custom content, mods, generated graphics or world overrides.')
    generated = [
        dict(name='MINIMAP', source='game/ui/GameplayUiRenderer.cpp',
             treatment='Rendered map content; restore the frame/buttons and symbol artwork, not one baked screenshot.'),
        dict(name='Save / Lloyd beacon thumbnails', source='game/ui/GameplayUiRuntime.cpp',
             treatment='Runtime scene captures; restore surrounding layouts.'),
        dict(name='Counters, labels, hover text', source='game/ui/GameplayHudCommon.cpp',
             treatment='Font/text rendering. Existing faithful TrueType fonts are inventoried separately.'),
        dict(name='Solid mobile controls / tint variants', source='game/ui/GameplayUiRuntime.cpp',
             treatment='Procedural quads and tinted copies; no separate source image per colour.'),
        dict(name='Actor inspection and house movies', source='game/ui/GameplayDialogueRenderer.cpp',
             treatment='World monster sprites and house videos are dependencies, not shared HUD skin bitmaps.')]
    result = dict(summary=summary, layouts=layouts, assets=assets, fonts=font_records, formats=formats,
                  generated_and_external=generated)
    (HERE / 'inventory.json').write_text(json.dumps(result, indent=2) + '\n')
    (HERE / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    with (HERE / 'assets.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['name', 'status', 'groups', 'screens', 'yaml_uses', 'source_paths', 'native_sizes', 'x2_sizes'])
        for row in assets:
            writer.writerow([row['name'], row['status'], ';'.join(row['groups']), ';'.join(row['screens']),
                             row['yaml_uses'], ';'.join(f['path'] for f in row['files']),
                             ';'.join(str(f.get('size')) for f in row['files']),
                             ';'.join(str(f.get('x2_size')) for f in row['files'])])
    write_html(result)
    print(json.dumps(summary, indent=2))


def write_html(result):
    data = json.dumps(result).replace('</', '<\\/')
    template = '''<!doctype html><html lang="en"><meta charset="utf-8">
<title>Shared HUD asset inventory</title><style>
body{margin:0;background:#161c20;color:#e7e4da;font:15px system-ui}header{padding:24px;background:#222c32}
h1{margin:0 0 10px}p{max-width:1000px;line-height:1.5}input,select{padding:9px;margin:5px;background:#faf6ec}
main{padding:20px;display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
article{background:#253138;padding:16px;overflow-wrap:anywhere}img{max-width:192px;max-height:144px;object-fit:contain}
.preview{height:154px;display:flex;align-items:center;justify-content:center;background:#11181c}
small{color:#bfcec8}a{color:#9ed7de}details{margin-top:10px}li{margin:7px 0}.missing{color:#ffc28e}
button{padding:10px;margin:20px}footer{padding:20px}
</style><header><h1>Shared MM8-style HUD · asset inventory</h1>
<p id="summary"></p><p>Default view: named assets from every shared UI YAML, including standard, expanded,
mobile and overlay screens. Dynamic families and source candidates are separately labelled. Previews retain
native palette colours, including transparency keys. This is an inventory, not restored artwork.</p>
<input id="q" placeholder="Search asset, element or source" size="35"><select id="screen"><option value="">All screens</option></select>
<select id="scope"><option value="yaml">YAML assets</option><option value="hud">Gameplay HUD only</option><option value="all">All inventoried names</option>
<option value="dynamic">Dynamic / code / table only</option><option value="missing">Missing files</option></select>
<span id="count"></span><p><a href="README.md">Coverage and use</a> · <a href="GOAL.md">Restoration goal</a> ·
<a href="scope.csv">Whole-folder census</a> · <a href="assets.csv">Usage CSV</a> ·
<a href="inventory.json">Full inventory and source lines</a></p></header><main></main>
<button id="more">Show next 100</button><footer>Generated offline by build.py. No runtime assets changed.</footer>
<script>const data=DATA;const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const $=s=>document.querySelector(s);let limit=100;
$('#summary').textContent=`${data.summary.layout_files} layouts · ${data.summary.yaml_asset_names} YAML asset names · ${data.summary.total_names_including_dynamic_candidates} names including dynamic families/candidates · ${data.summary.font_names} font names`;
for(const s of [...new Set(data.assets.flatMap(a=>a.screens))].sort())$('#screen').add(new Option(s,s));
function render(){const q=$('#q').value.toLowerCase(),scope=$('#scope').value,screen=$('#screen').value;
const matches=data.assets.filter(a=>(!q||JSON.stringify(a).toLowerCase().includes(q))&&(!screen||a.screens.includes(screen))&&
(scope==='all'||scope==='yaml'&&a.yaml_uses||scope==='hud'&&a.usages.some(u=>/\\/(gameplay|gameplay_mobile)\\.yml$/.test(u.source))||scope==='dynamic'&&!a.yaml_uses||scope==='missing'&&a.status==='missing'));
$('#count').textContent=` ${matches.length} matches`;$('#more').hidden=matches.length<=limit;
$('main').innerHTML=matches.slice(0,limit).map(a=>{const f=a.files[0];return `<article><div class="preview">${f&&f.preview?`<img loading="lazy" style="width:${Math.min(192,f.size[0]*2)}px;height:${Math.min(144,f.size[1]*2)}px;image-rendering:pixelated" src="${esc(f.preview)}" alt="${esc(a.name)}">`:`<span class="missing">${esc(a.status)}</span>`}</div>
<h3>${esc(a.name)}</h3><small>${esc(a.groups.join(' · '))}</small><p>${f?esc(f.size+' → '+f.x2_size+' at x2'):'No source bitmap'}<br>${esc(a.screens.join(', '))}</p>
<details><summary>${a.usages.length} references · ${a.files.length} source files</summary><ul>${a.files.map(f=>`<li><a href="../../../${esc(f.path)}">${esc(f.path)}</a></li>`).join('')}
${a.usages.map(u=>`<li>${esc(u.source)}:${u.line||''}<br>${esc([u.element,u.state,u.animation,u.format,u.note].filter(Boolean).join(' · '))}</li>`).join('')}</ul></details></article>`}).join('');}
for(const s of ['#q','#scope','#screen'])$(s).addEventListener('input',()=>{limit=100;render()});
$('#more').onclick=()=>{limit+=100;render()};render();</script></html>'''
    (HERE / 'index.html').write_text(template.replace('DATA', data))


if __name__ == '__main__':
    main()
