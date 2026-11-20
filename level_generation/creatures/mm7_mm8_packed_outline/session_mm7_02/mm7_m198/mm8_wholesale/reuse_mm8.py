"""User-authorized MM8 artwork reuse with unchanged MM7 native playback bindings.

This session-local bridge copies accepted exports, rather than regenerating or
reregistering poses. Shared material, placement, edge and viewer tools stay unchanged.
"""
import copy
import datetime
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[6]
CREATURES = REPO / 'level_generation/creatures'
SESSION = CREATURES / 'mm7_mm8_packed_outline/session_mm7_02'
DONORS = CREATURES / 'mm7_mm8_packed_outline/session_mm8_04'
sys.path.insert(0, str(CREATURES))
sys.path.insert(0, str(CREATURES / 'mm7_m514'))
sys.path.insert(0, str(CREATURES / 'mm8_remaining'))
import exact_placement
import build_viewer
import native_materials
from process import contour_score

FAMILIES = [('mm7_m198', 'mm8_m504', 'm198', 'm504'),
            ('mm7_m210', 'mm8_m500', 'm210', 'm500')]
AUTHORIZATION = '2026-10-02: then lets use MM8 water/earth elementals wholesale here I guess, would that work?'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return str(path.relative_to(REPO))


def verify_acceptance(path, base):
    record = read(path)
    count = 0
    for key in ['artifact_hashes', 'artifact_sha256', 'inherited_artifact_sha256']:
        for name, digest in record.get(key, {}).items():
            asset = REPO / name if name.startswith('level_generation/') else base / name
            assert sha(asset) == digest, str(asset)
            count += 1
    return dict(path=relative(path), sha256=sha(path), artifacts_verified=count)


def composite(image, background='#292d2b'):
    result = Image.new('RGBA', image.size, background)
    result.alpha_composite(image.convert('RGBA'))
    return result.convert('RGB')


def native(sources, name, palette):
    indices = np.asarray(Image.open(REPO / sources['sources'][name]['path']))
    colours = np.frombuffer((REPO / sources['palette_sources'][str(palette)]['path']).read_bytes()[:768],
                           np.uint8).reshape(256, 3)
    return Image.fromarray(np.dstack((colours[indices], (indices != 0) * 255)).astype(np.uint8))


