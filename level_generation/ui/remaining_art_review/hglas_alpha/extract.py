#!/usr/bin/env python3
"""Fit the four retained/edited hourglass sheets to 121 transparent x2 frames."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
ROOT = REVIEW.parents[2]
HUD = ROOT / 'level_generation/ui/hud_inventory'

ALPHA_MASTERS = {
    '807e40c25812423989b50b533dedf526': HERE / 'raw_rgb_sheet_1_alpha.png',
    'e59cc5d4d4ca4f03800a734c6492f5dd': HERE / 'raw_rgb_sheet_2_alpha.png',
    '6f9cfc8a92494a0f879e4ec4b87ff4ef': HUD / 'checkpoint/attempts/6f9cfc8a92494a0f879e4ec4b87ff4ef/raw.png',
    'e90f5603df7e440ea6e54e7b54af8cb1': HUD / 'checkpoint/attempts/e90f5603df7e440ea6e54e7b54af8cb1/raw.png',
}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def native_subject_bbox(card):
    with Image.open(REVIEW / card['original']) as image:
        pixels = np.asarray(image.convert('RGB')).astype(np.int16)
    red, green, blue = pixels[:, :, 0], pixels[:, :, 1], pixels[:, :, 2]
    if card['name'] == 'hglas000':
        subject = (red > 70) & (red - green > 25) & (red - blue > 30)
    else:
        subject = (blue < 95) & (red - blue > 20)
    opened = ndimage.binary_opening(subject, iterations=1)
    labels, _ = ndimage.label(opened)
    areas = np.bincount(labels.ravel())
    areas[0] = 0
    relevant = areas[labels] >= max(2, areas.max() * .05)
    ys, xs = np.nonzero(relevant)
    if not len(xs):
        raise ValueError(f'Cannot locate native hourglass subject: {card["id"]}')
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def subject_region(box, all_boxes, size):
    x0, y0, x1, y1 = box
    bounds = [max(0, x0 - 32), max(0, y0 - 32), min(size[0], x1 + 32), min(size[1], y1 + 32)]
    for other in all_boxes:
        if other == box:
            continue
        ox0, oy0, ox1, oy1 = other
        if min(y1, oy1) - max(y0, oy0) > .4 * min(y1 - y0, oy1 - oy0):
            if ox1 <= x0:
                bounds[0] = max(bounds[0], (ox1 + x0) // 2)
            elif ox0 >= x1:
                bounds[2] = min(bounds[2], (ox0 + x1) // 2)
        if min(x1, ox1) - max(x0, ox0) > .4 * min(x1 - x0, ox1 - ox0):
            if oy1 <= y0:
                bounds[1] = max(bounds[1], (oy1 + y0) // 2)
            elif oy0 >= y1:
                bounds[3] = min(bounds[3], (oy0 + y1) // 2)
    return bounds


def raw_subject_bbox(image):
    alpha = np.asarray(image.getchannel('A'))
    labels, _ = ndimage.label(alpha >= 32, structure=np.ones((3, 3), dtype=np.uint8))
    areas = np.bincount(labels.ravel())
    areas[0] = 0
    relevant = areas[labels] >= max(4, areas.max() * .001)
    ys, xs = np.nonzero(relevant)
    if not len(xs):
        raise ValueError('Empty returned hourglass frame')
    return [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]


def main():
    cards = json.loads((REVIEW / 'catalog.js').read_text().split('=', 1)[1].strip().removesuffix(';'))['items']
    selected = [card for card in cards if card['name'].startswith('hglas')]
    if len(selected) != 121:
        raise ValueError(f'Expected 121 hourglass frames, got {len(selected)}')
    attempts = {attempt['id']: attempt for attempt in json.loads(
        (HUD / 'checkpoint/state.json').read_text())['attempts']}
    records = {}
    for attempt_id, master_path in ALPHA_MASTERS.items():
        attempt = attempts[attempt_id]
        layout_path = Path(attempt['payload'])
        layout = json.loads(layout_path.read_text())['execution_layout']
        reference_size = layout['canvas_size']
        raw_hash = digest(master_path)
        with Image.open(master_path) as image:
            if image.mode != 'RGBA' or image.getchannel('A').getextrema() != (0, 255):
                raise ValueError(f'Not a transparent sheet: {master_path}')
            sx = image.width / reference_size[0]
            sy = image.height / reference_size[1]
            projected = {
                key: [round(rect[0] * sx), round(rect[1] * sy),
                      round((rect[0] + rect[2]) * sx), round((rect[1] + rect[3]) * sy)]
                for key, rect in layout['cell_rects'].items()
            }
            for card in selected:
                if card['raw']['attempt'] != attempt_id:
                    continue
                region_box = subject_region(projected[card['id']], list(projected.values()), image.size)
                region = image.crop(tuple(region_box))
                local_bbox = raw_subject_bbox(region)
                raw_box = [region_box[0] + local_bbox[0], region_box[1] + local_bbox[1],
                           region_box[0] + local_bbox[2], region_box[1] + local_bbox[3]]
                native_bbox = native_subject_bbox(card)
                native_width = native_bbox[2] - native_bbox[0]
                native_height = native_bbox[3] - native_bbox[1]
                sampling = [(raw_box[2] - raw_box[0]) / native_width,
                            (raw_box[3] - raw_box[1]) / native_height]
                if min(sampling) < 2:
                    records[card['id']] = {'status': 'hold', 'reason': 'subject_sampling_below_2x',
                                           'sampling': sampling, 'raw_box': raw_box}
                    continue
                if max(sampling) / min(sampling) > 1.2:
                    records[card['id']] = {'status': 'hold', 'reason': 'subject_aspect_mismatch',
                                           'sampling': sampling, 'raw_box': raw_box}
                    continue
                crop = image.crop(tuple(raw_box)).convert('RGBa')
                fitted = crop.resize((native_width * 2, native_height * 2),
                                     Image.Resampling.LANCZOS).convert('RGBA')
                candidate = Image.new('RGBA', tuple(card['x2_size']), (0, 0, 0, 0))
                candidate.alpha_composite(fitted, (native_bbox[0] * 2, native_bbox[1] * 2))
                path = HERE / 'candidates' / (card['id'] + '.png')
                path.parent.mkdir(exist_ok=True)
                candidate.save(path)
                records[card['id']] = {
                    'status': 'candidate_technical', 'artifact': str(path.relative_to(REVIEW)),
                    'artifact_sha256': digest(path), 'master': str(master_path.relative_to(ROOT)),
                    'master_sha256': raw_hash, 'attempt': attempt_id, 'layout': str(layout_path.relative_to(ROOT)),
                    'source_sha256': card['source_sha256'],
                    'raw_box': raw_box, 'region_box': region_box, 'native_subject_bbox': native_bbox,
                    'sampling': sampling,
                    'transparent_foreground_override': True,
                    'visual_status': 'pending_manual_review',
                }
    if len(records) != 121:
        raise ValueError(f'Only {len(records)} of 121 frames extracted')
    closing_key = 'engine--icons--hglas120.bmp'
    closing_master = HERE / 'hglas120-imagegen-master.png'
    if records[closing_key]['status'] == 'hold' and closing_master.is_file():
        card = next(card for card in selected if card['id'] == closing_key)
        with Image.open(closing_master) as image:
            if image.mode != 'RGBA' or image.getchannel('A').getextrema() != (0, 255):
                raise ValueError('Closing plate master has no transparent alpha')
            # Imagegen leaves near-zero alpha noise outside the visible plate.
            # Bound the actual foreground, while retaining feathered edge pixels
            # immediately adjacent to it in the crop.
            alpha = np.asarray(image.getchannel('A'))
            ys, xs = np.nonzero(alpha >= 32)
            bounds = (max(0, int(xs.min()) - 2), max(0, int(ys.min()) - 2),
                      min(image.width, int(xs.max()) + 3), min(image.height, int(ys.max()) + 3))
            native_bbox = native_subject_bbox(card)
            native_size = (native_bbox[2] - native_bbox[0], native_bbox[3] - native_bbox[1])
            sampling = [(bounds[2] - bounds[0]) / native_size[0],
                        (bounds[3] - bounds[1]) / native_size[1]]
            if min(sampling) < 2 or max(sampling) / min(sampling) > 1.2:
                raise ValueError(f'Closing plate master sampling/shape: {sampling}')
            plate = image.crop(bounds).convert('RGBa').resize(
                (native_size[0] * 2, native_size[1] * 2), Image.Resampling.LANCZOS).convert('RGBA')
            candidate = Image.new('RGBA', tuple(card['x2_size']), (0, 0, 0, 0))
            candidate.alpha_composite(plate, (native_bbox[0] * 2, native_bbox[1] * 2))
            output = HERE / 'candidates' / (closing_key + '.png')
            candidate.save(output)
            records[closing_key] = {
                'status': 'candidate_technical', 'artifact': str(output.relative_to(REVIEW)),
                'artifact_sha256': digest(output), 'master': str(closing_master.relative_to(ROOT)),
                'source_sha256': card['source_sha256'],
                'master_sha256': digest(closing_master), 'raw_box': bounds,
                'native_subject_bbox': native_bbox, 'sampling': sampling,
                'transparent_foreground_override': True, 'visual_status': 'pending_manual_review',
                'method': 'single-frame transparent closing-plate imagegen repair',
            }
    (HERE / 'report.json').write_text(json.dumps({'schema': 1, 'items': records}, indent=2) + '\n')
    print(f'{sum(row["status"] == "candidate_technical" for row in records.values())} transparent '
          f'hourglass frames, {sum(row["status"] == "hold" for row in records.values())} holds')


if __name__ == '__main__':
    main()
