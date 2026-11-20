"""Read-only atlas/landmark motion audit and native-time review export for staged families.

Errors are relative to each native pose, not to a stationary silhouette. Landmark
ratios are screening evidence, not proof that generated anatomy has uniform scale.
"""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
import yaml

from exact_placement import native_offset, validate_animation_bindings, validate_landmark_usage, validate_manifest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def live_groups():
    base = REPO/'assets_dev/engine/rendering'
    groups = {}
    for path in [base/'sprite_frame_data_common.yml', *sorted((base/'sprite_frames/monsters').glob('*.yml'))]:
        for group in yaml.load(path.read_text(), Loader=yaml.CSafeLoader)['sprites']:
            groups[group['sprite_name'].lower()] = (group, path)
    return groups


def live_bindings(root, sources, manifest, groups):
    errors, paths, redirects, count = [], {}, set(), 0
    for variant in sources['variants'].values():
        for saved in variant['actions'].values():
            name = saved['sprite_name'].lower()
            if name not in groups:
                errors.append(name+': missing live group')
                continue
            current, path = groups[name]
            paths[str(path.relative_to(REPO))] = sha(path)
            count += 1
            def selected(frames, installed=False):
                output = []
                for frame in frames:
                    row = {k: frame.get(k) for k in ('texture_name', 'frame_length_raw', 'flags', 'scale', 'palette_id')}
                    prefix = f'atlas:{root.parent.name}/'
                    if installed and row['texture_name'].startswith(prefix):
                        redirects.add(row['texture_name'])
                        row['texture_name'] = row['texture_name'][len(prefix):]
                    output.append(row)
                return output
            if (current.get('animation_length_raw') != saved.get('animation_length_raw') or
                    selected(current['frames'], True) != selected(saved['frames'])):
                errors.append(name+': live native timing/pose/scale/mirror binding')
    installed_path = REPO/'assets_dev/engine/sprites_new'/root.parent.name/'manifest.json'
    installed = None
    if installed_path.exists():
        runtime = read(installed_path)
        comparable = {n: {k: f[k] for k in ('page', 'atlas_xywh', 'crop_origin_px')}
                      for n, f in manifest['frames'].items()}
        installed = dict(path=str(installed_path.relative_to(REPO)), sha256=sha(installed_path),
                         frame_mapping_matches_staged=runtime['frames'] == comparable)
    return dict(groups_checked=count, errors=sorted(set(errors)), source_hashes=paths,
                installed_atlas_redirects=sorted(redirects), installed_package=installed,
                method='Compare current native groups after resolving only this family\'s explicit installed atlas prefix')


