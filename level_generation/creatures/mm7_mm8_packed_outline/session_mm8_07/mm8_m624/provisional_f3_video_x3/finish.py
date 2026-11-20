"""Build the authorized four-frame neural supplement without changing accepted imagegen assets."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
REPO = ROOT.parents[4]
CREATURES = REPO / 'level_generation/creatures'
sys.path.insert(0, str(ROOT.parent / 'mm8_m596'))
import session_workflow as w
sys.path.insert(0, str(CREATURES / 'mm8_remaining'))
import native_materials
import native_package
sys.path.insert(0, str(CREATURES / 'mm6_peasants'))
from package_family import edge_stats, overlay
from exact_placement import validate_manifest


def read(path):
    return json.loads(path.read_text())


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def finish():
    source = read(ROOT / 'sources.json')
    baseline = ROOT / 'redo_2x'
    original = read(baseline / 'manifest.json')
    accepted = read(baseline / 'review/acceptance.json')
    meta = read(OUT / 'upscale.json')
    assert w.sha(baseline / 'manifest.json') == meta['baseline_manifest']['sha256']
    assert w.sha(baseline / 'review/acceptance.json') == meta['baseline_acceptance']['sha256']
    for path, digest in accepted['artifact_sha256'].items():
        assert w.sha(REPO / path) == digest, path
    for entry in meta['model_files']:
        assert w.sha(REPO / entry['path']) == entry['sha256']
    assert w.sha(OUT / 'input/unused_f_3_rgb_extended.png') == meta['inference_input_sha256']
    assert w.sha(OUT / 'input/unused_f_3_native_rgba.png') == meta['native_sheet_sha256']
    raw_path = OUT / 'raw/unused_f_3_video_x3_rgb.png'
    raw = Image.open(raw_path).convert('RGB')
    cw, ch = meta['cell_native_size']
    assert raw.size == (cw * 6, ch * 6)
    names = meta['native_frame_names']
    assert names == original['missing_frames']
    config = read(baseline / 'material_settings.json')
    # These supports are authored on the enhanced pixels after inspecting native and enhanced materials.
    # FA3 exposes one tiny green costume sliver at the shoulder; the other three rear poses hide it.
    # Native palette tables also vary a few grey blade/tail pixels, which belong to protected materials.
    config['enhanced_material_support'] = dict(
        units='physical_2x_master_pixels', feather_px=.7,
        polygons={'m624fa3': [[278, 220], [286, 220], [294, 238], [282, 242], [276, 229]],
                  'm624fb3': [], 'm624fc3': [], 'm624fd3': []},
        method='Reviewed visible costume regions gate enhanced-RGB mask coverage. No resized native index mask.')
    save(OUT / 'material_settings.json', config)
    records = {}
    edges = {}
    for entry in meta['inputs']:
        name = entry['frame']
        native_path = OUT / entry['native_path']
        assert w.sha(native_path) == entry['native_sha256']
        native = Image.open(native_path).convert('RGBA')
        box = [v * 3 for v in entry['cell_rect']]
        clean = raw.crop(box).convert('RGBA')
        clean.putalpha(native.getchannel('A').resize(clean.size, Image.Resampling.LANCZOS))
        clean_path = OUT / 'masters_3x' / (name + '.png')
        clean.save(clean_path)
        master = clean.convert('RGBa').resize((cw * 2, ch * 2), Image.Resampling.LANCZOS).convert('RGBA')
        # Preserve the native silhouette at the physical export tier directly, without a second alpha resize.
        alpha = native.getchannel('A').resize(master.size, Image.Resampling.LANCZOS)
        master.putalpha(alpha)
        assert np.array_equal(np.array(master)[:, :, 3], np.array(alpha))
        assert not any(np.array(alpha)[edge].any() for edge in (0, -1))
        assert not np.array(alpha)[:, (0, -1)].any()
        path = OUT / 'aligned_2x' / (name + '.png')
        master.save(path)
        shutil.copy2(path, OUT / 'toned_2x' / path.name)
        mask_pixels = native_materials.masks(master, config)
        support = Image.new('L', master.size)
        polygon = config['enhanced_material_support']['polygons'][name]
        if polygon:
            ImageDraw.Draw(support).polygon(polygon, fill=255)
            support = support.filter(ImageFilter.GaussianBlur(config['enhanced_material_support']['feather_px']))
        mask = Image.fromarray(np.round(mask_pixels * (np.array(support) / 255)).astype(np.uint8))
        mask.save(OUT / 'masks_2x' / path.name)
        for palette in config['palette_deltas']:
            variant = native_materials.recolor(master, mask, int(palette), config)
            assert np.array_equal(np.array(variant)[:, :, 3], np.array(master)[:, :, 3])
            if int(palette) == source['base_palette']:
                assert np.array_equal(variant, master)
            variant.save(OUT / 'previews' / f'{name}_{palette}.png')
        origin = [meta['native_crop'][i] * 2 for i in (0, 1)]
        records[name] = dict(batch='unused_f_3_sheet', method='native_realesr_animevideov3_x3_temporary',
            raw_path=str(raw_path.relative_to(REPO)), raw_sha256=w.sha(raw_path), raw_size=list(raw.size),
            raw_rect=box, clean_path=str(clean_path.relative_to(REPO)), clean_sha256=w.sha(clean_path),
            native_crop=meta['native_crop'], native_bounds=entry['source']['native_bbox'], scale=2 / 3,
            effective_sampling_xy=[3, 3], sampling_kind='neural_upscale_of_native_1x_not_imagegen_detail',
            translate=origin, canvas_origin_px=origin, aligned_size_px=list(master.size), raw_clip=False,
            registration_native_offset=[0, 0], alpha_method='native_alpha_lanczos_at_each_physical_tier')
        edges['clean:' + name] = edge_stats(clean, 'magenta')
    subset = dict(source, sources={name: source['sources'][name] for name in names}, bindings={},
                  pixel_aliases={}, orphan_images=names)
    save(OUT / 'sources.json', subset)
    save(OUT / 'registration.json', records)
    for palette, entry in source['palette_sources'].items():
        destination = OUT / 'native_palettes' / (palette + '.bin')
        shutil.copy2(REPO / entry['path'], destination)
        assert w.sha(destination) == entry['sha256']
    native_package.ROOT = OUT
    native_package.run()
    supplement = read(OUT / 'draft_manifest.json')
    pages = []
    for page in original['pages']:
        page = deepcopy(page)
        for key in ('base', 'mask'):
            page[key] = '../redo_2x/' + page[key]
        pages.append(page)
    frames = deepcopy(original['frames'])
    for frame in frames.values():
        frame['physical_master'] = '../redo_2x/' + frame['physical_master']
        frame['restoration_method'] = 'packed_whole_animation_outline_imagegen'
    for name, frame in supplement['frames'].items():
        frame['page'] += len(pages)
        origin = np.asarray(frame['aligned_canvas_origin_px'])
        crop = np.asarray(frame['crop_in_aligned_px'][:2])
        size = frame['atlas_xywh'][2:]
        logical_origin = (origin + crop) / 2
        anchors = dict(bottom_center=source['logical_pivot'], center=[v / 2 for v in source['logical_canvas']])
        frame.update(native_offset=[0, 0], registration_native_offset=[0, 0],
            crop_origin_px=(origin + crop).tolist(), logical_crop_origin=logical_origin.tolist(),
            logical_size=[v / 2 for v in size], native_anchor_mapping={
                key: (np.asarray(anchor) - logical_origin).tolist() for key, anchor in anchors.items()},
            mirrored_anchor_mapping={key: [size[0] / 2 - (anchor[0] - logical_origin[0]),
                anchor[1] - logical_origin[1]] for key, anchor in anchors.items()},
            effective_neural_upscale_sampling_xy=[3, 3], physical_master='aligned_2x/' + name + '.png',
            restoration_method='temporary_native_realesr_animevideov3_x3', referenced=False)
        frames[name] = frame
    combined = deepcopy(original)
    combined.update(status='temporary_mixed_method_review_pending', frames=frames,
        pages=pages + supplement['pages'], missing_frames=[], unrestored_native_art={}, enhanced_frames=160,
        source_manifest='sources.json', source_run='../redo_2x/run.json', acceptance_record='review/acceptance.json',
        method='156 packed outline imagegen poses plus four user-authorized temporary native AnimeVideo x3 upscales',
        full_native_asset_coverage=True, full_latest_imagegen_method_coverage=False,
        coverage_by_method=dict(packed_outline_imagegen=156, temporary_native_video_x3=4),
        native_palettes={key: dict(path='native_palettes/' + key + '.bin', sha256=value['sha256'])
            for key, value in source['palette_sources'].items()},
        review_method='Prior hash-verified accepted imagegen review plus four new native-registered neural poses; pending new visual review.',
        upscale_record='upscale.json')
    combined['actual_generated_sampling']['scope'] = '156 imagegen poses only; the four native neural upscales are excluded.'
    all_records = dict(read(baseline / 'registration.json'), **records)
    assert not validate_manifest(combined, all_records)
    assert combined['animations'] == source['bindings'] == original['animations']
    assert set(frames) == set(source['sources'])
    assert {name for name, f in frames.items() if not f['referenced']} == set(source['orphan_images'])
    save(OUT / 'registration.json', all_records)
    save(OUT / 'sources.json', source)
    save(OUT / 'draft_manifest.json', combined)
    review_contacts(source, records, edges, supplement, len(pages))
    checks = read(OUT / 'review/export_checks.json')
    checks.update(exact_native_animation_bindings=True, unused_art_excluded_from_playback=True,
        exact_fractional_anchor_mapping=True, exact_mirrored_anchor_mapping=True,
        exact_native_alpha_at_physical_tier=True, no_new_raw_border_clip=True,
        prior_accepted_artifacts_verified_unchanged=len(accepted['artifact_sha256']),
        enhanced_frames=160, temporary_upscaled_frames=4, packed_imagegen_frames=156,
        full_latest_imagegen_method_coverage=False, installed=False, timed_playback_viewed=False)
    save(OUT / 'review/export_checks.json', checks)
    row = next(r for r in read(CREATURES / 'remaining_inventory.json')['families']
               if r['world'] == 'mm8' and r['label'] == source['label'])
    assert w.validate_native(source, row) == read(baseline / 'run.json')['current_native_tables']
    meta.update(status='exported_visual_review_pending', output_sha256=w.sha(raw_path),
        output_size=list(raw.size), backend=(OUT / 'raw/inference.log').read_text().splitlines()[:3],
        model_inference_complete=True, finished_utc=datetime.now(timezone.utc).isoformat())
    save(OUT / 'upscale.json', meta)
    print('Four x3 neural masters; four checked physical 2x masters; combined native coverage 160/160.')


def review_contacts(source, records, edges, supplement, page_offset):
    names = list(records)
    crop = read(OUT / 'upscale.json')['native_crop']
    for start in (0, 2):
        panel = Image.new('RGB', (1060, 1230), '#292d2b')
        draw = ImageDraw.Draw(panel)
        for row, name in enumerate(names[start:start + 2]):
            native = w.native_queue.native(ROOT, name, source['base_palette']).crop(crop)
            native = native.resize((530, 584), Image.Resampling.NEAREST)
            master = Image.open(OUT / 'aligned_2x' / (name + '.png')).convert('RGBA')
            for col, (label, image) in enumerate([('native 2x reference', native), ('Video x3 -> physical 2x', master)]):
                x, y = col * 530, row * 615
                draw.text((x + 3, y + 3), name + ' ' + label, fill='white')
                panel.paste(image, (x, y + 22), image)
        panel.save(OUT / 'review' / f'native_restored_{start // 2}.png')
    panel = Image.new('RGB', (1060, 1230), '#292d2b')
    draw = ImageDraw.Draw(panel)
    samples = []
    for row, name in enumerate(names):
        master = Image.open(OUT / 'aligned_2x' / (name + '.png')).convert('RGBA')
        mask = Image.open(OUT / 'masks_2x' / (name + '.png'))
        for col, palette in enumerate(['625', '626', '627', 'mask']):
            im = overlay(master, mask) if palette == 'mask' else Image.open(OUT / 'previews' / f'{name}_{palette}.png').convert('RGBA')
            im = im.convert('RGBa').resize((265, 292), Image.Resampling.LANCZOS).convert('RGBA')
            x, y = col * 265, row * 307
            draw.text((x + 3, y + 3), name + ' ' + palette, fill='white')
            panel.paste(im, (x, y + 15), im)
        clean = Image.open(OUT / 'masters_3x' / (name + '.png')).convert('RGBA')
        samples.append((name + ' clean edge', clean, edges['clean:' + name]['position']))
        frame = supplement['frames'][name]
        page = supplement['pages'][frame['page'] - page_offset]
        x, y, width, height = frame['atlas_xywh']
        tile = Image.open(OUT / page['base']).convert('RGBA').crop((x, y, x + width, y + height))
        stats = edge_stats(tile, 'magenta')
        edges['atlas:' + name] = stats
        samples.append((name + ' atlas edge', tile, stats['position']))
    panel.save(OUT / 'review/palette_mask_poses.png')
    for name, point, label in [('m624fa3', [351, 235], 'hair and gold costume'),
                               ('m624fa3', [360, 530], 'scales and skin')]:
        samples.append((label, Image.open(OUT / 'masters_3x' / (name + '.png')).convert('RGBA'), point))
    panel = Image.new('RGB', (1072, 462), '#333333')
    draw = ImageDraw.Draw(panel)
    for i, (label, im, point) in enumerate(samples):
        x, y = i % 4 * 268, i // 4 * 154
        draw.text((x + 3, y + 3), label, fill='white')
        cx, cy = point
        patch = im.crop((cx - 64, cy - 64, cx + 64, cy + 64))
        for side, color in enumerate(['#262a28', '#eee9df']):
            bg = Image.new('RGBA', (128, 128), color)
            bg.alpha_composite(patch)
            panel.paste(bg, (x + side * 134, y + 22))
    panel.save(OUT / 'review/detail_edges_100pct.png')
    save(OUT / 'review/edge_checks.json', dict(status='visual_review_pending', frames=edges,
         cleaned_frames_scanned=4, atlas_frames_scanned=4, all_alpha_levels_included=True,
         method='Shared alpha-weighted magenta-excess contour diagnostic; alpha-zero RGB ignored. Inference input has no matte color.'))


if __name__ == '__main__':
    finish()
