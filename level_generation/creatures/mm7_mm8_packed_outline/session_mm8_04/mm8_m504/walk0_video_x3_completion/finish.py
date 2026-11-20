"""Local bridge for the authorized mixed-method supplement; reuse shared exporters."""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
REPO = ROOT.parents[4]
C = REPO / 'level_generation/creatures'
sys.path[:0] = [str(C), str(C / 'mm8_remaining')]
import native_materials
import native_package
from mm8_restore_queue import native
from exact_placement import validate_manifest


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def composite(image, colour):
    bg = Image.new('RGBA', image.size, colour)
    bg.alpha_composite(image)
    return bg.convert('RGB')


def finish():
    meta = read(OUT / 'upscale.json')
    original = read(ROOT / 'draft_manifest.json')
    accepted = read(ROOT / 'review/partial_acceptance.json')
    assert sha(ROOT / 'draft_manifest.json') == meta['baseline_manifest']['sha256']
    assert sha(ROOT / 'review/partial_acceptance.json') == meta['baseline_acceptance']['sha256']
    for path, digest in accepted['artifact_hashes'].items():
        assert sha(ROOT / path) == digest, path
    for row in meta['model_files']:
        assert sha(REPO / row['path']) == row['sha256']
    assert sha(REPO / meta['inference_input']) == meta['input_sha256']
    assert sha(REPO / meta['native_sheet']) == meta['native_sheet_sha256']
    sources = read(ROOT / 'sources.json')
    config = read(ROOT / 'material_settings.json')
    names = meta['native_frame_names']
    assert set(names) == set(original['missing_frames'])
    raw_path = OUT / 'raw/walk_0_video_x3_rgb.png'
    raw = Image.open(raw_path).convert('RGB')
    cw, ch = meta['cell_native_size']
    assert raw.size == (cw * meta['columns'] * 3, ch * meta['rows'] * 3)
    records = {}
    for row in meta['inputs']:
        name = row['frame']
        assert sha(REPO / sources['sources'][name]['path']) == row['source_sha256']
        reference = native(ROOT, name, sources['base_palette']).crop(meta['native_crop'])
        reference.save(OUT / 'input' / (name + '.png'))
        clean = raw.crop([v * 3 for v in row['cell_rect']]).convert('RGBA')
        clean.putalpha(reference.getchannel('A').resize(clean.size, Image.Resampling.LANCZOS))
        clean.save(OUT / 'masters_3x' / (name + '.png'))
        master = clean.convert('RGBa').resize((cw * 2, ch * 2), Image.Resampling.LANCZOS).convert('RGBA')
        alpha = reference.getchannel('A').resize(master.size, Image.Resampling.LANCZOS)
        master.putalpha(alpha)
        assert not np.asarray(alpha)[[0, -1]].any() and not np.asarray(alpha)[:, [0, -1]].any()
        master.save(OUT / 'aligned_2x' / (name + '.png'))
        master.save(OUT / 'toned_2x' / (name + '.png'))
        mask = Image.fromarray(native_materials.masks(master, config))
        mask.save(OUT / 'masks_2x' / (name + '.png'))
        for palette in config['palette_deltas']:
            variant = native_materials.recolor(master, mask, int(palette), config)
            assert np.array_equal(np.asarray(variant)[:, :, 3], np.asarray(master)[:, :, 3])
            if int(palette) == sources['base_palette']:
                assert np.array_equal(variant, master)
            variant.save(OUT / 'previews' / f'{name}_{palette}.png')
            native(ROOT, name, int(palette)).save(OUT / 'native_variants' / f'{name}_{palette}.png')
        origin = [v * 2 for v in meta['native_crop'][:2]]
        records[name] = dict(batch='walk_0_sheet', method=meta['method'], raw_path=str(raw_path.relative_to(REPO)),
            raw_sha256=sha(raw_path), raw_size=list(raw.size), raw_rect=[v * 3 for v in row['cell_rect']],
            clean_path=str((OUT / 'masters_3x' / (name + '.png')).relative_to(REPO)),
            native_crop=meta['native_crop'], native_bounds=sources['sources'][name]['native_bbox'],
            scale=2 / 3, effective_sampling_xy=[3, 3], sampling_kind=meta['generated_detail_kind'],
            translate=origin, canvas_origin_px=origin, aligned_size_px=list(master.size), raw_clip=False,
            registration_native_offset=[0, 0], alpha_method='native_alpha_lanczos_at_each_physical_tier')
    save(OUT / 'sources.json', dict(sources, sources={n: sources['sources'][n] for n in names},
         bindings={}, pixel_aliases={}, orphan_images=[]))
    save(OUT / 'registration.json', records)
    save(OUT / 'material_settings.json', config)
    for palette, row in sources['palette_sources'].items():
        shutil.copy2(REPO / row['path'], OUT / 'native_palettes' / (palette + '.bin'))
    native_package.ROOT = OUT
    native_package.run()
    supplement = read(OUT / 'draft_manifest.json')
    pages = deepcopy(original['pages'])
    for page in pages:
        for key in ('base', 'mask'):
            page[key] = '../' + page[key]
    frames = deepcopy(original['frames'])
    for name, frame in frames.items():
        frame.update(physical_master='../aligned_2x/' + name + '.png',
                     restoration_method='packed_whole_animation_outline_imagegen')
    for name, frame in supplement['frames'].items():
        frame['page'] += len(pages)
        frame.update(physical_master='aligned_2x/' + name + '.png',
            restoration_method=meta['method'], effective_neural_upscale_sampling_xy=[3, 3])
        frames[name] = frame
    all_records = dict(read(ROOT / 'registration.json'), **records)
    for name, frame in frames.items():
        origin = np.asarray(frame['aligned_canvas_origin_px']) + frame['crop_in_aligned_px'][:2]
        frame.update(native_offset=[0, 0], registration_native_offset=[0, 0], crop_origin_px=origin.tolist(),
            logical_crop_origin=(origin / 2).tolist(), logical_size=[v / 2 for v in frame['atlas_xywh'][2:]],
            native_anchor_mapping={k: (np.asarray(a) - origin / 2).tolist()
                for k, a in dict(center=[128, 128], bottom_center=[128, 256]).items()},
            mirrored_anchor_mapping={k: [frame['atlas_xywh'][2] / 2 - (a[0] - origin[0] / 2), a[1] - origin[1] / 2]
                for k, a in dict(center=[128, 128], bottom_center=[128, 256]).items()})
    combined = dict(deepcopy(original), frames=frames, pages=pages + supplement['pages'],
        status='mixed_method_visual_review_pending', full_coverage=True, missing_frames=[],
        source_manifest='sources.json', review_evidence='review/acceptance.json', anchor='center',
        full_latest_imagegen_method_coverage=False, coverage_by_method=dict(packed_outline_imagegen=152, native_video_x3=8),
        native_palette_exports={p: dict(path='native_palettes/' + p + '.bin', sha256=r['sha256'])
            for p, r in sources['palette_sources'].items()}, installed=False)
    combined.pop('packing_snapshot', None)
    combined.pop('partial_contract', None)
    assert set(frames) == set(sources['sources'])
    assert combined['animations'] == sources['bindings']
    assert not validate_manifest(combined, all_records)
    save(OUT / 'sources.json', sources)
    save(OUT / 'registration.json', all_records)
    save(OUT / 'draft_manifest.json', combined)
    for start in range(0, 8, 2):
        panel = Image.new('RGB', (664, 890), '#292d2b')
        draw = ImageDraw.Draw(panel)
        for i, name in enumerate(names[start:start + 2]):
            reference = Image.open(OUT / 'input' / (name + '.png')).convert('RGBA').resize((332, 420), Image.Resampling.NEAREST)
            master = Image.open(OUT / 'aligned_2x' / (name + '.png')).convert('RGBA')
            for col, im in enumerate((reference, master)):
                draw.text((col * 332 + 4, i * 445 + 4), name + (' native 2x' if col == 0 else ' Video x3 -> 2x'), fill='white')
                panel.paste(im, (col * 332, i * 445 + 22), im)
        panel.save(OUT / 'review' / f'poses_{start // 2}.png')
    for start in range(0, 8, 4):
        panel = Image.new('RGB', (1328, 1768), '#292d2b')
        draw = ImageDraw.Draw(panel)
        for i, name in enumerate(names[start:start + 4]):
            master = Image.open(OUT / 'aligned_2x' / (name + '.png')).convert('RGBA')
            for col, palette in enumerate(('504', '506', '507', 'mask')):
                if palette == 'mask':
                    mask = Image.open(OUT / 'masks_2x' / (name + '.png')).convert('RGB').convert('RGBA')
                    mask.putalpha(master.getchannel('A'))
                    im = mask
                else:
                    im = Image.open(OUT / 'previews' / f'{name}_{palette}.png').convert('RGBA')
                draw.text((col * 332 + 4, i * 442 + 3), name + ' ' + palette, fill='white')
                panel.paste(im, (col * 332, i * 442 + 20), im)
        panel.save(OUT / 'review' / f'palettes_masks_{start // 4}.png')
    detail = Image.new('RGB', (1024, 1056), '#292d2b')
    draw = ImageDraw.Draw(detail)
    for i, name in enumerate(names):
        master = Image.open(OUT / 'masters_3x' / (name + '.png')).convert('RGBA')
        # Material and contour patches at actual inference resolution, never enlarged.
        for col, box in enumerate(((150, 55, 406, 311), (65, 80, 321, 336))):
            patch = master.crop(box)
            for side, colour in enumerate(('#292d2b', '#eee9df')):
                x = (col * 2 + side) * 256
                y = i * 132
                selected = patch.crop((0, 0, 256, 128))
                detail.paste(composite(selected, colour), (x, y + 4))
                draw.text((x + 3, y + 4), name, fill='white')
    detail.save(OUT / 'review/detail_edges_100pct.png')
    meta.update(status='exported_visual_review_pending', output_sha256=sha(raw_path), output_size=list(raw.size),
        backend='realesrgan-ncnn-vulkan, RTX 3060 Ti, realesr-animevideov3-x3, tile 256',
        prior_accepted_artifacts_verified_unchanged=len(accepted['artifact_hashes']))
    save(OUT / 'upscale.json', meta)
    print('Earth: 160/160 exports, 152 packed imagegen + eight native Video x3; visual review pending')


if __name__ == '__main__':
    finish()
