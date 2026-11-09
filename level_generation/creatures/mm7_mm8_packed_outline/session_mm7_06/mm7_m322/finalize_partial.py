"""Artifact-bound local completion gate and shared reviewer index for session 06."""
import datetime
import html
import os
import re
import numpy as np
from PIL import Image
from scipy import ndimage
import session_workflow as workflow


def verify_inputs(root, run, sources):
    for entry in list(sources['sources'].values()) + sources['group_sources'] + list(sources['palette_sources'].values()):
        assert workflow.sha(workflow.REPO / entry['path']) == entry['sha256'], entry['path']
    descriptor = workflow.REPO / 'assets_dev/engine/data_tables/monster_descriptors.txt'
    assert workflow.sha(descriptor) == run['source_descriptor_sha256']
    rows = {line.split('\t')[0]: line.split('\t') for line in descriptor.read_text().splitlines()}
    assert all(rows[row[0]] == row for row in sources['descriptor_rows'])
    old_hashes = workflow.read(root / 'review/prior_artifact_hashes.json')
    assert all(workflow.sha(workflow.REPO / path) == digest for path, digest in old_hashes.items())
    seen = set()
    for job in run['jobs']:
        prompt = workflow.REPO / job['prompt']
        assert prompt.read_text().startswith(workflow.CONTEXT)
        for entry in job['prepared_assets']:
            assert workflow.sha(workflow.REPO / entry['path']) == entry['sha256']
        colour = Image.open(workflow.REPO / job['references'][0]).convert('RGBA')
        outline = Image.open(workflow.REPO / job['references'][1]).convert('RGB')
        reference_scale = job.get('reference_scale',2)
        w, h = [int(value * reference_scale) for value in job['cell_native_px']]
        assert colour.size == outline.size == (w*job['columns'], h*job['rows'])
        crop = [int(value*2) for value in job['native_union_crop']]
        for index, name in enumerate(job['frames']):
            native, _ = workflow.native_2x(sources['sources'][name], sources, sources['base_palette'])
            expected = native.crop(crop)
            if reference_scale != 2:
                expected = expected.resize((w,h),Image.Resampling.NEAREST)
            x, y = index % job['columns'] * w, index // job['columns'] * h
            piece = colour.crop((x,y,x+w,y+h))
            assert np.array_equal(np.asarray(piece), np.asarray(expected)), (job['id'], name)
            inside = np.asarray(expected)[::reference_scale,::reference_scale,3] > 0
            boundary = inside & ~ndimage.binary_erosion(inside, structure=np.ones((3,3),bool))
            guide = np.full((*inside.shape,3),255,np.uint8)
            guide[boundary] = 0
            assert np.array_equal(np.asarray(outline.crop((x,y,x+w,y+h)))[::reference_scale,::reference_scale],guide)
            seen.add(name)
        for attempt in job['attempts']:
            assert workflow.sha(workflow.REPO / attempt['prompt']) == attempt['prompt_sha256']
            assert (workflow.REPO / attempt['prompt']).read_text().startswith(workflow.CONTEXT)
            for entry in attempt['references']:
                assert workflow.sha(workflow.REPO / entry['path']) == entry['sha256']
            if attempt.get('path'):
                assert workflow.sha(workflow.REPO / attempt['path']) == attempt['sha256']
    assert seen == set(sources['sources'])
    return dict(native_sources_and_palettes_unchanged=True, current_descriptors_unchanged=True,
                prior_project_artifacts_unchanged=True, prior_artifact_count=len(old_hashes),
                all_native_colour_sheets_exact=True, all_separate_outline_sheets_exact=True,
                complete_job_inventory=True, all_prompt_and_raw_hashes_verified=True)


