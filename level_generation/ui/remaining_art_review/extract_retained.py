#!/usr/bin/env python3
"""Extract technical review candidates from retained UI sheet masters.

Only measured, fully bounded cells become candidates. The source, attempt,
crop, and sampling stay in a separate report. No checkpoint/art acceptance is
performed here.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HUD = ROOT / 'level_generation/ui/hud_inventory'
OUTPUT = HERE / 'extracted_retained'
sys.path.insert(0, str(HUD))
from freeze_targets import rendered  # noqa: E402


def read_json(path):
    return json.loads(path.read_text())


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def layout_for(raw, attempts):
    attempt_id = raw['attempt']
    if attempt_id.startswith('dense:'):
        _, bundle, sheet = attempt_id.split(':')
        layout_path = HUD / 'chat_bundles/dense64_20260916' / bundle / 'sheets' / sheet / 'layout.json'
        layout = read_json(layout_path)
        return layout['reference_size'], {cell['id']: cell['reference_rect'] for cell in layout['cells']}, \
            str(layout_path.relative_to(ROOT))
    attempt = attempts.get(attempt_id)
    if attempt is None:
        return None
    payload_path = Path(attempt['payload'])
    payload = read_json(payload_path)
    layout = payload.get('execution_layout')
    if not layout:
        if attempt_id == '63141cd6ecfb45d698b17ae88fd99ae1':
            with Image.open(attempt['raw']) as master:
                width, height = master.size
            middle = width // 2
            return [width, height], {
                'engine--icons--item150.bmp': [0, 0, middle, height],
                'engine--icons--item151.bmp': [middle, 0, width - middle, height],
            }, 'reviewed left/right subject assignment from original two-cell master'
        return None
    return layout['canvas_size'], layout['cell_rects'], str(payload_path.relative_to(ROOT))


def magenta_mask(pixels):
    red = pixels[:, :, 0].astype(np.int16)
    green = pixels[:, :, 1].astype(np.int16)
    blue = pixels[:, :, 2].astype(np.int16)
    return ((red > 165) & (blue > 165) & (green < 105)
            & (red - green > 85) & (blue - green > 85))


def projected_box(rect, reference_size, raw_size):
    x, y, width, height = rect
    scale_x = raw_size[0] / reference_size[0]
    scale_y = raw_size[1] / reference_size[1]
    return [round(x * scale_x), round(y * scale_y), round((x + width) * scale_x),
            round((y + height) * scale_y)]


def opaque_box(pixels, box, projected_boxes):
    """Find the image boundary near a nominal slot without crossing a neighbor."""
    height, width = pixels.shape[:2]
    x0, y0, x1, y1 = box
    padding = max(3, min(16, round(min(x1 - x0, y1 - y0) * .035)))
    search = [max(0, x0 - padding), max(0, y0 - padding),
              min(width, x1 + padding), min(height, y1 + padding)]
    for other in projected_boxes:
        if other == box:
            continue
        ox0, oy0, ox1, oy1 = other
        if min(y1, oy1) - max(y0, oy0) > .6 * min(y1 - y0, oy1 - oy0):
            if ox1 <= x0:
                search[0] = max(search[0], (ox1 + x0) // 2)
            elif ox0 >= x1:
                search[2] = min(search[2], (ox0 + x1) // 2)
        if min(x1, ox1) - max(x0, ox0) > .6 * min(x1 - x0, ox1 - ox0):
            if oy1 <= y0:
                search[1] = max(search[1], (oy1 + y0) // 2)
            elif oy0 >= y1:
                search[3] = min(search[3], (oy0 + y1) // 2)
    sx0, sy0, sx1, sy1 = search
    region = pixels[sy0:sy1, sx0:sx1]
    if region.size == 0:
        return None, 'empty_search_region'
    matte = magenta_mask(region)
    if matte.mean() < .005:
        return box, 'projected_no_matte_separator'
    content = ~matte
    x_score = content.mean(axis=0)
    y_score = content.mean(axis=1)
    x_content = np.flatnonzero(x_score > .45)
    y_content = np.flatnonzero(y_score > .45)
    if not len(x_content) or not len(y_content):
        return None, 'no_opaque_rectangle'
    found = [sx0 + int(x_content[0]), sy0 + int(y_content[0]),
             sx0 + int(x_content[-1]) + 1, sy0 + int(y_content[-1]) + 1]
    ratios = ((found[2] - found[0]) / (x1 - x0), (found[3] - found[1]) / (y1 - y0))
    if not all(.93 <= ratio <= 1.07 for ratio in ratios):
        return None, f'boundary_size_mismatch:{ratios[0]:.3f},{ratios[1]:.3f}'
    return found, 'measured_matte_boundary'


def region_around(box, boxes, image_size):
    x0, y0, x1, y1 = box
    padding = max(16, round(min(x1 - x0, y1 - y0) * .55))
    bounds = [max(0, x0 - padding), max(0, y0 - padding),
              min(image_size[0], x1 + padding), min(image_size[1], y1 + padding)]
    for other in boxes:
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


def matte_and_visible(region):
    pixels = np.asarray(region.convert('RGBA'))
    rgb = pixels[:, :, :3]
    if region.mode == 'RGBA' and (pixels[:, :, 3] == 0).mean() > .02:
        visible = pixels[:, :, 3] >= 16
        return 'returned_alpha', visible, region.convert('RGBA')
    magenta = magenta_mask(rgb)
    black = rgb.max(axis=2) < 20
    if magenta.mean() > .1:
        background = magenta
        mode = 'magenta_matte'
    elif black.mean() > .1:
        background = black
        mode = 'black_matte'
    else:
        return None, None, None
    border = np.zeros(background.shape, dtype=bool)
    border[0] = background[0]
    border[-1] = background[-1]
    border[:, 0] = background[:, 0]
    border[:, -1] = background[:, -1]
    exterior = ndimage.binary_propagation(border, mask=background)
    if not exterior.any():
        return None, None, None
    visible = ~exterior
    # Isolated internal holes in a cutout are usually the same extraction matte.
    if mode == 'magenta_matte':
        visible &= ~ndimage.binary_erosion(background, iterations=1)
    else:
        visible &= ~ndimage.binary_erosion(background, iterations=1)
    core = ndimage.binary_erosion(visible, iterations=2)
    if not core.any():
        core = visible.copy()
    if not core.any():
        return None, None, None
    rgb_float = rgb.astype(np.float32) / 255
    _, fg_indices = ndimage.distance_transform_edt(~core, return_indices=True)
    _, bg_indices = ndimage.distance_transform_edt(~exterior, return_indices=True)
    foreground = rgb_float[fg_indices[0], fg_indices[1]]
    backdrop = rgb_float[bg_indices[0], bg_indices[1]]
    direction = foreground - backdrop
    numerator = ((rgb_float - backdrop) * direction).sum(axis=2)
    denominator = np.maximum((direction * direction).sum(axis=2), 1e-8)
    alpha = np.clip(numerator / denominator, 0, 1)
    alpha[core] = 1
    alpha[exterior] = 0
    alpha[~ndimage.binary_dilation(visible, iterations=3)] = 0
    recovered = (rgb_float - (1 - alpha[:, :, None]) * backdrop) / np.maximum(alpha[:, :, None], 1 / 255)
    if mode == 'magenta_matte':
        expected = np.minimum(foreground[:, :, 0], foreground[:, :, 2]) - foreground[:, :, 1]
        excess = np.maximum(0, np.minimum(recovered[:, :, 0], recovered[:, :, 2])
                            - recovered[:, :, 1] - expected - 2 / 255)
        recovered[:, :, 0] -= excess
        recovered[:, :, 2] -= excess
    recovered[core] = rgb_float[core]
    recovered[alpha == 0] = 0
    rgba = np.round(np.clip(np.dstack([recovered, alpha]), 0, 1) * 255).astype(np.uint8)
    return mode, visible, Image.fromarray(rgba, 'RGBA')


def extract_cutout(card, target, image, reference_size, rects, raw_path, layout_path):
    boxes = {key: projected_box(rect, reference_size, image.size) for key, rect in rects.items()}
    if card['id'] not in boxes:
        return {'status': 'hold', 'reason': 'target_missing_from_layout'}
    projected = boxes[card['id']]
    region_box = region_around(projected, list(boxes.values()), image.size)
    sx0, sy0, sx1, sy1 = region_box
    if sx1 <= sx0 or sy1 <= sy0:
        return {'status': 'hold', 'reason': 'empty_search_region'}
    region = image.crop(tuple(region_box))
    mode, visible, cleaned = matte_and_visible(region)
    if mode is None:
        return {'status': 'hold', 'reason': 'matte_or_alpha_unresolved', 'projected_box': projected}
    label, count = ndimage.label(visible, structure=np.ones((3, 3), dtype=np.uint8))
    areas = np.bincount(label.ravel())
    if len(areas) < 2:
        return {'status': 'hold', 'reason': 'empty_foreground'}
    areas[0] = 0
    min_area = max(3, round(areas.max() * .001))
    chosen = areas[label] >= min_area
    ys, xs = np.nonzero(chosen)
    if not len(xs):
        return {'status': 'hold', 'reason': 'empty_after_noise_filter'}
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    if bbox[0] == 0 or bbox[1] == 0 or bbox[2] == region.width or bbox[3] == region.height:
        opened = ndimage.binary_opening(visible, iterations=2)
        opened_labels, opened_count = ndimage.label(opened, structure=np.ones((3, 3), dtype=np.uint8))
        opened_areas = np.bincount(opened_labels.ravel())
        opened_areas[0] = 0
        border_labels = set(np.unique(np.concatenate((opened_labels[0], opened_labels[-1],
                                                       opened_labels[:, 0], opened_labels[:, -1]))))
        for border_label in border_labels:
            opened_areas[border_label] = 0
        if opened_count and opened_areas.max() >= max(8, round(chosen.sum() * .02)):
            main_label = int(opened_areas.argmax())
            core = opened_labels == main_label
            core = ndimage.binary_dilation(core, iterations=4) & visible
            ys, xs = np.nonzero(core)
            bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        if bbox[0] == 0 or bbox[1] == 0 or bbox[2] == region.width or bbox[3] == region.height:
            return {'status': 'hold', 'reason': 'foreground_touches_slot_boundary',
                    'projected_box': projected, 'region_box': region_box, 'local_bbox': bbox}
    source = ROOT / target['source_path']
    if digest(source) != target['source_sha256']:
        return {'status': 'hold', 'reason': 'source_hash_changed'}
    with Image.open(source) as native_file:
        native = rendered(native_file, target['compositing']['profiles'][0]).convert('RGBA')
    native_bbox = native.getchannel('A').getbbox()
    if native_bbox is None:
        return {'status': 'hold', 'reason': 'empty_native_alpha'}
    native_width = native_bbox[2] - native_bbox[0]
    native_height = native_bbox[3] - native_bbox[1]
    raw_width = bbox[2] - bbox[0]
    raw_height = bbox[3] - bbox[1]
    sampling = [raw_width / native_width, raw_height / native_height]
    if min(sampling) < 2:
        return {'status': 'hold', 'reason': 'subject_sampling_below_2x', 'sampling': sampling,
                'local_bbox': bbox}
    fit_ratio = max(sampling) / min(sampling)
    if fit_ratio > 1.2:
        return {'status': 'hold', 'reason': 'subject_aspect_mismatch', 'sampling': sampling,
                'local_bbox': bbox}
    cutout = cleaned.crop(tuple(bbox)).convert('RGBa')
    output = Image.new('RGBA', tuple(target['x2_size']), (0, 0, 0, 0))
    destination = (native_width * 2, native_height * 2)
    fitted = cutout.resize(destination, Image.Resampling.LANCZOS).convert('RGBA')
    output.alpha_composite(fitted, (native_bbox[0] * 2, native_bbox[1] * 2))
    artifact = OUTPUT / 'candidates' / (card['id'] + '.png')
    artifact.parent.mkdir(parents=True, exist_ok=True)
    output.save(artifact)
    raw_box = [sx0 + bbox[0], sy0 + bbox[1], sx0 + bbox[2], sy0 + bbox[3]]
    return {'status': 'candidate_technical', 'method': 'measured_' + mode + '_subject_bbox',
            'projected_box': projected, 'raw_box': raw_box, 'region_box': region_box,
            'sampling': sampling, 'fit_ratio': fit_ratio,
            'native_alpha_bbox': native_bbox, 'artifact': str(artifact.relative_to(HERE)),
            'artifact_sha256': digest(artifact), 'raw': str(raw_path.relative_to(ROOT)),
            'raw_sha256': digest(raw_path), 'layout': layout_path,
            'cleanup': target['compositing']['cleanup'], 'visual_status': 'pending_manual_review'}


def extract_opaque(card, target, image, reference_size, rects, raw_path, layout_path):
    raw_size = image.size
    boxes = {key: projected_box(rect, reference_size, raw_size) for key, rect in rects.items()}
    if card['id'] not in boxes:
        return {'status': 'hold', 'reason': 'target_missing_from_layout'}
    box = boxes[card['id']]
    pixels = np.asarray(image.convert('RGB'))
    measured, method = opaque_box(pixels, box, list(boxes.values()))
    if measured is None:
        return {'status': 'hold', 'reason': method, 'projected_box': box}
    x0, y0, x1, y1 = measured
    if x0 < 0 or y0 < 0 or x1 > raw_size[0] or y1 > raw_size[1]:
        return {'status': 'hold', 'reason': 'outside_master', 'raw_box': measured}
    sampling = [(x1 - x0) / target['native_size'][0], (y1 - y0) / target['native_size'][1]]
    if min(sampling) < 2 or max(sampling) / min(sampling) > 1.05:
        return {'status': 'hold', 'reason': 'insufficient_or_distorted_sampling',
                'raw_box': measured, 'sampling': sampling}
    returned_alpha = (card['name'].startswith('hglas') and image.mode == 'RGBA'
                      and image.getchannel('A').getextrema()[0] == 0)
    if returned_alpha:
        candidate = image.crop(tuple(measured)).convert('RGBa').resize(
            tuple(target['x2_size']), Image.Resampling.LANCZOS).convert('RGBA')
        method += '+returned_foreground_alpha'
    else:
        candidate = image.crop(tuple(measured)).convert('RGB').resize(tuple(target['x2_size']),
                                                                      Image.Resampling.LANCZOS)
    out = OUTPUT / 'candidates' / (card['id'] + '.png')
    out.parent.mkdir(parents=True, exist_ok=True)
    candidate.save(out)
    return {'status': 'candidate_technical', 'method': method, 'projected_box': box,
            'raw_box': measured, 'sampling': sampling, 'artifact': str(out.relative_to(HERE)),
            'artifact_sha256': digest(out), 'raw': str(raw_path.relative_to(ROOT)),
            'raw_sha256': digest(raw_path), 'layout': layout_path,
            'cleanup': target['compositing']['cleanup'],
            'visual_status': 'pending_manual_review'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['opaque', 'cutout'], default='opaque')
    args = parser.parse_args()
    catalog = json.loads(
        (HERE / 'catalog.js').read_text().split('=', 1)[1].strip().removesuffix(';'))
    targets = {target['id']: target for target in read_json(HUD / 'expected_targets.json')['targets']}
    attempts = {attempt['id']: attempt for attempt in read_json(HUD / 'checkpoint/state.json')['attempts']}
    selected = [card for card in catalog['items'] if not card['candidates'] and card['raw']
                and (targets[card['id']]['compositing']['cleanup'] == 'opaque_canvas') == (args.mode == 'opaque')]
    for card in selected:
        if card['id'] == 'engine--icons--7item134.bmp':
            attempt = attempts['b11956b69e4a4ba284f9943a840fc157']
            card['raw'] = {'master': str(Path(attempt['raw']).relative_to(HERE, walk_up=True)),
                           'attempt': attempt['id']}
    grouped = {}
    for card in selected:
        grouped.setdefault(card['raw']['master'], []).append(card)
    OUTPUT.mkdir(exist_ok=True)
    report_path = OUTPUT / 'report.json'
    report = read_json(report_path) if report_path.is_file() else {'schema': 1, 'items': {}}
    for index, (name, cards) in enumerate(grouped.items(), 1):
        path = (HERE / name).resolve()
        layout = layout_for(cards[0]['raw'], attempts)
        with Image.open(path) as image:
            for card in cards:
                if layout is None:
                    record = {'status': 'hold', 'reason': 'missing_execution_layout'}
                else:
                    size, rects, layout_path = layout
                    extractor = extract_opaque if args.mode == 'opaque' else extract_cutout
                    record = extractor(card, targets[card['id']], image, size, rects, path, layout_path)
                report['items'][card['id']] = record
        report_path.write_text(json.dumps(report, indent=2) + '\n')
        print(f'{index}/{len(grouped)} {len(cards)} cells from {path.name}: '
              f'{sum(report["items"][card["id"]]["status"] == "candidate_technical" for card in cards)} '
              'candidates', flush=True)


if __name__ == '__main__':
    main()
