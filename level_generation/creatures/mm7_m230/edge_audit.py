"""Fast m230 contour audit; scores nominate patches for visual review, not ground-truth alpha.

Run automatically by package.py. Optional --before compares against a saved pre-correction
project containing cleaned/, aligned_2x/, registration.json and manifest.json.
The green base has no intentional magenta material; never apply this score as a variant filter.
"""
from pathlib import Path
import argparse
import json

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parent


def measure(im):
    rgba = np.asarray(im).astype(float)
    alpha = rgba[:, :, 3] / 255
    band = (alpha > 0) & ((ndimage.distance_transform_edt(alpha >= .5) <= 4) | (alpha < 1))
    excess = np.maximum(0, np.minimum(rgba[:, :, 0], rgba[:, :, 2]) - rgba[:, :, 1]) * alpha
    score = np.where(band, excess, 0)
    y, x = np.unravel_index(np.argmax(score), score.shape)
    return {'edge_pixels': int(band.sum()), 'over8': int((score > 8).sum()),
            'over16': int((score > 16).sum()), 'max_visible_magenta': round(float(score.max()), 3),
            'max_xy': [int(x), int(y)]}


def composite(im, color):
    result = Image.new('RGBA', im.size, (*color, 255))
    result.alpha_composite(im)
    return result.convert('RGB')


def audit(before=None, project=None):
    root = Path(project) if project else ROOT
    manifest = json.loads((root / 'manifest.json').read_text())
    pages = [Image.open(root / p['base']).convert('RGBA') for p in manifest['pages']]
    records = []
    for name, frame in manifest['frames'].items():
        x, y, w, h = frame['atlas_xywh']
        final = pages[frame['page']].crop((x, y, x + w, y + h))
        clean = Image.open(root / f'cleaned/{name}.png').convert('RGBA')
        row = {'frame': name, 'cleaned': measure(clean), 'final': measure(final)}
        if before:
            old_clean = Image.open(before / f'cleaned/{name}.png').convert('RGBA')
            old_aligned = Image.open(before / f'aligned_2x/{name}.png').convert('RGBA')
            aligned = Image.open(root / f'aligned_2x/{name}.png').convert('RGBA')
            assert old_clean.size == clean.size and old_aligned.size == aligned.size, name
            assert np.array_equal(np.asarray(old_clean)[:, :, 3], np.asarray(clean)[:, :, 3]), name
            assert np.array_equal(np.asarray(old_aligned)[:, :, 3], np.asarray(aligned)[:, :, 3]), name
            row['before_cleaned'] = measure(old_clean)
            row['before_final'] = measure(old_aligned.crop(frame['crop_in_aligned_px']))
        records.append(row)
    if before:
        old_manifest = json.loads((before / 'manifest.json').read_text())
        for key in ['frames', 'animations', 'native_group_bindings', 'logical_pivot', 'memory_bytes']:
            assert old_manifest[key] == manifest[key], key
        old_registration = json.loads((before / 'registration.json').read_text())
        registration = json.loads((root / 'registration.json').read_text())
        assert old_registration == registration, 'Registration or extraction changed'
    stages = ['cleaned', 'final'] + (['before_cleaned', 'before_final'] if before else [])
    totals = {stage: {key: sum(row[stage][key] for row in records) for key in ['edge_pixels', 'over8', 'over16']}
              for stage in stages}
    for stage in stages:
        totals[stage]['max_visible_magenta'] = max(row[stage]['max_visible_magenta'] for row in records)
    report = {'frames': len(records), 'band_width_px': 4,
              'score': 'alpha * max(0,min(R,B)-G); RGB 0..255; transparent padding excluded',
              'interpretation': 'Candidate ranking only; inspect contact before accepting. Base palette only.',
              'compared_alpha_registration_placement_timing_unchanged': bool(before),
              'totals': totals, 'records': records}
    filename = 'edge_correction' if before else 'edge_current'
    (root / f'review/{filename}.json').write_text(json.dumps(report, indent=2) + '\n')
    # Worst candidates after export, plus the previously reported five problem locations.
    patches = [('m230ad1', [250, 251]), ('m230wc4', [360, 340]), ('m230wc2', [205, 373]),
               ('m230ab2', [150, 264]), ('m230ne2', [225, 197])]
    patches = [item for item in patches if item[0] in manifest['frames']]
    for row in sorted(records, key=lambda r: -r['final']['max_visible_magenta'])[:6]:
        frame = manifest['frames'][row['frame']]
        x, y = row['final']['max_xy']
        patches.append((row['frame'], [x + frame['crop_in_aligned_px'][0], y + frame['crop_in_aligned_px'][1]]))
    columns = 4 if before else 2
    contact = Image.new('RGB', (columns * 224, len(patches) * 250), (40, 40, 40))
    draw = ImageDraw.Draw(contact)
    for row, (name, (x, y)) in enumerate(patches):
        frame = manifest['frames'][name]
        px, py, w, h = frame['atlas_xywh']
        final = pages[frame['page']].crop((px, py, px + w, py + h))
        cx, cy = frame['crop_in_aligned_px'][:2]
        box = (x - 16, y - 16, x + 16, y + 16)
        crop = final.crop((box[0] - cx, box[1] - cy, box[2] - cx, box[3] - cy))
        pictures = []
        for label, color in [('dark', (30, 30, 30)), ('light', (238, 238, 238))]:
            if before:
                old = Image.open(before / f'aligned_2x/{name}.png').convert('RGBA').crop(box)
                pictures.append((f'Before / {label}', composite(old, color)))
            pictures.append((f'Corrected / {label}', composite(crop, color)))
        for col, (title, picture) in enumerate(pictures):
            origin = (col * 224, row * 250)
            draw.text((origin[0] + 3, origin[1] + 5), f'{name} {title}', fill='white')
            contact.paste(picture.resize((224, 224), Image.Resampling.NEAREST), (origin[0], origin[1] + 26))
    contact.save(root / f'review/{filename}.png')
    print(json.dumps({'edge_audit': filename, 'frames': len(records), 'totals': totals}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path)
    parser.add_argument('--project', type=Path)
    args = parser.parse_args()
    audit(args.before, args.project)
