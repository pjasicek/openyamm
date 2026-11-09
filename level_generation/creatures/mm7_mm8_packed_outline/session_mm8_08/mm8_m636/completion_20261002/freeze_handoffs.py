"""Freeze the two locally reviewed repairs; never change inherited packages."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import html
import json

REPO = Path(__file__).resolve().parents[6]
BASE = REPO / 'level_generation/creatures/mm7_mm8_packed_outline'
AIR = BASE / 'session_mm7_02/mm7_m508/completion_20261002'
FISH = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(package, value):
    path = Path(value)
    if path.is_absolute():
        return path
    if (REPO / path).is_file():
        return REPO / path
    return package / path


def rel(path):
    return str(path.resolve().relative_to(REPO))


def make_index(package, title, text, inherited=None):
    groups = [('Pose and independent placement review', '*placement*.png'),
              ('Every final pose', '*all_poses.png'),
              ('Every palette and material mask', '*palettes_masks*.png'),
              ('Every palette and material mask', 'palette_masks*.png'),
              ('Material and alpha at 100%', '*100pct*.png'),
              ('Raw alpha composites', '*dark*.png')]
    body = ['<!doctype html><html lang="en"><meta charset="utf-8">',
            '<title>' + html.escape(title) + '</title>',
            '<style>body{font:16px system-ui;max-width:1000px;margin:40px auto;background:#232725;color:#eee8dc}'
            'a{color:#7ddbd3}li{margin:6px 0}p{line-height:1.5}</style>',
            '<h1>' + html.escape(title) + '</h1><p>' + html.escape(text) + '</p>',
            '<p>Review consists of static pose contacts and material/edge patches at original pixel scale. '
            'Timed playback was not watched. This is a local handoff; no gameplay installation.</p>',
            '<p><a href="../manifest.json">Complete manifest</a> · '
            '<a href="acceptance.json">Frozen acceptance</a> · '
            '<a href="actual_attachment_provenance.json">Actual image attachments</a> · '
            '<a href="final_validation.json">Export and placement checks</a></p>']
    used = set()
    for label, pattern in groups:
        files = [p for p in sorted((package / 'review').glob(pattern)) if p.name not in used]
        if not files:
            continue
        used.update(p.name for p in files)
        body.append('<h2>' + label + '</h2><ul>')
        body.extend('<li><a href="' + html.escape(p.name) + '">' + html.escape(p.name) + '</a></li>'
                    for p in files)
        body.append('</ul>')
    if inherited:
        body.append('<h2>Preserved earlier acceptance</h2><p><a href="' + inherited + '">'
                    'The earlier 131-pose acceptance and its review evidence</a></p>')
    body.append('</html>')
    (package / 'review/index.html').write_text('\n'.join(body) + '\n')


for package in [AIR, FISH]:
    if (package / 'review/acceptance.json').exists():
        raise SystemExit('Refusing to overwrite frozen acceptance: ' + str(package))

now = datetime.now(timezone.utc).isoformat()
rejected = FISH / 'review/rejected_death0_v2'
rejected.mkdir(exist_ok=True)
for name in ['m636dh0_independent.png', 'm636di0_independent.png', 'm636dj0_independent.png',
             'death0_return_partitions.png', 'death_0_raw_composite.png']:
    path = FISH / 'review' / name
    if path.exists():
        path.rename(rejected / name)
(rejected / 'README.md').write_text(
    'These are rejected version-2 diagnostics. The returned sheet omitted four fish in each of its '
    'last four schools. They do not describe the accepted version-3 death animation. '
    'See ../death_0_sheet_all_poses.png for all ten accepted twelve-fish schools.\n')
write(FISH / 'review/processing_attempts.json', {
    'status': 'resolved', 'final_processing_session': 64481,
    'attempts': [
        {'stage': 'initial candidate', 'status': 'rejected_visual_review',
         'reason': 'Single-body cell seeds assigned fish components to adjacent schools.'},
        {'session': 16328, 'status': 'failed_extraction',
         'reason': 'Death view 0 component/cell assignment rejected; candidate not accepted.'},
        {'session': 61144, 'status': 'failed_extraction',
         'reason': 'Unused death view 3 component/cell assignment rejected; candidate not accepted.'},
        {'session': 5441, 'status': 'rejected_visual_review',
         'reason': 'Component ownership fixed, but death version 2 still omitted four fish in each final school.'},
        {'session': 64481, 'status': 'accepted_after_visual_review',
         'reason': 'Version 3 death has all twelve fish in every native pose; all 130 final poses reviewed.'}
    ]})

for package in [AIR, FISH]:
    manifest = read(package / 'manifest.json')
    run_names = ['run.json', 'full_run.json'] if package == AIR else ['run.json']
    for name in run_names:
        run = read(package / name)
        for job in run['jobs']:
            selected = job.get('selected_raw')
            if selected is None:
                candidates = [a for a in job['attempts'] if a.get('status', '').startswith('accepted')]
                if len(candidates) != 1:
                    raise ValueError('Ambiguous accepted raw for ' + job['id'])
                selected = candidates[0].get('raw', candidates[0].get('raw_path'))
                job['selected_raw'] = selected
            matched = 0
            for attempt in job['attempts']:
                raw = attempt.get('raw_path', attempt.get('raw'))
                if raw and resolve(package, raw).resolve() == resolve(package, selected).resolve():
                    attempt.setdefault('previous_status', attempt['status'])
                    attempt['status'] = 'accepted_whole_sheet'
                    attempt['review_status'] = 'accepted_static_pose_material_alpha_palette_placement_review'
                    attempt['review_record'] = rel(package / 'review/acceptance.json')
                    matched += 1
                elif attempt.get('rejection_reason') or attempt.get('review_failure'):
                    attempt['status'] = 'failed_visual_review'
            assert matched == 1, (job['id'], matched)
            job['status'] = 'accepted_whole_sheet'
            job['selected_raw_accepted'] = True
            job['final_review'] = 'accepted; complete native cycle, matching outline actually attached'
        run['status'] = 'accepted_complete_local'
        run['installed'] = False
        run['review_record'] = 'review/acceptance.json'
        write(package / name, run)

    registration = read(package / 'registration.json')
    if package == FISH:
        features = read(package / 'review/independent_fish_features.json')
        assert set(features) == set(registration)
        for frame, record in registration.items():
            record['review_status'] = 'accepted'
            record['independent_placement_review'] = 'passed_static_visual_correspondence'
            record['independent_placement_features'] = features[frame]
            record['independent_placement_evidence'] = 'review/' + record['batch'] + '_all_poses.png'
            record['placement_review_notes'] = (
                'Upper and rightmost actual fish bodies, their head/tail orientation, subgroup spacing and full '
                'school arrangement inspected against native. Markers are diagnostics, not fitted transforms; '
                'overlapping native bodies require visual identity judgment.')
    else:
        for record in registration.values():
            if record.get('batch') in {j['id'] for j in read(package / 'run.json')['jobs']}:
                record['review_status'] = 'accepted'
                record['independent_placement_review'] = 'passed_static_actual_anatomy_review'
    write(package / 'registration.json', registration)

    processing = read(package / 'processing.json')
    processing['status'] = 'accepted_after_complete_static_visual_review'
    processing['timed_playback_viewed'] = False
    processing['review_record'] = 'review/acceptance.json'
    write(package / 'processing.json', processing)
    checks = read(package / 'review/export_checks.json')
    checks.update(visual_review_complete=True, animation_review_complete=True, timed_playback_viewed=False,
                  review_method='Every static pose, independent actual-art features, every native palette/mask, '
                                '100% material and alpha patches; exact native animation metadata validation')
    write(package / 'review/export_checks.json', checks)
    manifest['viewer'] = 'review/index.html'
    manifest['review_record'] = 'review/acceptance.json'
    manifest['installed'] = False
    write(package / 'manifest.json', manifest)

make_index(AIR, 'Air Elemental — complete 160-pose handoff',
           'All 160 native images, including 20 unused images, are restored. Five repaired whole-sheet jobs '
           'supply 29 new poses; 131 previously accepted poses remain unchanged. '
           'The new attack view samples at about 1.76x; the whole family minimum is 1.711x. '
           'Physical masters are 2x.', '../../redo_2x/review/acceptance.json')
make_index(FISH, 'School of Fish — complete 130-pose handoff',
           'All 130 unique native images, including 44 unused images, are restored. '
           'All fifteen swim poses at each stored view are on one complete returned sheet. '
           'The final death sheet retains all twelve fish in every pose. Actual generated sampling '
           'has a 1.335x minimum; physical masters are 2x. All three native palettes were inspected.')
(AIR / 'README.md').write_text(
    '# Air Elemental complete local handoff\n\n'
    'Use `manifest.json` and `review/acceptance.json` in this directory. They cover all 160 native images '
    'for MM8 descriptors 82–84 and the shared MM7 family, with original world-specific bindings intact. '
    'The older `redo_2x` package remains a preserved 131-pose checkpoint.\n\n'
    'The five new complete sheets restore walk view 0, attack view 1 and unused death views 2–4. '
    'Native colour, its matching separate outline PNG and detailed same-family art were actually attached '
    'on every selected imagegen call. Attachment paths, roles, SHA-256 hashes and recovered historical '
    'dispatch evidence are in `review/actual_attachment_provenance.json` and '
    '`review/inherited_actual_attachment_provenance.json`.\n\n'
    'All poses have checked 2x physical masters, RGBA/R8 atlases, palette 508 and exact fractional placement '
    'and native animation metadata. The new attack sheet has about 1.76x actual generated sampling; '
    'the full family minimum is 1.711x. These were accepted after review under whole-cycle priority. '
    'No sheet was split or regenerated solely to reach 2x. All 20 unused images remain archival art.\n\n'
    'Review evidence is indexed in `review/index.html`. Static poses, independent anatomical features, '
    'material detail at 100%, soft alpha edges and every palette/mask pose were inspected. '
    'Timed playback was not watched. No gameplay installation or shared-file edits.\n')
(FISH / 'README.md').write_text(
    '# School of Fish complete local handoff\n\n'
    'Use `manifest.json` and `review/acceptance.json` in this directory: all 130 unique native images '
    'for MM8 descriptors 178–180 are accepted. Older partial outputs remain preserved. '
    'Fifteen complete whole-sheet jobs cover every stored animation and unused-art cycle. '
    'The five stored swim views each retain all fifteen native poses; the death cycle retains '
    'all ten twelve-fish schools. Native corpse/death aliases and original playback bindings are exact.\n\n'
    'Three repaired swim sheets and the repaired death sheet used built-in imagegen with the actual '
    'native colour, matching separate outline PNG and adequate same-family appearance PNG attached in '
    'that order. Historical corpse generation established the first adequate appearance using native '
    'and outline inputs; its bootstrap exception is recorded. All selected and failed attempts, '
    'actual input paths, roles and hashes are in `run.json` and `review/actual_attachment_provenance.json`.\n\n'
    'A family-local extractor keeps entire fish components with their own school, including when '
    'transparent grid gutters are irregular. It removes reviewed alpha 1–8 scatter, then applies one '
    'uniform whole-cycle scale and rigid whole-school translation. It does not move individual fish, '
    'warp anatomy or impose a native alpha stencil. Rejected version-2 death diagnostics are under '
    '`review/rejected_death0_v2/`; the accepted version-3 result restores the omitted lower fish.\n\n'
    'Checked 2x physical masters, base/mask atlases, exact metadata and all native 636/637/638 palettes '
    'are exported. Actual generated sampling has a 1.335x minimum, accepted after review under '
    'whole-cycle priority. All 44 unused images are included without adding them to playback.\n\n'
    'All 130 poses, independent fish placement features, all 390 palette variants and every mask '
    'were inspected. Material and atlas alpha patches for every pose were inspected at 100% '
    'on dark/ivory backgrounds. `review/index.html` indexes this evidence. Timed playback was '
    'not watched. No gameplay installation or shared-file edits.\n')

for package in [AIR, FISH]:
    manifest = read(package / 'manifest.json')
    provenance = read(package / 'review/actual_attachment_provenance.json')
    validation = read(package / 'review/final_validation.json')
    assert validation['status'] == provenance['status'] == 'passed'
    assert validation['frames'] == len(manifest['frames'])
    sampling = manifest.get('actual_generated_detail', manifest.get('generated_detail'))
    source = read(package / 'sources.json')
    # The local artifacts and every external selected input/raw are hash-bound.
    artifacts = {rel(p): sha(p) for p in sorted(package.rglob('*'))
                 if p.is_file() and '__pycache__' not in p.parts and p.name != 'acceptance.json'}
    for job in provenance['selected_attempts']:
        for item in job['submitted_inputs']:
            path = resolve(package, item['path'])
            assert sha(path) == item['sha256']
            artifacts[rel(path)] = item['sha256']
    fullrun = read(package / ('full_run.json' if package == AIR else 'run.json'))
    for job in fullrun['jobs']:
        raw = resolve(package, job['selected_raw'])
        artifacts[rel(raw)] = sha(raw)
    for frame in manifest['frames'].values():
        path = resolve(package, frame['physical_master'])
        artifacts[rel(path)] = sha(path)
    for page in manifest['pages']:
        for field in ['base', 'mask']:
            path = resolve(package, page[field])
            artifacts[rel(path)] = sha(path)
    inherited = {}
    if package == AIR:
        previous_path = package.parent / 'redo_2x/review/acceptance.json'
        previous = read(previous_path)
        verified = read(package / 'review/merge_validation.json')['inherited_accepted_artifacts_verified']
        for name, expected in verified.items():
            path = REPO / name
            assert sha(path) == expected, str(path)
            inherited[rel(path)] = expected
        prior = {'path': rel(previous_path), 'sha256': sha(previous_path),
                 'accepted_poses_preserved': 131, 'verified_artifact_count': len(inherited)}
        newposes = sorted(read(package / 'draft_manifest.json')['frames'])
        detail = ('Cloud head, hand and wrist ownership, torso lean and vortex tail checked in every new pose; '
                  'opening death raised-hand features checked independently. Fine vapor filaments and natural '
                  'grey shading retained; no copied guide bands. Soft alpha edges clean on dark and light.')
    else:
        prior = None
        newposes = sorted(manifest['frames'])
        detail = ('All fish, head/tail orientation, native subgroup spacing and school movement checked in every '
                  'pose. Final death cycle preserves all twelve fish throughout. Fine scales, gills and fin rays, '
                  'natural orange contrast and all palette/mask poses inspected. Clean alpha on dark and light.')
    acceptance = {
        'schema_version': 1, 'family': 'mm8_air_elemental' if package == AIR else 'mm8_school_of_fish',
        'status': 'accepted_complete_latest_packed_outline', 'frozen': True, 'complete': True,
        'local_final_acceptance': True, 'frozen_utc': now,
        'reviewer': 'Codex static visual review; no separate user approval claimed',
        'coverage': manifest['coverage'], 'whole_sheet_jobs': len(fullrun['jobs']),
        'full_latest_imagegen_method_coverage': True,
        'actual_submitted_attachment_provenance': 'review/actual_attachment_provenance.json',
        'sampling': sampling, 'prior_acceptance': prior,
        'visual_review': {'method': 'Every final pose, independent actual-art placement features, every palette/mask '
                                   'pose, original-scale material and atlas-alpha patches; retained earlier accepted '
                                   'Air poses inherit their unchanged review.',
                          'new_pose_coverage': newposes, 'material_anatomy_placement_findings': detail,
                          'palette_ids': [508] if package == AIR else [636, 637, 638],
                          'timed_playback_viewed': False,
                          'evidence_index': 'review/index.html',
                          'unused_art_added_to_playback': False},
        'validation': validation,
        'installed': False, 'shared_tools_skills_global_ledgers_runtime_assets_modified': False,
        'artifact_sha256_path_base': 'repository_root', 'artifact_sha256': artifacts,
        'inherited_artifact_sha256': inherited}
    write(package / 'review/acceptance.json', acceptance)
    write(package.parent / 'current_handoff_20261002.json', {
        'status': acceptance['status'], 'manifest': rel(package / 'manifest.json'),
        'manifest_sha256': sha(package / 'manifest.json'),
        'acceptance': rel(package / 'review/acceptance.json'),
        'acceptance_sha256': sha(package / 'review/acceptance.json'),
        'coverage': manifest['coverage'], 'installed': False})
    print(package.parent.name, 'frozen', len(manifest['frames']), 'poses;', len(artifacts),
          'artifact hashes;', len(inherited), 'unchanged inherited artifact hashes')
