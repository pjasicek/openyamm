#!/usr/bin/env python3
"""Read-only asset audit; writes inventory/review artifacts beside this script.

Run with Python 3.10+ and Pillow from any directory. No generation or installation.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "util"))
from map_export import parse_blv_file, parse_odm_file

WORLDS = ("mm6", "mm7", "mm8")
SKY = re.compile(r"^(?:[67]?plansky\d+|[67]?sky\w*|testsky\d+|sgstars|cloudsabove|sunsetclouds|stormclds)$")


def rel(path):
    return path.relative_to(ROOT).as_posix()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def table(name):
    return list(csv.reader((ROOT / 'assets_dev/engine/data_tables' / name).read_text().splitlines(), delimiter='\t'))


def main():
    map_stats = {r[2].lower(): r for r in table('map_stats.txt') if r and r[0].isdigit()}
    bolster = {int(r[0]): r for r in table('bolster_maps.txt') if r and r[0].isdigit()}
    continents = {int(r[0]): [s.strip().lower() for s in r[21].split(',')]
                  for r in table('continent_settings.txt') if r and r[0].isdigit()}
    source_paths = sorted(p for world in (*WORLDS, 'mmmerge')
                          for p in (ROOT / 'assets_dev/worlds' / world / 'textures').glob('*')
                          if p.suffix.lower() in ('.bmp', '.png') and SKY.fullmatch(p.stem.lower()))
    sky_names = {p.stem.lower() for p in source_paths}
    uses = defaultdict(list)
    maps = []
    errors = []
    counts = Counter()
    extras = set()
    # Include IndoorSky faces even when the texture's name does not contain 'sky'.
    for world in WORLDS:
        for path in sorted((ROOT / 'assets_dev/worlds' / world / 'maps').iterdir()):
            if path.suffix.lower() not in ('.odm', '.blv'):
                continue
            counts[world + path.suffix.lower()] += 1
            try:
                data = (parse_odm_file(path) if path.suffix.lower() == '.odm' else parse_blv_file(path))['payload']
            except Exception as exc:
                errors.append({'path': rel(path), 'error': str(exc)})
                continue
            stat = map_stats.get(path.name.lower(), [])
            row = {'world': world, 'file': path.name, 'name': stat[1] if stat else path.stem,
                   'id': int(stat[0]) if stat else None, 'path': rel(path)}
            if path.suffix.lower() == '.odm':
                row['native_header_sky'] = data['sky_texture'].lower()
                b = bolster.get(row['id'], [])
                row['continent'] = int(b[2]) if b and b[2].isdigit() else None
                row['weather_enabled'] = b[6] if len(b) > 6 else None
                row['custom_sky'] = b[9].lower() if len(b) > 9 else ''
                row['weather_skies'] = continents.get(row['continent'], [])
                # Raw native headers are recorded separately: merged weather supersedes these.
                for name in row['weather_skies']:
                    uses[name].append({'kind': 'weather_table', 'world': world, 'map': path.name})
                for field, kind in [('custom_sky', 'custom_sky'), ('native_header_sky', 'native_header')]:
                    if row[field]:
                        uses[row[field]].append({'kind': kind, 'world': world, 'map': path.name})
                faces = [face for model in data['bmodels'] for face in model.get('faces', [])]
            else:
                faces = data['faces']
            face_uses = Counter()
            for face in faces:
                name = face['texture_name'].lower()
                indoor_sky = path.suffix.lower() == '.blv' and bool(face['attributes'] & 0x00400000)
                if name and (indoor_sky or name in sky_names):
                    kind = 'indoor_sky_face' if indoor_sky else 'sky_named_surface'
                    face_uses[(name, kind)] += 1
                    extras.add(name)
            row['sky_surfaces'] = [{'texture': n, 'kind': k, 'faces': c} for (n, k), c in sorted(face_uses.items())]
            for use in row['sky_surfaces']:
                uses[use['texture']].append({'kind': use['kind'], 'world': world, 'map': path.name,
                                            'faces': use['faces']})
            if path.suffix.lower() == '.odm' or row['sky_surfaces']:
                maps.append(row)
    events = []
    for world in WORLDS:
        for path in sorted((ROOT / 'assets_dev/worlds' / world / 'events').rglob('*.lua')):
            for number, line in enumerate(path.read_text(errors='replace').splitlines(), 1):
                for match in re.finditer(r'evt\.(SetOutdoorSky|SetTexture)\([^\n]*?"([^"\n]+)"', line):
                    method, name = match.groups()
                    name = name.lower()
                    if method == 'SetOutdoorSky' or name in sky_names:
                        event = {'kind': method, 'world': world, 'path': rel(path), 'line': number, 'texture': name}
                        events.append(event)
                        uses[name].append(event)
                        extras.add(name)
    scenes = []
    for world in WORLDS:
        for path in sorted((ROOT / 'assets_dev/worlds' / world / 'maps').glob('*.scene.yml')):
            for match in re.finditer(r'^\s*sky_texture:\s*"([^"\n]+)"', path.read_text(), re.M):
                name = match[1].lower()
                scenes.append({'world': world, 'path': rel(path), 'texture': name})
                uses[name].append({'kind': 'scene_sky', 'world': world, 'path': rel(path)})
                extras.add(name)
    for world in (*WORLDS, 'mmmerge'):
        for p in (ROOT / 'assets_dev/worlds' / world / 'textures').glob('*'):
            if p.stem.lower() in extras and p.suffix.lower() in ('.png', '.bmp') and p not in source_paths:
                source_paths.append(p)
    # Legacy time-of-day runtime path, used when no merged weather profile applies.
    for name in ('plansky1', 'plansky3', 'sky01', 'sky05', 'sky6pm', 'sunsetclouds'):
        uses[name].append({'kind': 'runtime_fallback', 'world': 'all'})
    records = []
    (OUT / 'thumbnails').mkdir(exist_ok=True)
    for path in sorted(source_paths):
        world, name = path.parts[-3], path.stem.lower()
        with Image.open(path) as original:
            rgb = original.convert('RGB')
            w, h = rgb.size
            pixel_sha = sha(f'{w}x{h}:RGB:'.encode() + rgb.tobytes())
            preview = rgb.copy()
            preview.thumbnail((160, 160))
            thumb = OUT / 'thumbnails' / f'{world}_{name}.png'
            preview.save(thumb)
        target = ROOT / 'assets_dev/worlds' / world / 'textures_x2' / (name + '.png')
        installed = None
        if target.exists():
            with Image.open(target) as img:
                installed = {'path': rel(target), 'size': list(img.size), 'sha256': sha(target.read_bytes())}
        record = {'world': world, 'name': name, 'source': rel(path), 'native_size': [w, h],
                  'x2_size': [w * 2, h * 2], 'source_sha256': sha(path.read_bytes()), 'rgb_sha256': pixel_sha,
                  'target': rel(target), 'installed': installed, 'uses_by_name': uses[name],
                  'thumbnail': rel(thumb)}
        records.append(record)
    groups = defaultdict(list)
    for row in records:
        groups[row['rgb_sha256']].append(row['source'])
    summary = {'native_files_by_world': dict(Counter(r['world'] for r in records)),
               'unique_rgb_images': len(groups), 'distinct_names': len({r['name'] for r in records}),
               'maps_scanned': dict(sorted(counts.items())), 'maps_with_sky_surfaces': sum(bool(m['sky_surfaces']) for m in maps),
               'installed_files': [r['installed'] for r in records if r['installed']],
               'scan_errors': errors}
    # The accepted MM6 alias has no same-name native source in MM6; report it explicitly.
    alias = ROOT / 'assets_dev/worlds/mm6/textures_x2/plansky1.png'
    summary['accepted_mm6_alias'] = {'path': rel(alias), 'sha256': sha(alias.read_bytes())} if alias.exists() else None
    inventory = {'scope': 'Development MM6/MM7/MM8 maps and sky art; mmmerge duplicate sources included. '
                         'uses_by_name records references, not proof of selected source at runtime. '
                         'Native map headers may be overridden by merged weather. No saves/mods/packages scanned.',
                 'summary': summary, 'continent_skies': continents, 'assets': records,
                 'pixel_duplicate_groups': [v for v in groups.values() if len(v) > 1],
                 'maps': maps, 'events': events, 'nonempty_scene_skies': scenes}
    # Explicit source-to-destination plan: native ownership plus world-local outdoor closure.
    ancillary = {'orair256', '7solid01'}
    weather_names = set().union(*(continents[i] for i in (1, 2, 3))) | {'sunsetclouds'}
    legacy_names = {'plansky1', 'plansky3', 'sky01', 'sky05', 'sky6pm', 'sunsetclouds'}
    sky_records = [r for r in records if r['world'] != 'mmmerge' and r['name'] not in ancillary]
    by_name = {r['name']: r for r in sky_records}
    installs = {r['target']: {'source': r['source'], 'target': r['target'], 'size': r['x2_size'],
                             'reason': 'native owner'} for r in sky_records}
    for world, continent in [('mm6', 3), ('mm7', 2), ('mm8', 1)]:
        names = set(continents[continent]) | legacy_names
        names.update(m['custom_sky'] for m in maps
                     if m['world'] == world and m.get('custom_sky'))
        names.update(e['texture'] for e in events
                     if e['world'] == world and e['kind'] == 'SetOutdoorSky')
        for name in sorted(names):
            r = by_name[name]
            target = f'assets_dev/worlds/{world}/textures_x2/{name}.png'
            installs[target] = {'source': r['source'], 'target': target, 'size': r['x2_size'],
                                'reason': 'world-local outdoor weather/custom/event/fallback closure'}
    jobs = []
    for pixel_sha, paths in groups.items():
        rows = [r for r in sky_records if r['rgb_sha256'] == pixel_sha]
        if not rows:
            continue
        names = {r['name'] for r in rows}
        wave = ('A0: MM6 native fair-weather baseline' if '6plansky1' in names else
                'A: outdoor weather/custom' if names & weather_names else
                'B: legacy outdoor fallback' if names & legacy_names else
                'C: additional map/event artwork' if any(r['uses_by_name'] for r in rows) else 'D: native archive')
        accepted = 'plansky1' in names
        jobs.append({'source': rows[0]['source'], 'pixel_sha256': pixel_sha,
                     'equivalent_sources': paths, 'wave': wave,
                     'status': 'accepted MM8-palette artwork; not an authentic MM6 baseline' if accepted else 'pending review/restoration',
                     'destinations': [v for v in installs.values() if v['source'] in paths]})
        project = OUT.parent / rows[0]['world'] / rows[0]['name']
        manifest_path = project / 'manifest.json'
        if manifest_path.exists():
            restored_manifest = json.loads(manifest_path.read_text())
            selected_export = project / restored_manifest['selected_export']
            assert sha(selected_export.read_bytes()) == restored_manifest['runtime_sha256']
            jobs[-1].update({'status': restored_manifest['status'], 'project_manifest': rel(manifest_path),
                             'selected_export': rel(selected_export),
                             'runtime_sha256': restored_manifest['runtime_sha256']})
    inventory['restoration_jobs'] = sorted(jobs, key=lambda j: (j['wave'], j['source']))
    inventory['summary']['sky_art_files_mm6_mm8'] = len(sky_records)
    inventory['summary']['sky_art_jobs_by_wave'] = dict(Counter(j['wave'] for j in jobs))
    inventory['summary']['planned_sky_install_paths'] = len(installs)
    (OUT / 'install_plan.json').write_text(json.dumps({'status': 'PROVISIONAL: native lists corrected and user-confirmed; restored-art acceptance and runtime tier checks pending',
                                                    'entries': sorted(installs.values(), key=lambda v: v['target'])}, indent=2) + '\n')
    md = ['# MM6–MM8 sky inventory', '', 'Generated by `build_inventory.py`; see the adjacent restoration plan for acceptance and rollout.', '',
          '## Native assets', '', '| World | Texture | Native → x2 | Reference kinds | Existing x2 |',
          '| --- | --- | --- | --- | --- |']
    for r in records:
        kinds = ', '.join(sorted({u['kind'] for u in r['uses_by_name']})) or 'No reference found'
        size = ' × '.join(map(str, r['native_size'])) + ' → ' + ' × '.join(map(str, r['x2_size']))
        md.append(f"| {r['world']} | `{r['name']}` | {size} | {kinds} | {'Present; review provenance' if r['installed'] else 'Missing'} |")
    md += ['', 'The accepted MM6 `plansky1` alias is recorded separately in inventory.json; its native source is MM8.', '',
           '## Outdoor map coverage', '', '| World | Map | Name | Weather list | Custom sky |', '| --- | --- | --- | --- | --- |']
    for m in maps:
        if m['file'].lower().endswith('.odm'):
            md.append(f"| {m['world']} | `{m['file']}` | {m['name']} | {m['continent']} | {m['custom_sky'] or '—'} |")
    md += ['', 'Weather lists: 1 = Jadam, 2 = Antagarich, 3 = Enroth. Custom sky takes precedence over the list.', '',
           '## Sky art on map surfaces', '', '| World | Map | Name | Texture / face count |', '| --- | --- | --- | --- |']
    for m in maps:
        if m['sky_surfaces']:
            detail = ', '.join(f"{u['texture']} ({u['faces']}; {u['kind']})" for u in m['sky_surfaces'])
            md.append(f"| {m['world']} | `{m['file']}` | {m['name']} | {detail} |")
    (OUT / 'INVENTORY.md').write_text('\n'.join(md) + '\n')
    (OUT / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    with (OUT / 'inventory.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['world', 'name', 'native_size', 'x2_size', 'source', 'source_sha256', 'rgb_sha256', 'target', 'usage_kinds'])
        for r in records:
            writer.writerow([r['world'], r['name'], 'x'.join(map(str, r['native_size'])),
                             'x'.join(map(str, r['x2_size'])), r['source'], r['source_sha256'], r['rgb_sha256'],
                             r['target'], ', '.join(sorted({u['kind'] for u in r['uses_by_name']}))])
    parts = ['<!doctype html><meta charset="utf-8"><title>MM6–MM8 sky inventory</title>',
             '<style>body{background:#20232a;color:#eee;font:16px system-ui;margin:24px}a{color:#9dd2ff}'
             '.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px}'
             'article{background:#303641;padding:12px}img{width:160px;height:160px;object-fit:contain}'
             'small{display:block;overflow-wrap:anywhere}h2{margin-top:36px}</style>',
             '<h1>MM6–MM8 native sky inventory</h1><p>Native previews, not generated restorations. '
             'Name references include weather, native headers and surfaces; see the plan for lookup precedence.</p>',
             '<p><a href="../MM6_MM8_SKY_RESTORATION_PLAN.md">Restoration plan</a> · '
             '<a href="inventory.json">Full map/use/hash inventory</a> · <a href="inventory.csv">CSV</a></p>']
    for world in (*WORLDS, 'mmmerge'):
        parts.append(f'<h2>{world}</h2><div class="grid">')
        world_rows = [r for r in records if r['world'] == world]
        contact = Image.new('RGB', (5 * 200, ((len(world_rows) + 4) // 5) * 210), '#20232a')
        draw = ImageDraw.Draw(contact)
        for i, r in enumerate(world_rows):
            usage = ', '.join(sorted({u['kind'] for u in r['uses_by_name']})) or 'No reference found; archive candidate'
            parts.append(f'<article><strong>{r["name"]}</strong><br><img src="thumbnails/{world}_{r["name"]}.png">'
                         f'<small>{r["native_size"]} → {r["x2_size"]}<br>{html.escape(usage)}</small></article>')
            with Image.open(ROOT / r['thumbnail']) as thumb:
                x, y = (i % 5) * 200, (i // 5) * 210
                contact.paste(thumb, (x + 20, y + 5))
                draw.text((x + 5, y + 168), r['name'], fill='white')
                draw.text((x + 5, y + 184), 'x'.join(map(str, r['native_size'])), fill='white')
        contact.save(OUT / f'{world}_contact_sheet.png')
        parts.append('</div>')
    (OUT / 'index.html').write_text('\n'.join(parts) + '\n')
    print(json.dumps(summary, indent=2))
    print('Duplicate groups:', json.dumps(inventory['pixel_duplicate_groups']))
    print('Sky surface maps:', json.dumps([{k: m[k] for k in ('world', 'file', 'name', 'sky_surfaces')}
                                          for m in maps if m['sky_surfaces']], indent=2))
    if errors:
        raise SystemExit('Map parse errors: inventory is incomplete.')


if __name__ == '__main__':
    main()
