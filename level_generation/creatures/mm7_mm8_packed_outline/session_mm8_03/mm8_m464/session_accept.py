"""Bind this session's explicit static review to the existing local acceptance format.

Preparation and numeric checks never grant visual acceptance. The final switch is
used only after the agent has inspected all available native-order pose contacts,
independent placement, delivered detail/alpha, and every native palette/mask pose.
"""
import argparse
import copy
from datetime import datetime, timezone
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

from session_prepare import CREATURES, HEADER, REPO, ROLES, STAGE, STEMS, read, save
from session_finish import sha

sys.path.insert(0, str(CREATURES))
from exact_placement import validate_animation_bindings, validate_manifest


def audit(root):
    out = root / 'redo_2x'
    sources = read(root / 'sources.json')
    run = read(out / 'run.json')
    manifest = read(out / 'draft_manifest.json')
    records = read(out / 'registration.json')
    assert manifest['animations'] == sources['bindings']
    assert set(records) == set(manifest['frames'])
    assert not validate_manifest(manifest, records)
    assert not read(out / 'processing.json').get('extraction_failures')
    for source in sources['sources'].values():
        assert sha(REPO / source['path']) == source['sha256']
    for source in sources['source_tables'] + [sources['descriptor_table']]:
        assert sha(REPO / source['path']) == source['sha256']
    protocol = []
    for job in run['jobs']:
        selected = job.get('selected_raw')
        for number, attempt in enumerate(job['attempts'], 1):
            refs = attempt['references']
            assert [x['role'] for x in refs[:2]] == ROLES[:2]
            if len(refs) == 3:
                assert refs[2]['role'] in (ROLES[2], 'same_family_detailed_appearance_geometry_not_authoritative')
            assert len(refs) == (2 if attempt['bootstrap_exception'] else 3)
            assert attempt['actual_tool_arguments']['referenced_image_paths'] == [x['path'] for x in refs]
            assert attempt['actual_tool_arguments']['transparent_background'] is True
            for asset in refs:
                assert sha(Path(asset['path'])) == asset['sha256']
            native, outline = [Image.open(x['path']) for x in refs[:2]]
            assert native.size == outline.size
            rgb = np.asarray(outline.convert('RGB'))
            assert np.all(rgb[:, :, 0] == rgb[:, :, 1]) and np.all(rgb[:, :, 1] == rgb[:, :, 2])
            assert set(np.unique(rgb)) <= {0, 255}
            prompt = REPO / attempt['prompt']
            assert prompt.read_text().startswith(HEADER)
            assert sha(prompt) == attempt['prompt_sha256']
            if attempt.get('raw'):
                assert sha(REPO / attempt['raw']) == attempt['sha256']
            protocol.append(dict(job=job['id'], attempt=number, raw=attempt.get('raw'),
                sha256=attempt.get('sha256'), status=attempt['status'],
                selected=bool(selected and selected == attempt.get('raw')),
                inputs=refs, prompt=attempt['prompt'], prompt_sha256=attempt['prompt_sha256'],
                bootstrap_exception=attempt['bootstrap_exception'],
                actual_tool_arguments=attempt['actual_tool_arguments'],
                failure=attempt.get('failure'), review_status=attempt.get('review_status'),
                rejection_reason=attempt.get('rejection_reason')))
        if selected:
            assert any(a.get('raw') == selected for a in job['attempts'])
        assigned = [r for r in records.values() if r['batch'] == job['id']]
        assert len({r['scale'] for r in assigned}) <= 1, job['id']
    for name, record in records.items():
        assert record['raw_clip'] is False
        assert sha(REPO / record['raw_path']) == record['raw_sha256']
        assert sha(REPO / record['clean_path']) == record['clean_sha256']
        canonical = sources['pixel_aliases'].get(name, name)
        base = np.asarray(Image.open(out / 'toned_2x' / (canonical+'.png')).convert('RGBA'))
        for palette in manifest['native_palettes']:
            preview = np.asarray(Image.open(out / 'previews' / f'{name}_{palette}.png').convert('RGBA'))
            assert np.array_equal(base[:, :, 3], preview[:, :, 3])
            if int(palette) == sources['base_palette']:
                assert np.array_equal(base, preview)
        if name in sources['pixel_aliases']:
            canonical = sources['pixel_aliases'][name]
            for palette in manifest['native_palettes']:
                assert sha(out/'previews'/f'{name}_{palette}.png') == sha(out/'previews'/f'{canonical}_{palette}.png')
    for palette, info in manifest['native_palettes'].items():
        assert sha(out / info['path']) == info['sha256'] == sources['palette_sources'][palette]['sha256']
    return sources, run, manifest, records, protocol