def audit(root, groups):
    root = root.resolve()
    out = root/'review/production_motion'
    out.mkdir(parents=True, exist_ok=True)
    manifest, registration = read(root/'manifest.json'), read(root/'registration.json')
    sources = read(root/'sources.json')
    annotation = read(root/'review/anatomy_points.json')
    errors = validate_manifest(manifest, registration) + validate_animation_bindings(manifest)
    errors += validate_landmark_usage(annotation, registration)
    live = live_bindings(root, sources, manifest, groups)
    tier = manifest['pixels_per_logical_pixel']
    assert tier == 2, 'This review preserves native half pixels at physical 2x'
    images, frames, pages, bounds = {}, {}, {}, []
    for name, f in manifest['frames'].items():
        r = registration[name]
        source = sources['sources'][name]
        indexed = Image.open(REPO/source['path'])
        ix = np.array(indexed)
        palette = str(source.get('fixed_palette', sources.get('base_palette', f['source_palette'])))
        colors = np.frombuffer((REPO/sources['palette_sources'][palette]['path']).read_bytes()[:768],
                              np.uint8).reshape(256, 3)
        native = Image.fromarray(np.dstack([colors[ix], (ix != 0).astype(np.uint8)*255]))
        native = native.resize((native.width*2, native.height*2), Image.Resampling.NEAREST)
        offset = native_offset(manifest['logical_canvas'], indexed.size, manifest['anchor'])
        if list(indexed.size) != f['source_canvas']:
            errors.append(name+': actual source dimensions')
        if sha(REPO/source['path']) != source['sha256']:
            errors.append(name+': changed native source')
        page = f['page']
        if page not in pages:
            pages[page] = Image.open(root/manifest['pages'][page]['base']).convert('RGBA')
        x, y, w, h = f['atlas_xywh']
        enhanced = pages[page].crop((x, y, x+w, y+h))
        master = Image.open(root/'aligned_2x'/f'{name}.png').convert('RGBA').crop(f['crop_in_aligned_px'])
        aa, bb = np.array(master), np.array(enhanced)
        visible_equal = aa.shape == bb.shape and np.array_equal(aa[:, :, 3], bb[:, :, 3]) and np.all(
            (aa[:, :, :3] == bb[:, :, :3]) | (aa[:, :, 3:] == 0))
        hidden_rgb_difference = bool(visible_equal and not np.array_equal(aa, bb))
        if not visible_equal:
            errors.append(name+': atlas/master mismatch')
        images[name] = [(native, [int(v*2) for v in offset]), (enhanced, f['crop_origin_px'])]
        for im, origin in images[name]:
            box = im.getchannel('A').getbbox()
            bounds.append([box[i]+origin[i % 2] for i in range(4)])
        correction = np.array(f.get('anchor_correction_px', [0, 0]))/2
        points = {}
        for label, point in r.get('review_landmarks', {}).items():
            n = np.array(point['native'])+correction
            e = (np.array(point['restored_before_translation'])+r['translate'])/2+correction
            points[label] = dict(native=n.tolist(), restored=e.tolist(), residual=(e-n).tolist(),
                                 diagnostic=label in r.get('diagnostic_landmarks', []),
                                 geometry_control=label in r.get('local_geometry', {}).get('control_landmarks', []))
        labels = list(points)
        ratios = {}
        if labels:
            anchor = points[labels[0]]
            for label in labels[1:]:
                point = points[label]
                nd = math.dist(anchor['native'], point['native'])
                ed = math.dist(anchor['restored'], point['restored'])
                ratios[label] = ed/nd if nd else None
        frames[name] = dict(landmarks=points, span_ratios=ratios, batch=r['batch'],
                            transparent_rgb_only_difference=hidden_rgb_difference,
                            half_pixel_native_offset=any(v % 1 for v in offset),
                            anchor_correction_px=f.get('anchor_correction_px', [0, 0]),
                            deliberate_normalization=bool(r.get('post_registration_normalization')))
    crop = [math.floor(min(b[0] for b in bounds)/2)*2-20, math.floor(min(b[1] for b in bounds)/2)*2-20,
            math.ceil(max(b[2] for b in bounds)/2)*2+20, math.ceil(max(b[3] for b in bounds)/2)*2+20]
    width, height = (crop[2]-crop[0])//2, (crop[3]-crop[1])//2
    rendered = {}
    for name, pairs in images.items():
        tiles = []
        for im, origin in pairs:
            tile = im.crop([crop[i]-origin[i % 2] for i in range(4)])
            tiles.append(tile.convert('RGBa').resize((width, height), Image.Resampling.LANCZOS).convert('RGBA'))
        rendered[name] = tiles
    sequences, seen, covered = [], set(), set()
    for action, animation in manifest['animations'].items():
        for view, steps in animation['views'].items():
            if int(view) > 4 or not steps:
                continue
            signature = json.dumps(steps, sort_keys=True)
            if signature in seen:
                continue
            seen.add(signature)
            names = [s['frame'] for s in steps]
            covered.update(names)
            transitions = list(zip(names, names[1:]))
            if animation['playback'] == 'loop' and len(names) > 1:
                transitions.append((names[-1], names[0]))
            next_action = animation.get('next_action')
            if next_action and manifest['animations'].get(next_action, {}).get('views', {}).get(view):
                transitions.append((names[-1], manifest['animations'][next_action]['views'][view][0]['frame']))
            deltas = []
            for before, after in transitions:
                a, b = frames[before], frames[after]
                for label in a['landmarks'].keys() & b['landmarks'].keys():
                    if a['landmarks'][label]['diagnostic'] or b['landmarks'][label]['diagnostic']:
                        continue
                    if a['landmarks'][label]['geometry_control'] or b['landmarks'][label]['geometry_control']:
                        continue
                    delta = np.array(b['landmarks'][label]['residual'])-a['landmarks'][label]['residual']
                    ra, rb = a['span_ratios'].get(label), b['span_ratios'].get(label)
                    deltas.append(dict(before=before, after=after, landmark=label,
                        residual_delta_xy=delta.tolist(), magnitude=float(np.linalg.norm(delta)),
                        span_ratio_delta_pp=(rb-ra)*100 if ra is not None and rb is not None else None,
                        intentional_native_departure=a['deliberate_normalization'] or b['deliberate_normalization'],
                        batch_boundary=a['batch'] != b['batch']))
            sequences.append(dict(action=action, view=view, frames=names, playback=animation['playback'],
                next_action=next_action, native_scales=sorted({s['native_scale'] for s in steps}),
                durations_ms=[s['duration_ms'] for s in steps],
                transitions=sorted(deltas, key=lambda d: d['magnitude'], reverse=True)))
    unused = sorted(set(frames)-covered)
    if unused:
        sequences.append(dict(action='unused', view='0', frames=unused, transitions=[],
                              playback='not_runtime_bound', next_action=None))
    contact_paths = []
    for sequence in sequences:
        names = sequence['frames']
        columns = max(1, min(4, 1400//width))
        contacts = []
        for start in range(0, len(names), columns):
            selected = names[start:start+columns]
            panel = Image.new('RGB', (width*len(selected), height*2+72), (36, 40, 38))
            draw = ImageDraw.Draw(panel)
            draw.text((4, 2), f"{sequence['action']}/{sequence['view']} | exact native above / actual atlas below", fill='white')
            for col, name in enumerate(selected):
                for row in range(2):
                    x, y = col*width, 24+row*(height+20)
                    tile = rendered[name][row]
                    panel.paste(tile, (x, y), tile)
                    px, py = [manifest['logical_pivot'][i]-crop[i]/2 for i in range(2)]
                    draw.line((x+px, y, x+px, y+height), fill=(125, 65, 65))
                    draw.line((x, y+py, x+width, y+py), fill=(125, 65, 65))
                    for label, point in frames[name]['landmarks'].items():
                        xx, yy = point['native' if row == 0 else 'restored']
                        xx, yy = x+xx-crop[0]/2, y+yy-crop[1]/2
                        draw.line((xx-3, yy, xx+3, yy), fill=(40, 240, 240))
                        draw.line((xx, yy-3, xx, yy+3), fill=(40, 240, 240))
                        draw.text((xx+4, yy), label, fill=(40, 240, 240))
                    draw.text((x+3, y+height+2), name, fill='white')
            path = out/f"{sequence['action']}_{sequence['view']}_{start//columns:02}.png"
            panel.save(path)
            contacts.append(str(path.relative_to(root)))
            contact_paths.append(path)
        sequence['contacts'] = contacts
    # Common family crop and common display scale, including action boundaries.
    ratio = min(220/width, 145/height)
    small = (round(width*ratio), round(height*ratio))
    for page in range(math.ceil(len(sequences)/4)):
        selected = sequences[page*4:page*4+4]
        columns = max(len(s['frames']) for s in selected)
        panel = Image.new('RGB', (columns*230, len(selected)*340), (36, 40, 38))
        draw = ImageDraw.Draw(panel)
        for row, sequence in enumerate(selected):
            draw.text((4, row*340+2), f"{sequence['action']}/{sequence['view']} | native above / atlas below", fill='white')
            for col, name in enumerate(sequence['frames']):
                for k, tile in enumerate(rendered[name]):
                    tile = tile.resize(small, Image.Resampling.LANCZOS)
                    panel.paste(tile, (col*230, row*340+20+k*150), tile)
                draw.text((col*230+3, row*340+320), name, fill='white')
        path = out/f'sequences_{page:02}.png'
        panel.save(path)
        contact_paths.append(path)
    template = (HERE/'mm6_peasants/viewer.html').read_text()
    title = manifest['creature']+' — authoritative native timing / exported atlas placement'
    viewer = root/'authoritative_review.html'
    viewer.write_text(template.replace('__TITLE__', html.escape(title))
        .replace('/* MANIFEST */', json.dumps(manifest, separators=(',', ':')))
        .replace('id="loop" type="checkbox" checked', 'id="loop" type="checkbox"'))
    report = dict(status='pending_visual_motion_review', manifest_sha256=sha(root/'manifest.json'),
        registration_sha256=sha(root/'registration.json'), geometry_errors=errors,
        authoritative_viewer=str(viewer.relative_to(root)), viewer_sha256=sha(viewer),
        units='Native logical pixels before actor scale; native-relative error differences, not intentional motion',
        limits='Saved manual landmark correspondence must be inspected. Calibration spans are not independent '
               'scale evidence. Limb/effect-span changes may be pose differences, not uniform body scaling. '
               'Contacts are static; browser exercise is mechanical, not watched playback. '
               'Residual transitions touching deliberately normalized frames measure the intended departure '
               'from native art, not the restored animation step.',
        half_pixel_frames=sum(f['half_pixel_native_offset'] for f in frames.values()),
        contact_crop_physical_2x=crop, contact_cell_logical=[width, height],
        frame_count=len(frames), frames=frames, sequences=sequences,
        deliberately_normalized_frames=sorted(n for n, f in frames.items() if f['deliberate_normalization']),
        live_bindings=live,
        evidence_artifacts={str(p.relative_to(root)): sha(p) for p in contact_paths})
    (out/'audit.json').write_text(json.dumps(report, indent=2)+'\n')
    worst = sorted([dict(action=s['action'], view=s['view'], **d) for s in sequences for d in s['transitions']
                    if not d['intentional_native_departure']],
                   key=lambda d: d['magnitude'], reverse=True)[:8]
    print(json.dumps(dict(package=str(root), geometry_errors=errors, half_pixel_frames=report['half_pixel_frames'],
                         frames=len(frames), sequences=len(sequences), worst_transitions=worst)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packages', type=Path, nargs='+')
    args = parser.parse_args()
    groups = live_groups()
    for package in args.packages:
        audit(package, groups)
