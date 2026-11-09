"""Conservative restoration-scope overlay; never deletes assets or rewrites frozen receipts.

Exact tokens are evidence candidates, not proof of runtime reachability. Unknown dynamic
lookups stay on a usage-audit hold, not on the artwork queue and not on a deletion list.
"""
import collections
import csv
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / 'review/second_pass'
RASTER = {'.bmp', '.png', '.pcx'}
TEXT = {'.txt', '.yml', '.yaml', '.lua', '.json', '.cpp', '.h', '.hpp'}
LEGACY_UI = re.compile(r'^(?:6(?:arrow|backhand|bardata|butt|compass|con)|6book$|x_ok|wtr\d+$)', re.I)
DYNAMIC_KINDS = {'paperdoll_table', 'portrait_table_family', 'equipment_variant_family',
                 'hud_animation_table', 'journal_animation_family', 'dynamic_format_family',
                 'minimap_symbol_family', 'map_presentation_catalog'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(name, references, dynamic):
    # Positive evidence wins over filename heuristics: e.g. 6book2 is an inventory item.
    if references:
        return 'referenced_candidate'
    if dynamic:
        return 'dynamic_consumer_candidate'
    if LEGACY_UI.match(name):
        return 'excluded_legacy_ui'
    return 'usage_audit_hold'


def canonical_key(row):
    path = row['source_path']
    # Repository content ownership: original NPCs world-local, carried items/shared art global.
    world_npc = bool(re.fullmatch(r'npc\d+', Path(path).stem, re.I))
    preferred = ('/worlds/' in path) if world_npc else ('/engine/' in path)
    return (not preferred, path)


def apply_hold_review(row, decision):
    """Exact reviewed bytes only; new positive evidence overrides old negative decisions."""
    if row['source_sha256'] != decision['source_sha256']:
        raise ValueError(f'Reviewed source changed: {row["source_path"]}')
    row['hold_review'] = decision
    if row['status'] != 'usage_audit_hold':
        return
    row['status'] = decision['status']
    row['restoration_active'] = decision['status'] == 'dynamic_consumer_candidate'
    if row['restoration_active']:
        row['dynamic_evidence'].append(dict(kind=decision['rule'], note=decision['reason'],
                                           source='game/ui/GameplayHudRenderer.cpp'))


def main():
    roots = [ROOT / 'assets_dev/engine/icons', *sorted((ROOT / 'assets_dev/worlds').glob('*/icons'))]
    files = sorted(p for root in roots for p in root.rglob('*') if p.is_file() and p.suffix.lower() in RASTER)
    names = {p.stem.lower() for p in files}
    refs = collections.defaultdict(list)
    input_hashes = {}
    # Scan current authored runtime sources, not generated restoration metadata or reference trees.
    sources = set()
    for root in (ROOT / 'game', ROOT / 'engine'):
        sources.update(p for p in root.rglob('*') if p.suffix.lower() in TEXT and p.is_file())
    for root in (ROOT / 'assets_dev/engine', *sorted((ROOT / 'assets_dev/worlds').glob('*'))):
        for folder in ('data_tables', 'ui', 'events', 'rendering'):
            sources.update(p for p in (root / folder).rglob('*') if p.suffix.lower() in TEXT and p.is_file())
        sources.update(p for p in root.glob('*') if p.suffix.lower() in TEXT and p.is_file())
    token = re.compile(r'[a-zA-Z0-9_][a-zA-Z0-9_.-]*')
    for source in sorted(sources):
        rel = source.relative_to(ROOT).as_posix()
        input_hashes[rel] = sha(source)
        for number, line in enumerate(source.read_text(errors='replace').splitlines(), 1):
            if line.lstrip().startswith(('//', '--', '#')):
                continue
            hits = set()
            for value in token.findall(line.lower()):
                stem = Path(value).stem if Path(value).suffix in RASTER else value
                if stem in names:
                    hits.add(stem)
            for name in hits:
                refs[name].append({'source': rel, 'line': number, 'kind': 'current_exact_token'})

    dynamic = collections.defaultdict(list)
    previous = json.loads((HERE / 'inventory.json').read_text())
    classifications = {r['path']: r for r in json.loads((HERE / 'classification.json').read_text())['files']}
    input_hashes[str((HERE / 'classification.json').relative_to(ROOT))] = sha(HERE / 'classification.json')
    input_hashes[str((HERE / 'inventory.json').relative_to(ROOT))] = sha(HERE / 'inventory.json')
    for asset in previous['assets']:
        for use in asset['usages']:
            if use['kind'] in DYNAMIC_KINDS and (ROOT / use['source']).is_file():
                dynamic[asset['name'].lower()].append(use)
    # Names derived from map filenames are not literal bitmap tokens in map_stats.
    for table in (ROOT / 'assets_dev/engine/data_tables').glob('map_stats.txt'):
        for number, line in enumerate(table.read_text(errors='replace').splitlines(), 1):
            fields = line.split('\t')
            if len(fields) > 2 and fields[0].isdigit():
                name = Path(fields[2]).stem.lower()
                if name in names:
                    dynamic[name].append({'source': str(table.relative_to(ROOT)), 'line': number,
                                          'kind': 'map_filename_derived',
                                          'note': 'Protect pending actual minimap/PCX consumer resolution.'})
    # NPC filenames are formatted from numeric IDs; absence of a literal npcNNNN is not disuse.
    # Existing dynamic-format evidence protects generated/random NPC ranges as well as table IDs.
    for table_name, column in [('npc.txt', 2), ('character_data.txt', 22)]:
        table = ROOT / 'assets_dev/engine/data_tables' / table_name
        for number, line in enumerate(table.read_text(errors='replace').splitlines(), 1):
            fields = line.split('\t')
            if len(fields) > column and fields[0].isdigit() and fields[column].isdigit():
                name = f'npc{int(fields[column]):04d}'
                if name in names:
                    refs[name].append({'source': str(table.relative_to(ROOT)), 'line': number,
                                       'kind': 'numeric_npc_picture_id', 'column': column})
    review_path = OUT / 'usage_hold_review.json'
    review = json.loads(review_path.read_text()) if review_path.exists() else None
    reviewed = {r['source_path']: r for r in review['files']} if review else {}
    if review:
        assert len(reviewed) == review['cohort_size'] == 1882
        input_hashes[str(review_path.relative_to(ROOT))] = sha(review_path)
        for source, expected_hash in review['evidence_hashes'].items():
            assert sha(ROOT / source) == expected_hash, f'Hold review evidence changed: {source}; re-audit required'
            input_hashes[source] = expected_hash
    rows = []
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        name = path.stem.lower()
        status = classify(name, refs[name], dynamic[name])
        old = classifications.get(rel, {})
        legacy_namespace = '/worlds/mm6/' in rel or name.startswith(('6', '7'))
        if status == 'usage_audit_hold' and legacy_namespace and old.get('treatment') in {
                'legacy_ui_art', 'ui_state_set', 'ui_background', 'ui_frame_or_panel',
                'ui_animation_family', 'spellbook_page', 'spell_icon_pair'}:
            status = 'excluded_legacy_ui'
        if '/worlds/mm9/' in rel:
            status = 'preserved_mm9_exclusion'
        row = dict(source_path=rel, source_sha256=sha(path), bytes=path.stat().st_size,
                         status=status, restoration_active=status in ('referenced_candidate', 'dynamic_consumer_candidate'),
                         references=refs[name], dynamic_evidence=list(dynamic[name]), canonical_source=None,
                         historical_treatment=old.get('treatment'))
        if rel in reviewed:
            apply_hold_review(row, reviewed[rel])
        rows.append(row)
    assert set(reviewed).issubset(r['source_path'] for r in rows), 'Reviewed source missing'
    # Same basename AND bytes can share restoration work. Different names/bytes never auto-merge.
    groups = collections.defaultdict(list)
    content_groups = collections.defaultdict(list)
    for row in rows:
        groups[(Path(row['source_path']).name.lower(), row['source_sha256'])].append(row)
        content_groups[row['source_sha256']].append(row['source_path'])
    duplicates = []
    for group in groups.values():
        if len(group) < 2:
            continue
        active = [r for r in group if r['restoration_active']]
        canonical = min(active or group, key=canonical_key)
        duplicates.append(dict(canonical_source=canonical['source_path'],
                               sources=[r['source_path'] for r in group],
                               sha256=canonical['source_sha256'], physical_deletion_authorized=False))
        for row in active:
            if row is not canonical:
                row['canonical_source'] = canonical['source_path']
                row['status'] = 'duplicate_restoration_alias'
                row['restoration_active'] = False
    summary = dict(files=len(rows), statuses=dict(collections.Counter(r['status'] for r in rows)),
                   active_restoration_sources=sum(r['restoration_active'] for r in rows),
                   same_name_byte_duplicate_groups=len(duplicates),
                   all_byte_duplicate_groups=sum(len(g) > 1 for g in content_groups.values()),
                   scanned_runtime_text_files=len(sources), runtime_deletions=0,
                   reference_audit_complete=False,
                   original_hold_cohort_resolved=len(reviewed),
                   hold_review_statuses=review['statuses'] if review else {},
                   restoration_holds_resolved=not any(r['status'] == 'usage_audit_hold' for r in rows),
                   policy='No legacy MM6/MM7 interface restoration. Positive runtime/data evidence protected; '
                          'unknowns require usage audit before any artwork work. Same-name identical copies share '
                          'review work but retain destination contracts. No source/receipt/acceptance deleted.')
    document = dict(summary=summary, files=rows, same_name_duplicates=duplicates,
                    content_duplicate_candidates=[dict(sha256=h, sources=g) for h, g in content_groups.items() if len(g)>1],
                    input_hashes=input_hashes)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'usage_scope.json').write_text(json.dumps(document, indent=2) + '\n')
    with (OUT / 'usage_scope.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['source_path', 'status', 'restoration_active',
                                                    'canonical_source', 'source_sha256'], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    (OUT / 'USAGE_SCOPE.md').write_text('# Runtime usage and lean restoration scope\n\n'
        'This overlay supersedes whole-folder restoration assignments. It does not delete runtime files.\n\n'
        '```json\n' + json.dumps(summary, indent=2) + '\n```\n\n'
        '[Per-file CSV](usage_scope.csv) · [Evidence, hashes and duplicate groups](usage_scope.json)\n\n'
        '[Original 1,882-file hold review](usage_hold_review.json): exact paths and native hashes, '
        'individual decisions, family explanations and consumer/table evidence hashes. '
        '1,829 excluded from restoration; 53 protected metadata-driven context/fallback button states. '
        'Exclusions are current-scope decisions, not permission to remove compatibility originals. '
        'Future unknowns still become holds; changed evidence requires re-audit.\n\n'
        'Limits: exact tokens can be comments/data candidates, not proven live loader calls. Historical dynamic '
        'families are conservatively protected, not automatically accepted. Map binary/event references, random NPC '
        'portrait ranges, concatenated names and path-qualified consumers require follow-up before deletion. '
        'The original hold cohort is resolved for restoration selection, not a proof that every preserved '
        'reference candidate is reachable or that arbitrary old saves/mods cannot name excluded files. '
        'New unreferenced unknowns are usage-audit holds, not asserted unused. Same-name identical copies are restoration '
        'aliases only; physical consolidation must preserve package availability, explicit paths and x2/x4 tiers. '
        'Different-name identical bytes remain candidates, not automatic deletion or universal visual acceptance.\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
