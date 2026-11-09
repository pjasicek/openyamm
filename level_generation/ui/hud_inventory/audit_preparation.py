"""Audit the preparation boundary. Artwork acceptance and in-game restored previews are a later phase."""
import collections
import importlib.util
import json
from pathlib import Path

from PIL import Image

from finalize_classification import HERE, ROOT, digest, read, write


def main():
    spec = importlib.util.spec_from_file_location('hud_prepared_queue', HERE / 'queue.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    queue = module.Queue()
    validation = queue.validate()
    scope, classification = read('scope.json'), read('classification.json')
    paths = {r['id'] for r in scope['files']}
    current = {p.relative_to(ROOT).as_posix() for root in scope['summary']['roots']
               for p in (ROOT / root).rglob('*') if p.is_file()}
    assert current == paths, 'Reconcile added/deleted source files'
    census_rows = [r for r in classification['files'] if r['scope'] == 'icon_census']
    assert len(census_rows) == len(paths) and {r['path'] for r in census_rows} == paths
    allowed = {'restore', 'reuse_verified_x2', 'alias_verified_x2', 'retain_non_target', 'missing_required'}
    assert all(r['disposition'] in allowed and r['reason'] for r in classification['files'])
    restores = {r['path']: r for r in classification['files'] if r['disposition'] == 'restore'}
    assert {t['source_path'] for t in queue.targets.values()} == set(restores)
    assert len(restores) == len(queue.targets)
    assert not validation['missing_required'], 'Required missing sources remain unresolved'
    assert all(r['disposition'] == 'retain_non_target' for r in classification['missing_references'])
    assert len({t['output_path'].lower() for t in queue.targets.values()}) == len(queue.targets)
    states = collections.defaultdict(set)
    target_jobs = collections.defaultdict(set)
    for job in queue.jobs.values():
        assert job['prompt'] and job['review_checks']
        for member in job['members']:
            target_jobs[member['target']].add(job['id'])
    for target in queue.targets.values():
        source = ROOT / target['source_path']
        with Image.open(source) as image:
            assert list(image.size) == target['native_size']
        assert target['native_baseline']['native_baseline_verified']
        assert target['usages'] == restores[target['source_path']]['usages']
        assert target['compositing']['profiles'] and target['compositing']['fingerprints']
        assert target['logical_canvas'] == [0, 0, *target['native_size']]
        assert target['output_path'].startswith(str(HERE.relative_to(ROOT)) + '/exports/')
        assert not (ROOT / target['output_path']).exists(), 'Unexpected production artwork during preparation'
        for usage in target['usages']:
            if usage['kind'] == 'yaml':
                assert usage['layout_chain']
                if target['treatment'] == 'ui_state_set' and usage['state'] in {
                        'default', 'highlighted', 'pressed', 'selected'}:
                    states[(target['namespace'], usage['source'], usage['element'])].add(target['id'])
        for alias in target['state_aliases']:
            assert alias['artifact_target'] == target['id']
            actual = {u['state'] for u in target['usages'] if u['kind'] == 'yaml'
                      and u['source'] == alias['source'] and u['element'] == alias['element']}
            assert set(alias['states']) == actual
        if target['treatment'] == 'player_portrait_frames':
            assert target['frame'] and 'portrait_expression_frames' in target
        if target['treatment'] == 'fitted_equipment_variants':
            assert target['equipment_registration']['selector']
        for recipe in target.get('page_dependencies', []):
            page = queue.targets[recipe['page_target']]
            x, y, width, height = recipe['x2_draw_rect']
            assert x >= 0 and y >= 0 and x + width <= page['x2_size'][0] and y + height <= page['x2_size'][1]
    for state_targets in states.values():
        assert len(set.union(*(target_jobs[t] for t in state_targets))) == 1, 'Split control-state family'
    for job in queue.jobs.values():
        if job['treatment'] == 'spell_icon_pair':
            pairs = collections.defaultdict(list)
            for member in job['members']:
                target = queue.targets[member['target']]
                pairs[target['page_dependencies'][0]['element']].append(member)
                assert any(d.get('target') == target['page_dependencies'][0]['page_target']
                           for d in job['dependencies'])
            for pair in pairs.values():
                assert len(pair) == 2 and pair[0]['reference_cell_rect'][1] == pair[1]['reference_cell_rect'][1]
        if job['kind'] == 'deterministic_uniform_regions':
            assert all(m['source_color_rgba'] and not m['card_definitions'] for m in job['members'])
        if job['kind'] == 'imagegen_sheet' and not job['pilot']:
            assert any(d['kind'] == 'accepted_treatment_pilot' for d in job['dependencies'])
    for font in queue.manifest['fonts']:
        assert font['disposition'] == 'retain_non_target' and (ROOT / font['owner']).is_file()
        assert font['source_hashes']
    for dependency in queue.manifest['generated_and_external']:
        assert dependency['disposition'] == 'retain_non_target'
        assert all((ROOT / owner).is_file() for owner in dependency['owners'])
    repairs = queue.manifest['source_repair_prerequisites']
    for repair in repairs['repairs']:
        assert repair['status'] == 'applied_source_cleanup'
        assert digest(ROOT / repair['source']) == repair['source_sha256']
        assert repair['missing_reference'] not in (ROOT / repair['source']).read_text()
    assert not queue.state['attempts'] and not queue.state['cells'] and not queue.state.get('claims')
    report = dict(preparation_structure_verified=True, generation_started=False, structural_validation=validation,
        census_files=len(paths), additional_sources=len(classification['files']) - len(paths),
        dispositions=classification['summary']['dispositions'],
        missing_reference_dispositions=classification['summary']['missing_reference_dispositions'],
        jobs_by_kind=dict(collections.Counter(j['kind'] for j in queue.jobs.values())),
        fonts=len(queue.manifest['fonts']), generated_or_external_owners=len(queue.manifest['generated_and_external']),
        applied_source_repairs=repairs['changed_files'],
        scope='Classification, target-manifest finalization and generation-queue preparation only. '
              'No restored bitmap, accepted artwork or runtime restored-preview completion is claimed.',
        artifact_hashes={name: digest(HERE / name) for name in ['classification.json', 'expected_targets.json',
                                                              'jobs.json', 'repairs/source_repairs.json']})
    write('review/classification/completion_audit.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
