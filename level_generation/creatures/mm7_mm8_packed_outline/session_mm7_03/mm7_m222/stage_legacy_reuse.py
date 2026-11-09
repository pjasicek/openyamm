"""Stage the fifteen user-authorized older generated frames after current imagegen failures.

The previous accepted package remains immutable. Its original high-detail cleaned
masters and exact physical exports are copied, with SHA-bound generation provenance.
These copies remain candidates until current placement, detail and palette review.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil

REPO = Path.cwd().resolve()
HERE = Path(__file__).resolve().parent
OUT = HERE / 'redo_2x'
PREVIOUS = REPO / 'level_generation/creatures/mm7_m222'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copied(path, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    assert sha(path) == sha(target)
    return dict(original=str(path.relative_to(REPO)), original_sha256=sha(path),
        path=str(target.relative_to(REPO)), sha256=sha(target))


def stage():
    acceptance = read(PREVIOUS / 'review/acceptance.json')
    assert acceptance['status'] == 'accepted'
    for path, digest in acceptance['artifact_hashes'].items():
        assert sha(PREVIOUS / path) == digest, path
    run = read(OUT / 'run.json')
    registration = read(OUT / 'registration.json')
    previous_registration = read(PREVIOUS / 'registration.json')
    batches = read(PREVIOUS / 'batches.json')
    generation = read(PREVIOUS / 'generation.json')
    old_sources = read(PREVIOUS / 'sources.json')
    sources = read(HERE / 'sources.json')
    legacy = OUT / 'legacy_reuse'
    archive = legacy / 'latest_outline_partial_before_reuse'
    archive.mkdir(parents=True, exist_ok=True)
    for name in ('run.json', 'registration.json', 'manifest.json', 'validation.json', 'review/acceptance.json'):
        target = archive / name
        if not target.exists():
            copied(OUT / name, target)
    retained = {}
    for job in run['jobs']:
        if job.get('selected_raw'):
            continue
        assert job['id'] in ('standing_3_sheet', 'attack_4_sheet', 'hit_4_sheet')
        batch = previous_registration[job['frames'][0]]['batch']
        selected = generation['batches'][batch]['selected']
        attempt = next(a for a in generation['batches'][batch]['attempts'] if a['raw']['path'] == selected)
        assert attempt['accepted'] is True
        assert set(job['frames']) <= set(batches[batch]['frames'])
        if batch != 'standing':
            assert job['frames'] == batches[batch]['frames']
        provenance = dict(user_authorization='2026-10-03: If generation fails, check older x2 restorations and reuse suitable generated sheets or standalone masters.',
            method='previous_accepted_generated_restoration_without_outline',
            current_outline_return=False, previous_project=str(PREVIOUS.relative_to(REPO)),
            previous_acceptance=dict(path=str((PREVIOUS / 'review/acceptance.json').relative_to(REPO)), sha256=sha(PREVIOUS / 'review/acceptance.json')),
            previous_metadata_sha256={p:sha(PREVIOUS / p) for p in ('registration.json', 'manifest.json', 'generation.json', 'sources.json')},
            batch=batch, original_batch=batches[batch], original_attempt=attempt,
            source_raw=copied(PREVIOUS / selected, OUT / 'raw/legacy_reuse' / Path(selected).name),
            source_prompt=copied(PREVIOUS / attempt['prompt']['path'], legacy / 'prompts' / Path(attempt['prompt']['path']).name),
            frames={})
        assert provenance['source_raw']['sha256'] == attempt['raw']['sha256']
        assert provenance['source_prompt']['sha256'] == attempt['prompt']['sha256']
        scales = {previous_registration[n]['scale'] for n in job['frames']}
        assert len(scales) == 1 and 2 / next(iter(scales)) >= 2
        for name in job['frames']:
            old = previous_registration[name]
            assert not old['raw_clip']
            for key, value in old_sources['sources'][name].items():
                assert sources['sources'][name][key] == value
            files = dict(clean=copied(PREVIOUS / f'cleaned/{name}.png', legacy / f'cleaned/{name}.png'),
                master=copied(PREVIOUS / f'aligned_2x/{name}.png', OUT / f'aligned_2x/{name}.png'))
            row = copy.deepcopy(old)
            row.update(batch=job['id'], raw_path=provenance['source_raw']['path'], raw_sha256=provenance['source_raw']['sha256'],
                clean_path=files['clean']['path'], clean_sha256=files['clean']['sha256'],
                effective_sampling_xy=[2 / old['scale']] * 2,
                retained_from=dict(project=str(PREVIOUS.relative_to(REPO)), batch=batch,
                    files=files, original_registration=old, previous_acceptance_sha256=provenance['previous_acceptance']['sha256'],
                    reason='User-authorized reuse of previously accepted generated art after a current outline job failed.'),
                registration='Retain the previous reviewed whole-sheet scale, pose translation and physical master. Exact native placement checked in the current package.',
                review_status='pending_current_independent_placement_detail_palette_review')
            registration[name] = row
            provenance['frames'][name] = files
        provenance['minimum_actual_generated_sampling'] = min(min(registration[n]['effective_sampling_xy']) for n in job['frames'])
        job['retained_restoration'] = provenance
        job['retained_native_frames'] = list(job['frames'])
        retained[job['id']] = provenance
    assert sum(len(p['frames']) for p in retained.values()) == 15
    run['legacy_reuse'] = dict(status='current_visual_review_pending', jobs=retained,
        rule='These frames complete native coverage without claiming successful current outline returns.')
    run['accepted'] = False
    run['status'] = 'candidate_with_legacy_reuse_pending_review'
    write(OUT / 'registration.json', registration)
    write(OUT / 'run.json', run)
    write(legacy / 'provenance.json', run['legacy_reuse'])
    journal = HERE.parent / 'mm7_m214/reviewed_resume_paths.json'
    review = read(journal)
    review['family_decisions']['mm7_m222'].update(accepted=False, available_poses_reviewed=False)
    write(journal, review)
    print('Staged 15 older generated frames; current coverage', len(registration), '/124; review pending.')


if __name__ == '__main__':
    stage()
