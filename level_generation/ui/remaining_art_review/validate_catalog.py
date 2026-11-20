#!/usr/bin/env python3
"""Validate review artifacts and rank visible edge anomalies for inspection."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def spill_summary(path):
    with Image.open(path) as image:
        pixels = np.asarray(image.convert('RGBA')).astype(np.int16)
    rgb = pixels[:, :, :3]
    alpha = pixels[:, :, 3]
    visible = alpha >= 32
    core = alpha >= 192
    contour = core & ~ndimage.binary_erosion(core, iterations=3, border_value=1)
    contour |= visible & ~core
    red, green, blue = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    pink = contour & (np.minimum(red, blue) - green >= 80) & (red >= 140) & (blue >= 140)
    key_green = contour & (green - np.maximum(red, blue) >= 80) & (green >= 140)
    return {
        'visible_pixels': int(visible.sum()),
        'pink_edge_pixels': int(pink.sum()),
        'green_edge_pixels': int(key_green.sum()),
        'pink_edge_fraction': round(float(pink.sum() / max(1, contour.sum())), 5),
        'green_edge_fraction': round(float(key_green.sum() / max(1, contour.sum())), 5),
    }


def audit_first_pass_alpha_crops(items):
    plan = json.loads((HERE / 'imagegen_regen/plan.json').read_text())
    by_id = {cell['id']: (sheet, cell) for sheet in plan['sheets'] for cell in sheet['cells']}
    selected = defaultdict(list)
    for item in items:
        if not item.get('imagegen_slice') or not item['candidates'][0]['path'].startswith(
                'imagegen_regen/candidates/'):
            continue
        sheet, cell = by_id[item['id']]
        if sheet['role'] == 'alpha':
            selected[sheet['id']].append((sheet, cell))
    checked = 0
    for sheet_id, entries in selected.items():
        with Image.open(HERE / 'imagegen_regen/returns' / f'{sheet_id}.png') as image:
            alpha = np.asarray(image.convert('RGBA').getchannel('A')) >= 16
            raw_size = image.size
        labels, count = ndimage.label(alpha)
        yy, xx = np.indices(labels.shape)
        areas = np.bincount(labels.ravel())
        centers_x = np.bincount(labels.ravel(), weights=xx.ravel()) / np.maximum(areas, 1)
        centers_y = np.bincount(labels.ravel(), weights=yy.ravel()) / np.maximum(areas, 1)
        sheet = entries[0][0]
        sx = raw_size[0] / sheet['native_sheet_size'][0]
        sy = raw_size[1] / sheet['native_sheet_size'][1]
        for _, cell in entries:
            x, y, width, height = cell['rect']
            left, top, right, bottom = (round(x * sx), round(y * sy),
                                        round((x + width) * sx), round((y + height) * sy))
            owned = [index for index in range(1, count + 1) if areas[index] >= 30
                     and left <= centers_x[index] < right and top <= centers_y[index] < bottom]
            if not owned:
                raise ValueError(f'No generated component in nominal crop: {cell["id"]}')
            retained = np.bincount(labels[top:bottom, left:right].ravel(), minlength=count + 1)
            coverage = sum(retained[index] for index in owned) / sum(areas[index] for index in owned)
            if coverage < 0.97:
                raise ValueError(f'Clipped first-pass imagegen component: {cell["id"]}: {coverage:.3f}')
            checked += 1
    return checked


def two_pixel_magenta_edge(path):
    with Image.open(path) as image:
        pixels = np.asarray(image.convert('RGBA')).astype(np.int16)
    red, green, blue = pixels[:, :, 0], pixels[:, :, 1], pixels[:, :, 2]
    magenta = (red > 150) & (blue > 150) & (green < 140) & (np.minimum(red, blue) - green > 70)
    outer = np.zeros(magenta.shape, dtype=bool)
    outer[:2, :] = True
    outer[-2:, :] = True
    outer[:, :2] = True
    outer[:, -2:] = True
    return int(np.sum(magenta & outer))


def audit_effect_sequence_alignment(sequence, items):
    jobs = json.loads((HERE / 'review_repairs/full_sequences/jobs.json').read_text())['jobs']
    by_id = {item['id']: item for item in items}
    expected_ids = {frame['id'] for job in jobs.values() for frame in job['frames']}
    if set(sequence) != expected_ids:
        raise ValueError('Whole-sequence frames differ from the prepared eight-frame jobs')
    checked = 0
    for group, job in jobs.items():
        frames = job['frames']
        if len(frames) != 8:
            raise ValueError(f'Incomplete effect sequence: {group}')
        native_boxes = []
        for frame in frames:
            item = by_id[frame['id']]
            with Image.open(HERE / item['original']) as image:
                box = image.convert('RGBA').getchannel('A').getbbox()
            if box is None or list(box) != sequence[frame['id']]['native_opaque_box']:
                raise ValueError(f'Changed native frame bounds: {frame["id"]}')
            native_boxes.append(box)
        envelope = [2 * min(box[0] for box in native_boxes), 2 * min(box[1] for box in native_boxes),
                    2 * max(box[2] for box in native_boxes), 2 * max(box[3] for box in native_boxes)]
        center = [(envelope[0] + envelope[2]) / 2, (envelope[1] + envelope[3]) / 2]
        for index, frame in enumerate(frames):
            row = sequence[frame['id']]
            if row['sequence'] != group or row['frame_index'] != index + 1 \
                    or row['sequence_oval_box_2x'] != envelope or row['sequence_oval_center_2x'] != center:
                raise ValueError(f'Effect frame has a different oval envelope: {frame["id"]}')
            with Image.open(HERE / row['artifact']) as image:
                restored = image.convert('RGBA')
            if list(restored.size) != by_id[frame['id']]['x2_size']:
                raise ValueError(f'Effect frame has a different canvas: {frame["id"]}')
            opaque_box = restored.getchannel('A').point(lambda alpha: 255 if alpha >= 64 else 0).getbbox()
            if opaque_box is None or any(abs(edge - expected) > 1 for edge, expected in zip(opaque_box, envelope)):
                raise ValueError(f'Effect oval changes scale or placement: {frame["id"]}: {opaque_box}')
            actual_center = [(opaque_box[0] + opaque_box[2]) / 2,
                             (opaque_box[1] + opaque_box[3]) / 2]
            if any(abs(actual - expected) > 0.5 for actual, expected in zip(actual_center, center)):
                raise ValueError(f'Effect oval moves off center: {frame["id"]}: {actual_center}')
            checked += 1
    return checked


def audit_remaining_effect_sequences(report, items):
    jobs = json.loads((HERE / 'review_repairs/remaining_sequences/jobs.json').read_text())['jobs']
    by_id = {item['id']: item for item in items}
    expected_ids = {frame['id'] for job in jobs.values() for frame in job['frames']}
    rows = report['items']
    if len(jobs) != 18 or len(rows) != 142 or set(rows) != expected_ids:
        raise ValueError('Incomplete remaining PC effect sequences')
    if set(rows) - set(by_id) != {'engine--icons--sp21a10.bmp'}:
        raise ValueError('Unexpected effect frame outside the main review catalog')
    for source in report['sources'].values():
        if digest(HERE / source['path']) != source['sha256']:
            raise ValueError(f'Changed whole-sequence imagegen return: {source["path"]}')
    checked = 0
    for family, job in jobs.items():
        frames = job['frames']
        if [frame['number'] for frame in frames] != list(range(1, len(frames) + 1)):
            raise ValueError(f'Incomplete frame order: {family}')
        boxes = []
        for frame in frames:
            original = HERE / 'pc_effect_sequences' / frame['original']
            if digest(original) != frame['original_sha256']:
                raise ValueError(f'Changed native frame: {frame["id"]}')
            with Image.open(original) as image:
                native = image.convert('RGBA')
            box = native.getchannel('A').getbbox()
            if box is None or list(box) != frame['native_box'] or list(native.size) != frame['native_size']:
                raise ValueError(f'Changed native effect geometry: {frame["id"]}')
            boxes.append(box)
        envelope = [min(box[0] for box in boxes), min(box[1] for box in boxes),
                    max(box[2] for box in boxes), max(box[3] for box in boxes)]
        center = [envelope[0] + envelope[2], envelope[1] + envelope[3]]
        if envelope != job['native_envelope'] or [value * 2 for value in job['native_envelope_center']] != center:
            raise ValueError(f'Changed native sequence center: {family}')
        for frame in frames:
            row = rows[frame['id']]
            placed = [2 * edge for edge in frame['native_box']]
            if row['sequence'] != family or row['frame_index'] != frame['number'] \
                    or row['source_sha256'] != frame['source_sha256'] \
                    or row['native_opaque_box'] != frame['native_box'] \
                    or row['native_envelope'] != envelope \
                    or row['sequence_oval_center_2x'] != center or row['placed_box_2x'] != placed \
                    or min(row['sampling']) < 2 or min(row['raw_core_insets']) < 8:
                raise ValueError(f'Invalid sequence placement or raw sampling: {frame["id"]}')
            artifact = HERE / row['artifact']
            if digest(artifact) != row['artifact_sha256']:
                raise ValueError(f'Changed fitted effect candidate: {frame["id"]}')
            with Image.open(artifact) as image:
                fitted = image.convert('RGBA')
            if list(fitted.size) != [2 * size for size in frame['native_size']]:
                raise ValueError(f'Wrong fitted effect canvas: {frame["id"]}')
            if fitted.getchannel('A').getbbox() is None:
                raise ValueError(f'Empty fitted effect candidate: {frame["id"]}')
            checked += 1
    return checked


def audit_idle_stabilization(report, base_report):
    jobs = json.loads((HERE / 'review_repairs/remaining_sequences/jobs.json').read_text())['jobs']
    expected_families = {'sp21a', 'sp27a', 'sp109'}
    expected_ids = {frame['id'] for family in expected_families for frame in jobs[family]['frames']}
    family_rows = report['families']
    changed = report['items']
    if set(family_rows) != expected_families or len(expected_ids) != 22 \
            or {row['id'] for rows in family_rows.values() for row in rows} != expected_ids \
            or len(changed) != 14 or not set(changed).issubset(expected_ids):
        raise ValueError('Incomplete idle animation stabilization')
    selected = {}
    for family, rows in family_rows.items():
        frames = jobs[family]['frames']
        if [row['id'] for row in rows] != [frame['id'] for frame in frames]:
            raise ValueError(f'Idle animation frame order changed: {family}')
        selected[family] = []
        for row in rows:
            target_id = row['id']
            base = base_report[target_id]
            if row['source_sha256'] != base['source_sha256'] \
                    or row['input_sha256'] != base['artifact_sha256'] \
                    or row['changed'] != (target_id in changed):
                raise ValueError(f'Stale idle animation input: {target_id}')
            current = changed.get(target_id, base)
            artifact = HERE / current['artifact']
            if digest(artifact) != current['artifact_sha256']:
                raise ValueError(f'Changed stabilized frame: {target_id}')
            with Image.open(artifact) as image:
                pixels = np.asarray(image.convert('RGBA')).copy()
            with Image.open(HERE / base['artifact']) as image:
                original = np.asarray(image.convert('RGBA'))
            if pixels.shape != original.shape or row['changed'] == np.array_equal(pixels, original):
                raise ValueError(f'Idle frame did not match its change record: {target_id}')
            if target_id in changed:
                replacement = changed[target_id]
                if replacement['status'] != 'candidate_technical' \
                        or replacement['input_sha256'] != base['artifact_sha256']:
                    raise ValueError(f'Invalid stabilized review candidate: {target_id}')
            selected[family].append(pixels)
    boot_centers = []
    for pixels in selected['sp21a']:
        red, green, blue, alpha = [pixels[:, :, channel].astype(float) for channel in range(4)]
        y, _ = np.indices(alpha.shape)
        mask = (alpha > 96) & (y >= 50) & (y < 116) & (red > 55) \
            & (red > green * 1.15) & (green > blue * 1.1)
        labels, count = ndimage.label(mask)
        sizes = np.bincount(labels.ravel())
        sizes[0] = 0
        if count == 0 or sizes.max() < 1000:
            raise ValueError('Missing stable boot core')
        yy, xx = np.nonzero(labels == np.argmax(sizes))
        boot_centers.append((float(xx.mean()), float(yy.mean())))
    if any(np.ptp([point[axis] for point in boot_centers]) > 1.0 for axis in range(2)):
        raise ValueError('Winged boot still wanders between frames')
    platform_centers = []
    for pixels in selected['sp27a']:
        red, green, blue, alpha = [pixels[:, :, channel].astype(float) for channel in range(4)]
        y, _ = np.indices(alpha.shape)
        mask = (alpha > 64) & (y >= 92) & (blue > red * 1.2) & (blue > green * 1.08)
        yy, xx = np.nonzero(mask)
        if len(xx) < 2000:
            raise ValueError('Missing stationary walking platform')
        platform_centers.append((float(xx.mean()), float(yy.mean())))
    if any(np.ptp([point[axis] for point in platform_centers]) > 1.5 for axis in range(2)):
        raise ValueError('Walking platform still wanders between frames')
    robe_centers = []
    robe_tops = []
    for pixels in selected['sp109']:
        yy, xx = np.nonzero(pixels[:92, :, 3] >= 32)
        robe_centers.append((float(xx.mean()), float(yy.mean())))
        robe_tops.append(int(yy.min()))
    if np.ptp(robe_tops) > 1 or any(np.ptp([point[axis] for point in robe_centers]) > 1.0
                                      for axis in range(2)):
        raise ValueError('Robed figure still wanders between frames')
    return len(expected_ids)


def audit_idle_cores(report, stabilization, base_report):
    jobs = json.loads((HERE / 'review_repairs/remaining_sequences/jobs.json').read_text())['jobs']
    masters = {'sp21a': 3, 'sp27a': 4, 'sp109': 3}
    expected_ids = {frame['id'] for family in masters for frame in jobs[family]['frames']}
    if set(report['families']) != set(masters) or set(report['items']) != expected_ids \
            or len(expected_ids) != 22:
        raise ValueError('Incomplete fixed-core idle animation pass')
    for family, master_index in masters.items():
        frames = jobs[family]['frames']
        if [row['id'] for row in report['families'][family]] != [frame['id'] for frame in frames]:
            raise ValueError(f'Fixed-core frame order changed: {family}')
        selected_inputs = [stabilization['items'].get(frame['id'], base_report[frame['id']])
                           for frame in frames]
        master_id = frames[master_index]['id']
        master_sha = selected_inputs[master_index]['artifact_sha256']
        outputs = []
        for index, frame in enumerate(frames):
            row = report['items'][frame['id']]
            artifact = HERE / row['artifact']
            if row != report['families'][family][index] or digest(artifact) != row['artifact_sha256'] \
                    or row['source_sha256'] != base_report[frame['id']]['source_sha256'] \
                    or row['input_sha256'] != selected_inputs[index]['artifact_sha256'] \
                    or row['master_id'] != master_id or row['master_sha256'] != master_sha \
                    or row['status'] != 'candidate_technical':
                raise ValueError(f'Stale or changed fixed-core candidate: {frame["id"]}')
            with Image.open(artifact) as image:
                pixels = np.asarray(image.convert('RGBA')).copy()
            if pixels.shape != (128, 128, 4) or not np.any(pixels[:, :, 3]):
                raise ValueError(f'Invalid fixed-core image: {frame["id"]}')
            outputs.append(pixels)
        reference = outputs[master_index]
        if family == 'sp21a':
            if any(not np.array_equal(image[68:], reference[68:]) \
                    or not np.array_equal(image[55:68, 43:101], reference[55:68, 43:101])
                    for image in outputs):
                raise ValueError('Fly boot or wing roots still wobble')
            if len({image[:55].tobytes() for image in outputs}) < 4:
                raise ValueError('Fly wings lost their animated phases')
        elif family == 'sp27a':
            if any(not np.array_equal(image[:, :, 3], reference[:, :, 3]) \
                    or not np.array_equal(image[:83, 36:94], reference[:83, 36:94])
                    for image in outputs):
                raise ValueError('Water Walk figure or silhouette still wobbles')
            if len({image.tobytes() for image in outputs}) != len(outputs):
                raise ValueError('Water Walk light phases are duplicated')
        else:
            if any(not np.array_equal(image[:, :, 3], reference[:, :, 3]) \
                    or not np.array_equal(image[:92], reference[:92]) for image in outputs):
                raise ValueError('Levitate figure or silhouette still wobbles')
            if len({image.tobytes() for image in outputs}) != len(outputs):
                raise ValueError('Levitate cloud light phases are duplicated')
    return len(expected_ids)


def main():
    catalog = json.loads((HERE / 'catalog.js').read_text().split('=', 1)[1].strip().removesuffix(';'))
    items = catalog['items']
    if len(items) != 1718 or len({item['id'] for item in items}) != len(items):
        raise ValueError('Wrong target set')
    if catalog['summary']['with_candidate'] != 1718:
        raise ValueError(f"Incomplete fitted review art: {catalog['summary']}")
    imagegen_slice = [item for item in items if item.get('imagegen_slice')]
    if len(imagegen_slice) != 590 or catalog['summary']['imagegen_slice_candidates'] != 590:
        raise ValueError('Incomplete 590-target imagegen replacement slice')
    perimeter = json.loads((HERE / 'magenta_perimeter/report.json').read_text())['items']
    perimeter_targets = {item['id'] for item in items if item['name'].lower().startswith(('terra', 't_', 'bt_'))}
    perimeter_targets.update({
        'engine--icons--ticon03.bmp', 'engine--icons--ticon04.bmp',
        'engine--icons--tpharmon.bmp', 'engine--icons--tpisl.bmp',
        'engine--icons--tpmist.bmp', 'engine--icons--tpwarl.bmp',
        'worlds-mm8--icons--outside.bmp',
    })
    if len(perimeter_targets) != 276 or set(perimeter) != perimeter_targets:
        raise ValueError('Incomplete opaque magenta perimeter cleanup')
    reviewed = json.loads((HERE / 'user_review_2026-09-24.json').read_text())['decisions']
    historical_repairs = {}
    for name in ('component_reuse_report.json', 'effect_report.json', 'inventory_regen_report.json',
                 'spill_report.json', 'ui_regen_report.json'):
        rows = json.loads((HERE / 'review_repairs' / name).read_text())['items']
        if set(historical_repairs) & set(rows):
            raise ValueError(f'Duplicate user-review repair in {name}')
        historical_repairs.update(rows)
    flags = {target_id for target_id, decision in reviewed.items() if decision['decision'] == 'flag'}
    if len(flags) != 72 or not flags.issubset(historical_repairs) or len(historical_repairs) != 80:
        raise ValueError(f'Incomplete user-review repair: {len(flags & historical_repairs)}/{len(flags)} flags')
    kept_sequence = json.loads((HERE / 'review_repairs/full_sequences/report.json').read_text())['items']
    remaining_report = json.loads((HERE / 'review_repairs/remaining_sequences/report.json').read_text())
    stabilization = json.loads((HERE / 'review_repairs/remaining_sequences/stabilization_report.json').read_text())
    stabilized_frames = audit_idle_stabilization(stabilization, remaining_report['items'])
    idle_core = json.loads((HERE / 'review_repairs/remaining_sequences/idle_core_report.json').read_text())
    locked_frames = audit_idle_cores(idle_core, stabilization, remaining_report['items'])
    remaining_sequence = {target_id: row for target_id, row in remaining_report['items'].items()
                          if target_id != 'engine--icons--sp21a10.bmp'}
    remaining_sequence.update({target_id: row for target_id, row in stabilization['items'].items()
                               if target_id != 'engine--icons--sp21a10.bmp'})
    remaining_sequence.update({target_id: row for target_id, row in idle_core['items'].items()
                               if target_id != 'engine--icons--sp21a10.bmp'})
    if set(kept_sequence) & set(remaining_sequence) or len(remaining_sequence) != 141:
        raise ValueError('Overlapping or missing effect sequence candidates')
    sequence = {**kept_sequence, **remaining_sequence}
    shared = json.loads((HERE / 'review_repairs/shared_world_primary_report.json').read_text())['items']
    world_links = json.loads((HERE / 'review_repairs/world_item_links/report.json').read_text())
    if len(kept_sequence) != 32 or len(sequence) != 173 or len(shared) != 2:
        raise ValueError('Incomplete whole-sequence or shared-world replacement')
    if {row['sequence'] for row in kept_sequence.values()} != {'sp05e', 'spell14e', 'spell36e', 'spell68e'} \
            or any(row['sampling'][0] < 2.5 or row['sampling'][1] < 2.5 for row in kept_sequence.values()):
        raise ValueError('Changed four kept effect sequences')
    aligned_effect_frames = audit_effect_sequence_alignment(kept_sequence, items)
    aligned_effect_frames += audit_remaining_effect_sequences(remaining_report, items)
    if world_links['summary']['same_native_drawing'] != 139 \
            or world_links['summary']['fitted_approved_world_candidate'] != 138 \
            or world_links['summary']['overhang_fitted'] != 26 \
            or world_links['summary']['inventory_to_world_source'] != 1:
        raise ValueError('Changed inventory/world master crosswalk')
    repaired = {**historical_repairs, **sequence, **shared}
    if len(repaired) != 236:
        raise ValueError(f'Wrong current repair set: {len(repaired)}')
    origin_counts = Counter()
    anomalies = []
    introduced_pink = []
    for item in items:
        original = HERE / item['original']
        source = HERE / item['source']
        if digest(source) != item['source_sha256']:
            raise ValueError(f"Stale source: {item['id']}")
        with Image.open(original) as image:
            if image.size != tuple(item['native_size']):
                raise ValueError(f"Wrong original canvas: {item['id']}")
        candidate = item['candidates'][0]
        if item['id'] in repaired:
            row = repaired[item['id']]
            world = world_links['items'].get(item['id'], {})
            world_selected = world.get('candidate') and item['id'] != 'engine--icons--7item263.bmp' \
                and candidate['path'] == world['candidate'] and candidate['sha256'] == world['candidate_sha256']
            if item['source_sha256'] != row['source_sha256'] or not any(
                    option['path'] == row['artifact'] and option['sha256'] == row['artifact_sha256']
                    for option in item['candidates']):
                raise ValueError(f'User-review repair is missing: {item["id"]}')
            if not world_selected and (candidate['path'] != row['artifact']
                                       or candidate['sha256'] != row['artifact_sha256']):
                raise ValueError(f'User-review repair is not primary: {item["id"]}')
            if item['id'] in flags and any(option['sha256'] == reviewed[item['id']]['candidate_sha256']
                                           for option in item['candidates']):
                raise ValueError(f'Flagged artwork is still offered: {item["id"]}')
        if item['id'] in perimeter:
            cleaned = perimeter[item['id']]
            if candidate['path'] != cleaned['artifact'] or candidate['sha256'] != cleaned['artifact_sha256']:
                raise ValueError(f'Magenta perimeter repair is not primary: {item["id"]}')
            if two_pixel_magenta_edge(HERE / candidate['path']):
                raise ValueError(f'Magenta remains within two pixels of edge: {item["id"]}')
        origin_counts[candidate['origin']] += 1
        if any('Real-ESRGAN' in option['origin'] for option in item['candidates']):
            raise ValueError(f"Real-ESRGAN still offered in review: {item['id']}")
        if item.get('imagegen_slice') and candidate['origin'] not in ('Imagegen restoration',
                'Native geometry redraw', 'Approved world sprite master'):
            raise ValueError(f"Imagegen slice has wrong primary candidate: {item['id']}")
        world = world_links['items'].get(item['id'], {})
        if world.get('candidate'):
            if candidate['sha256'] != world['candidate_sha256'] or candidate['path'] != world['candidate']:
                raise ValueError(f"Approved world master is not primary: {item['id']}")
            source_world = HERE.parents[2] / world['approved_world']['path']
            with Image.open(source_world) as approved, Image.open(HERE / world['candidate']) as fitted:
                approved = approved.convert('RGBA')
                fitted = fitted.convert('RGBA')
                source_box = world['fit_source_box_2x']
                placed = world['fit_placed_box_2x']
                cropped = approved.crop(tuple(source_box))
                if world['fit_method'] == 'uniformly scaled to fit inventory canvas':
                    cropped = cropped.resize((placed[2] - placed[0], placed[3] - placed[1]),
                                             Image.Resampling.LANCZOS)
                expected = Image.new('RGBA', tuple(item['x2_size']))
                expected.paste(cropped, tuple(placed[:2]))
                if fitted.tobytes() != expected.tobytes():
                    raise ValueError(f"Approved world master fit changed: {item['id']}")
        elif world.get('reuse_status') == 'inventory restoration selected for ground sprite' \
                and item['id'] != 'engine--icons--7item263.bmp':
            raise ValueError(f"Unexpected inventory-to-world override: {item['id']}")
        if item.get('sequence_repair') != (item['id'] in sequence):
            raise ValueError(f"Incorrect animation sequence marker: {item['id']}")
        for option in item['candidates']:
            path = HERE / option['path']
            if not path.is_file() or digest(path) != option['sha256']:
                raise ValueError(f"Missing/stale candidate: {item['id']}: {path}")
            with Image.open(path) as image:
                if image.size != tuple(item['x2_size']):
                    raise ValueError(f"Wrong candidate canvas: {item['id']}: {path}")
        if item['x2_size'] != [2 * value for value in item['native_size']]:
            raise ValueError(f"Not exact x2 geometry: {item['id']}")
        score = spill_summary(HERE / candidate['path'])
        if item.get('imagegen_slice'):
            old_score = spill_summary(original)
            # item218 is a saturated amethyst in the native source, so its
            # complete new silhouette legitimately exposes more purple rim.
            if item['id'] != 'engine--icons--item218.bmp' and score['pink_edge_pixels'] > 15 and score['pink_edge_fraction'] > \
                    old_score['pink_edge_fraction'] + 0.10:
                introduced_pink.append(item['id'])
        if score['pink_edge_pixels'] or score['green_edge_pixels']:
            anomalies.append({'id': item['id'], 'origin': candidate['origin'], **score})
    if introduced_pink:
        raise ValueError(f"New saturated pink edges in imagegen slice: {introduced_pink}")
    first_pass_alpha_crops_checked = audit_first_pass_alpha_crops(items)
    anomalies.sort(key=lambda row: max(row['pink_edge_pixels'], row['green_edge_pixels']), reverse=True)
    report = {
        'schema': 1, 'total': len(items), 'primary_origins': dict(origin_counts),
        'imagegen_slice_candidates': len(imagegen_slice), 'introduced_pink_edge_cases': introduced_pink,
        'first_pass_alpha_crops_checked': first_pass_alpha_crops_checked,
        'magenta_perimeter_repaired': len(perimeter),
        'magenta_border_pixels_removed': sum(row['input_boundary_magenta'] for row in perimeter.values()),
        'user_review_flag_repairs': len(flags), 'user_review_total_new_candidates': len(repaired),
        'whole_sequence_frames': len(sequence),
        'aligned_effect_frames': aligned_effect_frames,
        'stabilized_idle_frames': stabilized_frames,
        'locked_idle_frames': locked_frames,
        'fitted_approved_world_inventory_candidates': world_links['summary']['fitted_approved_world_candidate'],
        'visible_edge_color_suspects': anomalies,
    }
    (HERE / 'validation_report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'total': len(items), 'primary_origins': origin_counts,
                      'edge_suspects': len(anomalies), 'top_edge_suspects': anomalies[:20]}, indent=2))


if __name__ == '__main__':
    main()
