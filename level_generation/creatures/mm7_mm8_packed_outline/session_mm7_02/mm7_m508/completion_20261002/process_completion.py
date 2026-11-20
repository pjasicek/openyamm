"""Local bridge for legacy Air schema and multi-school Fish supplements.

Shared extraction, registration measurements, materials and atlas exports retain ownership.
This bridge writes candidates only; visual decisions and frozen acceptance are separate.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

REPO = Path(__file__).resolve().parents[6]
C = REPO / 'level_generation/creatures'
sys.path[:0] = [str(C), str(C / 'mm6_remaining/redo_2x'), str(C / 'mm8_remaining'),
               str(C / 'mm7_mm8_packed_outline/session_mm8_04/mm8_m496')]
from extract_run import connected_cells
from annotate_radial import box_and_alpha, core, envelope
from process_session import preserve_detached_components
from mm8_restore_queue import native
import native_materials
import native_package
from exact_placement import validate_manifest


def read(path):
    return json.loads(path.read_text())


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def composite(im, colour):
    bg = Image.new('RGBA', im.size, colour)
    bg.alpha_composite(im)
    return bg.convert('RGB')


def multi_school_components(raw, job):
    """Candidate ownership for interleaved schools: move whole components, never cut a fish."""
    pixels = np.asarray(raw)
    labels, count = ndimage.label(pixels[:, :, 3] > 0)
    component_owner = np.zeros(count + 1, dtype=np.int16)
    assignments = []
    partitions = job.get('reviewed_return_partitions')
    if partitions:
        assert partitions['raw_sha256'] == sha(REPO / job['selected_raw'])
        assert partitions['reason']
    for label, bounds in enumerate(ndimage.find_objects(labels), 1):
        selected = labels[bounds] == label
        weight = pixels[bounds][:, :, 3] * selected
        yy, xx = np.indices(selected.shape)
        x = float((xx * weight).sum() / weight.sum() + bounds[1].start)
        y = float((yy * weight).sum() / weight.sum() + bounds[0].start)
        if partitions:
            row = int(np.searchsorted(partitions['ycuts'], y, side='right') - 1)
            column = int(np.searchsorted(partitions['xcuts'][row], x, side='right') - 1)
            cell = row * job['columns'] + column
        else:
            cell = int(y * job['rows'] / raw.height) * job['columns'] + int(x * job['columns'] / raw.width)
        assert cell < len(job['frames']), 'Foreground in an unused cell requires visual rejection'
        component_owner[label] = cell + 1
        assignments.append(dict(component=label, alpha_weighted_center=[x, y], cell=cell,
            pixels=int(selected.sum()), whole_component_bounds=[bounds[1].start, bounds[0].start,
                bounds[1].stop, bounds[0].stop]))
    ownership = component_owner[labels]
    cells = []
    assigned = 0
    for index in range(len(job['frames'])):
        selected = pixels.copy()
        selected[ownership != index + 1] = 0
        assigned += int((selected[:, :, 3] > 0).sum())
        im = Image.fromarray(selected)
        box = im.getbbox()
        assert box, 'Missing returned school'
        rect = [max(0, box[0] - 12), max(0, box[1] - 12), min(raw.width, box[2] + 12), min(raw.height, box[3] + 12)]
        cells.append((rect, im.crop(rect)))
    assert assigned == int((pixels[:, :, 3] > 0).sum())
    return cells, [dict(method='Whole generated components assigned by reviewed cell centres; no component cut',
                        status='candidate_requires_every_school_review', assignments=assignments)]


def process(root, out, fish=False):
    source = read(root / 'sources.json')
    run = read(out / 'run.json')
    for folder in ('cleaned', 'aligned_2x', 'toned_2x', 'masks_2x', 'previews', 'native_variants', 'native_palettes', 'review'):
        (out / folder).mkdir(exist_ok=True)
    if not fish:
        source['creature'] = 'mm8:m508 (shared MM7/MM8 native art)'
        source['label'] = 'Elemental Air A'
        source['bindings'] = {}
        source['orphan_images'] = source['unreferenced']
        for name, row in source['sources'].items():
            row.update(base_palette=508, native_bbox=row['visible_bounds'], transparent_index=0,
                pixel_hash=hashlib.sha256(Image.open(REPO / row['path']).tobytes()).hexdigest())
    save(out / 'sources.json', source)
    config = (read(root / 'material_settings.json') if fish else
        dict(base_palette=508, base_exact_bypass=True, palette_deltas={'508': [[0, 0, 0]] * 255},
             regions=[], operation='exact_base_bypass', mask_semantics='R8 zero: sole native palette'))
    save(out / 'material_settings.json', config)
    for palette, row in source['palette_sources'].items():
        assert sha(REPO / row['path']) == row['sha256']
        shutil.copy2(REPO / row['path'], out / 'native_palettes' / (palette + '.bin'))
    records, extraction, calibration = {}, {}, {}
    for job in run['jobs']:
        if not job.get('selected_raw'):
            continue
        raw_path = REPO / job['selected_raw']
        raw = Image.open(raw_path).convert('RGBA')
        noise = 0
        if fish:
            pixels = np.array(raw)
            low = (pixels[:, :, 3] > 0) & (pixels[:, :, 3] <= 8)
            noise = int(low.sum())
            pixels[low] = 0
            raw = Image.fromarray(pixels)
        if job.get('reviewed_return_partitions'):
            cells, changes = multi_school_components(raw, job)
        else:
            try:
                cells = connected_cells(raw, job, grid_groups=True, seed_alpha_threshold=4 if fish else 64)
                cells, changes = preserve_detached_components(raw, cells, job)
            except AssertionError as error:
                # Interleaved multi-fish schools are unsupported by the ordinary single-body seeds.
                if fish:
                    cells, changes = multi_school_components(raw, job)
                    changes[0]['shared_gutter_failure'] = str(error)
                else:
                    changes = [dict(status='manual_ownership_review_required', reason=str(error))]
        ratios = []
        for i, (name, (_, clean)) in enumerate(zip(job['frames'], cells, strict=True)):
            if not fish and name.startswith('m508d') and i >= 2:
                continue
            nb, _ = box_and_alpha(native(out, name, source['base_palette']))
            rb, _ = box_and_alpha(clean)
            ratios.append((rb[3] - rb[1]) / (nb[3] - nb[1]))
        sampling = float(np.median(ratios))
        factor = 2 / sampling
        calibration[job['id']] = dict(generated_sampling=sampling, per_pose_height_ratios=ratios,
            common_scale_to_2x=factor, method='One common median envelope-height scale per whole animation; '
            'Air dissolution uses first two anatomical poses, not shrinking particle endpoints. Independent features require visual review.')
        extraction[job['id']] = dict(raw_path=str(raw_path.relative_to(REPO)), raw_sha256=sha(raw_path),
            seed_alpha_threshold=4 if fish else 64, supplied_alpha_noise_floor=8 if fish else 0,
            removed_near_transparent_noise_pixels=noise, detached_component_ownership_repairs=changes,
            method='Shared connected-component grouping; whole detached components retained; no native alpha stencil.', frames=[])
        for start in range(0, len(cells), 4):
            panel = Image.new('RGB', (1024, 548 * min(4, len(cells) - start)), '#292d2b')
            draw = ImageDraw.Draw(panel)
            for i in range(start, min(start + 4, len(cells))):
                name = job['frames'][i]
                rect, clean = cells[i]
                reference = native(out, name, source['base_palette'])
                nb, npix = box_and_alpha(reference)
                rb, rpix = box_and_alpha(clean)
                particle = fish or (name.startswith('m508d') and i >= 2)
                nc, rc = core(npix, nb, particle=particle), core(rpix, rb, particle=particle)
                anchor_feature = 'school_alpha_centroid' if fish else 'core_anchor'
                if not fish and name.startswith('m508d') and i < 2:
                    # Reviewed native raised fingertips remain visible in both opening death poses.
                    # Darkness centroid is unstable as the rear torso becomes translucent.
                    nc, rc = envelope(npix, nb, True), envelope(rpix, rb, True)
                    anchor_feature = 'raised_hand_tip'
                size = [max(1, round(v * factor)) for v in clean.size]
                effective = np.asarray(size) / clean.size
                translation = np.round(np.asarray(nc) * 2 - np.asarray(rc) * effective).astype(int)
                resized = clean.convert('RGBa').resize(size, Image.Resampling.LANCZOS).convert('RGBA')
                bounds = resized.getbbox()
                origin = np.minimum([0, 0], translation + bounds[:2] - 4)
                end = np.maximum(np.asarray(source['logical_canvas']) * 2, translation + bounds[2:] + 4)
                aligned = Image.new('RGBA', tuple(end - origin))
                aligned.paste(resized, tuple(translation - origin))
                points = dict(core_anchor=dict(native=nc, restored=rc),
                    upper_envelope=dict(native=envelope(npix, nb, True), restored=envelope(rpix, rb, True)),
                    lower_envelope=dict(native=envelope(npix, nb, False), restored=envelope(rpix, rb, False)))
                extraction[job['id']]['frames'].append(dict(frame=name, raw_rect=rect, clean_bounds=rb))
                if name not in records:
                    clean_path = out / 'cleaned' / (name + '.png')
                    clean.save(clean_path)
                    aligned.save(out / 'aligned_2x' / (name + '.png'))
                    aligned.save(out / 'toned_2x' / (name + '.png'))
                    mask = (Image.fromarray(native_materials.masks(aligned, config)) if fish else Image.new('L', aligned.size))
                    mask.save(out / 'masks_2x' / (name + '.png'))
                    for palette in config['palette_deltas']:
                        variant = native_materials.recolor(aligned, mask, int(palette), config) if fish else aligned.copy()
                        assert np.array_equal(np.asarray(variant)[:, :, 3], np.asarray(aligned)[:, :, 3])
                        if int(palette) == source['base_palette']:
                            assert np.array_equal(variant, aligned)
                        variant.save(out / 'previews' / f'{name}_{palette}.png')
                        native(out, name, int(palette)).save(out / 'native_variants' / f'{name}_{palette}.png')
                    records[name] = dict(batch=job['id'], raw_path=str(raw_path.relative_to(REPO)), raw_sha256=sha(raw_path),
                        raw_size=list(raw.size), raw_rect=rect, clean_path=str(clean_path.relative_to(REPO)),
                        clean_sha256=sha(clean_path), native_crop=job['native_crop'], native_bounds=nb,
                        scale=factor, effective_sampling_xy=(2 / effective).tolist(),
                        translate=translation.tolist(), canvas_origin_px=origin.tolist(), aligned_size_px=list(aligned.size),
                        raw_clip=False, placement_landmarks=points, translation_anchor_feature=anchor_feature,
                        independent_placement_review='pending')
                y = (i - start) * 548
                draw.text((4, y + 4), f'{i + 1}: {name} native / enhanced; independent features pending', fill='white')
                native_display = reference.resize((512, 512), Image.Resampling.NEAREST)
                panel.paste(native_display, (0, y + 24), native_display)
                display = Image.new('RGBA', (512, 512))
                display.paste(aligned, tuple(origin))
                panel.paste(display, (512, y + 24), display)
                for label, point in points.items():
                    for col in (0, 1):
                        xy = np.asarray(point['native']) * 2 if col == 0 else np.asarray(point['restored']) * effective + translation
                        x, yy = xy[0] + col * 512, xy[1] + y + 24
                        draw.line((x - 3, yy, x + 3, yy), fill='#30eeee' if label == 'core_anchor' else '#ffb050')
                        draw.line((x, yy - 3, x, yy + 3), fill='#30eeee' if label == 'core_anchor' else '#ffb050')
            panel.save(out / 'review' / f'{job["id"]}_placement_{start // 4}.png')
        print(job['id'], len(cells), 'poses, sampling', round(sampling, 3), flush=True)
    save(out / 'registration.json', records)
    save(out / 'processing.json', dict(status='candidate_visual_review_pending', extraction=extraction, calibration=calibration,
        alpha='Preserved generated alpha; Fish removes only reviewed alpha<=8 RGB scatter; no native silhouette transfer',
        whole_animation_resolution_policy='One full native cycle per view per returned sheet; below2x measured and reviewable'))
    subset = dict(source, sources={n: source['sources'][n] for n in records}, bindings={}, pixel_aliases={})
    save(out / 'sources.json', subset)
    native_package.ROOT = out
    native_package.run()
    manifest = read(out / 'draft_manifest.json')
    manifest.update(logical_canvas=source['logical_canvas'], logical_pivot=source['logical_pivot'],
        anchor='bottom-center', generated_sampling_min=min(min(r['effective_sampling_xy']) for r in records.values()),
        placement_registration='registration.json')
    for name, frame in manifest['frames'].items():
        origin = np.asarray(frame['aligned_canvas_origin_px']) + frame['crop_in_aligned_px'][:2]
        frame.update(native_offset=[0, 0], registration_native_offset=[0, 0], crop_origin_px=origin.tolist(),
            logical_crop_origin=(origin / 2).tolist(), logical_size=[v / 2 for v in frame['atlas_xywh'][2:]],
            native_anchor_mapping={k: (np.asarray(a) - origin / 2).tolist()
                for k, a in dict(center=[128, 128], bottom_center=[128, 256]).items()},
            mirrored_anchor_mapping={k: [frame['atlas_xywh'][2] / 2 - (a[0] - origin[0] / 2), a[1] - origin[1] / 2]
                for k, a in dict(center=[128, 128], bottom_center=[128, 256]).items()},
            effective_generated_sampling_xy=records[name]['effective_sampling_xy'], physical_master='aligned_2x/' + name + '.png')
    assert not validate_manifest(manifest, records)
    if fish:
        assert set(records) == set(source['sources'])
        manifest['animations'] = source['bindings']
        manifest['missing_frames'] = []
    save(out / 'sources.json', source)
    save(out / 'draft_manifest.json', manifest)
    print(len(records), 'candidates exported; visual acceptance remains pending')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('out', type=Path)
    p.add_argument('--fish', action='store_true')
    a = p.parse_args()
    process(a.root.resolve(), a.out.resolve(), a.fish)