def export():
    for family, donor_family, target_stem, donor_stem in FAMILIES:
        if len(sys.argv) > 2 and family not in sys.argv[2:]:
            continue
        parent, donor = SESSION / family, DONORS / donor_family
        out = parent / 'mm8_wholesale'
        for folder in ['aligned_2x', 'masks_2x', 'trimmed_2x', 'trimmed_masks_2x',
                       'atlas', 'previews', 'native_palettes', 'review']:
            (out / folder).mkdir(parents=True, exist_ok=True)
        sources = read(parent / 'sources.json')
        donor_sources = read(donor / 'sources.json')
        prior_manifest = read(parent / 'redo_2x/manifest.json')
        prior_acceptance = verify_acceptance(parent / 'redo_2x/review/acceptance.json', parent)
        earth = family == 'mm7_m198'
        donor_export = donor / 'walk0_video_x3_completion' if earth else donor
        donor_manifest = read(donor_export / ('manifest.json' if earth else 'draft_manifest.json'))
        donor_acceptance = verify_acceptance(donor_export / 'review/acceptance.json', donor_export)
        donor_records = read(donor_export / 'registration.json')
        donor_run = read(donor / 'run.json')
        names = sorted(sources['sources'])
        mapping = {n: n.replace(target_stem, donor_stem, 1) for n in names}
        compatibility = {}
        for name, source_name in mapping.items():
            s, d = sources['sources'][name], donor_sources['sources'][source_name]
            assert sha(REPO / s['path']) == s['sha256']
            assert sha(REPO / d['path']) == d['sha256']
            p, q = np.asarray(Image.open(REPO / s['path'])), np.asarray(Image.open(REPO / d['path']))
            assert p.shape == q.shape and list(p.shape[::-1]) == s['size'] == d['size']
            assert not np.any((p != q) & (p != 0)), name
            ys, xs = np.where(p != q)
            for y in np.unique(ys):
                changed = xs[ys == y]
                assert len(changed) == 1 and changed[0] == np.where(q[y] != 0)[0][-1], name
            compatibility[name] = dict(donor_frame=source_name, common_visible_indices_exact=True,
                                       mm7_missing_rightmost_row_pixels=len(xs), same_native_canvas=True)
        assert len(names) == 120
        cfg = read(donor / 'material_settings.json')
        extra_cfg = None
        if not earth:
            extra_cfg = copy.deepcopy(cfg)
            base = np.asarray(cfg['base_samples'])
            colours = np.frombuffer((REPO / sources['palette_sources']['503']['path']).read_bytes()[:768],
                                   np.uint8).reshape(256, 3)[1:].astype(float)
            delta = colours - base
            extra_cfg['palette_deltas'] = {'501': [[0, 0, 0]] * 255, '503': delta.tolist()}
            extra_cfg['changed_samples'] = (np.max(abs(delta), axis=1) >= 10).astype(int).tolist()
            extra_cfg['regions'] = ['MM7 ACT503-varying scale, fin and ventral colours on unchanged enhanced RGB']
        pages, bases, masks, appearances = [], {}, {}, {}
        for i, page in enumerate(donor_manifest['pages']):
            source_base = (donor_export / page['base']).resolve()
            target_base = out / f'atlas/base_{i}.png'
            shutil.copy2(source_base, target_base)
            assert sha(source_base) == sha(target_base)
            base = Image.open(target_base).convert('RGBA')
            bases[i] = base
            old_mask = np.array(Image.open(donor_export / page['mask']).convert('L'))
            old_mask[np.asarray(base)[:, :, 3] == 0] = 0
            masks[i] = Image.new('L', base.size) if earth else Image.fromarray(
                np.stack((old_mask, np.zeros_like(old_mask), np.zeros_like(old_mask)), axis=2))
            for palette in sources['palettes']:
                appearances[palette, i] = base.copy()
            pages.append(dict(base=f'atlas/base_{i}.png', mask=f'atlas/mask_{i}.png', size=list(base.size),
                              base_format='RGBA8 sRGB', mask_format=('R8' if earth else 'RGB8') + ' linear',
                              gutter_px=page.get('gutter_px', 16), mipmaps=False))
        frames, registration, frame_hashes, edges = {}, {}, {}, {}
        generation_jobs = {}
        for name, source_name in mapping.items():
            donor_frame = copy.deepcopy(donor_manifest['frames'][source_name])
            supplemental = earth and donor_frame.get('restoration_method', '').startswith('user_authorized_native')
            master_root = donor_export if supplemental else donor
            original_master = master_root / f'runtime_aligned_2x/{source_name}.png'
            shutil.copy2(original_master, out / f'aligned_2x/{name}.png')
            master = Image.open(out / f'aligned_2x/{name}.png').convert('RGBA')
            original_mask = Image.open(master_root / f'runtime_masks_2x/{source_name}.png').convert('L')
            channel_r = np.array(original_mask)
            channel_r[np.asarray(master)[:, :, 3] == 0] = 0
            if earth:
                mask = Image.new('L', master.size)
            else:
                channel_g = native_materials.masks(master, extra_cfg)
                mask = Image.fromarray(np.stack((channel_r, channel_g, np.zeros_like(channel_r)), axis=2))
            mask.save(out / f'masks_2x/{name}.png')
            frame = donor_frame
            frame.update(source=name + '.bmp', source_palette=sources['base_palette'], referenced=True,
                         donor_frame=source_name, physical_master=f'aligned_2x/{name}.png',
                         native_offset=[0.0, 0.0], registration_native_offset=[0.0, 0.0])
            frame['crop_origin_px'] = [frame['aligned_canvas_origin_px'][i] + frame['crop_in_aligned_px'][i]
                                       for i in range(2)]
            for key in ['native_anchor_mapping', 'mirrored_anchor_mapping', 'logical_crop_origin', 'logical_size']:
                frame.pop(key, None)
            frame['restoration_method'] = ('user_authorized_native_realesr_animevideov3_x3' if supplemental
                                            else 'reused_mm8_packed_whole_animation_outline_imagegen')
            page_id, (x, y, w, h) = frame['page'], frame['atlas_xywh']
            box = frame['crop_in_aligned_px']
            tile = bases[page_id].crop((x, y, x + w, y + h))
            assert np.array_equal(tile, master.crop(box)), name
            rebuilt = Image.new('RGBA', master.size)
            rebuilt.paste(tile, box[:2])
            assert np.array_equal(rebuilt, master), name
            tile.save(out / f'trimmed_2x/{name}.png')
            mask.crop(box).save(out / f'trimmed_masks_2x/{name}.png')
            masks[page_id].paste(mask.crop(box), (x, y))
            for palette in sources['palettes']:
                if palette == sources['base_palette']:
                    preview = master.copy()
                elif palette == 502:
                    preview = Image.open(donor / f'previews/{source_name}_{palette}.png').convert('RGBA')
                else:
                    preview = native_materials.recolor(master, Image.fromarray(channel_g), palette, extra_cfg)
                assert np.array_equal(np.asarray(preview)[:, :, 3], np.asarray(master)[:, :, 3])
                preview.save(out / f'previews/{name}_{palette}.png')
                appearances[palette, page_id].paste(preview.crop(box), (x, y))
            record = copy.deepcopy(donor_records[source_name])
            record.update(donor_frame=source_name, donor_project=relative(donor),
                          logical_pivot=sources['logical_pivot'], registration_native_offset=[0.0, 0.0],
                          scale=record.get('scale_to_2x', record.get('scale')),
                          reused_art_user_authorization=AUTHORIZATION)
            record['clean_path'] = (record.get('clean_path') or relative(donor / f'cleaned/{source_name}.png'))
            if record.get('clean_sha256'):
                clean = Image.open(REPO / record['clean_path']).convert('RGBA')
                assert hashlib.sha256(clean.tobytes()).hexdigest() == record['clean_sha256']
            assert sha(REPO / record['raw_path']) == record['raw_sha256']
            registration[name] = record
            frames[name] = frame
            frame_hashes[name] = dict(native=sha(REPO / sources['sources'][name]['path']),
                                     donor_native=sha(REPO / donor_sources['sources'][source_name]['path']),
                                     donor_master_2x=sha(original_master), master_2x=sha(out / f'aligned_2x/{name}.png'),
                                     material_mask_2x=sha(out / f'masks_2x/{name}.png'),
                                     cleaned=sha(REPO / record['clean_path']))
            edges[name] = dict(cleaned=contour_score(Image.open(REPO / record['clean_path']).convert('RGBA'), not earth),
                               atlas=contour_score(tile, not earth))
            if not supplemental:
                job = next(j for j in donor_run['jobs'] if j['id'] == record['batch'])
                assert job['status'].startswith('accepted'), job['id']
                generation_jobs[record['batch']] = copy.deepcopy(job)
        for palette, source in sources['palette_sources'].items():
            assert sha(REPO / source['path']) == source['sha256']
            shutil.copy2(REPO / source['path'], out / f'native_palettes/{palette}.act')
        for i, page in enumerate(pages):
            masks[i].save(out / page['mask'])
            for palette in sources['palettes']:
                appearances[palette, i].save(out / f'previews/palette_{palette}_page_{i}.png')
        manifest = copy.deepcopy(prior_manifest)
        manifest.update(pages=pages, frames=frames, installed=False, review_record='review/acceptance.json',
                        schema_status='User-authorized whole-family MM8 artwork reuse; MM7 native bindings',
                        regions=[] if earth else [dict(id='mm8_palette502_materials', channel='R'),
                                                 dict(id='mm7_palette503_materials', channel='G')],
                        recolor=dict(operation='identity' if earth else 'per_palette_soft_native_delta_knn',
                                     material_settings='material_settings.json', base_exact_bypass=True,
                                     palette_mask_channel={'502': 'R', '503': 'G'} if not earth else {}))
        for variant in manifest['variants']:
            variant.pop('regions', None)
            variant['material_config'] = 'identity' if earth else str(variant['palette_id'])
        for actions in manifest['descriptor_animations'].values():
            for animation in actions.values():
                for steps in animation['directions'].values():
                    for step in steps:
                        step.pop('missing', None)
                        assert step['frame'] in frames
        manifest['animations'] = copy.deepcopy(manifest['descriptor_animations'][str(min(map(int, sources['descriptor_bindings'])))])
        assert not exact_placement.validate_manifest(manifest, registration)
        latest_count = sum(f['restoration_method'].startswith('reused_mm8_packed') for f in frames.values())
        sampling = min(min(registration[n]['effective_sampling_xy']) for n in names
                       if frames[n]['restoration_method'].startswith('reused_mm8_packed'))
        pixels = sum(page['size'][0] * page['size'][1] for page in pages)
        manifest['memory_bytes'] = dict(base_rgba8=pixels * 4, mask_rgb8=pixels * 3 if not earth else 0,
                                      mask_r8=pixels if earth else 0, shared_total=pixels * (5 if earth else 7),
                                      includes_unbound_mm8_atlas_art=True)
        manifest['coverage'] = dict(complete=True, native_images=120, restored_images=120, missing_images=[],
                                    reused_packed_outline_images=latest_count, native_video_x3_images=120-latest_count,
                                    full_latest_imagegen_method_coverage=latest_count == 120,
                                    native_unused_images=0, unused_art_added_to_playback=False)
        manifest['actual_generated_detail'] = dict(minimum_sampling=sampling, physical_export_scale=2,
            imagegen_images=latest_count, neural_upscale_images=120-latest_count,
            neural_scale_is_not_generated_imagegen_detail=True)
        manifest['limitations'] = ['MM8 accepted artwork is reused under explicit user scope; no new MM7 imagegen calls.',
            'Local MM7 originals omit the final opaque pixel of each occupied native row; other visible indices match MM8 exactly.',
            'Native MM7 descriptor scales, palette choices, flags, aliases, timing, mirrors and fractional placement remain authoritative.',
            'Valid artifact-bound MM8 pose, material, alpha and independent-placement reviews are inherited unchanged.',
            'Static review; timed playback was not watched.']
        if earth:
            manifest['limitations'].append('Eight front-walk poses use the accepted neural x3 native fallback, exported at physical 2x; full packed imagegen coverage remains incomplete.')
        source_receipt = dict(user_authorization=AUTHORIZATION, donor_project=relative(donor),
                              donor_manifest=dict(path=relative(donor_export / ('manifest.json' if earth else 'draft_manifest.json')),
                                                  sha256=sha(donor_export / ('manifest.json' if earth else 'draft_manifest.json'))),
                              donor_acceptance=donor_acceptance, prior_mm7_acceptance=prior_acceptance,
                              frame_mapping=mapping, native_compatibility=compatibility,
                              donor_extra_images_retained_in_original_package=40,
                              target_playback_unchanged=True, original_packages_unchanged=True)
        write(out / 'sources.json', sources)
        write(out / 'config.json', read(parent / 'config.json'))
        write(out / 'registration.json', registration)
        write(out / 'generation.json', dict(method='accepted_cross_world_art_reuse', new_imagegen_calls=0,
                                           inherited_original_jobs=generation_jobs, source_receipt=source_receipt))
        write(out / 'material_settings.json', dict(identity=earth, palette502=cfg if not earth else None,
                                                 palette503=extra_cfg, masks='R: original MM8 palette502; G: MM7 palette503; B: zero' if not earth else 'R8 zero; MM7 has only ACT504'))
        write(out / 'processing.json', dict(method='copy_accepted_mm8_export_pixels', receipt=source_receipt,
                                           reused_frame_sha256=frame_hashes,
                                           art_resampled=False, anatomical_transforms_changed=False,
                                           alpha_changed=False, mask_padding_zeroed=True))
        write(out / 'manifest.json', manifest)
        write(out / 'review/edge_audit.json', dict(frames=edges, source_alpha_and_visible_rgb_unchanged=True,
                                                 intentional_native_water_fin_colours_protected=not earth))
        make_contacts(out, sources, manifest, masks, bases)
        validate(out)
        print(json.dumps(dict(family=family, reused=len(frames), imagegen=latest_count,
                              neural=120-latest_count, sampling=sampling, donor_verified=donor_acceptance['artifacts_verified'])), flush=True)


