"""Validate and pin this session's partial review evidence without accepting missing or defective art."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

REPO = Path.cwd().resolve()
SESSION = REPO / 'level_generation/creatures/mm7_mm8_packed_outline/session_mm7_03'
HERE = SESSION / 'mm7_m214'
FAMILIES = ['mm7_m' + str(n) for n in (214, 218, 222, 226, 230, 234, 238, 242)]
spec = importlib.util.spec_from_file_location('session_exports', HERE / 'export_session.py')
exports = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exports)
read, write, sha = exports.read, exports.write, exports.sha
sys.path.insert(0, str(REPO / 'level_generation/creatures'))
from exact_placement import validate_manifest
sys.path.insert(0, str(REPO / 'level_generation/creatures/mm6_remaining/redo_2x'))
from prepare_packed_outline import native_2x
from whole_animation_resolution import record_detail_policy, validate_policy
sys.path.insert(0, str(REPO / 'level_generation/creatures/mm6_remaining/acceptance_viewer'))
from serve import load_family

CONTEXT = ('TASK CONTEXT — MM7 FANTASY-GAME ASSET RESTORATION: This is an upscale and faithful restoration '
           'of an EXISTING Might and Magic VII (MM7) fantasy role-playing game sprite asset, using the supplied '
           'original animation bitmaps. Restore the existing fantasy-game character and its original animation; '
           'preserve its native costume, material coverage, anatomy and poses. The request is game-art restoration.')

def record(family):
    root, out = SESSION / family, SESSION / family / 'redo_2x'
    run, sources, manifest, registration = (read(p) for p in (
        out/'run.json', root/'sources.json', out/'manifest.json', out/'registration.json'))
    expected = set(sources['sources'])
    retained_names = {n for n,r in registration.items() if 'retained_from' in r}
    retained_jobs = [j for j in run['jobs'] if j.get('retained_restoration')]
    for job in retained_jobs:
        reuse = job['retained_restoration']
        assert reuse['user_authorization'] and not reuse['current_outline_return']
        previous = REPO / reuse['previous_project']
        old_acceptance = read(previous/'review/acceptance.json')
        assert old_acceptance['status'] == 'accepted'
        assert sha(REPO/reuse['previous_acceptance']['path']) == reuse['previous_acceptance']['sha256']
        for path,digest in old_acceptance['artifact_hashes'].items():
            assert sha(previous/path) == digest, path
        assert set(reuse['frames']) == set(job['frames'])
        for item in (reuse['source_raw'],reuse['source_prompt']):
            assert sha(REPO/item['original']) == item['original_sha256'] == sha(REPO/item['path']) == item['sha256']
        for name,files in reuse['frames'].items():
            row = registration[name]
            assert 'retained_from' in row and not row['raw_clip'] and min(row['effective_sampling_xy']) >= 2
            assert sha(REPO/row['raw_path']) == row['raw_sha256']
            assert sha(REPO/row['clean_path']) == row['clean_sha256']
            for item in files.values():
                assert sha(REPO/item['original']) == item['original_sha256']
            original = np.array(Image.open(REPO/files['master']['original']).convert('RGBA'))
            current = np.array(Image.open(out/f'aligned_2x/{name}.png').convert('RGBA'))
            assert original.shape == current.shape and np.array_equal(original[:,:,3],current[:,:,3])
            assert np.array_equal(original[original[:,:,3]>0],current[original[:,:,3]>0]), name
    represented = {name for job in run['jobs'] for name in job['frames']}
    assert represented == expected
    source_assets = list(sources['sources'].values()) + list(sources['palette_sources'].values()) + run['source_metadata']
    for item in source_assets:
        assert sha(REPO/item['path']) == item['sha256'], item['path']
    native = {n:native_2x(s,sources,sources['base_palette'])[0] for n,s in sources['sources'].items()}
    checkpoint = read(HERE/'reviewed_resume_paths.json')
    visual = checkpoint.get('family_decisions', {}).get(family, {})
    evidence_hashes = {p.split('/redo_2x/', 1)[1]: digest
        for p, digest in checkpoint.get('evidence_sha256', {}).items()
        if p.startswith(family+'/redo_2x/') and sha(SESSION/p) == digest}
    old_record = read(out/'review/acceptance.json')
    for path, digest in old_record.get('review_evidence', {}).items():
        if (out/path).exists() and sha(out/path) == digest:
            evidence_hashes.setdefault(path, digest)
    missing = sorted(expected-set(registration))
    approved = visual.get('accepted') is True
    available_reviewed = approved or visual.get('available_poses_reviewed') is True
    if approved:
        assert not missing, 'Family acceptance cannot include missing native art.'
    if available_reviewed:
        assert visual.get('review') and visual.get('independent_features')
        for registry in ('complete_placement', 'all_palette_mask'):
            info = read(out/f'review/{registry}.json')
            assert set(info['frames']) == set(registration)
            assert all(path in evidence_hashes for path in info['pages']), registry
        detail = read(out/'review/resume_detail_100pct.json')['evidence']
        reviewed_detail = {name for row in detail
            if evidence_hashes.get(row['path']) == row['sha256']
            and all(registration[name]['raw_sha256'] == row['raw_sha256'] for name in row['frames'])
            for name in row['frames']}
        assert reviewed_detail == set(registration), 'Missing 100% pose review: '+str(sorted(set(registration)-reviewed_detail))
        assert 'review/edge_closeups.png' in evidence_hashes
        for name in retained_names:
            registration[name]['review_status'] = 'accepted_after_current_static_visual_review'
        write(out/'registration.json',registration)
    issues = list(visual.get('unresolved_issues', []))
    if not available_reviewed:
        issues.append(dict(kind='pending_final_visual_review', finding='Every available pose still requires current 100% material/alpha, independent placement and all-palette/mask review.'))
    if missing:
        issues.append(dict(kind='blocked_native_art', frames=missing,
            jobs=[j['id'] for j in run['jobs'] if not j.get('selected_raw')],
            finding='User-requested attempts using previous successful prompts remain moderation blocked. No missing native art was substituted; the family remains partial.'))
    failure_record = read(root/'blocked_jobs.json')
    failures = failure_record['errors']
    resolved = failure_record.setdefault('resolved_errors', {})
    for job in run['jobs']:
        if job.get('selected_raw') and job['id'] in failures:
            resolved.setdefault(job['id'], []).append(failures.pop(job['id']))
    write(root/'blocked_jobs.json',failure_record)
    returned = 0
    for job in run['jobs']:
        assert (REPO/job['prompt']).read_text().startswith(CONTEXT)
        assert job['reference_roles'][:2] == ['untouched_native_complete_animation', 'outline_only_geometry_no_shading']
        for item in job['prepared_assets'] + [job['appearance_source']]:
            assert sha(REPO/item['path']) == item['sha256'], item['path']
        cw,ch = job['cell_native_size']
        packed = Image.open(REPO/job['references'][0]).convert('RGBA')
        assert packed.size == (job['columns']*cw*2,job['rows']*ch*2)
        crop = tuple(round(v*2) for v in job['native_crop'])
        for i,name in enumerate(job['frames']):
            x,y = i%job['columns']*cw*2,i//job['columns']*ch*2
            assert np.array_equal(np.array(packed.crop((x,y,x+cw*2,y+ch*2))),np.array(native[name].crop(crop)))
        guide = np.array(Image.open(REPO/job['references'][1]).convert('RGB'))
        assert np.isin(guide,[0,255]).all() and np.array_equal(guide[:,:,0],guide[:,:,1]) and np.array_equal(guide[:,:,1],guide[:,:,2])
        if job.get('selected_raw'):
            attempt = next(a for a in job['attempts'] if a['raw']==job['selected_raw'])
            assert sha(REPO/attempt['raw']) == attempt['sha256']
            assert sha(REPO/attempt['prompt']) == attempt['prompt_sha256']
            assert set(job['frames']) <= set(registration)
            job['status'] = 'validated_staged' if available_reviewed else 'returned_candidate_not_accepted'
            returned += 1
        else:
            assert job['id'] in failures
            error = failures[job['id']]
            job['status'] = 'blocked_moderation' if 'moderation_blocked' in error else 'blocked_usage_limit'
            job['failure'] = dict(error=error,automatic_retry=False,
                reason='Preserve the recorded tool block; do not bypass moderation or repeat known quota failures.')
        job['visual_acceptance'] = available_reviewed and bool(job.get('selected_raw') or job.get('retained_restoration'))
        job['latest_outline_return_accepted'] = available_reviewed and bool(job.get('selected_raw'))
        if job.get('retained_restoration'):
            job['retained_restoration_review'] = 'accepted_after_current_review' if available_reviewed else 'pending_current_review'
        if job.get('selected_raw'): job.pop('failure',None)
        job['review_issues'] = [issue for issue in issues if job['id'] in issue.get('jobs',[])]
    run.update(status=('validated_staged_with_reviewed_legacy_reuse' if retained_names else 'validated_staged') if approved else ('partial_reviewed_with_blocked_native_art' if available_reviewed else 'partial_with_pending_review'),accepted=approved,
        latest_method_complete=returned==len(run['jobs']) and not retained_names,
        coverage=dict(returned_sheets=returned,required_sheets=len(run['jobs']),exported_frames=len(registration),native_frames=len(expected),
            reused_sheets=len(retained_jobs),reused_frames=len(retained_names),
            covered_animation_views=returned+len(retained_jobs),latest_outline_frames=len(registration)-len(retained_names)),
        blockers=dict(usage_limit=sum('usage_limit_reached' in e for e in failures.values()),
            moderation=sum('moderation_blocked' in e for e in failures.values())))
    write(out/'run.json',run)
    if retained_jobs:
        run['legacy_reuse']['status'] = 'accepted_after_current_review' if available_reviewed else 'current_visual_review_pending'
        write(out/'legacy_reuse/provenance.json',run['legacy_reuse'])
        write(out/'run.json',run)
    assert not validate_manifest(manifest,registration)
    assert manifest['native_descriptor_animations'] == exports.native_animations(sources)
    assert manifest['native_group_bindings_full'] == sources['descriptor_bindings']
    assert manifest['native_groups'] == sources['groups']
    assert manifest['source_coverage']['missing'] == sorted(expected-set(registration))
    policy = read(out/'processing.json')['whole_animation_resolution_policy']
    full_native = exports.native_animations(sources)
    for job in run['jobs']:
        for binding in job['bindings']:
            animation = full_native[str(binding['descriptor'])][binding['action']]
            assert animation['native_group'] == binding['native_group']
            assert [s['frame'] for s in animation['directions'][str(binding['view'])]] == binding['native_frames']
    primary = full_native[str(sources['descriptor_rows'][0][0])]
    native_contract = dict(animations={action:dict(views=animation['directions']) for action,animation in primary.items()})
    validate_policy(policy,run,native_contract,registration)
    manifest['generated_detail']['measured_minimum'] = min(min(row['effective_sampling_xy']) for row in registration.values())
    record_detail_policy(manifest,policy,registration)
    manifest.update(quality_status=(('validated_staged_with_reviewed_legacy_reuse' if retained_names else 'validated_staged_complete_animation_below_target') if manifest['generated_detail']['below_target_frames'] or retained_names else 'validated_staged_complete_animation') if approved else ('partial_reviewed_with_blocked_native_art' if available_reviewed else 'partial_with_pending_review'),
        schema_status='Complete reviewed staged package' if approved else ('Reviewed partial staged package with blocked native art' if available_reviewed else 'Partial staged candidate'),visual_acceptance=approved,
        review_record='review/acceptance.json',review_issues=issues,sheet_coverage=run['coverage'],
        blocked_jobs={j['id']:j['status'] for j in run['jobs'] if not j.get('selected_raw')})
    manifest['generated_detail']['measurement_status'] = ('Independent visual review accepted anatomical sampling and restored material detail for every available frame; actual sampling remains separate from physical 2x export.' if available_reviewed else 'Provisional sampling; final visual gates pending. Physical exports are 2x.')
    if available_reviewed:
        manifest['limitations'] = [line for line in manifest['limitations'] if not line.startswith(('Anatomical scales',)) and (not approved or not line.startswith('Incomplete family:'))]
    manifest['latest_method_complete'] = run['latest_method_complete']
    if retained_names:
        manifest['limitations'].append('Three current outline jobs remain moderation blocked. Fifteen user-authorized older accepted generated frames complete native coverage; they do not constitute current outline returns.')
    exports.reviewer_regions(manifest,out)
    for i,page in enumerate(manifest['pages']):
        with Image.open(out/page['mask']) as atlas:
            for name,frame in manifest['frames'].items():
                if frame['page']!=i:continue
                x,y,w,h=frame['atlas_xywh']
                tile=atlas.crop((x,y,x+w,y+h))
                original=Image.open(out/f'trimmed_masks_2x/{name}.png')
                if original.mode=='L':
                    assert np.array_equal(np.array(tile.getchannel('R')),np.array(original))
                    assert tile.getchannel('G').getextrema()==(0,0) and tile.getchannel('B').getextrema()==(0,0)
                else:
                    assert np.array_equal(np.array(tile),np.array(original))
    write(out/'manifest.json',manifest)
    validation = read(out/'validation.json')
    validation.update(raw_cells_unclipped=True if available_reviewed else None,source_hashes_unchanged=True,submitted_native_rgba_exact=True,
        separate_outline_only_verified=True,full_native_bindings_exact=True,all_native_art_prepared=True,
        family_complete=approved,visual_acceptance_frozen=approved,available_pose_review_frozen=available_reviewed,actual_generated_detail_at_least_2x=(manifest['generated_detail']['measured_minimum']>=2) if available_reviewed else None,
        latest_method_complete=run['latest_method_complete'],reviewed_legacy_reuse_frames=len(retained_names),
        legacy_visible_master_pixels_exact=True if retained_names else None,
        minimum_actual_generated_sampling=manifest['generated_detail']['measured_minimum'],
        numerical_sampling_at_least_2x=manifest['generated_detail']['measured_minimum']>=2,
        generated_detail_visually_accepted=available_reviewed,packed_mask_channels_exact=True,
        memory_bytes=manifest['memory_bytes'])
    write(out/'validation.json',validation)
    evidence=[]
    for path in ('review/complete_placement.json','review/all_palette_mask.json'):
        info=read(out/path)
        assert set(info['frames'])==set(registration)
        evidence += info['pages']
        info['status']='accepted_after_static_visual_review' if available_reviewed else 'pending_final_visual_review'
        write(out/path,info)
    evidence += ['review/detail_alpha_100pct.png']
    if family=='mm7_m214':evidence += [f'review/hair_mask_review_{i}.png' for i in range(4)]
    if family=='mm7_m218':evidence += ['review/hit_0_alpha_detail_100pct.png']
    if family=='mm7_m230':evidence += ['review/standing_2_3_detail_100pct.png']
    checked=load_family(
        manifest['review_label'],out/'manifest.json','Latest packed outline candidate',manifest['quality_status'])
    paths=['manifest.json','sources.json','registration.json','validation.json','variants.json','run.json','processing.json']
    if retained_names:
        paths += ['legacy_reuse/material_protection.json','legacy_reuse/provenance.json']
    acceptance=dict(status=('accepted_with_reviewed_legacy_reuse' if retained_names else 'accepted') if approved else 'partial_not_accepted',accepted=approved,acceptance_frozen=approved,available_pose_review_frozen=available_reviewed,reviewer='Codex static visual review',
        latest_method_complete=run['latest_method_complete'],retained_generated_frames=sorted(retained_names),
        reviewed_utc=datetime.now(timezone.utc).isoformat(),coverage=run['coverage'],blockers=run['blockers'],
        artifact_sha256=checked.artifact_sha256,artifact_hashes={p:sha(out/p) for p in paths},
        review_evidence=evidence_hashes,
        visual_review=visual.get('review','Final visual review remains pending.'),
        independent_features=visual.get('independent_features',[]),
        checks=([visual['review'],
                 'Every available canonical pose inspected at 100% delivered pixels on dark and light backgrounds; independent native head, torso, limb, contact and equipment features checked.',
                 'Every available pose inspected in all native palettes and material masks; alpha edges and protected materials reviewed.',
                 'Native sources, unchanged submitted RGBA, separate outline-only guides, exact fractional native anchors, aliases, timing and mirrored bindings verified.',
                 'Base bypass, alpha, soft mask weights and identical atlas crop reconstruction verified for every native palette.',
                 'Static review only; no watched playback claimed. Staged only; not installed into gameplay.',
                 'Complete family acceptance frozen.' if approved else 'Available-frame review frozen; blocked native art prevents family acceptance.'] if available_reviewed else
            ['Current final visual review remains pending; no family acceptance is frozen.']),
        unresolved_issues=issues,missing_frames=manifest['source_coverage']['missing'],
        complete_detail_frames=(len(registration) if available_reviewed else None))
    write(out/'review/acceptance.json',acceptance)
    return dict(family=family,label=manifest['review_label'],descriptors=[dict(id=int(r[0]),label=r[1]) for r in sources['descriptor_rows']],
        status=acceptance['status'],accepted=approved,available_poses_reviewed=available_reviewed,**run['coverage'],blockers=run['blockers'],palettes=sources['palettes'],
        latest_method_complete=run['latest_method_complete'],
        unused_native=sorted(n for n,s in sources['sources'].items() if not s['referenced']),
        minimum_actual_generated_sampling=manifest['generated_detail']['measured_minimum'],
        manifest=str((out/'manifest.json').relative_to(SESSION)),acceptance=str((out/'review/acceptance.json').relative_to(SESSION)),
        blocked_jobs=str((root/'blocked_jobs.json').relative_to(SESSION)),unresolved_issues=issues)


if __name__=='__main__':
    families=[]
    for family in FAMILIES:
        row=record(family);families.append(row)
        print(json.dumps({k:row[k] for k in ('family','status','returned_sheets','required_sheets','exported_frames','native_frames')}),flush=True)
    exports.collection(FAMILIES)
    totals={key:sum(row[key] for row in families) for key in ('returned_sheets','required_sheets','exported_frames','native_frames','reused_sheets','reused_frames','covered_animation_views','latest_outline_frames')}
    complete = sum(row['accepted'] for row in families)
    latest_complete = sum(row['accepted'] and row['latest_method_complete'] for row in families)
    write(HERE/'session_status.json',dict(session='session_mm7_03',status=('complete_with_reviewed_legacy_reuse' if totals['reused_frames'] else 'complete') if complete==len(families) else 'partial_with_blocked_native_art',complete_families=complete,partial_families=8-complete,
        latest_method_complete_families=latest_complete,latest_method_partial_families=len(families)-latest_complete,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),totals=totals,
        blockers={key:sum(row['blockers'][key] for row in families) for key in ('usage_limit','moderation')},
        physical_export_scale=2,available_generated_detail_visually_reviewed=all(row['available_poses_reviewed'] for row in families),all_generated_sampling_at_least_2x=all(row['minimum_actual_generated_sampling']>=2 for row in families),installed_into_gameplay=False,
        review_collection='mm7_m214/review_collection.json',families=families))
