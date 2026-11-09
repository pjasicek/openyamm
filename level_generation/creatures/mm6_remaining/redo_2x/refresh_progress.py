"""Summarize the authorized redo without treating generated sheets as validated assets."""
import collections
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def read(path):
    return json.loads(path.read_text())


def main():
    inventory = read(HERE / 'inventory.json')
    installation = read(HERE.parent / 'installation.json')
    installed_by_descriptor = {row['descriptor_id']: row for row in installation['packages']}
    rows = []
    for family in inventory['families']:
        if not family['jobs']:
            continue
        out = REPO / family['project'] / 'redo_2x'
        run = read(out / 'run.json') if (out / 'run.json').exists() else {'jobs': []}
        generated = {n for j in run['jobs'] if j.get('selected_raw') for n in j['frames']}
        if (out / 'standing_01.json').exists():
            first = read(out / 'standing_01.json')
            if first.get('identity_reference'):
                generated.update(first['frames'])
        registration = read(out / 'registration.json') if (out / 'registration.json').exists() else {}
        sampled = {n for n, r in registration.items() if min(r.get('effective_sampling_xy', [0])) > 2}
        validation = read(out / 'validation.json') if (out / 'validation.json').exists() else {}
        # Only a separate reviewed acceptance can complete a family.
        acceptance = read(out / 'acceptance.json') if (out / 'acceptance.json').exists() else {}
        validated = acceptance.get('status') in ('validated', 'validated_with_detail_exceptions') and validation.get('visual_review_complete') is True
        state = acceptance['status'] if validated else 'partial' if generated else 'pending'
        package = installed_by_descriptor[family['descriptor_id']]
        review_record = out / 'review/acceptance.json'
        installed_manifest = REPO / family['installed_package'] / 'manifest.json'
        installed = (validated and review_record.is_file() and installed_manifest.is_file()
                     and package.get('acceptance_sha256') == hashlib.sha256(review_record.read_bytes()).hexdigest()
                     and hashlib.sha256(installed_manifest.read_bytes()).hexdigest()
                     == package['files']['manifest.json']['sha256'])
        row = dict(family=family['family'], project=family['project'], status=state,
                   required_names=family['counts']['insufficient'], generated_candidate_names=len(generated),
                   registered_above_2x_names=len(sampled), staged_atlas=(out / 'manifest.json').exists(),
                   run=str((out / 'run.json').relative_to(REPO)) if run['jobs'] else None,
                   installed_redo=installed, installed_art_unchanged=not installed)
        row['retained_detail_exception_names'] = sorted(n for n, r in registration.items()
                                                       if r.get('retained_detail_exception'))
        rows.append(row)
        family['execution_status'] = state
        for scope in family['jobs']:
            batches = [j for j in run['jobs'] if j['scope'] == scope['id']]
            if batches:
                scope['status'] = state if validated else 'partial' if any(j.get('selected_raw') for j in batches) else 'pending'
                scope['run'] = row['run']
                scope['attempts'] = [attempt for j in batches for attempt in j['attempts']]
    summary = dict(collections.Counter(r['status'] for r in rows))
    summary.update(generated_candidate_names=sum(r['generated_candidate_names'] for r in rows),
                   registered_above_2x_names=sum(r['registered_above_2x_names'] for r in rows),
                   installed_redo_families=sum(r['installed_redo'] for r in rows))
    result = dict(status='in_progress', minimum_sampling_exclusive=2, target_sampling=2.2,
                  installed_art_unchanged=not any(r['installed_redo'] for r in rows), summary=summary, families=rows)
    (HERE / 'progress.json').write_text(json.dumps(result, indent=2) + '\n')
    inventory['status'] = 'in_progress'
    (HERE / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    lines = ['# Authorized MM6 redo progress', '',
             'Generation and offline processing are authorized for all 56 insufficient families. Accepted redos are installed where marked.',
             'Generated candidates and registered sampling passes are **not** completed families.',
             '[Resume instructions](RUN.md) · [Workflow](WORKFLOW.md) · [Machine progress](progress.json)', '',
             '| Family | Execution | Installed redo | Required names | Generated candidates | Registered >2x |',
             '| --- | --- | --- | ---: | ---: | ---: |']
    for row in rows:
        lines.append('| {family} | {status} | {installed_redo} | {required_names} | {generated_candidate_names} | {registered_above_2x_names} |'.format(**row))
    (HERE / 'PROGRESS.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
