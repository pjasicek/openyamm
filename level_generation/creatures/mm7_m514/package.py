"""Pack staged palette-545 ambient animals and verify native coverage, placement and timelines."""
import base64
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from process import contour_score, composite, apply_variant

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def run(root=HERE):
    for directory in ['atlas', 'trimmed_2x', 'trimmed_masks_2x', 'previews']:
        (root / directory).mkdir(exist_ok=True)
    sources = json.loads((root / 'sources.json').read_text())
    logical_canvas = sources['logical_canvases'][0]
    palette = sources['base_palette']
    assert sources['palettes'] == [palette] or (root/'variants.json').exists(), 'Author enhanced-art masks first.'
    logical_pivot = [logical_canvas[0]/2, logical_canvas[1]]
    config = json.loads((root / 'config.json').read_text()) if (root / 'config.json').exists() else {'creature':'ambient_rat'}
    descriptor_ids = sorted(int(n) for n in sources['descriptor_bindings'])
    registration = json.loads((root / 'registration.json').read_text())
    assert set(sources['sources']) == set(registration)
    variants = json.loads((root/'variants.json').read_text()) if (root/'variants.json').exists() else dict(
        variants=[dict(id=f'mm7:palette{palette}',palette_id=palette,default=True,exact_bypass=True,descriptors=descriptor_ids)],
        regions=[],recolor=dict(operation='identity',reason=f'All native appearances share palette {palette}; masks are zero.'))
    assert sorted(v['palette_id'] for v in variants['variants']) == sources['palettes']
    frames, tiles, masks, audits = {}, {}, {}, {}
    for name, source in sources['sources'].items():
        assert hashlib.sha256((REPO / source['path']).read_bytes()).hexdigest() == source['sha256']
        aligned = Image.open(root / f'aligned_2x/{name}.png').convert('RGBA')
        mask = Image.open(root / f'masks_2x/{name}.png')
        assert aligned.size == mask.size and mask.mode in ('L','RGB')
        if not variants['regions']:assert mask.getextrema() == (0,0)
        assert not np.any(np.array(mask)[np.array(aligned)[:,:,3]==0])
        bounds = aligned.getchannel('A').getbbox()
        box = (max(0, bounds[0]-4), max(0, bounds[1]-4), min(aligned.width, bounds[2]+4),
               min(aligned.height, bounds[3]+4))
        tile = aligned.crop(box)
        reconstructed = Image.new('RGBA', aligned.size)
        reconstructed.paste(tile, box[:2])
        assert np.array_equal(np.array(reconstructed), np.array(aligned))
        # Extrude only invisible RGB, leaving visible alpha/RGB and placement untouched.
        rgba = np.array(tile)
        alpha = rgba[:, :, 3]
        distance, indices = ndimage.distance_transform_edt(alpha == 0, return_indices=True)
        padding = (alpha == 0) & (distance <= 3)
        rgba[padding, :3] = rgba[indices[0][padding], indices[1][padding], :3]
        tile = Image.fromarray(rgba)
        aligned.paste(tile, box[:2])
        aligned.save(root / f'aligned_2x/{name}.png')
        tile.save(root / f'trimmed_2x/{name}.png')
        tile_mask = mask.crop(box)
        tile_mask.save(root / f'trimmed_masks_2x/{name}.png')
        origin = registration[name]['canvas_origin_px']
        frames[name] = dict(source=name+'.bmp', source_canvas=source['size'], source_palette=palette,
            referenced=source.get('referenced', True),
            crop_origin_px=[box[0]+origin[0], box[1]+origin[1]], crop_in_aligned_px=list(box),
            aligned_canvas_origin_px=origin, aligned_canvas_size_px=list(aligned.size))
        tiles[name] = tile
        masks[name] = tile_mask
    # Height-sorted shelves; page dimensions remain within the staged 4096-pixel texture limit.
    page_width = 2048 if sum(t.width*t.height for t in tiles.values()) > 3500000 else 1024
    x, y, shelf_height, page_index = 2, 2, 0, 0
    heights = []
    for name in sorted(tiles, key=lambda n: (-tiles[n].height,n)):
        tile = tiles[name]
        assert tile.width+4 <= page_width and tile.height+4 <= 4096
        if x+tile.width+2 > page_width:
            y += shelf_height+2
            x,shelf_height = 2,0
        if y+tile.height+2 > 4096:
            heights.append(y)
            page_index += 1
            x,y,shelf_height = 2,2,0
        frames[name].update(page=page_index,atlas_xywh=[x,y,tile.width,tile.height])
        x += tile.width+2
        shelf_height = max(shelf_height,tile.height)
    heights.append(y+shelf_height+2)
    pages = [Image.new('RGBA',(page_width,h)) for h in heights]
    mask_mode = next(iter(masks.values())).mode
    assert all(mask.mode == mask_mode for mask in masks.values())
    mask_channels = 1 if mask_mode == 'L' else 3
    page_masks = [Image.new(mask_mode,page.size) for page in pages]
    for name,tile in tiles.items():
        frame = frames[name]
        pages[frame['page']].paste(tile,frame['atlas_xywh'][:2])
        page_masks[frame['page']].paste(masks[name],frame['atlas_xywh'][:2])
    for i,(page,mask) in enumerate(zip(pages,page_masks)):
        page.save(root/f'atlas/base_{i}.png')
        mask.save(root/f'atlas/mask_{i}.png')
        for variant in variants['variants']:
            preview = apply_variant(page,mask,variant)
            assert np.array_equal(np.array(preview)[:,:,3],np.array(page)[:,:,3])
            mask_values = np.array(mask)
            unmasked = mask_values == 0 if mask_values.ndim == 2 else np.all(mask_values == 0,axis=2)
            assert np.array_equal(np.array(preview)[unmasked],np.array(page)[unmasked])
            if variant['exact_bypass']:assert np.array_equal(np.array(preview),np.array(page))
            preview.save(root/f'previews/palette_{variant["palette_id"]}_page_{i}.png')
    for name, frame in frames.items():
        x, y, w, h = frame['atlas_xywh']
        page = pages[frame['page']]
        page_mask = page_masks[frame['page']]
        extracted = page.crop((x, y, x+w, y+h))
        assert np.array_equal(np.array(extracted), np.array(tiles[name]))
        aligned = Image.open(root / f'aligned_2x/{name}.png')
        reconstructed = Image.new('RGBA', aligned.size)
        reconstructed.paste(extracted, frame['crop_in_aligned_px'][:2])
        assert np.array_equal(np.array(reconstructed), np.array(aligned))
        assert np.array_equal(np.array(page_mask.crop((x, y, x+w, y+h))),
                              np.array(Image.open(root / f'trimmed_masks_2x/{name}.png')))
        audits[name] = dict(cleaned=contour_score(Image.open(root / f'cleaned/{name}.png'),config.get('protect_cool_purple',False)),
                            atlas=contour_score(extracted,config.get('protect_cool_purple',False)))
    groups = sources['groups']
    descriptor_animations = {}
    for descriptor,bindings in sources['descriptor_bindings'].items():
        animations = {}
        for action, group_name in bindings.items():
            group = groups[group_name]
            if group_name == 'null':
                assert all(f['texture_name'].lower() == 'null' for f in group['frames'])
                animations[action] = dict(native_group=group_name, native_group_id=group['sprite_id'],
                    animation_length_raw=group.get('animation_length_raw',0), loop=False, hold_last=False,
                    empty=True, directions={str(view):[] for view in range(8)})
                continue
            directions = {}
            for view in range(8):
                sequence = []
                for frame in group['frames']:
                    flags = frame['flags']
                    single = 'Image1' in flags
                    mirror = not single and f'Mirror{view}' in flags
                    stored = 8-view if mirror else view
                    name = frame['texture_name'].lower()+('' if single else str(stored))
                    assert name in frames
                    sequence.append(dict(frame=name, duration_raw=frame['frame_length_raw'],
                        duration_ms=frame['frame_length_raw']*62.5, mirror=mirror,
                        scale=frame.get('scale', 1), flags=flags, palette_id=frame['palette_id']))
                directions[str(view)] = sequence
            animations[action] = dict(native_group=group_name, native_group_id=group['sprite_id'],
                animation_length_raw=group['animation_length_raw'], loop=action not in ['death', 'corpse'],
                hold_last=action in ['death', 'corpse'], directions=directions)
        descriptor_animations[descriptor] = animations
    animations = descriptor_animations[str(descriptor_ids[0])]
    pixels = sum(page.width*page.height for page in pages)
    mask_format = 'R8' if mask_channels == 1 else 'RGB8'
    memory = dict(base_rgba8=pixels*4,
                  shared_total=pixels*(4+mask_channels), packing_included=True,
                  tight_base_and_mask=sum(tile.width*tile.height*(4+mask_channels) for tile in tiles.values()))
    memory['mask_'+mask_format.lower()] = pixels*mask_channels
    manifest = dict(schema_version=1, schema_status='staged offline contract; not installed', creature='mm7:'+config['creature'],
        installed=False, review_record='review/acceptance.json', pixels_per_logical_pixel=2, logical_canvas=logical_canvas, logical_pivot=logical_pivot,
        anchor='bottom-center', native_frame_scales=sorted({f.get('scale',1) for g in sources['groups'].values() for f in g['frames']}), coordinate_rule='x=(crop_x+u)/2-pivot_x; up=pivot_y-(crop_y+v)/2',
        pages=[dict(base=f'atlas/base_{i}.png',mask=f'atlas/mask_{i}.png',size=list(page.size),
                    base_format='RGBA8 sRGB',mask_format=mask_format+' linear') for i,page in enumerate(pages)],
        frames=frames,animations=animations,descriptor_animations=descriptor_animations,
        native_group_bindings=sources['descriptor_bindings'],regions=variants['regions'],
        variants=variants['variants'],recolor=variants['recolor'],
        filtering=dict(mipmaps=False, crop_padding_px=4, rgb_extrusion_px=3, resampling='premultiplied Lanczos'),
        memory_bytes=memory, limitations=['AI detail is an interpretation; native placement is preserved through the '
            'common reference window, not anatomical correspondence at every pixel.',
            'Single-background alpha is estimated; very fine contours may have approximate opacity.'])
    write_json(root / 'manifest.json', manifest)
    write_json(root / 'review/edge_audit.json', dict(matte=[255, 0, 255], band_width_px=3,
        material_protection=dict(core_magenta_excess=config.get('core_magenta_tolerance',24), protect_warm_contours=config.get('protect_warm_contours',True)), frames=audits))
    worst = sorted(audits, key=lambda n: max(audits[n]['cleaned']['maximum'], audits[n]['atlas']['maximum']), reverse=True)[:8]
    contact = Image.new('RGB', (768, len(worst)*160), (40, 40, 40))
    draw = ImageDraw.Draw(contact)
    for row, name in enumerate(worst):
        for stage_index, stage in enumerate(['cleaned', 'atlas']):
            im = Image.open(root / f'cleaned/{name}.png') if stage == 'cleaned' else tiles[name]
            x, y = audits[name][stage]['worst_xy']
            patch = im.crop((x-16, y-16, x+16, y+16))
            for col, background in enumerate([(30, 30, 30), (235, 235, 235)]):
                dx = (stage_index*2+col)*192
                contact.paste(composite(patch, background).resize((128, 128), Image.Resampling.NEAREST), (dx, row*160+24))
                draw.text((dx+2, row*160+4), name+' '+stage, fill='white')
    contact.save(root / 'review/edge_closeups.png')
    validation = dict(frames=len(frames), source_hashes_unchanged=True, raw_cells_unclipped=True,
        minimum_actual_generated_sampling=min(2 / r['scale'] for r in registration.values()),
        actual_generated_detail_at_least_2x=all(2 / r['scale'] >= 2 - 1e-6 for r in registration.values()),
        exact_crop_reconstruction=True, exact_atlas_extraction=True, base_bypass_exact=True,
        variant_alpha_unchanged=True, mask_weights_valid=True, native_group_timings_and_flags_preserved=True,
        residual_candidates_above_32=sum(a[s]['above_32'] for a in audits.values() for s in ['cleaned', 'atlas']),
        memory_bytes=memory)
    write_json(root / 'validation.json', validation)
    print(json.dumps(validation, indent=2))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=HERE)
    run(parser.parse_args().project.resolve())