def run(freeze=False):
    records = []
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    checks = ('source_hashes_unchanged','raw_cells_unclipped','exact_crop_reconstruction',
              'exact_atlas_extraction','base_bypass_exact','variant_alpha_unchanged','mask_weights_valid',
              'native_group_timings_and_flags_preserved','exact_native_anchors',
              'native_descriptor_bindings_verified','unused_art_retained_without_playback')
    for number in workflow.FAMILIES:
        family = f'mm7_m{number}'
        root = workflow.SESSION/family
        source, jobs, manifest, validation = [workflow.read(root/name) for name in
            ('sources.json','run.json','manifest.json','validation.json')]
        provenance = verify_inputs(root,jobs,source)
        evidence = workflow.read(root/'review/evidence_pages.json')
        log = workflow.read(root/'review/visual_log.json')['inspected']
        evidence_paths = [workflow.REPO/p for k in ('base_pose_pages','delivered_detail_pages','palette_mask_pages')
                          for p in evidence[k]] + [root/'review/edge_closeups.png',root/'review/death_0_sheet_poses.png']
        if number in (332,342,352):
            evidence_paths += sorted((root/'review').glob('palette_detail_100_*.png'))
        if number == 372:
            evidence_paths.append(root/'review/corpse_0_sheet_poses.png')
        assert set(evidence['frames']) == set(manifest['frames'])
        pending = [workflow.rel(p) for p in evidence_paths if workflow.rel(p) not in log or
                   log[workflow.rel(p)]['sha256'] != workflow.sha(p)]
        active = [j for j in jobs['jobs'] if j.get('selected_raw')]
        blocked = [dict(id=j['id'], native_frames=j['frames'],reason=j['attempts'][-1].get(
            'review_reason',j['attempts'][-1].get('reason','Missing complete sheet'))) for j in jobs['jobs']
            if not j.get('selected_raw')]
        decision_path = root/'review/visual_decision.json'
        decision = workflow.read(decision_path) if decision_path.exists() else {'passed':False,'issues':['Final visual decision pending.']}
        issues = list(decision.get('issues',[]))
        issues += [f'Current evidence needs inspection: {p}' for p in pending]
        if blocked:
            issues.append('Missing/rejected complete animation sheet(s).')
        if not validation['family_complete']:
            issues.append('Incomplete native bitmap coverage.')
        assert all(validation[k] is True for k in checks)
        coverage = dict(expected=len(source['sources']),exported=len(manifest['frames']),
            missing=sorted(set(source['sources'])-set(manifest['frames'])),
            unexpected=sorted(set(manifest['frames'])-set(source['sources'])))
        assert not coverage['missing'] and not coverage['unexpected']
        banner = (f'<p id="session-status" style="border:1px solid #d8ac62;padding:12px">'
                  f'{coverage["exported"]}/{coverage["expected"]} native bitmaps exported from '
                  f'{len(active)}/{len(jobs["jobs"])} complete sheets. '
                  '<a href="review/acceptance.json">Local acceptance and limitations</a>. Staged assets; not installed.</p>')
        viewer = root/'viewer.html'
        content = re.sub(r'<p id="session-(?:partial|status)".*?</p>','',viewer.read_text(),flags=re.S)
        content = content.replace('<h1 id="title"></h1>','<h1 id="title"></h1>'+banner)
        content = content.replace('href="review/all_comparison.png">All native/base poses',
            f'href="../mm7_m322/review/session_index.html#{family}">All pose and palette evidence')
        if content != viewer.read_text():
            viewer.write_text(content)
        browser_path = root/'review/browser_check.json'
        browser = workflow.read(browser_path) if browser_path.exists() else {}
        browser_passed = browser.get('status')=='passed' and browser.get('viewer_sha256')==workflow.sha(viewer)
        complete = freeze and decision['passed'] and not issues and browser_passed
        if freeze and decision['passed']:
            assert not pending, (family,pending)
            for path,digest in decision['artifact_hashes'].items():
                assert workflow.sha(workflow.REPO/path)==digest, (family,path,'Changed after visual decision')
            assert browser_passed, (family,'Current reviewer browser check required')
        validation['visual_acceptance_frozen'] = complete
        workflow.write(root/'validation.json',validation)
        if complete:
            for job in jobs['jobs']:
                job['status']='accepted_complete_sheet'
                for attempt in job['attempts']:
                    if attempt.get('path') == job['selected_raw']:
                        attempt['status']='accepted'
            workflow.write(root/'run.json',jobs)
        attempts = [a for j in jobs['jobs'] for a in j['attempts']]
        workflow.write(root/'review/blocked_jobs.json',dict(family=family,recorded_utc=now,
            blocked_jobs=blocked,current_visual_issues=issues,
            rule='Submit and return one complete native animation/view sheet; retain failed/rejected history.'))
        paths = [root/name for name in ('sources.json','manifest.json','registration.json','variants.json',
            'config.json','validation.json','run.json','review/evidence_pages.json','review/visual_log.json',
            'review/edge_audit.json','review/blocked_jobs.json','viewer.html')]
        paths += [root/'processing.json'] if (root/'processing.json').exists() else []
        paths += [root/'review/material_protection.json'] if (root/'review/material_protection.json').exists() else []
        paths += [decision_path] if decision_path.exists() else []
        paths += evidence_paths
        if browser_passed:
            paths += [browser_path]
        for name in manifest['frames']:
            paths += [root/directory/f'{name}.png' for directory in
                ('aligned_2x','masks_2x','trimmed_2x','trimmed_masks_2x','cleaned')]
        paths += [p for p in (root/'atlas').rglob('*') if p.is_file()]
        for job in active:
            paths += [workflow.REPO/job['selected_raw'],root/f'review/{job["id"]}/registration_candidates.json']
            paths += list((root/f'review/{job["id"]}').glob('*__step_*.png'))
        hashes = {workflow.rel(p):workflow.sha(p) for p in paths}
        record = dict(schema_version=1, family=family,label=workflow.read(root/'inventory.json')['label'],
            reviewer='Codex visual inspection',recorded_utc=now,status='complete_accepted' if complete else 'partial_unaccepted',
            complete=complete,frozen=complete,installed=False,physical_export_tier=2,
            merged_descriptor_ids=sorted(map(int,source['descriptor_bindings'])),coverage=coverage,
            whole_sheet_jobs=dict(expected=len(jobs['jobs']),selected=len(active),blocked=len(blocked),
                original_returned=sum(bool(a.get('path')) for a in attempts),
                historical_failed=sum(a['status']=='failed' for a in attempts),
                historical_quality_rejected=sum(a['status']=='rejected' for a in attempts)),
            generated_detail=manifest['generated_detail'],native_palettes=source['palettes'],
            unused=dict(expected=len(source['unreferenced']),exported=sum(n in manifest['frames'] for n in source['unreferenced']),
                inserted_into_playback=False),
            visual_review=dict(method='Static native/restored pose contacts, unresized 100% detail, light/dark edges and all palette/mask poses. No timed playback acceptance claimed.',
                independent_features=decision.get('independent_features','Pending'),
                notes=decision.get('notes',[]),issues=issues,
                all_current_evidence_inspected=not pending,evidence_hash_log=workflow.rel(root/'review/visual_log.json')),
            numerical_checks=validation,provenance_checks=provenance,artifact_hashes=hashes,
            reviewer_browser_check=browser if browser_passed else None,
            acceptance_blockers=issues + ([] if browser_passed else ['Current shared reviewer browser check pending.']),
            limitation='Enhanced material detail and palette ramp fits interpret original pixel art. Later changes require affected review and reacceptance.')
        workflow.write(root/'review/acceptance.json',record)
        workflow.write(root/'review/visual_progress.json',record['visual_review'])
        records.append(record)
    index_root = workflow.SESSION/'mm7_m322/review'
    totals = dict(complete_families=sum(r['complete'] for r in records),partial_families=sum(not r['complete'] for r in records),
        expected_native_bitmaps=sum(r['coverage']['expected'] for r in records),
        exported_native_bitmaps=sum(r['coverage']['exported'] for r in records),
        expected_whole_sheets=sum(r['whole_sheet_jobs']['expected'] for r in records),
        selected_whole_sheets=sum(r['whole_sheet_jobs']['selected'] for r in records),
        current_blocked_sheets=sum(r['whole_sheet_jobs']['blocked'] for r in records),
        historical_failed_calls=sum(r['whole_sheet_jobs']['historical_failed'] for r in records),
        historical_quality_rejected=sum(r['whole_sheet_jobs']['historical_quality_rejected'] for r in records),
        minimum_generated_sampling=min(r['generated_detail']['measured_minimum'] for r in records),
        native_palette_appearances=sum(len(r['native_palettes']) for r in records),
        unused_native_bitmaps=sum(r['unused']['expected'] for r in records),
        unused_exported_bitmaps=sum(r['unused']['exported'] for r in records),
        shared_reviewers_browser_checked=sum(bool(r['reviewer_browser_check']) for r in records))
    workflow.write(index_root/'session_status.json',dict(recorded_utc=now,
        status='complete_accepted' if all(r['complete'] for r in records) else 'partial_unaccepted',totals=totals,
        family_records=[workflow.rel(workflow.SESSION/r['family']/'review/acceptance.json') for r in records],
        scope='Assigned session family folders only; native and older projects unchanged. No gameplay installation or global ledger update.'))
    content = ['<!doctype html><meta charset="utf-8"><title>MM7 session 06 restoration review</title>',
        '<style>body{font:16px system-ui;max-width:1100px;margin:32px auto;background:#252725;color:#eee}'
        'a{color:#bce1ff}td,th{padding:8px;text-align:left;border-bottom:1px solid #666}section{margin:30px 0}</style>',
        '<h1>MM7 session 06 restoration review</h1>',
        f'<p>{totals["complete_families"]} complete families; {totals["partial_families"]} partial. '
        f'{totals["exported_native_bitmaps"]}/{totals["expected_native_bitmaps"]} native bitmaps exported at 2× physical tier from '
        f'{totals["selected_whole_sheets"]}/{totals["expected_whole_sheets"]} complete native action/view sheets. '
        f'Minimum measured generated detail: {totals["minimum_generated_sampling"]:.3f}×. '
        f'{totals["unused_exported_bitmaps"]} unused bitmaps retained outside playback. '
        f'{totals["native_palette_appearances"]} native palette appearances. No gameplay installation.</p>',
        '<p>Shared MM7 reviewer supports exact native placement, descriptor/palette bindings, actions, eight views, frame slider, zoom, backgrounds and material masks. '
        'Contacts provide the static visual acceptance evidence; functional browser checks do not claim timed playback review.</p>',
        '<p><a href="session_status.json">Session status</a></p><table><tr><th>Family</th><th>Acceptance</th><th>Native exports</th><th>Sheets</th><th>Generated detail</th><th>Reviewer</th></tr>']
    for r in records:
        family=r['family'];cov=r['coverage'];jobs=r['whole_sheet_jobs']
        content.append(f'<tr><td><a href="#{family}">{html.escape(r["label"])}</a> ({family})</td><td>{r["status"]}</td>'
            f'<td>{cov["exported"]}/{cov["expected"]}</td><td>{jobs["selected"]}/{jobs["expected"]}</td>'
            f'<td>{r["generated_detail"]["measured_minimum"]:.3f}×</td><td><a href="../../{family}/viewer.html">Open reviewer</a></td></tr>')
    content.append('</table>')
    for r in records:
        family=r['family'];root=workflow.SESSION/family
        content.append(f'<section id="{family}"><h2>{html.escape(r["label"])}</h2><p>{html.escape(r["visual_review"]["independent_features"])}</p>'
            f'<p><a href="../../{family}/review/acceptance.json">Acceptance record</a> · '
            f'<a href="../../{family}/review/blocked_jobs.json">Blocked sheets</a> · '
            f'<a href="../../{family}/manifest.json">Placement/animation metadata</a> · '
            f'<a href="../../{family}/review/browser_check.json">Browser check</a></p>')
        for issue in r['acceptance_blockers']:
            content.append('<p><strong>Unresolved:</strong> '+html.escape(issue)+'</p>')
        for note in r['visual_review']['notes']:
            content.append('<p>'+html.escape(note)+'</p>')
        evidence=workflow.read(root/'review/evidence_pages.json')
        for key,label in [('base_pose_pages','Native/base poses'),('delivered_detail_pages','100% material detail'),
                          ('palette_mask_pages','Every palette/mask pose')]:
            links=['<a href="'+html.escape(os.path.relpath(workflow.REPO/p,index_root))+'">Page '+str(i+1)+'</a>'
                   for i,p in enumerate(evidence[key])]
            content.append('<p>'+label+': '+' · '.join(links)+'</p>')
        content.append(f'<p><a href="../../{family}/review/edge_closeups.png">Light/dark alpha edges</a></p></section>')
    (index_root/'session_index.html').write_text('\n'.join(content)+'\n')
    print(totals)


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--freeze',action='store_true')
    run(parser.parse_args().freeze)
