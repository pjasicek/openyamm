"""Prepare exact prompts, paletted references and a complete offline restoration queue. No AI calls."""
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import re

import numpy as np
from PIL import Image, ImageDraw
import yaml

from policy import COMMON, PROFILES, SOLID_EFFECT_IDS, SOFT_DECORATION_IDS, WATER_GROUPS, UI_HINTS

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BASE = REPO / 'assets_dev'
SORPIGAL = HERE.parents[1] / 'decorations/mm6_new_sorpigal'
TRIAL = HERE.parent / 'concurrency_trial_10'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return str(path.relative_to(REPO))


def resolve(frame, octant):
    """Stored view plus mirror flag; matches current SpriteTables.cpp resolution semantics."""
    name = frame['texture_name'].lower()
    flags = frame.get('flags', [])
    mirrored = f'Mirror{octant}' in flags
    if 'Image1' in flags:
        return name, mirrored
    if 'Fidget' in flags:
        if octant in (3, 4, 5):
            return name[:-3] + ('sta4' if octant == 4 else 'sta3'), mirrored
        source = 2 if octant in (2, 6) else (0 if octant == 0 else 1)
    elif 'Images3' in flags:
        source = 4 if octant in (3, 4, 5) else (2 if octant in (2, 6) else 0)
    else:
        source = 8 - octant if octant and mirrored else octant
    return name if name.endswith('0') else name + str(source), mirrored


def palette_paths(number):
    paths = [BASE / f'worlds/{world}/textures/pal{number:03d}.act' for world in ('mm6', 'mm7', 'mm8')]
    paths.append(BASE / f'engine/textures/pal{number:03d}.act')
    return [p for p in paths if p.exists()]


def native_image(path, number):
    image = Image.open(path)
    assert image.mode == 'P', (path, image.mode)
    paths = palette_paths(number) if number > 0 else []
    hashes = {hashlib.sha256(p.read_bytes()[:768]).hexdigest() for p in paths}
    if len(hashes) > 1:
        raise ValueError(f'World-dependent palette {number}: add explicit world jobs before continuing')
    if paths:
        image.putpalette(paths[0].read_bytes()[:768])
    rgba = image.convert('RGBA')
    rgba.putalpha(image.point(lambda index: 255 if index else 0, 'L'))
    # Palette index zero is native transparency. Hidden RGB must not defeat visual deduplication.
    pixels = np.array(rgba)
    pixels[pixels[:, :, 3] == 0, :3] = 0
    rgba = Image.fromarray(pixels)
    return rgba, [dict(path=relative(p), sha256=sha(p)) for p in paths]


def choose_profile(group, hints):
    name = group['name']
    if name in ('rain', 'snow'):
        return 'weather'
    if group['category'] == 'interface_overlays':
        return 'ui'
    if group['sprite_id'] in SOFT_DECORATION_IDS:
        return 'soft_fx'
    if name in WATER_GROUPS:
        return 'water_prop'
    if group['category'] == 'effects_projectiles_other':
        return 'solid' if group['sprite_id'] in SOLID_EFFECT_IDS else 'soft_fx'
    text = (' '.join(hints) + ' ' + name).lower()
    if any(word in text for word in ('tree', 'plant', 'flower', 'bush', 'cactus', 'fern', 'grass',
                                      'seaweed', 'coral', 'leaf', 'leaves', 'weed', 'lily')):
        return 'foliage'
    return 'animated_prop' if group['animated'] else 'solid'


def matte_for(images, force_magenta=False):
    """Choose the least-conflicting key using actual foreground, never the embedded key index."""
    counts = [0, 0, 0]
    total = 0
    for image in images:
        pixels = np.array(image)
        rgb = pixels[pixels[:, :, 3] > 0, :3].astype(int)
        if not len(rgb):
            continue
        r, g, b = rgb.T
        counts[0] += int(np.sum(np.minimum(r, b) - g > 8))
        counts[1] += int(np.sum(np.minimum(g, b) - r > 8))
        counts[2] += int(np.sum(np.minimum(r, g) - b > 8))
        total += len(rgb)
    selected = 0 if force_magenta else min(range(3), key=lambda i: counts[i])
    return [[255, 0, 255], [0, 255, 255], [255, 255, 0]][selected], counts[selected] / max(total, 1)


