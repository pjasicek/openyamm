"""Session-local partial MM7 exports through existing material, atlas and shared reviewer tools.

The MM7 packager needs a complete supplied frame set. Its explicit temporary subset
exports available pixels while the final manifest retains every native binding.
No missing frame is substituted and no visual acceptance is inferred.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw

REPO = Path.cwd().resolve()
CREATURES = REPO / 'level_generation/creatures'
SESSION = CREATURES / 'mm7_mm8_packed_outline/session_mm7_03'
sys.path.insert(0, str(CREATURES / 'mm7_m514'))
sys.path.insert(0, str(CREATURES / 'mm6_remaining/redo_2x'))
from process import apply_variant, composite
from prepare_packed_outline import native_2x


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def masks(family, out, sources, records, config):
    if family == 'mm7_m214':
        authoring = read(out / 'hair_authoring.json')
        assert set(authoring['regions']) == set(records), 'New poses need fresh enhanced hair authoring.'
        write(out / 'hair_regions.json', authoring['regions'])
        write(out / 'hair_overlap_corrections.json', authoring['corrections'])
    if family == 'mm7_m242':
        write(out / 'bone_exclusions.json', {})
    if family in ('mm7_m214', 'mm7_m218', 'mm7_m234', 'mm7_m238', 'mm7_m242'):
        mod = module('session_material_'+family, CREATURES / family / 'variants.py')
        mod.HERE, mod.REPO = out, REPO
        mod.run()
        if family == 'mm7_m214':
            # Shared hair inclusions override its earlier feather exclusions. Apply the
            # freshly reviewed protected polygons to the finished soft masks as well.
            for name, polygon in authoring['corrections']['feather_exclusions'].items():
                path = out / f'masks_2x/{name}.png'
                mask = np.array(Image.open(path))
                cut = Image.new('L', (mask.shape[1], mask.shape[0]))
                ImageDraw.Draw(cut).polygon([tuple(p) for p in polygon], fill=255)
                mask[np.array(cut) > 0, 1] = 0
                Image.fromarray(mask).save(path)
            settings = read(out / 'variants.json')
            settings['recolor']['mask_filter'] += ' Fresh enhanced hair-core bounds replace prop-contaminated head-cap bounds; inspected feather polygons protect quiver overlaps after soft filtering.'
            write(out / 'variants.json', settings)
    else:
        if family in ('mm7_m226', 'mm7_m230'):
            pal = np.frombuffer((REPO / sources['palette_sources'][str(sources['base_palette'])]['path']).read_bytes()[:768],
                np.uint8).reshape(256,3).astype(float)
            changed = np.zeros(256, bool)
            for p in sources['palette_sources'].values():
                target = np.frombuffer((REPO / p['path']).read_bytes()[:768], np.uint8).reshape(256,3)
                changed |= (target != pal).any(axis=1)
            green = changed & (pal[:,1] > pal[:,0]*1.08) & (pal[:,1] > pal[:,2]*1.04)
            regions = [dict(name='garment_green', selector='green', thresholds=[.025,.16],
                palette_indices=np.flatnonzero(green).tolist(), mask_sigma=.45)]
            if family == 'mm7_m226':
                cyan = changed & (pal[:,1] > pal[:,0]*1.12) & (pal[:,2] > pal[:,0]*1.12) & ~green
                if cyan.any():
                    regions.append(dict(name='garment_teal_shadow', selector='cyan', thresholds=[.08,.3],
                        palette_indices=np.flatnonzero(cyan).tolist(), mask_sigma=.45,
                        native_palette_spatial_support=np.flatnonzero(green|cyan).tolist(), support_padding=5,
                        exclude_channels=[0]))
            config['materials'] = dict(regions=regions, limitation='Fresh enhanced garment masks; native palette ramp fits. Protected skin, steel and leather require all-pose review.')
        config['identity_frames'] = [n for n in records if 'sa' in n][:4]
        write(out / 'config.json', config)
        module('session_generic_materials', CREATURES / 'mm7_ambient/material_variants.py').run(out)
    if family == 'mm7_m222' and (out/'legacy_reuse/material_protection.json').exists():
        protection = read(out/'legacy_reuse/material_protection.json')
        assert set(protection['frames']) == {n for n,r in records.items() if 'retained_from' in r}
        for name,support in protection['frames'].items():
            assert records[name]['clean_sha256'] == support['clean_sha256']
            path = out/f'masks_2x/{name}.png'
            mask = np.array(Image.open(path))
            allowed = np.zeros(mask.shape[:2],bool)
            for x0,y0,x1,y1 in support['cloth_support_rectangles']:
                allowed[y0:y1,x0:x1] = True
            mask[~allowed,0] = 0
            Image.fromarray(mask).save(path)
        settings = read(out/'variants.json')
        settings['recolor']['limitation'] += ' Reviewed enhanced sleeve/waist support envelopes protect tinted metal and leather edges on the fifteen reused older poses; master pixels and hair weights remain unchanged.'
        write(out/'variants.json',settings)


def native_animations(sources):
    result = {}
    for descriptor, binding in sources['descriptor_bindings'].items():
        result[descriptor] = {}
        for action, group_name in binding.items():
            group = sources['groups'][group_name]
            directions = {}
            for view in range(8):
                steps = []
                if group_name != 'null':
                    for frame in group['frames']:
                        single = 'Image1' in frame['flags']
                        mirror = not single and f'Mirror{view}' in frame['flags']
                        stored = 8-view if mirror else view
                        name = frame['texture_name'].lower()+('' if single else str(stored))
                        steps.append(dict(frame=name, duration_raw=frame['frame_length_raw'],
                            duration_ms=frame['frame_length_raw']*62.5, mirror=mirror, flags=frame['flags'],
                            scale=frame.get('scale',1), palette_id=frame['palette_id']))
                directions[str(view)] = steps
            result[descriptor][action] = dict(native_group=group_name, native_group_id=group['sprite_id'],
                animation_length_raw=group.get('animation_length_raw',0), directions=directions,
                empty=group_name=='null', loop=action in ('standing','walk'), hold_last=action=='corpse',
                next_action='corpse' if action=='death' else 'standing' if action in ('attack','shoot','hit','fidget') else None)
    return result


def reviewer_regions(manifest, out):
    if isinstance(manifest.get('regions'), list):
        manifest['material_regions'] = manifest['regions']
        manifest['regions'] = {
            'mask_' + region.get('channel', 'RGB'[i]).lower(): region.get('id', region.get('name', 'Material'))
            for i, region in enumerate(manifest['material_regions'])}
    # The shared viewer reads PNG colour channels. Store logical R8 atlas coverage
    # in R with zero G/B; individual enhanced and trimmed R8 mask weights stay exact.
    for page in manifest['pages']:
        path = out / page['mask']
        with Image.open(path) as mask:
            if mask.mode == 'L':
                values = np.array(mask)
                carrier = np.zeros((*values.shape, 3), np.uint8)
                carrier[:, :, 0] = values
                Image.fromarray(carrier).save(path)
                page['mask_logical_channels'] = ['R']
                page['individual_mask_format'] = 'R8 linear'
                page['mask_format'] = 'RGB8 linear; R carries exact R8 coverage, G/B zero'
    pixels = sum(page['size'][0] * page['size'][1] for page in manifest['pages'])
    manifest['memory_bytes'].pop('mask_r8', None)
    manifest['memory_bytes'].update(mask_rgb8=pixels*3,shared_total=pixels*7,
        tight_base_and_mask=sum(f['atlas_xywh'][2]*f['atlas_xywh'][3]*7 for f in manifest['frames'].values()))


def export(family):
    root, out = SESSION / family, SESSION / family / 'redo_2x'
    sources, config, records, run = (read(p) for p in (root/'sources.json',root/'config.json',out/'registration.json',out/'run.json'))
    for key in ('reviewed_placement_translation_px','clear_alpha1_border_batches'):
        config.pop(key, None)
    for filename, value in [('sources.json',sources),('config.json',config),('processing_settings.json',dict(method=run['method'],visual_acceptance=False))]:
        write(out / filename, value)
    generation = {}
    for name, record in records.items():
        shutil.copy2(REPO / record['clean_path'], out / f'cleaned/{name}.png')
        job = next(j for j in run['jobs'] if j['id']==record['batch'])
        if 'retained_from' in record:
            generation[job['id']] = dict(retained_restoration=job['retained_restoration'],
                complete_current_outline_return=False)
        else:
            attempt = next(a for a in job['attempts'] if a['raw']==record['raw_path'])
            generation[job['id']] = attempt
    write(out / 'generation.json', dict(batches=generation,
        rule='Current generations return one full native animation/view. User-authorized older accepted restorations are explicitly recorded separately.'))
    masks(family, out, sources, records, config)
    full = native_animations(sources)
    subset = copy.deepcopy(sources)
    subset['sources'] = {n:sources['sources'][n] for n in records}
    subset['descriptor_bindings'] = {d:{a:sources['descriptor_bindings'][d][a] for a,animation in animations.items()
        if all(step['frame'] in records for seq in animation['directions'].values() for step in seq)} for d,animations in full.items()}
    work = out / '.partial_package_work'
    work.mkdir(exist_ok=False)
    try:
        write(work / 'sources.json', subset)
        write(work / 'registration.json', records)
        for name in ('config.json','variants.json'):
            shutil.copy2(out/name,work/name)
        for directory in ('aligned_2x','masks_2x','cleaned'):
            (work/directory).symlink_to(out/directory, target_is_directory=True)
        (work/'review').mkdir()
        module('session_mm7_package',CREATURES/'mm7_m514/package.py').run(work)
        for directory in ('atlas','trimmed_2x','trimmed_masks_2x','previews'):
            shutil.copytree(work/directory,out/directory,dirs_exist_ok=True)
        for name in ('manifest.json','validation.json','review/edge_audit.json','review/edge_closeups.png'):
            shutil.copy2(work/name,out/name)
    finally:
        shutil.rmtree(work)
    manifest = read(out/'manifest.json')
    variants = manifest['variants']
    manifest.update(schema_status='PARTIAL candidate; missing native art; not accepted or installed',
        quality_status='partial_pending_full_animation_and_variant_review', review_label=config['title'],
        native_descriptor_animations=full, native_group_bindings_full=sources['descriptor_bindings'], native_groups=sources['groups'],
        source_coverage=dict(expected=len(sources['sources']),exported=len(records),missing=sorted(set(sources['sources'])-set(records))),
        generated_detail=dict(physical_export_tier=2,measured_minimum=min(2/r['scale'] for r in records.values()),
            sampling_by_complete_sheet={j['id']:read(out/'calibration.json')[j['id']].get('generated_sampling') for j in run['jobs'] if j.get('selected_raw')},
            sampling_by_retained_job={j['id']:min(min(records[n]['effective_sampling_xy']) for n in j['frames'])
                for j in run['jobs'] if j.get('retained_restoration')},
            policy=read(out/'processing.json')['whole_animation_resolution_policy']),
        limitations=['Incomplete family: all missing art and unresolved visual issues must be completed before acceptance.',
            'Supplied generated alpha retained above the documented near-transparent noise floor.',
            'Anatomical scales and whole-pose translation candidates require independent visual review.'])
    retained = {n:r['retained_from'] for n,r in records.items() if 'retained_from' in r}
    manifest['restoration_provenance'] = dict(current_outline_generated_frames=len(records)-len(retained),
        reviewed_legacy_reuse_frames=len(retained), retained=retained,
        latest_method_complete=not retained and all(j.get('selected_raw') for j in run['jobs']))
    manifest['animations_by_palette'] = {}
    manifest['variants'] = {}
    for variant in variants:
        p = str(variant['palette_id'])
        descriptor = str(variant['descriptors'][0])
        actions = {}
        for action, animation in full[descriptor].items():
            views = {v:[dict(frame=s['frame'],duration_ms=s['duration_ms'],duration_raw=s['duration_raw'],mirrored=s['mirror'],
                native_scale=s['scale'],native_flags=s['flags']) for s in seq]
                for v,seq in animation['directions'].items() if seq and all(s['frame'] in records for s in seq)}
            if views:
                actions[action] = dict(views=views,native_group=animation['native_group'],native_length_raw=animation['animation_length_raw'],
                    sequence_ms=sum(s['duration_ms'] for s in next(iter(views.values()))),playback='loop' if animation['loop'] else 'hold' if animation['hold_last'] else 'once',
                    next_action=animation['next_action'],single_view='Image1' in next(iter(views.values()))[0]['native_flags'])
        manifest['animations_by_palette'][p] = actions
        manifest['variants'][p] = dict(variant, exact_base_bypass=variant['exact_bypass'],descriptor_ids=variant['descriptors'])
    manifest['animations'] = manifest['animations_by_palette'][str(sources['base_palette'])]
    manifest['native_frame_scale'] = 1
    for i,page in enumerate(manifest['pages']):
        page['variant_previews'] = {str(v['palette_id']):f'previews/palette_{v["palette_id"]}_page_{i}.png' for v in variants}
    (out/'native_variants').mkdir(exist_ok=True)
    for name,frame in manifest['frames'].items():
        frame.update(native_offset=sources['sources'][name]['native_offset'],registration_native_offset=sources['sources'][name]['native_offset'])
        for p in sources['palettes']:
            native_2x(sources['sources'][name],sources,p)[0].resize(tuple(sources['logical_canvas']),Image.Resampling.NEAREST).save(out/f'native_variants/{name}_{p}.png')
    sys.path.insert(0,str(CREATURES))
    from exact_placement import validate_manifest
    assert not validate_manifest(manifest,records)
    reviewer_regions(manifest, out)
    write(out/'manifest.json',manifest)
    validation = read(out/'validation.json')
    validation.update(family_complete=False,visual_acceptance_frozen=False,exact_native_anchors=True,
        raw_cells_unclipped=None,raw_border_review='review/raw_border_audit.json',native_metadata_preserved=True)
    write(out/'validation.json',validation)
    print(json.dumps(dict(family=family,exported=len(records),missing=len(manifest['source_coverage']['missing']),accepted=False)),flush=True)


def collection(families):
    sys.path.insert(0,str(CREATURES/'mm6_remaining/acceptance_viewer'))
    from serve import artifact_digest, load_family
    entries=[]
    accepted=0
    for family in families:
        path=SESSION/family/'redo_2x/manifest.json';raw=path.read_bytes();m=read(path)
        accepted += int(m.get('visual_acceptance') is True)
        provenance = m.get('restoration_provenance', {})
        source = ('Current outline restoration with explicitly reviewed older 2x reuse'
            if provenance.get('reviewed_legacy_reuse_frames') else 'Latest whole-animation outline candidate')
        loaded=load_family(m['review_label'],path,source,m['quality_status'])
        entries.append(dict(creature=m['creature'],label=m['review_label'],manifest=os.path.relpath(path,SESSION/'mm7_m214'),
            manifest_sha256=sha(path),artifact_sha256=loaded.artifact_sha256,frame_count=len(m['frames']),
            source=source,pipeline_status=m['quality_status']))
    write(SESSION/'mm7_m214/review_collection.json',dict(schema_version=1,collection_id='mm7-session-mm7-03',
        title=f'MM7 session 03 — {accepted} accepted, {len(entries)-accepted} partial families',
        pixels_per_logical_pixel=2,family_count=len(entries),frame_count=sum(e['frame_count'] for e in entries),families=entries))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('families',nargs='+')
    args=parser.parse_args()
    for family in args.families:
        export(family)
    collection(args.families)
