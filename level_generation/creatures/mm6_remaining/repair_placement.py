"""Preserve accepted checkpoints, correct export coordinates, and render exact-placement review contacts."""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
from exact_placement import export_placement, validate_animation_bindings, validate_manifest

OUT = HERE/'ground_anchor_review/accepted'
BASELINE = OUT/'checkpoints/before_anchor_correction/audit.json'


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2)+'\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def viewers(family_name=None):
    """Build the shared review UI without modifying accepted art or historical evidence."""
    template = (HERE.parent/'mm6_peasants/viewer.html').read_text()
    links = []
    for family in read(BASELINE)['families']:
        if family_name and family_name != family['family']:
            continue
        path = REPO/family['package']
        manifest = read(path)
        assert not validate_manifest(manifest, read(path.parent/'registration.json')), path
        assert not validate_animation_bindings(manifest), path
        for actions in manifest['animations_by_palette'].values():
            for action in actions.values():
                for steps in action['views'].values():
                    for step in steps:
                        scale = step.get('native_scale', action.get('native_frame_scale'))
                        assert scale is not None and scale > 0, (path, step)
        output = path.parent/'placement_review.html'
        output.write_text(template.replace('__TITLE__', html.escape(family['family'])+' — placement review pending')
                          .replace('/* MANIFEST */', json.dumps(manifest, separators=(',', ':'))))
        import os
        relative = os.path.relpath(output, OUT)
        links.append(f'<li><a href="{html.escape(relative)}">{html.escape(family["family"])}</a></li>')
    if not family_name:
        (OUT/'playback.html').write_text('<!doctype html><meta charset="utf-8"><title>MM6 placement review</title>'
            '<h1>MM6 placement review — 49 families</h1><p>Playback tools; review remains pending.</p>'
            '<p><a href="animation_review.html">Open native-timed capture board</a></p><ul>'
            + ''.join(links)+'</ul>')
    print(f'Built {len(links)} placement viewers; accepted artifacts unchanged')


def migrate():
    if not BASELINE.exists():
        BASELINE.parent.mkdir(parents=True)
        shutil.copy2(OUT/'audit.json', BASELINE)
    changed = 0
    for family in read(BASELINE)['families']:
        root = (REPO/family['package']).parent
        manifest = read(root/'manifest.json')
        registration = read(root/'registration.json')
        if not validate_manifest(manifest, registration):
            continue
        assert digest(root/'manifest.json') == family['manifest_sha256'], root
        count = 0
        for name, frame in manifest['frames'].items():
            previous = frame['native_offset'][:2]
            exact, origin, correction = export_placement(manifest['logical_canvas'], frame['source_canvas'],
                previous, registration[name]['canvas_origin_px'], manifest['pixels_per_logical_pixel'],
                manifest.get('anchor', 'bottom-center'))
            if not any(correction):
                continue
            frame.update(native_offset=exact, registration_native_offset=previous,
                         anchor_correction_px=correction, aligned_canvas_origin_px=origin,
                         crop_origin_px=[frame['crop_in_aligned_px'][i]+origin[i] for i in range(2)])
            count += 1
        if not count:
            continue
        checkpoint = root/'checkpoints/before_exact_anchor_20260922'
        assert not checkpoint.exists(), checkpoint
        checkpoint.mkdir(parents=True)
        for name in ('manifest.json', 'acceptance.json', 'validation.json', 'run.json', 'review.html',
                     'review/acceptance.json', 'review/decision.json'):
            path = root/name
            if path.exists():
                target = checkpoint/name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
        assert not validate_manifest(manifest, registration)
        manifest['exact_anchor_revision'] = dict(version=1, corrected_frames=count,
            previous_manifest_sha256=family['manifest_sha256'],
            method='Exact native placement from recorded registration basis; translate canvas metadata once. '
                   'RGBA, masks, atlas rectangles, animations and registration sampling unchanged.',
            checkpoint=str(checkpoint.relative_to(root)))
        manifest['quality_status'] = 'pending_placement_reacceptance'
        write(root/'manifest.json', manifest)
        record = dict(status='pending_placement_reacceptance', installed=False,
                      previous_acceptance=str((checkpoint/'review/acceptance.json').relative_to(root)),
                      reason='Exact anchor metadata corrected; final placement review required.',
                      corrected_frames=count)
        write(root/'review/acceptance.json', record)
        write(root/'acceptance.json', record)
        validation = read(root/'validation.json')
        validation.update(exact_native_anchor_mapping=True, visual_review_complete=False)
        write(root/'validation.json', validation)
        run = read(root/'run.json')
        run['status'] = 'partial'
        run['placement_review_status'] = 'pending'
        run['completion_note'] = record['reason']
        write(root/'run.json', run)
        template = (HERE.parent/'mm6_peasants/viewer.html').read_text()
        (root/'review.html').write_text(template.replace('__TITLE__', family['family']+' — placement review pending')
                                      .replace('/* MANIFEST */', json.dumps(manifest, separators=(',', ':'))))
        changed += count
        print(family['family'], count, flush=True)
    print('Corrected frames:', changed)