def prepare_reference(job, sources):
    images = [Image.open(HERE / sources[key]['native']) for key in job['assets']]
    count = len(images)
    cols = math.ceil(math.sqrt(count))
    rows = math.ceil(count / cols)
    cell_size = 1024 if count == 1 else 640
    w, h = max(im.width for im in images), max(im.height for im in images)
    factor = cell_size * .78 / max(w, h)
    matte, collision = matte_for(images, force_magenta=True)
    sheet = Image.new('RGBA', (cols * cell_size, rows * cell_size), (*matte, 255))
    cells = []
    for i, (key, im) in enumerate(zip(job['assets'], images)):
        x, y = i % cols * cell_size, i // cols * cell_size
        # One scale throughout the sheet. Full native canvases align at their shared center/bottom.
        new_size = (max(1, round(im.width * factor)), max(1, round(im.height * factor)))
        px = x + round((cell_size - new_size[0]) / 2)
        py = y + round((cell_size - new_size[1]) / 2) if job['alignment'] == 'center' else (
            y + round(cell_size * .90) - new_size[1])
        sheet.alpha_composite(im.resize(new_size, Image.Resampling.NEAREST), (px, py))
        cells.append(dict(asset=key, cell=[x, y, x + cell_size, y + cell_size],
                          native_rectangle=[px, py, px + new_size[0], py + new_size[1]],
                          native_size=list(im.size), native_bounds=list(sources[key]['native_bounds'])))
    path = HERE / 'references' / (job['id'] + '.png')
    sheet.convert('RGB').save(path)
    job.update(reference=relative(path), sheet_size=list(sheet.size), grid=[cols, rows],
               cells=cells, matte_rgb=matte, matte_collision_fraction=collision,
               reference_sha256=sha(path),
               cleanup_route='delivered_alpha_or_companion_mask' if collision > .015 else 'alpha_or_chroma',
               reference_pixels_per_native_pixel=factor)
    return job


def prompt_for(job, sources):
    cols, rows = job['grid']
    names = [sources[key]['aliases'][0]['name'] for key in job['assets']]
    text = COMMON + '\nAsset identity: ' + job['label'] + '.\n'
    text += PROFILES[job['profile']]['direction'] + '\n'
    text += (f'Layout: {cols} equal columns by {rows} equal rows; output aspect ratio '
             f'{job["sheet_size"][0]}:{job["sheet_size"][1]}. '
             f'{len(names)} occupied cells, in row-major order: {", ".join(names)}. '
             'All remaining cells stay empty. Keep exact cell-relative source placement, common scale, '
             'native anchor and margins. Do not individually center, enlarge or shrink poses. '
             'Do not draw grid lines. Request the highest available resolution, ideally at least '
             f'{job["sheet_size"][0]} by {job["sheet_size"][1]} pixels.\n')
    if job['timeline_frames'] > 1:
        text += ('Cells show DISTINCT source drawings in native timeline order, not new in-between frames. '
                 'Repeated native drawings are reused by metadata; do not add copies or new poses. '
                 'Preserve motion extent, not just object identity.\n')
    if job.get('depends_on'):
        text += ('Additional references are previously accepted sheets of this SAME source family, for material '
                 'and detail consistency only. The FIRST reference remains authoritative for poses, colors '
                 'and layout; do not copy the other sheets\' layout.\n')
    from policy import PLACEMENT, BACKGROUND
    return text + '\n' + PLACEMENT + '\n' + BACKGROUND



