"""Atlas exporter for inventoried MM8 families without a previous restoration package."""
import copy
import math
import shutil

import numpy as np
from PIL import Image
from scipy import ndimage

from prepare_detail import REPO, read, save, sha, native_queue

ROOT = None


def run():
    sources = read(ROOT / 'sources.json')
    records = read(ROOT / 'registration.json')
    aliases = sources.get('pixel_aliases', {})
    assert set(records) == set(sources['sources']) - set(aliases)
    config = read(ROOT / 'material_settings.json')
    palettes = list(config['palette_deltas'])
    for folder in ['atlas', 'runtime_aligned_2x', 'runtime_masks_2x']:
        (ROOT / folder).mkdir(exist_ok=True)
    frames, tiles, masks = {}, {}, {}
    for name, source in sources['sources'].items():
        assert sha(REPO / source['path']) == source['sha256'], name
        if name in aliases:
            canonical = sources['sources'][aliases[name]]
            assert source['pixel_hash'] == canonical['pixel_hash'] and source['size'] == canonical['size']
            for palette in palettes:
                assert np.array_equal(native_queue.native(ROOT, name, int(palette)),
                                      native_queue.native(ROOT, aliases[name], int(palette)))
            continue
        record = records[name]
        image = Image.open(ROOT / 'toned_2x' / (name + '.png')).convert('RGBA')
        pixels = np.array(image)
        mask = np.array(Image.open(ROOT / 'masks_2x' / (name + '.png')))
        assert mask.shape == pixels.shape[:2]
        solid = pixels[:, :, 3] > 0
        distance, nearest = ndimage.distance_transform_edt(~solid, return_indices=True)
        ring = (distance <= 3) & ~solid
        pixels[:, :, :3][~solid] = 0
        pixels[:, :, :3][ring] = pixels[nearest[0], nearest[1], :3][ring]
        mask[~solid] = 0
        mask[ring] = mask[nearest[0], nearest[1]][ring]
        image, coverage = Image.fromarray(pixels), Image.fromarray(mask)
        image.save(ROOT / 'runtime_aligned_2x' / (name + '.png'))
        coverage.save(ROOT / 'runtime_masks_2x' / (name + '.png'))
        bounds = image.getchannel('A').getbbox()
        box = [max(0, bounds[0] - 4), max(0, bounds[1] - 4),
               min(image.width, bounds[2] + 4), min(image.height, bounds[3] + 4)]
        tiles[name], masks[name] = image.crop(box), coverage.crop(box)
        for tile, original in [(tiles[name], image), (masks[name], coverage)]:
            rebuilt = Image.new(original.mode, original.size)
            rebuilt.paste(tile, box[:2])
            assert np.array_equal(rebuilt, original), name
        for palette in palettes:
            variant = np.asarray(Image.open(ROOT / 'previews' / f'{name}_{palette}.png'))
            assert np.array_equal(variant[:, :, 3], pixels[:, :, 3]), name
            if int(palette) == config['base_palette']:
                assert np.array_equal(variant[solid], pixels[solid]), name
        frames[name] = dict(source=name + '.bmp', source_canvas=source['size'],
                            crop_in_aligned_px=box, aligned_canvas_origin_px=record['canvas_origin_px'],
                            aligned_canvas_size_px=record['aligned_size_px'], referenced=source['referenced'])
    layouts, current = [], []
    x = y = row_height = 0
    for name, tile in sorted(tiles.items(), key=lambda pair: (-pair[1].height, pair[0])):
        width, height = [math.ceil((value + 32) / 16) * 16 for value in tile.size]
        assert max(width, height) <= 2048
        if x + width > 2048:
            x = 0
            y += row_height
            row_height = 0
        if y + height > 2048:
            layouts.append(current)
            current = []
            x = y = row_height = 0
        current.append((name, x, y, width, height))
        x += width
        row_height = max(row_height, height)
    if current:
        layouts.append(current)
    pages = []
    for page_id, layout in enumerate(layouts):
        size = (max(x + w for n, x, y, w, h in layout), max(y + h for n, x, y, w, h in layout))
        base, mask = Image.new('RGBA', size), Image.new('L', size)
        for name, x, y, width, height in layout:
            tile = tiles[name]
            rect = [x + 16, y + 16, tile.width, tile.height]
            base.paste(tile, rect[:2])
            mask.paste(masks[name], rect[:2])
            frames[name].update(page=page_id, atlas_xywh=rect)
            assert np.array_equal(base.crop((rect[0], rect[1], rect[0] + tile.width, rect[1] + tile.height)), tile)
            assert np.array_equal(mask.crop((rect[0], rect[1], rect[0] + tile.width, rect[1] + tile.height)), masks[name])
        bp, mp = f'atlas/base_{page_id}.png', f'atlas/mask_{page_id}.png'
        base.save(ROOT / bp)
        mask.save(ROOT / mp)
        pages.append(dict(base=bp, mask=mp, size=list(size), base_format='RGBA8', mask_format='R8',
                          base_color_space='sRGB', mask_color_space='linear coverage', gutter_px=16, mipmaps=False))
    for name, canonical in aliases.items():
        frames[name] = dict(copy.deepcopy(frames[canonical]), source=name + '.bmp', pixel_alias_of=canonical,
                            referenced=sources['sources'][name]['referenced'])
        for folder in ['runtime_aligned_2x', 'runtime_masks_2x']:
            shutil.copy2(ROOT / folder / (canonical + '.png'), ROOT / folder / (name + '.png'))
        for palette in palettes:
            shutil.copy2(ROOT / 'previews' / f'{canonical}_{palette}.png', ROOT / 'previews' / f'{name}_{palette}.png')
            native_queue.native(ROOT, name, int(palette)).save(ROOT / 'native_variants' / f'{name}_{palette}.png')
    for actor in sources['bindings'].values():
        for action in actor['actions'].values():
            for sequence in action['views'].values():
                assert all(step['frame'] is None or step['frame'] in frames for step in sequence)
    manifest = dict(schema_version=1, creature=sources['creature'], status='preproduction_review_pending',
                    pixels_per_logical_pixel=2, frames=frames, pages=pages, animations=sources['bindings'],
                    regions=config['regions'], variants=config, missing_frames=[], source_manifest='sources.json',
                    viewer='viewer.html', installed=False, pixel_aliases=aliases,
                    filter_policy='Premultiplied-alpha resizing; 3px hidden color bleed; 16px gutters; no mipmaps.',
                    runtime_support='Offline palette-delta previews; runtime installation is separate.')
    save(ROOT / 'draft_manifest.json', manifest)
    pixels = sum(page['size'][0] * page['size'][1] for page in pages)
    tight = sum(tile.width * tile.height * 5 for tile in tiles.values())
    save(ROOT / 'review/export_checks.json', dict(source_files=len(frames), unique_frames=len(records),
         full_coverage=True, pixel_aliases_verified=aliases, source_hashes_unchanged=True,
         exact_crop_reconstruction=True, exact_atlas_extraction=True, base_mask_placement_identical=True,
         variant_alpha_unchanged=True, base_bypass_exact=True, visual_review_complete=False,
         animation_review_complete=False, memory_bytes=dict(base_rgba8=pixels * 4, mask_r8=pixels,
         total_base_mask_packing=pixels * 5, tight_rgba_plus_mask=tight, packing_overhead=pixels * 5 - tight)))
    print(len(records), 'masters;', len(aliases), 'aliases;', len(pages), 'atlas pairs;', pixels * 5, 'bytes')
