"""Register art to native coordinates, export aligned and losslessly cropped PNGs, and validate placement.

Requires Pillow, NumPy, SciPy. Does not install assets or change engine/gameplay tables.
"""
from pathlib import Path
import hashlib
import json
import math
import statistics

import numpy as np
from PIL import Image, ImageDraw

from registration import native_image

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
CANVAS = (355, 289)
CORPSES = {'gobdyd0', 'gobdye0', 'gobdyf0'}


def resize(im, size):
    return im.convert('RGBa').resize(size, Image.Resampling.LANCZOS).convert('RGBA')


def composite(im, color):
    out = Image.new('RGBA', im.size, (*color, 255))
    out.alpha_composite(im)
    return out.convert('RGB')


def pack_atlas(frames, width):
    """Height-sorted shelves; deterministic, no sprite rotation, two extra pixels between crop rectangles."""
    shelves, placements = [], {}
    for name, im in sorted(frames.items(), key=lambda item: (-item[1].height, item[0])):
        options = [s for s in shelves if s['height'] >= im.height + 2 and s['x'] + im.width + 2 <= width]
        shelf = min(options, key=lambda s: s['height'] - im.height) if options else None
        if shelf is None:
            shelf = {'y': sum(s['height'] for s in shelves), 'height': im.height + 2, 'x': 0}
            shelves.append(shelf)
        placements[name] = [shelf['x'], shelf['y'], im.width, im.height]
        shelf['x'] += im.width + 2
    height = sum(s['height'] for s in shelves)
    atlas = Image.new('RGBA', (max(s['x'] for s in shelves), height))
    for name, im in frames.items():
        atlas.paste(im, tuple(placements[name][:2]))
    return atlas, placements