def prepare(root, manifest, sources, records):
    out = root / 'redo_2x'
    # Keep rejected masters as resumable evidence, outside the active export folders.
    for folder in ['aligned_2x', 'toned_2x', 'masks_2x', 'runtime_aligned_2x', 'runtime_masks_2x', 'native_variants', 'previews']:
        for path in (out / folder).glob('*.png'):
            name = path.stem.split('_')[0]
            if name not in manifest['frames']:
                destination = out / 'rejected_export_evidence' / folder / path.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                path.rename(destination)
    final = copy.deepcopy(manifest)
    final['label'] = sources['label']
    final['material_settings'] = 'material_settings.json'
    final['material_settings_sha256'] = sha(out / 'material_settings.json')
    final['native_descriptor_bindings'] = copy.deepcopy(sources['bindings'])
    final['animations_by_palette'] = {}
    final['native_group_bindings'] = {}
    final['review_descriptor_by_palette'] = {}
    final['variants'] = {}
    for palette in manifest['native_palettes']:
        actor_id, actor = next((key, row) for key, row in sources['bindings'].items()
            if any(step['palette'] == int(palette) for a in row['actions'].values()
                   for steps in a['views'].values() for step in steps))
        actions = copy.deepcopy(actor['actions'])
        for action in actions.values():
            group = action['native_group_record']
            action['native_length_raw'] = group.get('animation_length_raw', 0)
            action['sequence_ms'] = sum(x['frame_length_raw'] * 62.5 for x in group['frames'])
            if action['native_group'].lower() == 'null':
                action['no_image'] = True
            for steps in action['views'].values():
                for step in steps:
                    step['native_scale'] = step['scale']
        final['animations_by_palette'][palette] = actions
        final['native_group_bindings'][palette] = {'actions': {
            key: row['native_group_record'] for key, row in actions.items()}}
        final['review_descriptor_by_palette'][palette] = int(actor_id)
        final['variants'][palette] = dict(name='Native palette '+palette, palette_id=int(palette),
            exact_base_bypass=int(palette) == sources['base_palette'],
            operation=manifest['variants']['operation'], settings='material_settings.json')
    final['animations'] = copy.deepcopy(final['animations_by_palette'][str(sources['base_palette'])])
    for name, frame in final['frames'].items():
        frame['effective_sampling_xy'] = records[name]['effective_sampling_xy']
        frame['raw_path'] = records[name]['raw_path']
        frame['logical_size'] = sources['logical_canvas']
    for index, page in enumerate(final['pages']):
        page['base_sha256'] = sha(out / page['base'])
        page['mask_sha256'] = sha(out / page['mask'])
        page['variant_previews'] = {}
        for palette in final['variants']:
            if int(palette) == sources['base_palette']:
                page['variant_previews'][palette] = page['base']
                continue
            atlas = Image.new('RGBA', page['size'])
            for name, frame in final['frames'].items():
                if frame['page'] != index or 'pixel_alias_of' in frame:
                    continue
                pixels = np.array(Image.open(out/'previews'/f'{name}_{palette}.png').convert('RGBA'))
                solid = pixels[:, :, 3] > 0
                distance, nearest = ndimage.distance_transform_edt(~solid, return_indices=True)
                ring = (distance <= 3) & ~solid
                pixels[:, :, :3][~solid] = 0
                pixels[:, :, :3][ring] = pixels[nearest[0], nearest[1], :3][ring]
                tile = Image.fromarray(pixels).crop(frame['crop_in_aligned_px'])
                x, y, w, h = frame['atlas_xywh']
                atlas.paste(tile, (x, y))
                assert np.array_equal(atlas.crop((x, y, x+w, y+h)), tile)
            path = f'atlas/preview_{index}_{palette}.png'
            atlas.save(out/path)
            assert np.array_equal(np.asarray(atlas)[:, :, 3], np.asarray(Image.open(out/page['base']))[:, :, 3])
            page['variant_previews'][palette] = path
    samples = {name: min(row['effective_sampling_xy']) for name, row in records.items()}
    final['generated_detail'] = dict(measured_minimum=min(samples.values()), measured_maximum=max(samples.values()),
        physical_export_tier=2, sampling_method='actual raw-to-export anatomical registration including rounding',
        below_target_frames=sorted(n for n, x in samples.items() if x < 2),
        whole_animation_resolution_policy=read(out/'processing.json')['whole_animation_resolution_policy'],
        interpolation_is_not_new_detail=True)
    errors = validate_animation_bindings(final)
    if final['full_coverage']:
        assert not errors, errors
    else:
        assert all(': native frame, mirror, duration or scale' in x for x in errors), errors
    assert final['native_descriptor_bindings'] == sources['bindings']
    final['playback_ready'] = final['full_coverage']
    final['acceptance'] = 'pending_visual_review'
    save(out/'manifest.json', final)
    save(out/'review/package_validation.json', dict(status='passed' if not errors else 'partial_missing_native_frames',
        exact_placement_errors=validate_manifest(final, records), animation_binding_errors=errors,
        full_native_descriptor_metadata_exact=True, available_palette_atlas_tiles_exact=True,
        missing_frames=final['missing_frames']))
    return final


