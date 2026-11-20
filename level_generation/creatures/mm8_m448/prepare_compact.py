"""Lossless common-crop references and measured-layout queue for the Wererat Ratman Form."""
import datetime
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
import mm8_restore_queue as queue


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def layout(count, width, height):
    candidates = []
    for columns in range(1, min(count, 4) + 1):
        rows = math.ceil(count / columns)
        if rows > 4:
            continue
        nw, nh = columns * width, rows * height
        for ow, oh in [(1536, 1024), (1024, 1536), (1254, 1254)]:
            sampling = min(ow / nw, oh / nh)
            aspect_error = abs(math.log((ow / oh) / (nw / nh)))
            candidates.append((sampling, -aspect_error, columns, rows, ow, oh))
    return max(candidates)


def run():
    target = ROOT / 'compact_jobs.json'
    if target.exists():
        print('Existing compact queue preserved')
        return
    for folder in ['references', 'prompts', 'raw', 'review', 'checkpoints']:
        (ROOT / folder).mkdir(exist_ok=True)
    source = json.loads((ROOT / 'sources.json').read_text())
    groups = [('identity', ['m448sa' + str(v) for v in range(5)], 'standing', None)]
    for action in 'awndf':
        for view in range(5):
            names = sorted(n for n in source['sources'] if n[4] == action and n.endswith(str(view)))
            if action == 'd':
                names += sorted(n for n in source['sources'] if n[4] == 'x' and n.endswith(str(view)) and n not in source['pixel_aliases'])
            groups.append((action + '_v' + str(view), names, action, view))
    jobs = {}
    for key, names, action, view in groups:
        images = [queue.native(ROOT, name) for name in names]
        bounds = [image.getbbox() for image in images]
        crop = [min(b[0] for b in bounds) - 6, min(b[1] for b in bounds) - 6,
                max(b[2] for b in bounds) + 6, max(b[3] for b in bounds) + 6]
        width, height = crop[2] - crop[0], crop[3] - crop[1]
        capacity = len(names)
        while capacity > 1 and layout(capacity, width, height)[0] < 2.2:
            capacity -= 1
        chunks = []
        start = 0
        while start < len(names):
            end = min(start + capacity, len(names))
            chunks.append((start, end))
            if end == len(names):
                break
            start = end - 1
        for index, (start, end) in enumerate(chunks):
            selected = names[start:end]
            sampling, _, columns, rows, ow, oh = layout(len(selected), width, height)
            job_key = key if len(chunks) == 1 else key + '_' + str(index)
            sheet = Image.new('RGBA', (columns * width, rows * height), (255, 0, 255, 255))
            for cell, name in enumerate(selected):
                original = queue.native(ROOT, name)
                cropped = original.crop(crop)
                reconstructed = Image.new('RGBA', original.size)
                reconstructed.paste(cropped, crop[:2])
                a, b = np.array(original), np.array(reconstructed)
                assert np.array_equal(a[:, :, 3], b[:, :, 3])
                assert np.array_equal(a[a[:, :, 3] > 0], b[b[:, :, 3] > 0])
                sheet.alpha_composite(cropped, (cell % columns * width, cell // columns * height))
            reference = 'references/' + job_key + '_native.png'
            sheet.convert('RGB').save(ROOT / reference)
            description = {'standing': 'five native standing views, front through rear',
                           'a': 'native stored attack poses', 'w': 'walking cycle',
                           'n': 'hit reaction', 'd': 'falling sequence and final lying resting pose',
                           'f': 'idle fidget sequence'}[action]
            prompt = f'''Use case: style-transfer. Restore the original MM8 Wererat Ratman Form into faithful high-detail 2D game sprites.
Input 1 is the exact native pose/layout authority: {columns} columns by {rows} rows, row-major {', '.join(selected)}. {columns*rows-len(selected)} unused final cells stay empty magenta. This is {description}, stored view {view if view is not None else '0,1,2,3,4'}.
Preserve the SAME adult male anthropomorphic wererat from the native sprites: hunched lean build, coarse dark gray-brown fur, pointed rat muzzle with whiskers and sharp pale teeth, small dark eyes, large rounded ears, and a long thin bare pink-brown rat tail curved exactly as the native pose. He wears a ragged short gray cloth shirt with torn short sleeves and torn back hem, green trousers, brown waist belt, brown thigh sheath with metal tip, and torn brown boots exposing clawed furry toes. Brown-pink bare hands have long pale curved claws. He holds a short tapered steel sword in the right hand, with small crossguard and brown grip; the left clawed hand is free. Preserve the exact sword angle and foreshortening, tail shape, muzzle length, ears, gray shirt tears, waist belt and sheath placement across views. Preserve native muted colors and dark tonal weight. No human face, beard, extra fur mane, armor, helmet, added weapons or accessories, redesign or beautification.
Keep every head angle, hand gesture, limb position and foot contact from the corresponding native pose. Native input alone controls the pose; any second reference is accepted material/identity guidance only. Equal cells, common source-relative scale and placement; do not recenter or independently fit figures. Keep all fingers, sword tips and boot soles within their cells. Restore complete poses together consistently.
The common crop is {width}x{height} native pixels including six-pixel safety padding. Preserve sheet aspect {columns*width}:{rows*height}. Deliver the largest raster available at this aspect, aiming for at least {math.ceil(2.2*columns*width)}x{math.ceil(2.2*rows*height)} actual generated pixels. Do not add broad empty margins or shrink the subjects.
Background is perfectly flat magenta RGB255,0,255; no ground shadow, gradient, halo, reflections, text or grid lines. Generate the green base appearance only.'''
            prompt_path = 'prompts/' + job_key + '_v1.txt'
            (ROOT / prompt_path).write_text(prompt + '\n')
            jobs[job_key] = {'frames': selected, 'action': action, 'view': view,
                             'columns': columns, 'rows': rows, 'crop_native': crop,
                             'native_sheet_size': list(sheet.size), 'references': [reference],
                             'prompt': prompt_path, 'status': 'pending',
                             'budget_observed_envelope': [ow, oh], 'budget_sampling': sampling,
                             'common_crop_reconstruction_exact': True,
                             'overlap_previous': selected[:1] if index else []}
    save(target, {'schema_version': 1, 'jobs': jobs, 'native_pixel_aliases': source['pixel_aliases'], 'minimum_generated_sampling': 2,
                  'source_clipping': 'Native upright feet reach y=256; preserve source boundary and contacts.',
                  'palette_plan': 'Green trousers -> blue/red; protect gray shirt, gray-brown fur, bare hands/tail, claws, boots, leather straps/sheath and steel sword.'})
    ledger_path = ROOT.parent / 'mm8_remaining/progress.json'
    ledger = json.loads(ledger_path.read_text())
    ledger['families']['m448'].update(status='partial', processed_frames=0,
        resume='Generate compact_jobs.json identity first; inspect and accept, then restore pending action/view grids.')
    ledger['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save(ledger_path, ledger)
    print(len(jobs), 'compact jobs;', len(source['sources']), 'unique frames; minimum budget',
          min(j['budget_sampling'] for j in jobs.values()))


if __name__ == '__main__':
    run()