def build():
    source = json.loads((ROOT / 'source_manifest.json').read_text())
    landmarks = json.loads((ROOT / 'landmarks.json').read_text())
    by_group = {}
    for name, lm in landmarks.items():
        im = Image.open(ROOT / 'cleaned_source' / (name + '.png'))
        # Corrected walk cell was generated alone at a larger physical resolution.
        norm = 561 / im.width if name == 'gobwad0' else 1
        lm['resolution_normalization'] = norm
        group = 'prone' if name in CORPSES else lm['action']
        lm['scale_group'] = group
        s, g = lm['native'], lm['generated']
        if group == 'prone':
            ratio = (s['alpha_bounds'][2] - s['alpha_bounds'][0]) / (g['alpha_bounds'][2] - g['alpha_bounds'][0])
        else:
            ratio = (s['ground_y'] - s['head_top']) / ((g['ground_y'] - g['head_top']) * norm)
        by_group.setdefault(group, []).append(ratio)
    scales = {key: statistics.median(ratios) for key, ratios in by_group.items()}
    # Reduce the whole action uniformly only if the restored silhouette exceeds the native canvas.
    # A weapon near the side border may instead receive a recorded minimal horizontal translation.
    for name, lm in landmarks.items():
        s, g = lm['native'], lm['generated']
        b = g['alpha_bounds']
        limits = [(s['ground_y'] - 2) / (b[3] - b[1])]
        limits.append((CANVAS[0] - 4) / (b[2] - b[0]))
        group = lm['scale_group']
        scales[group] = min(scales[group], min(limits) / lm['resolution_normalization'] * .995)

    for folder in ['aligned_1x', 'aligned_2x', 'trimmed_1x', 'trimmed_2x', 'action_sheets_2x', 'previews/native']:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    records, all_frames = {}, {1: {}, 2: {}}
    for action in source['actions']:
        for frame in action['frames']:
            name = Path(frame['source']).stem
            assert hashlib.sha256((REPO / frame['source']).read_bytes()).hexdigest() == frame['sha256']
            lm = landmarks[name]
            im = Image.open(ROOT / 'cleaned_source' / (name + '.png'))
            scale = scales[lm['scale_group']] * lm['resolution_normalization']
            size = (round(im.width * scale * 2), round(im.height * scale * 2))
            scaled = resize(im, size)
            bounds = scaled.getchannel('A').getbbox()
            x = round(lm['native']['head_x'] * 2 - lm['generated']['head_x'] * size[0] / im.width)
            anatomical_x = x
            x = max(4 - bounds[0], min(x, 706 - bounds[2]))
            y = lm['native']['ground_y'] * 2 - bounds[3]
            visible = [bounds[0] + x, bounds[1] + y, bounds[2] + x, bounds[3] + y]
            assert 0 <= visible[0] < visible[2] <= 710, (name, visible)
            assert 0 <= visible[1] < visible[3] <= 578, (name, visible)
            master = Image.new('RGBA', (710, 578))
            master.paste(scaled, (x, y))
            native = native_image(name)
            native.save(ROOT / 'previews/native' / (name + '.png'))
            records[name] = {'action': action['name'], 'duration_seconds': frame['duration_seconds'],
                             'native_source': frame['source'], 'native_sha256': frame['sha256'],
                             'registration': {'uniform_logical_scale': scale, 'scale_group': lm['scale_group'],
                                              'resized_source_size': size, 'paste_origin_2x': [x, y],
                                              'border_translation_2x': x - anatomical_x,
                                              'landmarks': lm}, 'exports': {}}
            for tier in [1, 2]:
                aligned = master if tier == 2 else resize(master, CANVAS)
                aligned.save(ROOT / f'aligned_{tier}x' / (name + '.png'))
                all_frames[tier][name] = aligned
                b = aligned.getchannel('A').getbbox()
                # Two logical pixels of transparent filter padding; may extend outside the logical canvas.
                pad = 2 * tier
                crop = (b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad)
                trimmed = aligned.crop(crop)
                trimmed.save(ROOT / f'trimmed_{tier}x' / (name + '.png'))
                reconstructed = Image.new('RGBA', aligned.size)
                reconstructed.paste(trimmed, crop[:2])
                assert np.array_equal(np.array(aligned), np.array(reconstructed)), name
                pivot = [CANVAS[0] * tier / 2 - crop[0], CANVAS[1] * tier - crop[1]]
                records[name]['exports'][f'{tier}x'] = {
                    'aligned': f'aligned_{tier}x/{name}.png', 'trimmed': f'trimmed_{tier}x/{name}.png',
                    'physical_canvas': aligned.size, 'logical_canvas': CANVAS, 'pixels_per_logical_pixel': tier,
                    'visible_alpha_bounds': b, 'crop_xywh': [crop[0], crop[1], trimmed.width, trimmed.height],
                    'pivot_in_trimmed_pixels': pivot, 'pivot_in_trimmed_logical_pixels': [v / tier for v in pivot],
                    'filter_padding_pixels': pad, 'crop_reconstructs_aligned_exactly': True}

    memory = {}
    for tier in [1, 2]:
        crops = {n: Image.open(ROOT / f'trimmed_{tier}x' / (n + '.png')) for n in records}
        candidates = [pack_atlas(crops, width * tier) for width in [768, 896, 1024, 1152]]
        atlas, placements = min(candidates, key=lambda pair: pair[0].width * pair[0].height)
        atlas.save(ROOT / f'packed_front_{tier}x.png')
        for name, rect in placements.items():
            records[name]['exports'][f'{tier}x']['atlas_xywh'] = rect
            assert np.array_equal(np.array(crops[name]), np.array(atlas.crop(
                (rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]))))
        aligned_bytes = sum(im.width * im.height * 4 for im in all_frames[tier].values())
        trimmed_bytes = sum(im.width * im.height * 4 for im in crops.values())
        memory[f'{tier}x'] = {'aligned_rgba_bytes': aligned_bytes, 'trimmed_rgba_bytes': trimmed_bytes,
                              'individual_crop_savings_percent': 100 * (1 - trimmed_bytes / aligned_bytes),
                              'atlas_size': atlas.size, 'atlas_rgba_bytes': atlas.width * atlas.height * 4}

    review = Image.new('RGBA', (6 * 355, 7 * 289))
    full = Image.new('RGBA', (6 * 710, 7 * 578))
    for row, action in enumerate(source['actions']):
        names = [Path(f['source']).stem for f in action['frames']]
        sheet = Image.new('RGBA', (len(names) * 710, 578))
        comparisons, playbacks = [], []
        for col, name in enumerate(names):
            a = all_frames[1][name]
            b = all_frames[2][name]
            review.paste(a, (col * 355, row * 289))
            full.paste(b, (col * 710, row * 578))
            sheet.paste(b, (col * 710, 0))
            compare = Image.new('RGB', (710, 310), (42, 45, 44))
            compare.paste(composite(native_image(name), (42, 45, 44)), (0, 20))
            compare.paste(composite(a, (42, 45, 44)), (355, 20))
            d = ImageDraw.Draw(compare)
            d.text((5, 4), name + ' native | restored at same logical scale', fill='white')
            d.line((0, 309, 710, 309), fill=(60, 190, 220))
            comparisons.append(compare)
            playbacks.append(composite(b, (42, 45, 44)))
        label = action['name'].lower()
        sheet.save(ROOT / 'action_sheets_2x' / (label + '.png'))
        durations = [125] * len(names) if len(names) > 1 else [500]
        # APNG preserves 125ms exactly; GIF gets explicit 120/130ms alternation for review only.
        for images, suffix in [(playbacks, ''), (comparisons, '_comparison')]:
            images[0].save(ROOT / 'previews' / (label + suffix + '.png'), save_all=True,
                           append_images=images[1:], duration=durations, loop=0)
            images[0].save(ROOT / 'previews' / (label + suffix + '.gif'), save_all=True,
                           append_images=images[1:], duration=[120 if i % 2 == 0 else 130 for i in range(len(names))]
                           if len(names) > 1 else [500], loop=0)
        contact = Image.new('RGB', (710 * 3, 310 * math.ceil(len(names) / 3)), (42, 45, 44))
        for i, im in enumerate(comparisons):
            contact.paste(im, ((i % 3) * 710, (i // 3) * 310))
        contact.save(ROOT / 'previews' / (label + '_all_frames.png'))
    review.save(ROOT / 'front_all_actions_1x.png')
    full.save(ROOT / 'front_all_actions_2x.png')
    for label, color in [('dark', (34, 37, 36)), ('light', (225, 226, 222))]:
        im = composite(review, color)
        draw = ImageDraw.Draw(im)
        for i, action in enumerate(source['actions']):
            draw.text((8, i * 289 + 5), action['name'], fill=(150, 120, 50))
        im.save(ROOT / 'previews' / ('all_actions_' + label + '.png'))
    manifest = {'direction': 'front / native index 0', 'frame_count': len(records),
                'logical_canvas': CANVAS, 'logical_pivot': [177.5, 289], 'native_center_flag': False,
                'runtime_trim_support': False, 'installed': False,
                'alpha': 'straight RGBA PNG, local chroma matte plus RGB unmixing; filtered in premultiplied space',
                'scale_groups': scales, 'actions': source['actions'], 'frames': records, 'memory': memory,
                'checks': {'native_hashes_unchanged': True, 'restored_source_silhouettes_not_clipped': True,
                           'every_crop_reconstructs_aligned_frame_exactly': True, 'atlas_crops_match_individuals': True},
                'limitations': ['AI inferred detail and perspective differ from native art; registration is approximate.',
                                '2x is a packaging tier: six-frame AI sheets have about 1.5x native linear detail.',
                                'True-color PNG does not retain native indexed palette swaps.',
                                'No runtime assets/tables changed; cropped exports require offset-aware rendering.']}
    (ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'scales': scales, 'memory': memory, 'checks': manifest['checks']}, indent=2))


if __name__ == '__main__':
    build()