def freeze(root, sources, run, manifest, records, protocol):
    out = root/'redo_2x'
    now = datetime.now(timezone.utc).isoformat()
    complete = manifest['full_coverage']
    placement_note = ('Every available pose inspected in native order, including unused art and actual later returned '
        'occurrences of reused native frames. Uniform sheet scale and whole-pose translations preserve native motion; '
        'independent anatomy, garment, contact and equipment features inspected. Fine generated detail, light/dark '
        'alpha edges, all native palette poses and R8 overlays reviewed. Native spell light remains invariant. '
        'Native-colour and matching separate outline files are attached and hash bound on every attempt. '
        'The detailed appearance bootstrap exceptions are recorded individually. Local acceptance only.')
    if 'm464dc1' in records:
        placement_note += ' Unused m464dc1 has a reviewed approximately 15% shorter extended leg; overall pose is retained.'
    for row in records.values():
        landmarks = row.get('review_landmarks', {})
        if 'independent_visible_foot_contact' in landmarks:
            value = landmarks.pop('independent_visible_foot_contact')
            value['role'] = 'Independent lowest solid contour: visually identified as a foot, hand or other part in falling poses; never used to fit the transform.'
            landmarks.setdefault('independent_lowest_solid_contour', value)
        row['visual_review'] = dict(status='accepted_available_pose', mode='static_contacts', reviewed_utc=now)
    save(out/'registration.json', records)
    for filename in ['complete_placement.json', 'actual_reused_poses.json']:
        data = read(out/'review'/filename)
        data['status'] = 'accepted_available_static_pose_review'
        data['reviewed_utc'] = now
        save(out/'review'/filename, data)
    checks = read(out/'review/export_checks.json')
    checks.update(visual_review_complete=complete, animation_review_complete=complete,
        available_visual_review_complete=True, available_animation_review_complete=True,
        watched_playback=False)
    checks['palette_mask_review']['status'] = 'accepted_every_available_native_palette_pose'
    save(out/'review/export_checks.json', checks)
    for job in run['jobs']:
        if job.get('selected_raw'):
            job['status'] = 'accepted_local_complete_animation_view'
            for attempt in job['attempts']:
                if attempt.get('raw') == job['selected_raw']:
                    attempt['review_status'] = 'accepted_local_static_review'
    run['status'] = 'accepted_local' if complete else 'partial_available_art_reviewed_missing_jobs'
    save(out/'run.json', run)
    manifest.update(status=run['status'], quality_status=run['status'],
        review_label=sources['label']+' / packed outline session 03',
        acceptance='review/acceptance.json', driver_acceptance=complete, installed=False)
    save(out/'manifest.json', manifest)
    sys.path.insert(0, str(CREATURES/'mm6_remaining/acceptance_viewer'))
    from serve import load_family, VIEWER_REVISION
    reviewer = None
    try:
        reviewer = load_family(sources['label'], out/'manifest.json', 'staged MM8 package', run['status'])
        assert complete
        save(out/'review/shared_reviewer_check.json', dict(status='passed', **reviewer.summary()))
        state = root/'acceptance_state'
        state.mkdir(exist_ok=True)
        decision = dict(decision='accepted', note='Explicit static contact review: every available native-order pose, '
            'independent placement, representative 100% material/alpha detail, and every native palette/R8 pose inspected. '
            'Timed playback was not watched. Offline local acceptance; not installed.', updated_at=now,
            viewer_revision=VIEWER_REVISION, manifest_sha256=reviewer.manifest_sha256,
            artifact_sha256=reviewer.artifact_sha256, fixups_revision=0, fixups_snapshot={},
            guides_snapshot=None, colors_snapshot={}, preview_fixups=False, preview_scale=False)
        save(state/'decisions.json', dict(schema_version=1, decisions={reviewer.id: {reviewer.artifact_sha256: decision}}))
    except ValueError as error:
        assert not complete and 'unknown animation frame' in str(error), str(error)
        save(out/'review/shared_reviewer_check.json', dict(status='partial_rejected_as_expected',
            reason=str(error), missing_frames=manifest['missing_frames'], full_native_bindings_preserved=True))
    pages = []
    for filename, category in [('complete_placement.json', 'native_order_independent_placement'),
                               ('actual_reused_poses.json', 'actual_reused_returned_poses')]:
        pages += [(out / p, category) for p in read(out/'review'/filename)['pages']]
    pages += [(out / p, 'all_native_palettes_and_masks') for p in checks['palette_mask_review']['pages']]
    for filename in ['detail_alpha_100pct.png', 'worst_final_edges_100pct.png', 'palette_detail_100pct.png', 'native_hair_skin_check.png']:
        path = out/'review'/filename
        if path.exists():
            pages.append((path, 'representative_unresized_material_detail_and_alpha'))
    viewed = [dict(path=str(p.relative_to(REPO)), sha256=sha(p), category=category) for p, category in pages]
    artifacts = {}
    for folder in ['raw', 'references', 'prompts', 'cleaned', 'aligned_2x', 'toned_2x', 'masks_2x',
                   'runtime_aligned_2x', 'runtime_masks_2x', 'native_variants', 'previews', 'atlas', 'palettes']:
        for path in (out/folder).rglob('*'):
            if path.is_file():
                artifacts[str(path.relative_to(REPO))] = sha(path)
    for path in list(out.glob('*.json')) + list((out/'review').glob('*.json')) + [root/'sources.json', root/'manifest.json', root/'config.json']:
        if path.name != 'acceptance.json':
            artifacts[str(path.relative_to(REPO))] = sha(path)
    if reviewer:
        artifacts[str((root/'acceptance_state/decisions.json').relative_to(REPO))] = sha(root/'acceptance_state/decisions.json')
    artifacts.update({row['path']:row['sha256'] for row in viewed})
    for source in list(sources['sources'].values()) + sources['source_tables'] + [sources['descriptor_table']]:
        artifacts[source['path']] = source['sha256']
    for source in sources['palette_sources'].values():
        artifacts[source['path']] = source['sha256']
    for path in (STAGE/'mm8_m464').glob('session_*.py'):
        artifacts[str(path.relative_to(REPO))] = sha(path)
    for attempt in protocol:
        if attempt['selected']:
            attempt['review_status'] = 'accepted_local_static_review'
    frozen = dict(status='accepted' if complete else 'partial', reviewed_utc=now,
        review_mode='static_contacts', method=run['method'], reviewed_frames=sorted(manifest['frames']),
        coverage=dict(native_frames=len(sources['sources']), exported_frames=len(manifest['frames']),
            complete_animation_view_jobs=sum(bool(j.get('selected_raw')) for j in run['jobs']),
            required_animation_view_jobs=len(run['jobs']), palettes=list(map(int, manifest['native_palettes'])),
            descriptor_ids=list(map(int, sources['bindings'])), retained_frames=0,
            unused_native_frames=len(sources['orphan_images']), missing_frames=manifest['missing_frames']),
        checks=dict(faithful_detail=True, poses_and_placement=True, edges_and_alpha=True,
            masks_and_variants=True, attached_outline_every_selected_call=True,
            full_native_coverage=complete, watched_playback=False),
        placement_notes=placement_note, limitations='Static native-order sequence review; timed playback not watched. '
            'Offline export; not installed. '+('' if complete else 'Partial package must not be used for playback; native missing references stay explicit.'),
        generated_detail=manifest['generated_detail'], submitted_protocol=protocol,
        artifact_hashes=artifacts, visually_viewed_artifacts=viewed)
    if reviewer:
        frozen['reviewer_decision'] = str((root/'acceptance_state/decisions.json').relative_to(REPO))
        frozen['reviewer_artifact_sha256'] = reviewer.artifact_sha256
    save(out/'review/acceptance.json', frozen)
    print(root.name, frozen['status'], f"{len(manifest['frames'])}/{len(sources['sources'])}",
          f"actual detail {manifest['generated_detail']['measured_minimum']:.4f}x", 'missing', manifest['missing_frames'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stems', type=int, nargs='+')
    parser.add_argument('--freeze-after-static-review', action='store_true')
    args = parser.parse_args()
    for stem in args.stems:
        assert stem in STEMS
        root = STAGE/f'mm8_m{stem}'
        sources, run, draft, records, protocol = audit(root)
        if args.freeze_after_static_review:
            freeze(root, sources, run, read(root/'redo_2x/manifest.json'), records, protocol)
        else:
            final = prepare(root, draft, sources, records)
            print(stem, 'prepared and validated; explicit visual decision still required', flush=True)