def contacts(family_name=None):
    baseline = read(BASELINE)
    queue = []
    queue_path = OUT/'placement_queue.json'
    previous_report = read(queue_path) if queue_path.exists() else {}
    previous = previous_report.get('families', [])
    for family in baseline['families']:
        if family_name and family_name not in (family['family'], Path(family['package']).parts[-3]):
            continue
        root = (REPO/family['package']).parent
        manifest, registration = read(root/'manifest.json'), read(root/'registration.json')
        sources = read(root/'sources.json')
        # Warnings prioritize review; their absence does not establish anatomical fidelity.
        flagged = {r['frame'] for r in baseline['frames'] if r['family'] == family['family']
                   and abs(r['thresholds']['128'].get('bottom_delta', 0)) > 2}
        directory = root/'review/exact_placement'
        directory.mkdir(exist_ok=True)
        sequences, seen, covered = [], set(), set()
        for action, animation in manifest['animations'].items():
            for view, steps in animation.get('views', {}).items():
                if int(view) > 4:
                    continue
                names = tuple(s['frame'] for s in steps)
                if not names or names in seen:
                    continue
                seen.add(names)
                sequences.append((action, view, names))
                covered.update(names)
        missing = sorted(set(manifest['frames'])-covered)
        if missing:
            sequences.append(('unused', '0', missing))
        pages = {}
        entries = []
        for action, view, names in sequences:
            images, boxes = {}, []
            for name in names:
                f = manifest['frames'][name]
                source = sources['sources'][name]
                indexed = Image.open(REPO/source['path'])
                ix = np.array(indexed)
                palette = str(source.get('fixed_palette', sources.get('base_palette', f['source_palette'])))
                colors = np.frombuffer((REPO/sources['palette_sources'][palette]['path']).read_bytes()[:768],
                                       np.uint8).reshape(256, 3)
                native = Image.fromarray(np.dstack([colors[ix], (ix != 0).astype(np.uint8)*255]))
                native = native.resize((native.width*2, native.height*2), Image.Resampling.NEAREST)
                exact, _, _ = export_placement(manifest['logical_canvas'], indexed.size, [0, 0], [0, 0],
                                               anchor=manifest.get('anchor', 'bottom-center'))
                native_origin = [int(v*2) for v in exact]
                page = f['page']
                if page not in pages:
                    pages[page] = Image.open(root/manifest['pages'][page]['base']).convert('RGBA')
                x, y, w, h = f['atlas_xywh']
                restored = pages[page].crop((x, y, x+w, y+h))
                images[name] = [(native, native_origin), (restored, f['crop_origin_px'])]
                for im, origin in images[name]:
                    box = im.getchannel('A').getbbox()
                    if box:
                        boxes.append([box[i]+origin[i % 2] for i in range(4)])
            if not boxes:
                continue
            crop = [math.floor(min(b[0] for b in boxes)/2)-10, math.floor(min(b[1] for b in boxes)/2)-10,
                    math.ceil(max(b[2] for b in boxes)/2)+10, math.ceil(max(b[3] for b in boxes)/2)+10]
            width, height = crop[2]-crop[0], crop[3]-crop[1]
            columns = max(1, min(4, 1500//width))
            for start in range(0, len(names), columns):
                selected = names[start:start+columns]
                panel = Image.new('RGB', (width*len(selected), 2*height+70), (40, 42, 41))
                draw = ImageDraw.Draw(panel)
                draw.text((4, 3), family['family']+' '+action+'/'+view+' native / actual atlas; same logical coordinates', fill='white')
                for column, name in enumerate(selected):
                    f, r = manifest['frames'][name], registration[name]
                    correction = f.get('anchor_correction_px', [0, 0])
                    points = dict(r.get('review_landmarks', {}))
                    legacy = r.get('placement_landmarks', {})
                    if 'native_crown' in legacy:
                        points.setdefault('crown', dict(native=legacy['native_crown'],
                            restored_before_translation=legacy['restored_crown_before_translation']))
                    if 'native' in legacy and 'raw' in legacy:
                        # Older families store cleaned-cell points rather than transformed points.
                        # Use the measured per-axis resize, including integer output-size rounding.
                        landmark_names = legacy.get('names')
                        labels = landmark_names if isinstance(landmark_names, list) else [
                            f'point {i}' for i in range(len(legacy['native']))]
                        assert len(labels) == len(legacy['native']) == len(legacy['raw'])
                        for label, source_point, raw_point in zip(labels, legacy['native'], legacy['raw']):
                            points.setdefault(label, dict(native=source_point, restored_before_translation=[
                                raw_point[i]*2/r['effective_sampling_xy'][i] for i in range(2)]))
                    for row, (im, origin) in enumerate(images[name]):
                        rect = [crop[i]*2-origin[i % 2] for i in range(4)]
                        tile = im.crop(rect).convert('RGBa').resize((width, height), Image.Resampling.LANCZOS).convert('RGBA')
                        x, y = column*width, 24+row*(height+20)
                        panel.paste(tile, (x, y), tile)
                        px = x+manifest['logical_pivot'][0]-crop[0]
                        py = y+manifest['logical_pivot'][1]-crop[1]
                        if x <= px < x+width:
                            draw.line((px, y, px, y+height-1), fill=(120, 65, 65))
                        if y <= py < y+height:
                            draw.line((x, py, x+width-1, py), fill=(120, 65, 65))
                        for label, point in points.items():
                            color = (165, 165, 165) if label in r.get('diagnostic_landmarks', []) else (40, 240, 240)
                            xy = [point['native'][i]+correction[i]/2 for i in range(2)] if row == 0 else [
                                (point['restored_before_translation'][i]+r['translate'][i]+correction[i])/2
                                for i in range(2)]
                            mx, my = x+xy[0]-crop[0], y+xy[1]-crop[1]
                            draw.line((mx-3, my, mx+3, my), fill=color)
                            draw.line((mx, my-3, mx, my+3), fill=color)
                            draw.text((mx+4, my), label[:12], fill=color)
                        draw.text((x+3, y+height+2), name+(' *' if name in flagged else ''), fill='white')
                path = directory/f'{action}_{view}_{start//columns:02d}.png'
                panel.save(path)
                entries.append(dict(path=str(path.relative_to(REPO)), frames=list(selected), action=action, view=view,
                                    logical_crop=crop, cell_size=[width, height],
                                    row_y=[24, 24+height+20]))
        queue.append(dict(family=family['family'], package=family['package'], manifest_sha256=digest(root/'manifest.json'),
                          flagged_frames=sorted(flagged), contacts=entries, status='pending_visual_review'))
        print(family['family'], len(entries), 'contacts', flush=True)
    old_by_family = {f['family']: f for f in previous}
    for entry in queue:
        old = old_by_family.get(entry['family'], {})
        evidence = old.get('evidence_artifacts', {})
        if evidence and old.get('manifest_sha256') == entry['manifest_sha256'] and all(
                digest(REPO/path) == expected for path, expected in evidence.items()):
            # Keep all artifact-bound review history, including findings added by later reviews.
            # Only the generated inventory/contact fields belong to this command.
            generated_fields = {'family', 'package', 'manifest_sha256', 'flagged_frames', 'contacts'}
            for field, value in old.items():
                if field not in generated_fields:
                    entry[field] = value
    replacements = {f['family']: f for f in queue}
    if family_name:
        queue = [replacements.pop(f['family'], f) for f in previous] + list(replacements.values())
    previous_report.update(scope='Every pose in all 49 originally accepted families', families=queue)
    reviewed = [f for f in queue if f['status'].startswith('reviewed_')]
    pending = [f for f in queue if not f['status'].startswith('reviewed_')]
    previous_report.setdefault('summary', {}).update(fully_inspected_families=len(reviewed),
        fully_inspected_frame_records=sum(len(f.get('reviewed_frames', [])) for f in reviewed),
        queued_families=len(queue),
        unreviewed_families=len(pending),
        unreviewed_flagged_families=sum(bool(f['flagged_frames']) for f in pending),
        unreviewed_original_flagged_frames=sum(len(f['flagged_frames']) for f in pending),
        strict_placement_acceptance_complete=False)
    write(queue_path, previous_report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['migrate', 'contacts', 'viewers'])
    parser.add_argument('--family')
    args = parser.parse_args()
    if args.command == 'migrate':
        migrate()
    elif args.command == 'viewers':
        viewers(args.family)
    else:
        contacts(args.family)
