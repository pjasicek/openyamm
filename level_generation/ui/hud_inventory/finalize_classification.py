"""Freeze source dispositions and dimension evidence, without generating or installing art.

Run after the inventory and native/import audits. The census remains an immutable input;
classification and future queue state are separate artifacts.
"""
import collections
import csv
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def write(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2) + '\n')


def authored_baseline(path, size):
    """Require a checked-in x1 canvas, rather than accepting arbitrary working-tree dimensions."""
    relative = path.relative_to(ROOT).as_posix()
    commit = subprocess.check_output(
        ['git', 'log', '-1', '--format=%H', '--', relative], cwd=ROOT, text=True).strip()
    assert commit, f'No authored provenance: {relative}'
    historical = subprocess.check_output(['git', 'show', f'{commit}:{relative}'], cwd=ROOT)
    with Image.open(io.BytesIO(historical)) as image:
        historical_size = list(image.size)
    assert historical_size == size, f'Authored canvas changed: {relative}'
    assert hashlib.sha256(historical).hexdigest() == digest(path), f'Authored pixels changed: {relative}'
    return dict(native_baseline_verified=True, native_size=size,
                proof='project_authored_x1_canvas', commit=commit, committed_path=relative,
                committed_sha256=hashlib.sha256(historical).hexdigest(),
                policy='Use the checked-in project-native canvas in icons/ or ui/, including its margins. '
                       'This is a declared native baseline, not a claim of legacy-native pixels or accepted x2 art. '
                       'Do not infer a smaller canvas from a YAML draw rectangle or from an unrelated older design.')


def route(path, hint, size):
    name = path.stem.lower()
    if name == 'sprites':
        return 'registered_arcomage_atlas'
    if re.fullmatch(r'(?:[678])?pc\d+-\d+', name):
        return 'player_portrait_frames'
    if re.fullmatch(r'(?:[678])?npc\d+', name):
        return 'npc_portrait_family'
    if re.fullmatch(r'.*item\d+v\d+[ab]?', name):
        return 'fitted_equipment_variants'
    if re.fullmatch(r'(?:[678])?pc\d+[a-z]+', name):
        return 'paperdoll_parts'
    if re.fullmatch(r'(?:[678])?(?:terra|hglas)\d+', name):
        return 'ui_animation_family'
    if hint not in {'unreferenced_review', 'runtime_candidate_review'}:
        return hint
    if '/ui/maps/' in path.as_posix():
        return 'map_presentation'
    if re.fullmatch(r'sb[a-z]+000a?', name):
        return 'spellbook_page'
    if size[0] >= 384 and size[1] >= 240:
        return 'ui_background'
    if size[0] >= 300 or size[1] >= 240:
        return 'ui_frame_or_panel'
    if re.search(r'(?:_default|_pressed|_active|_disabled|_[udh]n|_[uh]t|_up)$', name):
        return 'ui_state_set'
    # Restoring these preserves the full census without asserting unsupported runtime reachability.
    return 'legacy_ui_art'