def make_contacts(out, sources, manifest, masks, bases):
    names = sorted(manifest['frames'])
    min_x = min(0, *(f['aligned_canvas_origin_px'][0] for f in manifest['frames'].values()))
    min_y = min(0, *(f['aligned_canvas_origin_px'][1] for f in manifest['frames'].values()))
    max_x = max(512, *(f['aligned_canvas_origin_px'][0]+f['aligned_canvas_size_px'][0] for f in manifest['frames'].values()))
    max_y = max(512, *(f['aligned_canvas_origin_px'][1]+f['aligned_canvas_size_px'][1] for f in manifest['frames'].values()))
    canvas_size = (max_x-min_x+64, max_y-min_y+64)
    cell_w, cell_h = (value//2 for value in canvas_size)
    row_height = cell_h+15
    actor_origin = (32-min_x, 32-min_y)
    # Full native-coordinate placement contacts; no per-pose fitting.
    for start in range(0, len(names), 6):
        sheet = Image.new('RGB', (cell_w*2, 6*row_height), '#292d2b')
        draw = ImageDraw.Draw(sheet)
        for row, name in enumerate(names[start:start+6]):
            frame = manifest['frames'][name]
            original = native(sources, name, sources['base_palette'])
            restored = Image.open(out / frame['physical_master']).convert('RGBA')
            origin = frame['aligned_canvas_origin_px']
            native_canvas = Image.new('RGBA', canvas_size)
            native_canvas.paste(original.resize((512, 512), Image.Resampling.NEAREST), actor_origin)
            art_canvas = Image.new('RGBA', native_canvas.size)
            art_canvas.paste(restored, (actor_origin[0]+origin[0], actor_origin[1]+origin[1]))
            for col, image in enumerate([native_canvas, art_canvas]):
                sheet.paste(composite(image).resize((cell_w,cell_h), Image.Resampling.LANCZOS), (col*cell_w,row*row_height+15))
                draw.text((col*cell_w+3,row*row_height), name + (' native MM7' if not col else ' reused MM8'), fill='white')
            ground = row*row_height+15+(actor_origin[1]+512)//2
            draw.line((0,ground,cell_w*2,ground), fill='#666666')
        sheet.save(out / f'review/placement_{start//6:02d}.png')
    if sources['base_palette'] == 501:
        # All new third-palette appearances, and both enhanced-pixel mask channels.
        for start in range(0, len(names), 8):
            sheet = Image.new('RGB', (1024, 2*708), '#292d2b')
            draw = ImageDraw.Draw(sheet)
            for index, name in enumerate(names[start:start+8]):
                col, row = index % 4, index // 4
                preview = Image.open(out / f'previews/{name}_503.png').convert('RGBA')
                frame = manifest['frames'][name]
                original = native(sources, name, 503)
                coverage = Image.open(out / f'masks_2x/{name}.png').convert('RGBA')
                coverage.putalpha(preview.getchannel('A'))
                for offset, image in [(18, original), (286, preview), (552, coverage)]:
                    image = image.copy()
                    image.thumbnail((250, 252 if offset != 552 else 140), Image.Resampling.LANCZOS)
                    sheet.paste(composite(image), (col*256+3, row*708+offset))
                draw.text((col*256+3, row*708+3), name+' ACT503 native / restored / RG masks', fill='white')
            sheet.save(out / f'review/palette503_masks_{start//8:02d}.png')
        detail_names = list(dict.fromkeys(names[::12]+['m210dc0','m210wf0','m210wg1']))
        for start in range(0,len(detail_names),8):
            panel = Image.new('RGB',(768,8*150),'#292d2b')
            draw = ImageDraw.Draw(panel)
            for row,name in enumerate(detail_names[start:start+8]):
                base = Image.open(out/f'previews/{name}_501.png').convert('RGBA')
                variant = Image.open(out/f'previews/{name}_503.png').convert('RGBA')
                ys,xs = np.where(np.asarray(base)[:,:,3]>128)
                cx,cy = int(np.median(xs)),int(np.median(ys))
                box = (cx-96,cy-64,cx+96,cy+64)
                for i,image in enumerate([base,variant]):
                    for light,colour in enumerate(['#292d2b','#eee9df']):
                        panel.paste(composite(image.crop(box),colour),((i*2+light)*192,row*150+20))
                draw.text((3,row*150+3),name+' ACT501 / ACT503 same pixels, actual 100% material',fill='white')
            panel.save(out/f'review/palette503_detail_100pct_{start//8:02d}.png')
    # Delivered 100% patches and the worst alpha edges, from actual atlas tiles.
    selected = names[::12]
    worst = read(out / 'review/edge_audit.json')['frames']
    selected += sorted(names, key=lambda n: worst[n]['atlas']['maximum'], reverse=True)[:6]
    if sources['base_palette'] == 504:
        selected += [n for n in names if n.startswith('m198w') and n.endswith('0')]
    selected = list(dict.fromkeys(selected))
    for start in range(0, len(selected), 8):
        sheet = Image.new('RGB', (768, 8*150), '#292d2b')
        draw = ImageDraw.Draw(sheet)
        for row, name in enumerate(selected[start:start+8]):
            frame = manifest['frames'][name]
            x,y,w,h = frame['atlas_xywh']
            tile = bases[frame['page']].crop((x,y,x+w,y+h))
            alpha = np.asarray(tile)[:,:,3]
            ys,xs = np.where(alpha>128)
            centre = [int(np.median(xs)), int(np.median(ys))]
            edge = worst[name]['atlas']['worst_xy']
            patches = [tile.crop((cx-96,cy-64,cx+96,cy+64)) for cx,cy in [centre, edge]]
            for index, patch in enumerate(patches):
                for light, colour in enumerate(['#292d2b','#eee9df']):
                    sheet.paste(composite(patch, colour), ((index*2+light)*192,row*150+20))
            draw.text((3,row*150+3), name+' actual 2x material / alpha edge, 100%', fill='white')
        sheet.save(out / f'review/detail_edges_100pct_{start//8:02d}.png')


def validate(out):
    manifest, sources, records = read(out/'manifest.json'), read(out/'sources.json'), read(out/'registration.json')
    assert set(manifest['frames']) == set(sources['sources']) == set(records)
    assert not exact_placement.validate_manifest(manifest, records)
    count = 0
    for descriptor, bindings in sources['descriptor_bindings'].items():
        for action, group_name in bindings.items():
            group = sources['groups'][group_name]
            animation = manifest['descriptor_animations'][descriptor][action]
            assert animation['native_group'] == group_name and animation['animation_length_raw'] == group['animation_length_raw']
            for view in range(8):
                sequence = animation['directions'][str(view)]
                assert len(sequence) == len(group['frames'])
                for step, source in zip(sequence, group['frames'], strict=True):
                    flags = source['flags']
                    mirror = 'Image1' not in flags and f'Mirror{view}' in flags
                    stored = 8-view if mirror else view
                    name = source['texture_name'].lower() + ('' if 'Image1' in flags else str(stored))
                    assert (step['frame'],step['duration_raw'],step['duration_ms'],step['mirror'],step['scale'],step['palette_id'],step['flags']) == (
                        name,source['frame_length_raw'],source['frame_length_raw']*62.5,mirror,source.get('scale',1),source['palette_id'],flags)
                    count += 1
    bases = [Image.open(out / p['base']).convert('RGBA') for p in manifest['pages']]
    masks = [Image.open(out / p['mask']) for p in manifest['pages']]
    variants = {palette:[Image.open(out / f'previews/palette_{palette}_page_{i}.png').convert('RGBA')
                         for i in range(len(bases))] for palette in sources['palettes']}
    for name, frame in manifest['frames'].items():
        x,y,w,h = frame['atlas_xywh']
        rect, page = (x,y,x+w,y+h), frame['page']
        master = Image.open(out / frame['physical_master']).convert('RGBA')
        mask = Image.open(out / f'masks_2x/{name}.png')
        assert np.array_equal(bases[page].crop(rect), master.crop(frame['crop_in_aligned_px']))
        assert np.array_equal(masks[page].crop(rect), mask.crop(frame['crop_in_aligned_px']))
        assert not np.any(np.asarray(mask)[np.asarray(master)[:,:,3]==0])
        for palette in sources['palettes']:
            preview = Image.open(out / f'previews/{name}_{palette}.png').convert('RGBA')
            assert np.array_equal(preview.getchannel('A'), master.getchannel('A'))
            assert np.array_equal(variants[palette][page].crop(rect), preview.crop(frame['crop_in_aligned_px']))
            if palette == sources['base_palette']:
                assert np.array_equal(preview, master)
        assert sha(REPO / sources['sources'][name]['path']) == sources['sources'][name]['sha256']
    write(out/'validation.json', dict(native_images=120, restored_images=120, complete_native_coverage=True,
        exact_crop_reconstruction=True, exact_atlas_extraction=True, matching_base_mask_placement=True,
        exact_native_fractional_anchors=True, native_animation_steps_verified=count,
        aliases_timing_mirrors_scales_flags_and_palette_bindings_preserved=True,
        source_hashes_unchanged=True, base_exact_bypass=True, variant_alpha_unchanged=True,
        no_new_playback_steps=True, visual_review_complete=False, playback_watched=False,
        installed=False, coverage_by_method=manifest['coverage']))


def freeze():
    for family, donor_family, _, _ in FAMILIES:
        out = SESSION / family / 'mm8_wholesale'
        validate(out)
        manifest, sources, records = read(out/'manifest.json'), read(out/'sources.json'), read(out/'registration.json')
        processing = read(out/'processing.json')
        receipt = processing['receipt']
        for key in ['donor_manifest','donor_acceptance','prior_mm7_acceptance']:
            assert sha(REPO/receipt[key]['path']) == receipt[key]['sha256']
        reused = {}
        for name,frame in manifest['frames'].items():
            donor = DONORS/donor_family
            if frame['restoration_method'].startswith('user_authorized_native'):
                donor = donor/'walk0_video_x3_completion'
            original_master = donor/f'runtime_aligned_2x/{frame["donor_frame"]}.png'
            assert sha(original_master) == sha(out/frame['physical_master']), name
            reused[name] = dict(donor_master_path=relative(original_master),donor_master_sha256=sha(original_master),
                               unchanged_reused_master_sha256=sha(out/frame['physical_master']))
        processing['reused_frame_sha256'] = reused
        processing['export_bridge'] = dict(path=relative(Path(__file__)),sha256=sha(Path(__file__)))
        placement = [13,14,15,16,17,18,19] if family=='mm7_m198' else [0,6,17,18,19]
        inspected = [f'review/placement_{i:02d}.png' for i in placement]
        inspected += [str(p.relative_to(out)) for p in sorted((out/'review').glob('*100pct*.png'))]
        if family=='mm7_m210':
            inspected += [f'review/palette503_masks_{i:02d}.png' for i in range(15)]
        processing['directly_inspected_contacts'] = inspected
        write(out/'processing.json',processing)
        validation = read(out/'validation.json')
        validation['visual_review_complete'] = True
        validation['visual_review'] = 'Inherited verified artifact-bound donor reviews; MM7 placement contacts, new ACT503/masks and 100% detail/alpha contacts directly reviewed.'
        write(out/'validation.json', validation)
        coverage = manifest['coverage']
        labels = dict(mm7_m182='Dragon',mm7_m186='Dragonfly',mm7_m190='Dwarf',mm7_m508='Air',
                      mm7_m198='Earth',mm7_m202='Fire',mm7_m206='Light',mm7_m210='Water')
        links = []
        for target, label in labels.items():
            folder = 'mm8_wholesale' if target in ['mm7_m198','mm7_m210'] else 'redo_2x'
            links.append(f'<a href="../../{target}/{folder}/viewer.html">{label}</a>')
        build_viewer.run(out)
        html = (out/'viewer.html').read_text().replace('let playing=true', 'let playing=false').replace(
            '<button id="play">Pause</button>', '<button id="play">Play</button>')
        contacts = ' · '.join(f'<a href="review/{p.name}">{p.stem}</a>' for p in sorted((out/'review').glob('*.png')))
        note = ('Earth: eight front-walk frames use the accepted native neural x3 fallback, exported at 2x.'
                if family=='mm7_m198' else 'Water: all 120 MM7 images reuse accepted MM8 imagegen art; MM7 ACT503 is exported separately.')
        navigation = '<nav>'+' · '.join(links)+'</nav><p>'+note+'</p><details><summary>Placement, palettes/masks and 100% detail/edges</summary>'+contacts+'</details>'
        html = html.replace('</style>', '</style>'+navigation, 1)
        (out/'viewer.html').write_text(html)
        write(out/'run.json', dict(status='complete_user_authorized_mm8_art_reuse', user_authorization=AUTHORIZATION,
                                  new_imagegen_calls=0, coverage=coverage, installed=False))
        frame_hashes = {n:dict(native=sha(REPO/sources['sources'][n]['path']),
                              master_2x=sha(out/f'aligned_2x/{n}.png'),
                              material_mask_2x=sha(out/f'masks_2x/{n}.png'),
                              cleaned=sha(REPO/records[n]['clean_path'])) for n in manifest['frames']}
        acceptance = dict(status='complete_user_authorized_mm8_reuse', complete=True, frozen=True,
            reviewed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            coverage=dict(coverage, accepted_images=120, native_images=120, missing_images=[]),
            sampling=manifest['actual_generated_detail'], user_authorization=AUTHORIZATION,
            reuse_provenance=receipt, frame_sha256=frame_hashes, validation=validation,
            frame_hash_contract=dict(native='original MM7 BMP file',cleaned='unchanged MM8 cleaned PNG file',
                                     master_2x='unchanged copied MM8 runtime master',material_mask_2x='local MM7 palette coverage'),
            visual_review=dict(method='Static contacts plus hash-bound unchanged donor reviews',
                pose_coverage=sorted(manifest['frames']), playback_watched=False,
                independent_placement='Artifact-bound donor independent-feature reviews inherited for every pose; native compatibility checked for every image and selected MM7 placement contacts directly compared without changing transforms.',
                materials='Source accepted fine-detail reviews resumed by hashes; delivered material patches and alpha edges directly inspected at 100%.',
                palettes='All MM7 palettes exported; ACT501/502 and ACT504 base art inherited unchanged; every new ACT503 appearance and RG mask checked.',
                directly_inspected_contacts=inspected,
                available_evidence=[str(p.relative_to(out)) for p in sorted((out/'review').glob('*.png'))]),
            limitations=manifest['limitations'], installed=False)
        acceptance['artifact_sha256'] = {str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*'))
            if p.is_file() and p.name != 'acceptance.json' and '__pycache__' not in p.parts}
        write(out/'review/acceptance.json', acceptance)
        handoff = dict(manifest='mm8_wholesale/manifest.json', acceptance='mm8_wholesale/review/acceptance.json',
            reviewer='mm8_wholesale/viewer.html', selected_art_source=donor_family,
            complete=True, full_latest_imagegen_method_coverage=coverage['full_latest_imagegen_method_coverage'],
            coverage_by_method=dict(reused_packed_outline_imagegen=coverage['reused_packed_outline_images'],
                                    native_video_x3=coverage['native_video_x3_images']),
            prior_mm7_outputs_preserved='redo_2x/', installed=False)
        write(out.parent/'current_handoff_20261002.json', handoff)
        print(f'{family}: selected complete 120/120 MM8 reuse; imagegen {coverage["reused_packed_outline_images"]}; neural {coverage["native_video_x3_images"]}', flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'contacts':
        for family, _, _, _ in FAMILIES:
            if len(sys.argv)>2 and family not in sys.argv[2:]:
                continue
            out = SESSION/family/'mm8_wholesale'
            m = read(out/'manifest.json')
            make_contacts(out,read(out/'sources.json'),m,{},
                          {i:Image.open(out/p['base']).convert('RGBA') for i,p in enumerate(m['pages'])})
            print(f'{family}: refreshed full union placement contacts',flush=True)
    else:
        {'export':export, 'freeze':freeze}[sys.argv[1]]()
