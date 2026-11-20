"""Extract raw cells for review. Does not register, rescale or certify animation."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from prepare_run import REPO, native

sys.path.insert(0, str(REPO / 'level_generation/creatures/mm6_peasants'))
import process_family as processing


def apply_rgb_patch(clean, patch):
    """Composite a hash-bound generated interior detail without changing silhouette or other pixels."""
    source = REPO / patch['source']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == patch['source_sha256']
    assert hashlib.sha256(clean.tobytes()).hexdigest() == patch['input_rgba_sha256']
    assert patch['reason'], 'Local artwork patches require an explicit review reason'
    donor = Image.open(source).convert('RGBA')
    sx0, sy0, sx1, sy1 = patch['source_rect']
    x0, y0, x1, y1 = patch['target_rect']
    assert 0 <= sx0 < sx1 <= donor.width and 0 <= sy0 < sy1 <= donor.height
    assert 0 <= x0 < x1 <= clean.width and 0 <= y0 < y1 <= clean.height
    assert sx1-sx0 >= x1-x0 and sy1-sy0 >= y1-y0, 'Do not enlarge patch detail'
    donor = donor.crop((sx0, sy0, sx1, sy1))
    assert donor.getchannel('A').getextrema()[0] >= 250, 'Patch must be near-opaque interior artwork'
    pixels = np.array(clean)
    region = pixels[y0:y1, x0:x1]
    assert (region[:, :, 3] >= 250).all(), 'Patch must be interior artwork; original alpha is preserved'
    donor = np.array(donor.resize((x1-x0, y1-y0), Image.Resampling.LANCZOS))
    yy, xx = np.indices(region.shape[:2])
    edge = np.minimum(np.minimum(xx+1, x1-x0-xx), np.minimum(yy+1, y1-y0-yy))
    feather = float(patch.get('feather_px', 0))
    assert 0 <= feather <= min(x1-x0, y1-y0)/2
    weight = np.minimum(1, edge/max(1, feather))[:, :, None]
    region[:, :, :3] = np.round(region[:, :, :3]*(1-weight) + donor[:, :, :3]*weight).astype(np.uint8)
    return Image.fromarray(pixels)


def connected_cells(delivered, job, grid_groups=False, seed_alpha_threshold=0):
    """Separate explicitly reviewed interleaved solid sprites without cutting their silhouettes."""
    pixels = np.array(delivered)
    assert 0 <= seed_alpha_threshold <= 64
    labels, _ = ndimage.label(pixels[:, :, 3] > seed_alpha_threshold)
    sizes = np.bincount(labels.ravel())
    sizes[0] = 0
    major = np.flatnonzero(sizes > sizes.max()*.1)
    if grid_groups:
        # Dissipation endpoints may be much smaller than the first effect pose.
        # Seed each requested grid cell from its own strongest delivered component;
        # global relative area must not erase a small native endpoint.
        seeds = set(int(label) for label in major)
        height, width = labels.shape
        for index in range(len(job['frames'])):
            row, column = divmod(index, job['columns'])
            cell = labels[round(row * height / job['rows']):round((row + 1) * height / job['rows']),
                          round(column * width / job['columns']):round((column + 1) * width / job['columns'])]
            local_sizes = np.bincount(cell.ravel(), minlength=len(sizes))
            local_sizes[0] = 0
            assert local_sizes.max() > 0, 'Requested cell has no delivered foreground'
            seeds.add(int(local_sizes.argmax()))
        major = np.array(sorted(seeds))
    if not grid_groups:
        assert len(major) == len(job['frames']), 'Expected one major connected body per native pose'
    centers = {int(label): ndimage.center_of_mass(labels == label) for label in major}
    ordered = sorted(major, key=lambda label: centers[int(label)][0])
    ordered = [label for start in range(0, len(ordered), job['columns'])
               for label in sorted(ordered[start:start+job['columns']], key=lambda value: centers[int(value)][1])]
    main = np.isin(labels, major)
    _, nearest = ndimage.distance_transform_edt(~main, return_indices=True)
    ownership = labels[nearest[0], nearest[1]]
    groups = [[label] for label in ordered]
    if grid_groups:
        groups = [[] for _ in job['frames']]
        for label in major:
            y, x = centers[int(label)]
            cell = int(y * job['rows'] / delivered.height) * job['columns'] + int(
                x * job['columns'] / delivered.width)
            assert cell < len(groups), 'Component belongs to an unused cell; review source layout'
            groups[cell].append(label)
        assert all(groups), 'Every pose must own a substantial component'
    output, assigned = [], 0
    for group in groups:
        selected = pixels.copy()
        selected[~np.isin(ownership, group)] = 0
        assigned += int((selected[:, :, 3] > 0).sum())
        image = Image.fromarray(selected)
        x0, y0, x1, y1 = image.getbbox()
        rect = [max(0, x0-12), max(0, y0-12), min(image.width, x1+12), min(image.height, y1+12)]
        output.append((rect, image.crop(rect)))
    assert assigned == int((pixels[:, :, 3] > 0).sum()), 'Every delivered foreground pixel must be retained once'
    return output


def extract(project, selected_jobs=None):
    root = REPO / project
    out = root / 'redo_2x'
    config = json.loads((root / 'config.json').read_text())
    policy_path = out / 'processing.json'
    policy = json.loads(policy_path.read_text()) if policy_path.exists() else {}
    color_correction = None
    if policy.get('base_color_correction'):
        correction = policy['base_color_correction']
        module_path = root / correction['module']
        assert hashlib.sha256(module_path.read_bytes()).hexdigest() == correction['sha256']
        assert correction['reason'], 'Base color correction requires a reviewed material policy'
        color_correction = processing.module('redo_base_color_correction', module_path)
    run = json.loads((out / 'run.json').read_text())
    first = json.loads((out / 'standing_01.json').read_text()) if (out / 'standing_01.json').exists() else None
    jobs = list(run['jobs'])
    if first:
        jobs.insert(0, dict(first, id='standing_01', selected_raw=first['identity_reference']))
    if selected_jobs:
        selected = set(selected_jobs)
        assert selected <= {job['id'] for job in jobs}, 'Unknown extraction job'
        jobs = [job for job in jobs if job['id'] in selected]
    for job in jobs:
        if not job.get('selected_raw'):
            continue
        path = REPO / job['selected_raw']
        delivered = Image.open(path).convert('RGBA')
        exclusions = policy.get('reviewed_background_exclusions', {}).get(job['id'])
        if exclusions:
            assert hashlib.sha256(path.read_bytes()).hexdigest() == exclusions['raw_sha256']
            assert exclusions['reason'], 'Background exclusions require a visual-review reason'
            pixels = np.array(delivered)
            for x0, y0, x1, y1 in exclusions['rectangles']:
                assert 0 <= x0 < x1 <= delivered.width and 0 <= y0 < y1 <= delivered.height
                pixels[y0:y1, x0:x1] = 0
            delivered = Image.fromarray(pixels)
        delivered_alpha = delivered.getchannel('A')
        has_alpha = delivered_alpha.getextrema()[0] < 255
        alpha_floor = policy.get('supplied_alpha_noise_floor', 0)
        alpha_noise_pixels = 0
        if has_alpha and alpha_floor:
            assert 0 <= alpha_floor <= 8, 'Only explicitly reviewed near-transparent noise may be removed'
            pixels = np.array(delivered)
            noise = (pixels[:, :, 3] > 0) & (pixels[:, :, 3] <= alpha_floor)
            alpha_noise_pixels = int(noise.sum())
            pixels[noise] = 0
            delivered = Image.fromarray(pixels)
            delivered_alpha = delivered.getchannel('A')
        sheet = delivered.convert('RGB')
        rgb = np.array(sheet).astype(float) / 255
        if config['matte'] == 'cyan':
            rgb = rgb[:, :, [1, 0, 2]]
        fg = (np.array(delivered_alpha) > 0 if has_alpha else
              np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1] < .55)
        column_first = job['id'] in policy.get('column_first_extraction_jobs', [])
        components = None
        seed_threshold = 0
        seed_policy = policy.get('component_seed_alpha_threshold_by_job', {}).get(job['id'])
        if seed_policy:
            assert seed_policy['raw_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
            assert seed_policy['reason'], 'Component seed thresholds require an artifact-bound review reason'
            seed_threshold = seed_policy['threshold']
        if job['id'] in policy.get('component_grid_extraction_jobs', []):
            assert has_alpha, 'Component extraction requires delivered alpha'
            components = connected_cells(delivered, job, grid_groups=True, seed_alpha_threshold=seed_threshold)
        elif job['id'] in policy.get('connected_body_extraction_jobs', []):
            assert has_alpha, 'Connected-body extraction requires delivered alpha'
            components = connected_cells(delivered, job, seed_alpha_threshold=seed_threshold)
        elif column_first:
            xcuts = processing.gutters(fg.any(axis=0), job['columns'])
        else:
            ycuts = processing.gutters(fg.any(axis=1), job['rows'])
        records = []
        occurrences = {}
        for i, name in enumerate(job['frames']):
            occurrence = occurrences.get(name, 0)
            occurrences[name] = occurrence + 1
            output_name = name if occurrence == 0 else f'{name}__step_{i:02d}'
            row, col = divmod(i, job['columns'])
            if components:
                rect, component_image = components[i]
            elif column_first:
                ycuts = processing.gutters(fg[:, xcuts[col]:xcuts[col + 1]].any(axis=1), job['rows'])
            else:
                xcuts = processing.gutters(fg[ycuts[row]:ycuts[row + 1]].any(axis=0), job['columns'])
            if not components:
                rect = [xcuts[col], ycuts[row], xcuts[col + 1], ycuts[row + 1]]
            cell = sheet.crop(rect)
            colors = np.array(cell)
            if config['matte'] == 'cyan':
                colors = colors[:, :, [1, 0, 2]]
            threshold = policy.get('matte_core_threshold', 8)
            extra_core = np.zeros(colors.shape[:2], dtype=bool)
            dark = policy.get('dark_foreground_core')
            if dark:
                rgb_int = colors.astype(int)
                dominance = np.minimum(rgb_int[:, :, 0], rgb_int[:, :, 2]) - rgb_int[:, :, 1]
                extra_core |= ((dominance <= dark['dominance_threshold'])
                               & (rgb_int.max(axis=2) < dark['maximum_channel']))
            thin = policy.get('thin_feature_cores', {}).get(name, {})
            if thin and thin['raw_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest():
                yy, xx = np.indices(colors.shape[:2])
                rgb_int = colors.astype(int)
                dominance = np.minimum(rgb_int[:, :, 0], rgb_int[:, :, 2]) - rgb_int[:, :, 1]
                for line in thin['lines']:
                    start, end = np.array(line['raw_points'], dtype=float) - np.array(rect[:2])
                    vector = end - start
                    length = np.linalg.norm(vector)
                    vector /= length
                    dx, dy = xx-start[0], yy-start[1]
                    along = dx*vector[0] + dy*vector[1]
                    distance = abs(dx*vector[1] - dy*vector[0])
                    extra_core |= ((along >= -2) & (along <= length+2) & (distance <= line['radius'])
                                   & (dominance <= line['threshold']) & (rgb_int.max(axis=2) < 100))
            if has_alpha:
                clean = component_image if components else delivered.crop(rect)
                stats = dict(method='Preserved delivered alpha; no second matte extraction',
                             supplied_alpha_noise_floor=alpha_floor,
                             sheet_near_transparent_noise_pixels=alpha_noise_pixels)
                if components:
                    stats['separation'] = 'Reviewed connected bodies; all supplied foreground pixels retained once'
            else:
                clean, stats = processing.matte.extract(Image.fromarray(colors), core_threshold=threshold,
                                                        foreground_core=extra_core)
            if thin:
                stats['reviewed_thin_feature_core'] = thin
            if dark:
                stats['dark_foreground_core'] = dark
            if config['matte'] == 'cyan' and not has_alpha:
                colors = np.array(clean)
                colors[:, :, :3] = colors[:, :, [1, 0, 2]]
                clean = Image.fromarray(colors)
            if not policy.get('preserve_matte_hued_materials', False):
                clean = processing.fix_contour(clean, config['matte'])
            if color_correction and (not correction.get('jobs') or job['id'] in correction['jobs']):
                corrected = color_correction.correct(clean)
                assert corrected.size == clean.size
                assert np.array_equal(np.array(corrected.getchannel('A')), np.array(clean.getchannel('A')))
                clean = corrected
                stats['native_palette_correction'] = correction
            patch = policy.get('local_rgb_patches', {}).get(name)
            if patch:
                clean = apply_rgb_patch(clean, patch)
                stats['local_rgb_patch'] = patch
            repairs = policy.get('alpha_repairs', {}).get(name, {})
            if repairs and repairs['raw_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest():
                repaired = np.array(clean)
                for x0, y0, x1, y1 in repairs['raw_clear_rects']:
                    repaired[y0-rect[1]:y1-rect[1], x0-rect[0]:x1-rect[0]] = 0
                clean = Image.fromarray(repaired)
                stats['reviewed_alpha_repair'] = repairs
            stats.update(core_threshold=threshold, material_policy=policy)
            folder = out / 'cleaned' / job['id']
            folder.mkdir(parents=True, exist_ok=True)
            clean.save(folder / (output_name + '.png'))
            a = np.array(clean)
            edge = (a[:, :, 3] > 0) & ((ndimage.distance_transform_edt(a[:, :, 3] >= 128) <= 4) | (a[:, :, 3] < 128))
            excess = np.minimum(a[:, :, 0].astype(int), a[:, :, 2].astype(int)) - a[:, :, 1].astype(int)
            box = clean.getchannel('A').getbbox()
            records.append(dict(frame=name, raw_rect=rect, clean_bounds=box,
                                native_bounds=native(root, name).getbbox(), matte=stats,
                                residual_spill_pixels=int(((excess > max(10, threshold + 2)) & edge).sum()),
                                clean_path=str((folder / (output_name + '.png')).relative_to(REPO))))
        report = dict(job=job['id'], raw=job['selected_raw'],
                      raw_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), raw_size=list(sheet.size),
                      native_crop=job['native_crop'], frames=records,
                      status='extracted_pending_anatomical_registration')
        (out / 'review' / (job['id'] + '_extraction.json')).write_text(json.dumps(report, indent=2) + '\n')
        # Compact review at native scale, explicitly a size-normalized diagnostic, not the export transform.
        w, h = job['cell_native_size']
        contact = Image.new('RGB', (w * len(records), h * 2 + 44), (42, 44, 43))
        draw = ImageDraw.Draw(contact)
        for i, record in enumerate(records):
            source = native(root, record['frame']).crop(job['native_crop'])
            clean = Image.open(REPO / record['clean_path'])
            contact.paste(source, (i * w, 20), source)
            box = record['clean_bounds']
            preview = clean.crop(box)
            nb = source.getbbox()
            scale = (nb[3] - nb[1]) / preview.height
            preview = preview.convert('RGBa').resize((round(preview.width * scale), round(preview.height * scale)), Image.Resampling.LANCZOS).convert('RGBA')
            contact.paste(preview, (i * w + nb[0], h + 40 + nb[1]), preview)
            draw.text((i * w + 2, 3), record['frame'], fill='white')
        contact.save(out / 'review' / (job['id'] + '_detail_contact.png'))
        print(job['id'], 'extracted', len(records), 'spill', sum(r['residual_spill_pixels'] for r in records))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('--jobs', nargs='+', help='Extract only these jobs; preserve all other cleaned artwork')
    args = parser.parse_args()
    extract(args.project, args.jobs)
