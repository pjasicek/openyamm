"""Offline packing and evidence for the configured families in this restoration goal."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from prepare_family import load, native, REPO
from process_family import recolor

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exact_placement import export_placement


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def frame_recolor_vectors(root, names, vectors):
    """Resolve explicit native material fits for frames with different palette ramps."""
    path = root / 'recolor_presets.json'
    if not path.exists():
        return {}, {}
    data = json.loads(path.read_text())
    assert data['reason'] and set(data['frames']) <= set(names)
    resolved = {}
    for name, preset in data['frames'].items():
        entry = data['presets'][preset]
        assert entry['source_frames'] and set(entry['source_frames']) <= set(names)
        fitted = {int(p): v for p, v in entry['vectors'].items()}
        assert set(fitted) == set(vectors)
        for palette in vectors:
            assert np.shape(fitted[palette]) == np.shape(vectors[palette])
            assert np.isfinite(fitted[palette]).all()
        resolved[name] = fitted
    return data, resolved


def edge_stats(im, matte):
    a = np.array(im.convert('RGBA'))
    c = a[:, :, :3].astype(float)
    if matte == 'cyan':
        c = c[:, :, [1, 0, 2]]
    alpha = a[:, :, 3]
    # Supplied PNGs can use alpha 253 across the entire opaque-looking body.
    # That is not a contour: avoid treating every interior jewel or leather pixel
    # as matte spill while retaining the actual contour and translucent exterior.
    band = (alpha > 0) & ((ndimage.distance_transform_edt(alpha >= 128) <= 4) | (alpha < 128))
    score = np.maximum(0, np.minimum(c[:, :, 0], c[:, :, 2]) - c[:, :, 1]) * alpha / 255 * band
    y, x = np.unravel_index(np.argmax(score), score.shape)
    return dict(max_score=float(score.max()), candidates_above_16=int((score > 16).sum()), position=[int(x), int(y)])


def overlay(im, mask):
    a = np.array(im)
    weight = np.array(mask).astype(float) / 255 * .7
    if weight.ndim == 3:
        colors = np.array([[255,80,0], [0,160,255], [220,0,255], [0,230,100]])
        a[:, :, :3] = np.round(a[:, :, :3] * (1-weight.sum(axis=2,keepdims=True)) +
                              np.einsum('hwk,kc->hwc',weight,colors)).astype(np.uint8)
    else:
        a[:, :, :3] = np.round(a[:, :, :3] * (1 - weight[:, :, None]) +
                               np.array([255, 110, 0]) * weight[:, :, None]).astype(np.uint8)
    return Image.fromarray(a)


def animation(group, action, frames):
    if group['sprite_name'].lower() == 'null':
        # Explicit native no-image sentinel, e.g. an elemental leaves no corpse.
        return dict(views={str(v): [] for v in range(8)}, single_view=True,
                    native_group=group['sprite_name'], native_length_raw=0, sequence_ms=0,
                    playback='hold', next_action=None, no_image=True)
    views = {}
    for view in range(8):
        steps = []
        for source in group['frames']:
            flags = source['flags']
            mirrored = f'Mirror{view}' in flags
            stored = 8 - view if mirrored else view
            name = source['texture_name'].lower() + ('' if 'Image1' in flags else str(stored))
            assert name in frames, name
            steps.append(dict(frame=name, duration_ms=source['frame_length_raw'] * 62.5,
                              # Native YAML omits unit scale; SpriteTables.cpp uses 1.0.
                              mirrored=mirrored, native_scale=source.get('scale', 1.0), native_flags=flags))
        views[str(view)] = steps
    return dict(views=views, single_view='Image1' in group['frames'][0]['flags'],
                # SpriteTables.cpp defaults omitted native animation lengths to zero (static corpse groups).
                native_group=group['sprite_name'], native_length_raw=group.get('animation_length_raw', 0),
                sequence_ms=sum(s['duration_ms'] for s in views['0']),
                playback='loop' if action in ['standing', 'walk'] else 'hold' if action == 'corpse' else 'once',
                next_action='corpse' if action == 'death' else
                'standing' if action in ['attack', 'attack2', 'hit', 'fidget'] else None)


def export(family, output_root=None, source_root=None):
    root, config, inv = load(family, source_root)
    if output_root is not None:
        root = Path(output_root).resolve()
    multi = config['mask_kind'] in ('mep_regions', 'gua_regions') or (bool(config.get('material_module')) and config.get('material_mask_channels', 4) == 4)
    mask_mode, mask_format, mask_bytes = ('RGBA','RGBA8',4) if multi else ('L','R8',1)
    source = json.loads((root / 'sources.json').read_text())
    reg = json.loads((root / 'registration.json').read_text())
    vectors = {int(p): v for p, v in json.loads((root / 'recolor_vectors.json').read_text()).items()}
    recolor_presets, frame_vectors = frame_recolor_vectors(root, reg, vectors)
    palettes = [int(p) for p in inv['variants']]
    base_palette = config['base_palette']
    canvas = inv['logical_canvas']
    anchor = source.get('anchor', 'bottom-center').split(';')[0]
    aliases = inv['pixel_aliases']
    assert set(source['sources']) == set(reg), 'Missing restored source files'
    assert not any(r['raw_clip'] for r in reg.values()), 'Clipped extraction boundaries'
    for d in ['atlas', 'trimmed_2x', 'trimmed_masks_2x', 'previews', 'native_variants', 'sheets', 'review']:
        (root / d).mkdir(exist_ok=True)
    generation = json.loads((root / 'generation.json').read_text())
    assert set(generation['batches']) == {r['batch'] for r in reg.values()}
    for batch in generation['batches'].values():
        for asset in [batch['raw'], batch['prompt'], *batch['references']]:
            assert hashlib.sha256((root / asset['path']).read_bytes()).hexdigest() == asset['sha256']
    for p in source['palette_sources'].values():
        assert hashlib.sha256((REPO / p['path']).read_bytes()).hexdigest() == p['sha256']
    frames, tiles, masks, aligned, audit = {}, {}, {}, {}, {}
    for name, r in reg.items():
        src = source['sources'][name]
        assert hashlib.sha256((REPO / src['path']).read_bytes()).hexdigest() == src['sha256']
        im = Image.open(root / f'aligned_2x/{name}.png').convert('RGBA')
        mask = Image.open(root / f'masks_2x/{name}.png').convert(mask_mode)
        assert im.size == mask.size
        a, w = np.array(im), np.array(mask)
        if multi:
            assert np.all(w.astype(int).sum(axis=2) <= 255), name
        solid = a[:, :, 3] > 0
        distance, nearest = ndimage.distance_transform_edt(~solid, return_indices=True)
        ring = (distance <= 3) & ~solid
        a[:, :, :3][~solid] = 0
        w[~solid] = 0
        a[:, :, :3][ring] = a[nearest[0], nearest[1], :3][ring]
        w[ring] = w[nearest[0], nearest[1]][ring]
        im, mask = Image.fromarray(a), Image.fromarray(w)
        im.save(root / f'aligned_2x/{name}.png')
        mask.save(root / f'masks_2x/{name}.png')
        aligned[name] = im
        b = im.getchannel('A').getbbox()
        if b is None:
            assert not np.array(Image.open(REPO/src['path'])).any(), 'Missing nonempty native artwork'
            b = [0, 0, 1, 1]
        else:
            b = [max(0, b[0]-4), max(0, b[1]-4), min(im.width, b[2]+4), min(im.height, b[3]+4)]
        tile, mt = im.crop(b), mask.crop(b)
        tiles[name], masks[name] = tile, mt
        tile.save(root / f'trimmed_2x/{name}.png')
        mt.save(root / f'trimmed_masks_2x/{name}.png')
        reconstructed = Image.new('RGBA', im.size)
        reconstructed.paste(tile, b[:2])
        assert np.array_equal(reconstructed, im), name
        exact_offset, origin, correction = export_placement(
            canvas, src['size'], src['native_offset'], r['canvas_origin_px'],
            anchor=anchor)
        frames[name] = dict(crop_origin_px=[b[0]+origin[0], b[1]+origin[1]], crop_in_aligned_px=b,
                            aligned_canvas_origin_px=origin, aligned_canvas_size_px=im.size,
                            source=name+'.bmp', source_palette=src.get('fixed_palette', base_palette), source_canvas=src['size'],
                            native_offset=exact_offset, registration_native_offset=src['native_offset'][:2],
                            anchor_correction_px=correction, referenced=src['referenced'])
        if name in aliases:
            frames[name]['pixel_alias'] = aliases[name]
        for pal in palettes:
            native(name, pal, canvas, inv).save(root / f'native_variants/{name}_{pal}.png')
            variant = recolor(tile, mt, pal, config, frame_vectors.get(name, vectors))
            assert np.array_equal(np.array(variant)[:, :, 3], np.array(tile)[:, :, 3])
            zero = np.array(mt).sum(axis=2) == 0 if multi else np.array(mt) == 0
            assert np.array_equal(np.array(variant)[zero], np.array(tile)[zero])
            if pal == base_palette:
                assert np.array_equal(variant, tile)
        audit[name] = dict(cleaned=edge_stats(Image.open(root / f'cleaned/{name}.png'), config['matte']),
                           exported=edge_stats(tile, config['matte']))

    layouts, current = [], []
    x = y = 2
    row_height = used_width = 0
    for name in sorted((n for n in tiles if n not in aliases), key=lambda n: (-tiles[n].height, -tiles[n].width, n)):
        w, h = tiles[name].size
        assert max(w, h)+4 <= 2048
        if x+w+2 > 2048:
            x = 2
            y += row_height+4
            row_height = 0
        if y+h+2 > 2048:
            layouts.append((current, used_width, max(py+tiles[n].height+2 for n, px, py in current)))
            current = []
            x = y = 2
            row_height = used_width = 0
        current.append((name, x, y))
        x += w+4
        row_height = max(row_height, h)
        used_width = max(used_width, x-2)
    if current:
        layouts.append((current, used_width, y+row_height+2))
    pages, pixel_count = [], 0
    for page, (layout, width, height) in enumerate(layouts):
        assert width <= 2048 and height <= 2048
        base = Image.new('RGBA', (width, height))
        mask = Image.new(mask_mode, (width, height))
        pixel_count += width*height
        for name, x, y in layout:
            tile = tiles[name]
            base.paste(tile, (x, y))
            mask.paste(masks[name], (x, y))
            frames[name].update(page=page, atlas_xywh=[x, y, tile.width, tile.height])
        base_path, mask_path = f'atlas/base_{page}.png', f'atlas/mask_{page}.png'
        base.save(root / base_path)
        mask.save(root / mask_path)
        previews = {}
        for pal in palettes:
            target = base_path if pal == base_palette else f'previews/palette_{pal}_page_{page}.png'
            if pal != base_palette:
                preview = recolor(base, mask, pal, config, vectors)
                for name, x, y in layout:
                    if name in frame_vectors:
                        preview.paste(recolor(tiles[name], masks[name], pal, config, frame_vectors[name]), (x, y))
                preview.save(root / target)
            previews[str(pal)] = target
        overlay_path = f'previews/mask_overlay_{page}.png'
        overlay(base, mask).save(root / overlay_path)
        pages.append(dict(base=base_path, mask=mask_path, size=[width, height], base_format='RGBA8',
                          mask_format=mask_format, variant_previews=previews, mask_overlay=overlay_path))
    for name, canonical in aliases.items():
        for k in ['page', 'atlas_xywh']:
            frames[name][k] = frames[canonical][k]
        assert np.array_equal(tiles[name], tiles[canonical]) and np.array_equal(masks[name], masks[canonical])
        assert frame_vectors.get(name, vectors) == frame_vectors.get(canonical, vectors)
    for name, f in frames.items():
        x, y, w, h = f['atlas_xywh']
        for key, expected in [('base', tiles[name]), ('mask', masks[name])]:
            extracted = Image.open(root / pages[f['page']][key]).crop((x, y, x+w, y+h))
            assert np.array_equal(extracted, expected)
            if key == 'base':
                audit[name]['atlas_extracted'] = edge_stats(extracted, config['matte'])
        if name in frame_vectors:
            for pal in palettes:
                path = pages[f['page']]['variant_previews'][str(pal)]
                extracted = Image.open(root / path).crop((x, y, x+w, y+h))
                expected = recolor(tiles[name], masks[name], pal, config, frame_vectors[name])
                assert np.array_equal(extracted, expected), (name, pal, 'recolor preset atlas mismatch')
    per_palette = {p: {a: animation(g, a, frames) for a, g in v['actions'].items()}
                   for p, v in inv['variants'].items()}
    animations = per_palette[str(base_palette)]
    memory = dict(original_indexed_bmp_disk=sum((REPO/s['path']).stat().st_size for s in source['sources'].values()),
                  original_all_files_rgba_one_palette=sum(s['size'][0]*s['size'][1]*4 for s in source['sources'].values()),
                  enhanced_atlas_base=pixel_count*4, enhanced_atlas_mask_r8=pixel_count,
                  enhanced_shared_base_and_mask=pixel_count*(4+mask_bytes),
                  enhanced_tight_base_unique=sum(t.width*t.height*4 for n, t in tiles.items() if n not in aliases),
                  variant_previews_excluded=True)
    if multi:
        del memory['enhanced_atlas_mask_r8']
        memory['enhanced_atlas_mask_rgba8'] = pixel_count*4
    manifest = dict(schema_version=1, creature='mm6:'+family, installed=False,
                    recolor_model='masked_luminance_rgb_v1',
                    schema_status='staged asset contract; validate loader before any future installation',
                    pixels_per_logical_pixel=2, logical_canvas=canvas,
                    logical_pivot=[canvas[0]/2, canvas[1]/(2 if anchor == 'center' else 1)],
                    anchor=anchor, native_frame_scale=animations['standing']['views']['0'][0]['native_scale'],
                    coordinate_rule='local=(crop_origin+texel)/2; x-=logical_pivot.x; up=logical_pivot.y-local.y; mirror local x and UV together',
                    pages=pages, frames=frames, animations=animations, animations_by_palette=per_palette,
                    native_group_bindings=inv['variants'],
                    variants={str(p): dict(name=config['variant_names'][str(p)],
                        **({'exact_base_bypass': True} if p == base_palette else {'luminance_vector': vectors[p]})) for p in palettes},
                    regions={'mask_r': config['regions']},
                    recolor=dict(model='masked_luminance_rgb_v1', space='sRGB encoded RGB; linear coverage mask',
                        operation='Y=dot(base.rgb,[0.2126,0.7152,0.0722]); target=Y*luminance_vector; out=lerp(base,target,mask); preserve alpha; base bypass',
                        fitting='Fixed least-squares RGB slopes over used native base-color indices; see process_family.py'),
                    filtering=dict(alpha='straight RGBA; premultiplied Lanczos resampling', crop_padding_px=4,
                                   transparent_extrusion_px=3, mipmaps=False), memory_bytes=memory,
                    limitations=['AI-reconstructed faces and fabric microdetails can vary slightly between poses.',
                                 'Native-only stored views; single-view actions and mirrored views retained.',
                                 '2x export tier does not imply 2x newly generated detail in each batch.',
                                 'Matte-derived alpha is an estimate, not recovered ground-truth transparency.'])
    if multi:
        if config.get('material_module'):
            from process_family import module
            REGIONS = module('family_materials', root/config['material_module']).REGIONS
        elif config['mask_kind'] == 'gua_regions':
            from process_family import module, HERE
            REGIONS = module('guard_materials', HERE.parent/'mm6_gua/materials.py').REGIONS
        else:
            from mep_materials import REGIONS
        manifest['recolor_model'] = 'multi_mask_luminance_rgb_v1'
        manifest['regions'] = REGIONS
        manifest['recolor'] = dict(model='multi_mask_luminance_rgb_v1',
            space='sRGB encoded RGB; four linear coverage channels, including mask alpha',
            operation='Y=dot(base.rgb,[0.2126,0.7152,0.0722]); out=base.rgb*(1-sum(mask))+Y*sum(mask[k]*vector[k]); preserve base alpha; exact base bypass',
            fitting='Fixed four-region native-index fits; see family material module',
            runtime='Requires four-channel coverage and four-vector shader/loader extension; staged only')
        for p in palettes:
            if p != base_palette:
                manifest['variants'][str(p)]['region_luminance_vectors'] = manifest['variants'][str(p)].pop('luminance_vector')
    if recolor_presets:
        manifest['recolor_presets'] = recolor_presets
        manifest['recolor']['preset_selection'] = 'Use frames[frame].recolor_preset when present; otherwise use family vectors.'
        manifest['recolor']['runtime'] = 'Palette atlases are baked with these presets. Dynamic recoloring requires per-frame preset support; staged only.'
        for name, preset in recolor_presets['frames'].items():
            frames[name]['recolor_preset'] = preset
    save_json(root / 'manifest.json', manifest)
    make_contacts(root, config, inv, reg, aligned, tiles, masks, audit, animations, vectors)
    save_json(root / 'review/edge_current.json', dict(matte=config['matte'], band_physical_px=4,
              score='alpha-weighted matte-channel excess over complementary channel', frames=audit))
    validation = dict(source_files=len(frames), referenced_files=sum(s['referenced'] for s in source['sources'].values()),
                      unique_enhanced_tiles=len(frames)-len(aliases), actions=list(animations), palettes=palettes,
                      source_hashes_unchanged=True, palette_hashes_unchanged=True, raw_cells_unclipped=True,
                      generation_provenance_hashes_verified=True,
                      exact_crop_reconstruction=True, exact_atlas_extraction=True, variant_alpha_unchanged=True,
                      zero_mask_unchanged=True, base_bypass_exact=True, per_palette_native_sequences_preserved=True,
                      residual_candidates_above_16={stage: sum(a[stage]['candidates_above_16'] for a in audit.values())
                                                    for stage in ['cleaned', 'exported', 'atlas_extracted']},
                      visual_review='See review_notes.md; automated checks alone are not visual acceptance.',
                      visual_review_complete=False,
                      memory_bytes=memory)
    if multi:
        validation['four_channel_weight_sum_valid'] = True
    validation['shipping_bytes'] = (root/'manifest.json').stat().st_size + sum(
        (root/p[k]).stat().st_size for p in pages for k in ['base', 'mask'])
    save_json(root/'validation.json', validation)
    print(json.dumps(validation))


def make_contacts(root, config, inv, reg, aligned, tiles, masks, audit, animations, vectors):
    _, frame_vectors = frame_recolor_vectors(root, reg, vectors)
    canvas = inv['logical_canvas']
    names = list(aligned)
    cell_w, cell_h = max(180, math.ceil(canvas[0]/2)+24), math.ceil(canvas[1]/2)+34
    for kind, bg in [('all_base_dark', (40,43,42)), ('all_masks_light', (230,230,227))]:
        contact = Image.new('RGB', (8*cell_w, math.ceil(len(names)/8)*cell_h), bg)
        d = ImageDraw.Draw(contact)
        for i, name in enumerate(names):
            im = aligned[name]
            if kind == 'all_masks_light':
                im = overlay(im, Image.open(root/f'masks_2x/{name}.png'))
            im = im.convert('RGBa').resize((round(im.width/4), round(im.height/4)), Image.Resampling.LANCZOS).convert('RGBA')
            origin = reg[name]['canvas_origin_px']
            x, y = i%8*cell_w, i//8*cell_h
            contact.paste(im, (x+12+round(origin[0]/4), y+26+round(origin[1]/4)), im)
            d.text((x+4,y+5), name, fill='black' if kind=='all_masks_light' else 'white')
        contact.save(root/f'review/{kind}.png')
    ranked = sorted(audit, key=lambda n: audit[n]['atlas_extracted']['max_score'], reverse=True)[:12]
    contact = Image.new('RGB', (6*280, 2*190), (55,55,55))
    d = ImageDraw.Draw(contact)
    for i, name in enumerate(ranked):
        x, y = audit[name]['atlas_extracted']['position']
        crop = tiles[name].crop((x-16,y-16,x+16,y+16)).resize((128,128),Image.Resampling.NEAREST)
        for j, bg in enumerate([(35,35,35),(240,240,240)]):
            patch = Image.new('RGBA', crop.size, (*bg,255))
            patch.alpha_composite(crop)
            contact.paste(patch.convert('RGB'), (i%6*280+j*132, i//6*190+30))
        d.text((i%6*280+2,i//6*190+8), name, fill='white')
    contact.save(root/'review/edge_current.png')
    order = ['attack', 'death', 'walk', 'hit', 'fidget', 'standing', 'corpse']
    cw, ch = canvas[0]*2+48, canvas[1]*2+48
    for view in range(5):
        columns = max(len(animations[action]['views'][str(view)]) for action in order)
        sheet = Image.new('RGBA', (columns*cw, len(order)*ch))
        for row, action in enumerate(order):
            anim = animations[action]
            if view and anim['single_view']:
                continue
            for col, step in enumerate(anim['views'][str(view)]):
                name = step['frame']
                ox, oy = reg[name]['canvas_origin_px']
                sheet.paste(aligned[name], (col*cw+24+ox, row*ch+24+oy))
        sheet.save(root/f'sheets/view_{view}_all_actions_2x.png')
    cw, ch = canvas[0]+12, canvas[1]+30
    contact = Image.new('RGB',(5*cw,3*ch),(43,45,43))
    d = ImageDraw.Draw(contact)
    for row, p in enumerate(inv['variants']):
        for view in range(5):
            name = animations['standing']['views'][str(view)][0]['frame']
            im = recolor(aligned[name], Image.open(root/f'masks_2x/{name}.png'), int(p), config,
                         frame_vectors.get(name, vectors))
            im = im.convert('RGBa').resize((round(im.width/2),round(im.height/2)),Image.Resampling.LANCZOS).convert('RGBA')
            ox, oy = reg[name]['canvas_origin_px']
            contact.paste(im,(view*cw+6+round(ox/2),row*ch+26+round(oy/2)),im)
            d.text((view*cw+4,row*ch+5),f'{p}: {name}',fill='white')
    contact.save(root/'review/standing_variants.png')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('family')
    export(parser.parse_args().family)
