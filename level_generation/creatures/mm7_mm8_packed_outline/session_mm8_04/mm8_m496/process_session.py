"""Session-local MM8 schema bridge for shared extraction, landmark and palette tools.

Writes provisional exports only. Actual visual review and acceptance remain explicit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

REPO = Path(__file__).resolve().parents[5]
CREATURES = REPO / 'level_generation/creatures'
SESSION = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CREATURES))
sys.path.insert(0, str(CREATURES / 'mm6_remaining/redo_2x'))
sys.path.insert(0, str(CREATURES / 'mm8_remaining'))
from extract_run import connected_cells
from annotate_radial import box_and_alpha, core, envelope
from mm8_restore_queue import native
from process_detail import edge_candidates, gutters
import native_materials
import native_package


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def composite(image, colour):
    result = Image.new('RGBA', image.size, colour)
    result.alpha_composite(image)
    return result.convert('RGB')


def green_eye(image):
    pixels = np.asarray(image)
    rgb = pixels[:, :, :3].astype(float)
    r, g, b = np.moveaxis(rgb, -1, 0)
    selected = (pixels[:, :, 3] >= 250) & (g > 75) & (g > r * 1.25) & (g > b * 1.2)
    y, x = np.where(selected)
    return [float(x.mean()), float(y.mean())] if len(x) else None


def preserve_detached_components(raw, frames, job):
    """Repair reviewed Voronoi splits of detached effect puffs in shared extraction."""
    pixels = np.array(raw)
    owner = np.zeros(pixels.shape[:2], dtype=np.int16)
    for index, (rect, clean) in enumerate(frames, 1):
        x0, y0, x1, y1 = rect
        visible = np.asarray(clean)[:, :, 3] > 0
        region = owner[y0:y1, x0:x1]
        assert not region[visible].any()
        region[visible] = index
    assert (owner[pixels[:, :, 3] > 0] > 0).all()
    labels, count = ndimage.label(pixels[:, :, 3] > 4)
    verified_grid = None
    foreground = pixels[:, :, 3] > 4
    try:
        ycuts = gutters(foreground.any(axis=1), job['rows'])
        xcuts = [gutters(foreground[ycuts[row]:ycuts[row + 1]].any(axis=0), job['columns'])
                 for row in range(job['rows'])]
        verified_grid = np.zeros(owner.shape, dtype=np.int16)
        for index in range(len(frames)):
            row, col = divmod(index, job['columns'])
            verified_grid[ycuts[row]:ycuts[row + 1], xcuts[row][col]:xcuts[row][col + 1]] = index + 1
        assert (verified_grid[foreground] > 0).all(), 'Art in an unused returned cell'
    except AssertionError:
        # The standing sheet interleaves filaments. Its shared component grouping
        # is retained; rectangular cuts there would sever those filaments.
        if job['id'] != 'standing_0_sheet':
            raise
        verified_grid = None
    component_owner = np.zeros(count + 1, dtype=np.int16)
    changes = []
    for label, bounds in enumerate(ndimage.find_objects(labels), 1):
        selected = labels[bounds] == label
        counts = np.bincount(owner[bounds][selected], minlength=len(frames) + 1)
        counts[0] = 0
        selected_owner = int(counts.argmax())
        if verified_grid is not None:
            cell_counts = np.bincount(verified_grid[bounds][selected], minlength=len(frames) + 1)
            cell_counts[0] = 0
            assert np.count_nonzero(cell_counts) == 1, 'Verified gutter cut visible anatomy'
            selected_owner = int(cell_counts.argmax())
        component_owner[label] = selected_owner
        if np.count_nonzero(counts) > 1 or selected_owner != int(counts.argmax()):
            changes.append(dict(component=label, original_owners=counts.tolist(),
                                selected_owner=selected_owner,
                                method='Shared verified empty gutters' if verified_grid is not None
                                       else 'Majority component ownership in interleaved sheet'))
    _, nearest = ndimage.distance_transform_edt(labels == 0, return_indices=True)
    repaired = component_owner[labels[nearest[0], nearest[1]]]
    output = []
    assigned = 0
    for index in range(1, len(frames) + 1):
        selected = pixels.copy()
        selected[repaired != index] = 0
        assigned += int((selected[:, :, 3] > 0).sum())
        image = Image.fromarray(selected)
        x0, y0, x1, y1 = image.getbbox()
        rect = [max(0, x0 - 12), max(0, y0 - 12), min(raw.width, x1 + 12), min(raw.height, y1 + 12)]
        output.append((rect, image.crop(rect)))
    assert assigned == int((pixels[:, :, 3] > 0).sum())
    return output, changes


def process(family):
    root = SESSION / family
    sources, run = read(root / 'sources.json'), read(root / 'run.json')
    prior_processing = read(root / 'processing.json') if (root / 'processing.json').exists() else {}
    colour_repairs = prior_processing.get('local_colour_repairs', {})
    for folder in ('cleaned', 'aligned_2x', 'toned_2x', 'masks_2x', 'previews', 'native_variants'):
        (root / folder).mkdir(exist_ok=True)
    palettes = sorted(map(int, sources['palette_sources']))
    if len(palettes) == 1:
        configuration = dict(base_palette=sources['base_palette'], base_exact_bypass=True,
            palette_deltas={str(palettes[0]): [[0, 0, 0]] * 255}, regions=[],
            operation='exact_base_bypass', mask_semantics='R8 zero: no native palette differences exist')
    else:
        assert prior_processing['materials']['native_palette_review']
        native_materials.ROOT = root
        configuration = native_materials.settings()
    write(root / 'material_settings.json', configuration)
    registration, extraction, calibration, worst = {}, {}, {}, []
    for job in run['jobs']:
        attempts = [a for a in job['attempts'] if a['status'] == 'returned'
                    and a.get('visual_screen', {}).get('status') != 'rejected']
        if not attempts:
            continue
        attempt = attempts[-1]
        path = REPO / attempt['raw_path']
        assert sha(path) == attempt['raw_sha256']
        raw = Image.open(path).convert('RGBA')
        assert attempt['actual_submitted_inputs'][1]['role'] == 'matching_outline_only_geometry'
        if family == 'mm8_m528':
            frames = connected_cells(raw, job, grid_groups=True, seed_alpha_threshold=4)
            frames, ownership_repairs = preserve_detached_components(raw, frames, job)
        else:
            seed_policy = prior_processing.get('component_seed_policy', {}).get(job['id'], {})
            if seed_policy:
                assert seed_policy['raw_sha256'] == sha(path) and seed_policy['reason']
            frames = connected_cells(raw, job, seed_alpha_threshold=seed_policy.get('threshold', 1),
                                     grid_groups=seed_policy.get('grid_groups', False))
            ownership_repairs = []
        ratios = []
        for name, (_, clean) in zip(job['frames'], frames, strict=True):
            nb, _ = box_and_alpha(native(root, name))
            rb, _ = box_and_alpha(clean)
            ratios.append((rb[3] - rb[1]) / (nb[3] - nb[1]))
        sampling = float(np.median(ratios))
        factor = 2 / sampling
        calibration[job['id']] = dict(raw_sha256=sha(path), generated_sampling=sampling,
            nominal_sheet_sampling=attempt['nominal_sheet_sampling'],
            method='One median native/generated alpha>=32 envelope-height scale for the entire sheet; '
                   'candidate requires independent anatomy review', per_cell_ratios=ratios)
        extraction[job['id']] = dict(raw_path=attempt['raw_path'], raw_sha256=sha(path),
            seed_alpha_threshold=4 if family == 'mm8_m528' else seed_policy.get('threshold', 1), alpha_preserved=True,
            method='Shared connected-component ownership; all generated foreground pixels assigned once',
            detached_component_ownership_repairs=ownership_repairs,
            ownership_review_reason='Atlas light/dark review revealed Voronoi splits of detached smoke puffs. '
                                    'Shared verified gutters assign whole components and their soft halos; '
                                    'the interleaved standing sheet retains majority component ownership.'
                                    if family == 'mm8_m528' else None,
            frames=[])
        panels = []
        for index, (name, (rect, clean)) in enumerate(zip(job['frames'], frames, strict=True)):
            repair = colour_repairs.get(name)
            if repair:
                assert repair['raw_sha256'] == sha(path) and repair['reason']
                pixels = np.array(clean)
                rgb = pixels[:, :, :3].astype(float)
                r, g, b = np.moveaxis(rgb, -1, 0)
                if 'warm_smoke_gain' in repair:
                    # Enhanced-pixel colour coverage: protect ivory lightning and cool mist.
                    coverage = np.clip(((r - b) / np.maximum(r + b, 1) - .12) / .16, 0, 1)
                    coverage *= np.clip((1.9 - r / np.maximum(g, 1)) / .25, 0, 1)
                    rgb *= 1 - coverage[:, :, None] * (1 - repair['warm_smoke_gain'])
                if repair.get('remove_added_violet_sparks'):
                    coverage = np.clip((b - np.maximum(r, g) - 20) / 10, 0, 1)
                    luminance = rgb @ np.array([.2126, .7152, .0722])
                    ivory = luminance[:, :, None] * np.array([1.05, 1.02, .86])
                    rgb = rgb * (1 - coverage[:, :, None]) + ivory * coverage[:, :, None]
                pixels[:, :, :3] = np.round(rgb).clip(0, 255).astype(np.uint8)
                clean = Image.fromarray(pixels)
            native_image = native(root, name)
            nb, native_pixels = box_and_alpha(native_image)
            rb, restored_pixels = box_and_alpha(clean)
            particle = family == 'mm8_m528' and name.startswith('m528d') and name[5] >= 'e'
            native_core = core(native_pixels, nb, particle=particle)
            restored_core = core(restored_pixels, rb, particle=particle)
            points = dict(core_anchor=dict(native=native_core, restored=restored_core),
                upper_envelope=dict(native=envelope(native_pixels, nb, True),
                                    restored=envelope(restored_pixels, rb, True)),
                lower_envelope=dict(native=envelope(native_pixels, nb, False),
                                    restored=envelope(restored_pixels, rb, False)))
            if family == 'mm8_m512' and job['native_sequence']:
                native_eye, restored_eye = green_eye(native_image), green_eye(clean)
                if native_eye is not None:
                    assert restored_eye is not None, f'Visible native green eye missing from restored pose {name}'
                    points['green_eye_independent'] = dict(native=native_eye, restored=restored_eye)
            size = [max(1, round(v * factor)) for v in clean.size]
            effective = np.array(size) / clean.size
            resized = clean.convert('RGBa').resize(size, Image.Resampling.LANCZOS).convert('RGBA')
            translation = np.round(np.array(native_core) * 2 - np.array(restored_core) * effective).astype(int)
            bounds = resized.getbbox()
            origin = np.minimum([0, 0], translation + bounds[:2] - 4)
            end = np.maximum(np.array(sources['logical_canvas']) * 2, translation + bounds[2:] + 4)
            aligned = Image.new('RGBA', tuple(end - origin))
            aligned.paste(resized, tuple(translation - origin))
            frame_record = dict(batch=job['id'], raw_path=attempt['raw_path'], raw_sha256=sha(path),
                raw_rect=rect, native_bounds=nb, logical_pivot=sources['logical_pivot'],
                exact_native_offset=[0, 0], translate=translation.tolist(), canvas_origin_px=origin.tolist(),
                aligned_size_px=list(aligned.size), scale_to_2x=factor,
                effective_sampling_xy=(2 / effective).tolist(), placement_landmarks=points,
                independent_placement_review='pending', clean_sha256=hashlib.sha256(clean.tobytes()).hexdigest())
            extraction[job['id']]['frames'].append(dict(frame=name, raw_rect=rect,
                duplicate_of_selected_source=name if name in registration else None))
            # Native held steps and cross-action reuse select one canonical source image.
            if name not in registration:
                clean.save(root / f'cleaned/{name}.png')
                aligned.save(root / f'aligned_2x/{name}.png')
                aligned.save(root / f'toned_2x/{name}.png')
                coverage = (Image.new('L', aligned.size) if len(palettes) == 1 else
                            Image.fromarray(native_materials.masks(aligned, configuration)))
                coverage.save(root / f'masks_2x/{name}.png')
                for palette in palettes:
                    preview = (aligned.copy() if palette == sources['base_palette'] else
                               native_materials.recolor(aligned, coverage, palette, configuration))
                    preview.save(root / f'previews/{name}_{palette}.png')
                    native(root, name, palette).save(root / f'native_variants/{name}_{palette}.png')
                registration[name] = frame_record
                score, _ = edge_candidates(clean)
                worst.append((float(score.max()), name, clean, np.unravel_index(score.argmax(), score.shape)))
            width, height = sources['logical_canvas']
            if family == 'mm8_m528':
                review_crop, zoom = [0, 0, width, height], 1
            else:
                review_crop = [int(v) + (-24 if i < 2 else 24) for i, v in enumerate(job['native_crop'])]
                zoom = 2
            review_width, review_height = review_crop[2] - review_crop[0], review_crop[3] - review_crop[1]
            panel = Image.new('RGB', (review_width * zoom * 2, review_height * zoom + 22), '#2a2c2b')
            draw = ImageDraw.Draw(panel)
            draw.text((4, 3), f'{index + 1}: {name}; common native crop {review_crop[:2]}', fill='white')
            native_display = native_image.crop(review_crop).resize((review_width * zoom, review_height * zoom),
                                                                  Image.Resampling.NEAREST)
            panel.paste(native_display, (0, 22), native_display)
            display = Image.new('RGBA', (review_width * 2, review_height * 2))
            display.paste(aligned, tuple(origin - np.array(review_crop[:2]) * 2))
            display = display.convert('RGBa').resize(
                (review_width * zoom, review_height * zoom), Image.Resampling.LANCZOS).convert('RGBA')
            panel.paste(display, (review_width * zoom, 22), display)
            for label, point in points.items():
                for side in (0, 1):
                    xy = point['native'] if side == 0 else (
                        (np.array(point['restored']) * effective + translation) / 2)
                    x = side * review_width * zoom + (xy[0] - review_crop[0]) * zoom
                    y = 22 + (xy[1] - review_crop[1]) * zoom
                    colour = '#30eeee' if label == 'core_anchor' else '#ffb050'
                    draw.line((x - 2, y, x + 2, y), fill=colour)
                    draw.line((x, y - 2, x, y + 2), fill=colour)
            panels.append(panel)
        cols = min(3 if panels[0].width < 700 else 2, len(panels))
        contact = Image.new('RGB', (panels[0].width * cols,
            panels[0].height * ((len(panels) + cols - 1) // cols)), '#2a2c2b')
        for i, panel in enumerate(panels):
            contact.paste(panel, (i % cols * panel.width, i // cols * panel.height))
        contact.save(root / f'review/{job["id"]}_placement.png')
    for alias, canonical in sources['pixel_aliases'].items():
        if canonical in registration:
            for folder in ('aligned_2x', 'toned_2x', 'masks_2x', 'cleaned'):
                shutil.copy2(root / folder / (canonical + '.png'), root / folder / (alias + '.png'))
    write(root / 'registration.json', registration)
    write(root / 'processing.json', dict(alpha_branch='Preserved delivered true alpha without threshold removal',
        extraction=extraction, calibration=calibration, local_colour_repairs=colour_repairs,
        materials=prior_processing.get('materials', {}),
        component_seed_policy=prior_processing.get('component_seed_policy', {}),
        processing_failures=prior_processing.get('processing_failures', []),
        superseded_component_seed_policies=prior_processing.get('superseded_component_seed_policies', []),
        status='candidate requires core identity, independent placement, detail, edge and variant review'))
    edge_contact = Image.new('RGB', (4 * 160, 160 * 2), '#202024')
    for i, (_, name, clean, (y, x)) in enumerate(sorted(worst, reverse=True, key=lambda row: row[0])[:4]):
        patch = clean.crop((x - 40, y - 40, x + 40, y + 40)).resize((160, 160), Image.Resampling.NEAREST)
        edge_contact.paste(composite(patch, '#eeeeee'), (i * 160, 0))
        edge_contact.paste(composite(patch, '#202024'), (i * 160, 160))
    edge_contact.save(root / 'review/worst_edges.png')
    write(root / 'review/edge_scan.json', dict(method='Shared local core-colour versus alpha/opaque-contour chroma scan',
        frames=len(registration), worst=[dict(frame=name, score=score) for score, name, _, _ in
                                        sorted(worst, reverse=True, key=lambda row: row[0])[:4]],
        status='visual review pending; chroma score is not a removal rule'))
    covered = set(registration) | {a for a, c in sources['pixel_aliases'].items() if c in registration}
    if covered == set(sources['sources']):
        native_package.ROOT = root
        native_package.run()
        manifest = read(root / 'draft_manifest.json')
        manifest.update(logical_canvas=sources['logical_canvas'], logical_pivot=sources['logical_pivot'],
                        placement_registration='registration.json', generated_sampling_min=min(
                            min(r['effective_sampling_xy']) for r in registration.values()))
        manifest.pop('viewer', None)
        manifest['review_evidence'] = 'review/acceptance.json'
        manifest['native_palette_exports'] = sources.get('staged_native_palettes', {})
        write(root / 'draft_manifest.json', manifest)
    run['coverage'].update(restored_files=len(covered), accepted_files=0, complete=False)
    run['status'] = 'exports_pending_visual_acceptance' if len(covered) == len(sources['sources']) else 'partial'
    write(root / 'run.json', run)
    print(f'{family}: {len(covered)}/{len(sources["sources"])} provisional masters; '
          f'minimum registered sampling {min(min(r["effective_sampling_xy"]) for r in registration.values()):.3f}x')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('family')
    process(parser.parse_args().family)