def main():
    scope, inventory = read('scope.json'), read('inventory.json')
    assert scope['summary']['inventory_sha256'] == digest(HERE / 'inventory.json')
    native, imported = read('source_audit.json'), read('import_audit.json')
    assert native['summary']['scope_sha256'] == digest(HERE / 'scope.json')
    baselines = {r['path']: r for r in native['files'] if r['native_baseline_verified']}
    baselines.update({r['path']: r for r in imported['files'] if r['native_baseline_verified']})
    usages, external = collections.defaultdict(list), {}
    census_paths = {r['id'] for r in scope['files']}
    for asset in inventory['assets']:
        for file in asset['files']:
            usages[file['path']].extend(asset['usages'])
            if file['path'] not in census_paths:
                external[file['path']] = file

    # Image lookup prefers PNG, BMP, PCX, then keeps the first sorted spelling for each folded name.
    siblings = collections.defaultdict(list)
    for row in scope['files']:
        path = Path(row['id'])
        siblings[(path.parent, path.stem.lower())].append(row['id'])
    shadowed = {}
    for (_, stem), paths in siblings.items():
        if len(paths) < 2:
            continue
        winner = min(paths, key=lambda p: ({'.png': 0, '.bmp': 1, '.pcx': 2}[Path(p).suffix.lower()], p))
        shadowed.update({p: winner for p in paths if p != winner})

    overrides = {r['census_path']: r for r in read('source_overrides.json')['overrides']}
    decisions, authored = [], []
    for row in scope['files']:
        path = ROOT / row['id']
        assert digest(path) == row['sha256'], f'Source drift: {path}'
        result = dict(path=row['id'], sha256=row['sha256'], scope='icon_census',
                      usages=usages[row['id']], disposition='restore')
        if not row['native_size']:
            assert path.suffix.lower() == '.md' and not row['decode_error']
            result.update(disposition='retain_non_target', reason='Bitmap provenance documentation; retain as evidence.')
        elif row['id'] in overrides:
            result.update(disposition='retain_non_target',
                          reason=overrides[row['id']]['reason'], replacement_source=overrides[row['id']]['source_path'])
        elif row['id'] in shadowed:
            result.update(disposition='retain_non_target', selected_source=shadowed[row['id']],
                          reason='Shadowed same-namespace source under the current bare-name extension/case lookup. '
                                 'Preserve the original file; do not overwrite the selected restoration with this variant.',
                          evidence=['engine/AssetFileSystem.cpp:enumerate',
                                    'engine/ImageAssetLoader.cpp:findAssetPathCaseInsensitive',
                                    'game/ui/MenuScreenBase.cpp',
                                    'game/ui/GameplayHudCommon.cpp:loadHudBitmapPixelsBgraCached'])
        else:
            baseline = baselines.get(row['id'])
            if not baseline:
                baseline = authored_baseline(path, row['native_size'])
                authored.append(dict(path=row['id'], **baseline))
            result.update(native_size=row['native_size'], x2_size=[v * 2 for v in row['native_size']],
                          baseline=baseline, treatment=route(path, row['route_hint'], row['native_size']),
                          reason='Restore the native canvas and all associated source states. '
                                 'Usage matches are evidence of a dependency candidate, not a claim that all mounted '
                                 'worlds draw this copy.' if usages[row['id']] else
                                 'Conservative inclusion of native/imported or project-authored legacy UI art. '
                                 'Lack of a literal runtime reference is not grounds for dropping this bitmap.',
                          reachability='associated_candidate' if usages[row['id']] else 'conservatively_included')
        decisions.append(result)

    for override in overrides.values():
        path = ROOT / override['source_path']
        assert digest(path) == override['source_sha256'] == digest(ROOT / override['native_origin'])
        decisions.append(dict(path=override['source_path'], sha256=override['source_sha256'], scope='native_replacement',
            disposition='restore', native_size=override['native_size'], x2_size=override['x2_size'],
            runtime_source=override['census_path'], usages=usages[override['census_path']], treatment='inventory_items',
            reason=override['reason'], baseline=dict(native_baseline_verified=True, proof='exact_native_file_bytes',
                                                   native_sources=[override['native_origin']])))

    native_maps = ROOT / 'mm9/extracted/ART/ART/INTERFACESCREENS/MAPSCREENS/MAPS'
    map_sources = {p.stem.lower(): p for p in native_maps.glob('*.pcx')}
    for name, file in sorted(external.items()):
        path = ROOT / name
        assert digest(path) == file['sha256']
        if '/ui/maps/' in name:
            source = map_sources[path.stem.lower()]
            assert digest(source) == file['sha256'], f'Map native mismatch: {name}'
            assert all(u['declared_size'] == file['size'] for u in usages[name])
            baseline = dict(native_baseline_verified=True, proof='exact_native_file_bytes',
                            native_sources=[source.relative_to(ROOT).as_posix()],
                            import_script='tools/mm9_import_discovery/promote_mm9_map_images.py')
        else:
            assert name == 'assets_dev/worlds/mm9/ui/dialogue/RUDEBG_OPENYAMM_LIGHT_ORNATE_SLIM.png'
            record = 'level_generation/terrain/mm6_new_sorpigal_dirt_fidelity/references/protected_playtest_hashes.json'
            hashes = json.loads((ROOT / record).read_text())
            assert hashes['original/' + name] == hashes['enhanced/' + name] == file['sha256']
            assert file['size'] == [540, 192]
            baseline = dict(native_baseline_verified=True, proof='project_authored_native_dialogue_canvas',
                native_size=[540, 192], historical_hash_record=record, historical_record_sha256=digest(ROOT / record),
                consumer='game/ui/GameplayDialogueRenderer.cpp:Mm9RudeBackgroundWidth',
                policy='Authored 540x192 canvas matches the explicit native dialogue contract and predates this '
                       'restoration, with identical original/enhanced playtest hashes. No accepted x2 art claimed.')
            authored.append(dict(path=name, **baseline))
        decisions.append(dict(path=name, sha256=file['sha256'], scope='external_ui', disposition='restore',
            native_size=file['size'], x2_size=file['x2_size'], usages=usages[name], baseline=baseline,
            treatment='map_presentation' if '/ui/maps/' in name else 'ui_background',
            reason='Explicit runtime image dependency outside icons/. Preserve map coordinates or dialogue registration.'))

    roster = list(csv.reader((ROOT / 'assets_dev/engine/data_tables/roster.txt').read_text(
        errors='replace').splitlines(), delimiter='\t'))
    assert not [r for r in roster[2:] if len(r) > 4 and r[4] == '29']
    missing = []
    for row in scope['missing_references']:
        result = dict(**row)
        if re.fullmatch(r'7pc(?:15|16|21|22)brd', row['name'], re.I):
            result.update(disposition='retain_non_target',
                reason='headAsset is parsed and compared as new-game exception metadata; no bitmap load consumes it.',
                evidence=['game/tables/CharacterDollTable.cpp:145', 'game/ui/screens/NewGameScreen.cpp:598'])
        elif row['name'].lower().startswith('pc30'):
            result.update(disposition='retain_non_target',
                reason='Reserved character 30 is unavailable at start and has race/class -1. No shipped roster '
                       'picture 29 selects it (characterDataId = pictureId + 1). Arbitrary edited saves are outside '
                       'shipped-content coverage; do not invent seven body pieces for a placeholder character.',
                evidence=['assets_dev/engine/data_tables/character_data.txt:31',
                          'assets_dev/engine/data_tables/roster.txt', 'game/party/Party.cpp:625',
                          'game/ui/screens/NewGameScreen.cpp:1253'])
        else:
            assert row['name'].lower() == 'asir08'
            result.update(disposition='missing_required',
                reason='Live mobile duplicate Immolation skull references absent native art. Existing Immolation '
                       'body indicator uses asiL10. Preparation proposes removing the redundant skull entry; '
                       'until that source repair is applied/reconciled, this remains an explicit prerequisite.',
                proposed_resolution='remove_duplicate_mobile_immolation_entry',
                evidence=['assets_dev/engine/ui/gameplay/gameplay_mobile.yml:363',
                          'game/ui/GameplayUiRenderer.cpp:466'])
        missing.append(result)

    summary = dict(census_files=len(scope['files']), additional_sources=len(decisions) - len(scope['files']),
                   dispositions=dict(collections.Counter(r['disposition'] for r in decisions)),
                   treatments=dict(collections.Counter(r['treatment'] for r in decisions if 'treatment' in r)),
                   missing_reference_dispositions=dict(collections.Counter(r['disposition'] for r in missing)),
                   generation_started=False, accepted_x2_artifacts=0,
                   classification_complete=True,
                   source_repairs_pending=sum(r['disposition'] == 'missing_required' for r in missing))
    write('authored_audit.json', dict(files=authored))
    write('classification.json', dict(schema_version=1, summary=summary,
        inputs={n: digest(HERE / n) for n in ['inventory.json', 'scope.json', 'source_audit.json',
                                             'import_audit.json', 'source_overrides.json']},
        files=decisions, missing_references=missing, fonts=inventory['fonts'],
        generated_and_external=inventory['generated_and_external']))
    write('classification_summary.json', summary)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