def build():
    inventory_path = HERE.parent / 'inventory.json'
    inventory = read(inventory_path)
    files = {f['name']: f for f in inventory['files'] if f['classification'] == 'referenced_non_creature'}
    frame_path = BASE / 'engine/rendering/sprite_frame_data_common.yml'
    frames = {g['sprite_id']: g for g in yaml.load(frame_path.read_text(), Loader=yaml.CSafeLoader)['sprites']}
    hints = defaultdict(list)
    for row in csv.reader((BASE / 'engine/data_tables/decoration_data.txt').open(), delimiter='\t'):
        if row and row[0].isdigit():
            hints[int(row[12])].append(row[1] + ': ' + row[2])
    for directory in ('native', 'references', 'jobs', 'prompts', 'audit'):
        (HERE / directory).mkdir(exist_ok=True)

    sources, pair_keys = {}, {}
    pairs = sorted({tuple(pair) for g in inventory['groups'] for pair in g['image_palette_pairs']
                    if pair[0] in files})
    accepted = read(SORPIGAL / 'manifest.json')['frames']
    accepted_sources = read(SORPIGAL / 'inventory.json')['sources']
    drafts = read(TRIAL / 'manifest.json')['frames']
    for name, palette in pairs:
        file_record = files[name]
        path = REPO / file_record['path']
        assert sha(path) == file_record['sha256'], f'Stale inventory: {path}'
        image, palettes = native_image(path, palette)
        digest = hashlib.sha256(str(image.size).encode() + image.tobytes()).hexdigest()
        key = 'a_' + digest[:20]
        pair_keys[(name, palette)] = key
        if key not in sources:
            native = HERE / 'native' / (key + '.png')
            image.save(native)
            sources[key] = dict(native=str(native.relative_to(HERE)), rgba_sha256=digest,
                                native_size=list(image.size), native_bounds=image.getbbox(), aliases=[])
        asset = sources[key]
        asset['aliases'].append(dict(name=name, path=file_record['path'], sha256=file_record['sha256'],
                                     palette_id=palette, palettes=palettes,
                                     palette_mode='act' if palettes else 'embedded_bmp_runtime_fallback'))
        if image.getbbox() is None:
            asset['keep_native'] = 'Empty native placeholder; no visible art to restore or invent'
        if name in accepted and palette == accepted[name]['palette_baked']:
            old = accepted_sources[name]
            assert old['sha256'] == sha(path)
            assert any(p['sha256'] == old['palette_sha256'] for p in palettes)
            output = SORPIGAL / accepted[name]['file']
            assert sha(output) == accepted[name]['sha256']
            asset['reuse'] = dict(path=relative(output), sha256=sha(output),
                                 reason='Accepted New Sorpigal 2x native-canvas art; do not regenerate')
        elif name in drafts and palette == drafts[name]['palette_baked']:
            asset['draft'] = dict(raw=relative(TRIAL / 'raw' / (name + '.png')),
                                  enhanced=relative(TRIAL / drafts[name]['file']),
                                  repair=('shape' if name == '3amber' else 'pixel_steps' if name == '3apple' else None),
                                  status='review_existing_not_accepted')

    groups, jobs, owners, family_seeds = [], [], {}, {}
    category_order = {'decorations': 0, 'world_items': 1, 'effects_projectiles_other': 2, 'interface_overlays': 3}
    # Stable scenery-first ownership: a shared scenery/projectile image is restored only once.
    order = sorted(inventory['groups'], key=lambda g: (category_order[g['category']], g['sprite_id']))
    for group in order:
        raw = frames[group['sprite_id']]
        tracks = []
        seen_tracks = set()
        group_assets = []
        for octant in range(8):
            timeline = []
            for index, frame in enumerate(raw['frames']):
                name, mirror = resolve(frame, octant)
                key = pair_keys.get((name, frame.get('palette_id', 0)))
                timeline.append(dict(index=index, image=name, asset=key, mirrored=mirror,
                                     duration_raw=frame.get('frame_length_raw', 0),
                                     duration_ms=frame.get('frame_length_raw', 0) * 62.5,
                                     flags=frame.get('flags', []), scale=frame.get('scale', 1.0),
                                     palette_id=frame.get('palette_id', 0)))
                if key and key not in group_assets:
                    group_assets.append(key)
            # Mirrors are retained separately even when they share source drawings.
            signature = tuple((t['asset'], t['image'], t['mirrored']) for t in timeline)
            if signature not in seen_tracks:
                tracks.append(dict(octants=[octant], timeline=timeline))
                seen_tracks.add(signature)
            else:
                next(t for t in tracks if tuple((f['asset'], f['image'], f['mirrored'])
                                                for f in t['timeline']) == signature)['octants'].append(octant)
        label = '; '.join(hints[group['sprite_id']] or group['object_names'] or
                          [UI_HINTS.get(group['name'], group['name'] or group['images'][0])])
        profile = choose_profile(group, hints[group['sprite_id']])
        record = dict(sprite_id=group['sprite_id'], name=group['name'], label=label,
                      category=group['category'], profile=profile, native_group=raw,
                      tracks=tracks, assets=group_assets, missing_images=group['missing_images'])
        groups.append(record)
        seed = next((owners[k] for k in group_assets if k in owners), None)
        # Paired living/dead potted plants: the pot must keep its design between native states.
        family = re.sub(r'[ab]$', '', group['name']) if re.fullmatch(r'plant\d\d[ab]', group['name']) else None
        if family:
            seed = family_seeds.get(family, seed)
        # One native view per animation sheet; static multiple views share one sheet.
        batches = [[t['asset'] for t in track['timeline'] if t['asset']] for track in tracks]
        if len(raw['frames']) == 1:
            batches = [group_assets]
        for view, batch in enumerate(batches):
            unique = list(dict.fromkeys(batch))
            todo = [key for key in unique if key not in owners and 'reuse' not in sources[key]
                    and 'keep_native' not in sources[key]]
            if not todo:
                continue
            largest = max(max(sources[key]['native_size']) for key in todo)
            # Give large props enough pixels. Small related drawings can share six cells.
            limit = 1 if largest > 420 else 4 if largest > 220 else 6
            for offset in range(0, len(todo), limit):
                keys = todo[offset:offset + limit]
                job_id = f'g{group["sprite_id"]:05d}_v{view}_s{offset // limit}'
                centered = 'Center' in raw['frames'][0].get('flags', [])
                job = dict(id=job_id, sprite_id=group['sprite_id'], group=group['name'], label=label,
                           category=group['category'], profile=profile, assets=keys,
                           timeline_frames=len(raw['frames']),
                           alignment='center' if centered or profile in ('ui', 'weather') else 'bottom',
                           depends_on=[seed] if seed else [],
                           review_checks=PROFILES[profile]['checks'],
                           status='review_existing' if all('draft' in sources[k] for k in keys) else 'ready')
                prepare_reference(job, sources)
                job['prompt_file'] = 'prompts/' + job_id + '.txt'
                (HERE / job['prompt_file']).write_text(prompt_for(job, sources))
                job['prompt_sha256'] = sha(HERE / job['prompt_file'])
                write(HERE / 'jobs' / (job_id + '.json'), job)
                jobs.append({k: job[k] for k in ('id', 'group', 'label', 'category', 'profile', 'assets',
                                                'depends_on', 'status')})
                for key in keys:
                    owners[key] = job_id
                seed = seed or job_id
                if family:
                    family_seeds.setdefault(family, seed)
    assert set(sources) == set(owners) | {k for k, v in sources.items() if 'reuse' in v or 'keep_native' in v}
    for key, owner in owners.items():
        sources[key]['job'] = owner

    # Every ambiguous physical file gets a concrete triage instruction, with no invented ACT palette.
    triage = []
    for file in inventory['files']:
        if file['classification'] != 'unreferenced_needs_review':
            continue
        matches = [k for k, s in sources.items() if any(a['sha256'] == file['sha256'] for a in s['aliases'])]
        name = file['name']
        prefix = re.sub(r'[0-9]+[a-z]?$', '', name)
        relatives = sorted(n for n in files if len(prefix) >= 3 and n.startswith(prefix))[:16]
        triage.append(dict(id='triage_' + name, **file, exact_bmp_candidates=matches,
                           related_referenced_names=relatives, status='needs_source_usage_review',
                           instruction='Search this exact stem in game/, engine/, assets_dev/engine/rendering/ and '
                           'map events; inspect the original and related native sheets. Establish usage, frame order '
                           'and intended palette before restoring. A matching BMP hash alone is not a palette proof. '
                           'Record evidence as restore, alias, utility_keep_native, unused_keep_native or unresolved. '
                           'Never silently drop it or generate a guessed replacement.'))
    coverage = [dict(path=f['path'], sha256=f['sha256'],
                     assets=sorted({pair_keys[(f['name'], p)] for n, p in pairs if n == f['name']}))
                for f in files.values()]
    missing = [dict(sprite_id=g['sprite_id'], group=g['name'], names=g['missing_images'])
               for g in inventory['groups'] if g['missing_images']]
    summary = dict(referenced_files=len(coverage), source_name_palette_pairs=len(pairs),
                   unique_rendered_assets=len(sources), reuse_assets=sum('reuse' in s for s in sources.values()),
                   keep_native_assets=sum('keep_native' in s for s in sources.values()),
                   generation_or_review_jobs=len(jobs), jobs_by_profile=dict(Counter(j['profile'] for j in jobs)),
                   jobs_by_status=dict(Counter(j['status'] for j in jobs)),
                   triage_files=len(triage), missing_names=len(inventory['summary']['missing_image_names']),
                   groups=len(groups), source_pixel_multiplier=2,
                   palette_fallback_assets=sum(any(a['palette_mode'] != 'act' for a in s['aliases'])
                                               for s in sources.values()))
    write(HERE / 'sources.json', sources)
    write(HERE / 'groups.json', groups)
    write(HERE / 'index.json', jobs)
    # Rebuilds may retire a prepared placeholder or split differently. Preserve old files for audit,
    # but keep them outside the active jobs directory so a worker cannot accidentally execute them.
    active = {j['id'] for j in jobs}
    for path in (HERE / 'jobs').glob('*.json'):
        if path.stem not in active:
            retired = HERE / 'audit/retired_jobs' / path.name
            retired.parent.mkdir(exist_ok=True)
            path.replace(retired)
    write(HERE / 'triage.json', triage)
    write(HERE / 'coverage.json', dict(referenced=coverage, missing=missing,
                                     unreferenced_queue='triage.json', excluded=inventory['summary']['classifications']))
    write(HERE / 'summary.json', summary)
    provenance_paths = [inventory_path, frame_path, HERE / 'build.py', HERE / 'policy.py',
                        BASE / 'engine/data_tables/decoration_data.txt', BASE / 'engine/data_tables/object_list.txt']
    write(HERE / 'provenance.json', {relative(p): sha(p) for p in provenance_paths})
    # Compact visual index. All correctly paletted first drawings, labels and job ownership are inspectable.
    for category in category_order:
        subset = [g for g in groups if g['category'] == category and g['assets']]
        for page in range(math.ceil(len(subset) / 60)):
            sheet = Image.new('RGB', (1440, 1200), (40, 45, 42))
            draw = ImageDraw.Draw(sheet)
            for i, g in enumerate(subset[page * 60:(page + 1) * 60]):
                im = Image.open(HERE / sources[g['assets'][0]]['native'])
                im.thumbnail((170, 125), Image.Resampling.NEAREST)
                x, y = i % 8 * 180, i // 8 * 150
                sheet.paste(im, (x + (180 - im.width) // 2, y + 25), im)
                draw.text((x + 3, y + 1), f'{g["sprite_id"]} {g["name"]}', fill='white')
                draw.text((x + 3, y + 13), g['label'][:27], fill='white')
            sheet.save(HERE / 'audit' / f'{category}_{page:02d}.jpg')
    lines = ['# Prepared job list', '', 'Generated by `build.py`; use `queue.py next` for small batches.', '',
             '| Job | Category/profile | Native identity | Drawings | Initial action |',
             '| --- | --- | --- | ---: | --- |']
    for j in jobs:
        label = j['label'].replace('|', '/')
        lines.append(f'| [{j["id"]}](jobs/{j["id"]}.json) | {j["profile"]} | {label} | '
                     f'{len(j["assets"])} | {j["status"]} |')
    (HERE / 'JOB_LIST.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    build()
