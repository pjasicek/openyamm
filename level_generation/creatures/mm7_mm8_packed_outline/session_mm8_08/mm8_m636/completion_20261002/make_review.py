"""Local all-pose review panels; these do not confer acceptance."""
from pathlib import Path
import json
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[5]
sys.path.insert(0, str(REPO / 'level_generation/creatures'))
from mm8_restore_queue import native

def load(name):
    return json.loads((ROOT / name).read_text())

def opaque(im, colour):
    bg = Image.new('RGBA', im.size, colour)
    bg.alpha_composite(im)
    return bg.convert('RGB')

def master_canvas(name, palette=None, mask=False):
    record = registration[name]
    im = Image.open(ROOT / ('masks_2x' if mask else 'aligned_2x') / (name + '.png'))
    if palette is not None:
        im = Image.open(ROOT / 'previews' / f'{name}_{palette}.png')
    if mask:
        alpha = Image.open(ROOT / 'aligned_2x' / (name + '.png')).getchannel('A')
        im = Image.merge('RGBA', (im, im, im, alpha))
    canvas = Image.new('RGBA', (544, 544))
    origin = record['canvas_origin_px']
    canvas.alpha_composite(im.convert('RGBA'), (origin[0] + 16, origin[1] + 16))
    return canvas.convert('RGBa').resize((272, 272), Image.Resampling.LANCZOS).convert('RGBA')

def fish_features(im):
    # Independently measured fish-body centres, never used to fit translation or scale.
    alpha = np.asarray(im.convert('RGBA'))[:, :, 3]
    labels, count = ndimage.label(alpha > 64)
    features = []
    for label, bounds in enumerate(ndimage.find_objects(labels), 1):
        yy, xx = np.where(labels[bounds] == label)
        if len(xx) >= 12:
            features.append([float(xx.mean() + bounds[1].start), float(yy.mean() + bounds[0].start)])
    return dict(upper_fish_body=min(features, key=lambda p: p[1]),
                rightmost_fish_body=max(features, key=lambda p: p[0]))

run, registration, manifest = load('run.json'), load('registration.json'), load('draft_manifest.json')
review = ROOT / 'review'
features = {}
for job in run['jobs']:
    names = job['frames']
    panel = Image.new('RGB', (1632, ((len(names) + 2) // 3) * 290), '#292d2b')
    draw = ImageDraw.Draw(panel)
    for index, name in enumerate(names):
        x, y = index % 3 * 544, index // 3 * 290
        draw.text((x + 4, y + 3), f'{index + 1}: {name}  native | restored', fill='white')
        original = Image.new('RGBA', (272, 272))
        original.alpha_composite(native(ROOT, name, 636), (8, 8))
        panel.paste(original, (x, y + 18), original)
        restored = master_canvas(name)
        panel.paste(restored, (x + 272, y + 18), restored)
        if name not in features:
            n = fish_features(native(ROOT, name, 636))
            r = fish_features(Image.open(ROOT / 'aligned_2x' / (name + '.png')))
            origin = registration[name]['canvas_origin_px']
            r = {label: [(p[0] + origin[0]) / 2, (p[1] + origin[1]) / 2] for label, p in r.items()}
            features[name] = dict(native=n, enhanced_logical=r,
                purpose='Independent actual-art diagnostics; neither feature fitted translation or scale',
                correspondence_requires_visual_review=True)
        for col, key in enumerate(['native', 'enhanced_logical']):
            for label, point in features[name][key].items():
                px, py = x + col * 272 + 8 + point[0], y + 26 + point[1]
                colour = '#35dddd' if label == 'upper_fish_body' else '#eeac54'
                draw.ellipse((px - 3, py - 3, px + 3, py + 3), outline=colour)
    panel.save(review / f'{job["id"]}_all_poses.png')
    for start in range(0, len(names), 6):
        panel = Image.new('RGB', (1088, min(6, len(names) - start) * 290), '#292d2b')
        draw = ImageDraw.Draw(panel)
        for row, name in enumerate(names[start:start + 6]):
            for col, palette in enumerate([636, 637, 638, None]):
                x, y = col * 272, row * 290
                draw.text((x + 4, y + 3), f'{name}  ' + (str(palette) if palette else 'R8 mask'), fill='white')
                im = master_canvas(name, palette, palette is None)
                panel.paste(im, (x, y + 18), im)
        panel.save(review / f'{job["id"]}_palettes_masks_{start // 6}.png')

atlas = {}
for start in range(0, len(registration), 8):
    panel = Image.new('RGB', (512, min(8, len(registration) - start) * 150), '#292d2b')
    draw = ImageDraw.Draw(panel)
    for row, name in enumerate(list(registration)[start:start + 8]):
        frame = manifest['frames'][name]
        base = Image.open(ROOT / 'cleaned' / (name + '.png')).convert('RGBA')
        alpha = np.asarray(base)[:, :, 3]
        labels, count = ndimage.label(alpha > 128)
        sizes = np.bincount(labels.ravel()); sizes[0] = 0
        yy, xx = np.where(labels == sizes.argmax())
        cx, cy = int(np.median(xx)), int(np.median(yy))
        material = base.crop((cx - 64, cy - 64, cx + 64, cy + 64))
        if frame['page'] not in atlas:
            atlas[frame['page']] = Image.open(ROOT / manifest['pages'][frame['page']]['base']).convert('RGBA')
        x, y, w, h = frame['atlas_xywh']
        sprite = atlas[frame['page']].crop((x, y, x + w, y + h))
        a = np.asarray(sprite)[:, :, 3]
        ey, ex = np.where((a > 16) & (a < 224))
        # Pick an actual semitransparent fin edge, never hidden RGB at alpha zero.
        edge_x, edge_y = int(ex[len(ex) // 2]), int(ey[len(ey) // 2])
        edge = sprite.crop((edge_x - 64, edge_y - 64, edge_x + 64, edge_y + 64))
        draw.text((4, row * 150 + 2), f'{name} material 100% dark/ivory | atlas alpha 100% dark/ivory', fill='white')
        for col, (im, colour) in enumerate([(material, '#292d2b'), (material, '#eee8dc'),
                                           (edge, '#292d2b'), (edge, '#eee8dc')]):
            panel.paste(opaque(im, colour), (col * 128, row * 150 + 20))
    panel.save(review / f'all_material_alpha_100pct_{start // 8:02d}.png')
(review / 'independent_fish_features.json').write_text(json.dumps(features, indent=2) + '\n')
print('Reviewed candidate panels written:', len(list(review.glob('*all_poses.png'))),
      len(list(review.glob('*palettes_masks_*.png'))), len(list(review.glob('all_material_alpha_100pct_*.png'))))
