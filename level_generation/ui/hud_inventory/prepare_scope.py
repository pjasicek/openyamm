"""Account for every icon-root file and propose restoration routes without starting generation.

These are classification hints, not accepted exclusions or an executable imagegen queue.
"""
import collections
import csv
import hashlib
import json
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RASTER = {'.png', '.bmp', '.pcx'}


def classify(path, usages, size):
    name = path.stem.lower()
    kinds = {u['kind'] for u in usages}
    yaml_uses = [u for u in usages if u['kind'] == 'yaml']
    if path.suffix.lower() not in RASTER:
        return 'non_bitmap_review', 'Documentation/support data; review and retain appropriately, not imagegen.'
    if not usages:
        return 'unreferenced_review', 'Determine use, provenance and existing restoration before assigning art treatment.'
    spell_uses = [u for u in yaml_uses if u.get('screen') == 'Spellbook']
    if any('SpellbookPage' in u.get('element', '') and 'Spell' in u['element'][13:] for u in spell_uses):
        return 'spell_icon_pair', 'Page-first crop dependency; pilot 4–6 normal/hover pairs (8–12 cells).'
    if any(u.get('element', '').startswith('SpellbookPage') for u in spell_uses):
        return 'spellbook_page', 'Restore one school background first; it supplies accepted icon crops.'
    if yaml_uses:
        if size and size[0] >= 384 and size[1] >= 240:
            return 'ui_background', 'One complete background per image; coordinate shared frame pieces.'
        if size and (size[0] >= 300 or size[1] >= 240):
            return 'ui_frame_or_panel', 'One panel or a small adjoining set; lock border alignment.'
        return 'ui_state_set', 'Keep button states together; pilot 6–12 similarly sized cells.'
    if 'portrait_table_family' in kinds or name.startswith('pc') and '-' in name:
        return 'player_portrait_frames', 'One character per batch, 4–8 expressions with an accepted identity reference.'
    if any(u.get('format', '').lower().startswith('npc%') for u in usages):
        return 'npc_portrait_family', 'Small portrait batches; preserve each identity, not one averaged face.'
    if 'equipment_variant_family' in kinds:
        return 'fitted_equipment_variants', 'Group one item and compatible body/pose variants; preserve native fitting.'
    if 'paperdoll_table' in kinds:
        return 'paperdoll_parts', 'One character/body family; shared alignment, no independent fit-to-bounds scaling.'
    if 'item_table' in kinds:
        return 'inventory_items', 'Pilot 6–12 simple related icons; fewer for large/detailed silhouettes.'
    if kinds & {'hud_animation_table', 'journal_animation_family', 'dynamic_format_family'}:
        return 'ui_animation_family', 'Group consecutive frames from one animation; 4–8 initially, preserve timing.'
    return 'runtime_candidate_review', 'Confirm actual texture use, then assign background/icon/animation treatment.'


def main():
    inventory_path = HERE / 'inventory.json'
    inventory = json.loads(inventory_path.read_text())
    usages_by_file = collections.defaultdict(list)
    names_by_file = collections.defaultdict(set)
    for asset in inventory['assets']:
        for source in asset['files']:
            usages_by_file[source['path']].extend(asset['usages'])
            names_by_file[source['path']].add(asset['name'])
    directories = [ROOT / 'assets_dev/engine/icons',
                   *sorted((ROOT / 'assets_dev/worlds').glob('*/icons'))]
    records = []
    duplicates = collections.defaultdict(list)
    for directory in directories:
        for path in sorted(directory.rglob('*')):
            if not path.is_file():
                continue
            relative = path.relative_to(ROOT).as_posix()
            payload = path.read_bytes()
            sha = hashlib.sha256(payload).hexdigest()
            size = None
            mode = None
            error = None
            if path.suffix.lower() in RASTER:
                try:
                    with Image.open(path) as image:
                        size, mode = list(image.size), image.mode
                except (OSError, ValueError) as exception:
                    error = str(exception)
            usages = usages_by_file.get(relative, [])
            route, batch = classify(path, usages, size)
            unique_refs = sorted({(u['source'], u.get('line', 0)) for u in usages})
            records.append(dict(
                id=relative, root=directory.relative_to(ROOT).as_posix(), sha256=sha, bytes=len(payload),
                native_size=size, x2_size=[v * 2 for v in size] if size else None, mode=mode,
                native_baseline_verified=False,
                decode_error=error, names=sorted(names_by_file.get(relative, [])),
                usage_kinds=sorted({u['kind'] for u in usages}),
                references=[dict(source=s, line=n) for s, n in unique_refs],
                route_hint=route, batch_hint=batch,
                disposition='pending_classification',
                review_note='Usage associations are conservative name matches, not proof of mount priority or reachability.'))
            duplicates[sha].append(relative)
    missing = [dict(name=a['name'], usages=a['usages']) for a in inventory['assets'] if a['status'] == 'missing']
    summary = dict(
        total_files=len(records), bitmap_files=sum(r['native_size'] is not None for r in records),
        non_bitmap_files=sum(Path(r['id']).suffix.lower() not in RASTER for r in records),
        decode_errors=sum(r['decode_error'] is not None for r in records),
        associated_with_usage_inventory=sum(bool(r['usage_kinds']) for r in records),
        not_associated_with_usage_inventory=sum(not r['usage_kinds'] for r in records),
        missing_referenced_names=len(missing),
        roots=dict(collections.Counter(r['root'] for r in records)),
        route_hints=dict(collections.Counter(r['route_hint'] for r in records)),
        duplicate_byte_groups=sum(len(paths) > 1 for paths in duplicates.values()),
        classification_complete=False, generation_started=False,
        inventory_sha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest(),
        boundary='All files recursively under the listed native icon roots. x2/x4 roots are not native inputs. '
                 'Fonts and generated/external HUD dependencies remain in inventory.json. No pending row is an exclusion.')
    output = dict(summary=summary, files=records, missing_references=missing,
                  duplicate_byte_candidates=[dict(sha256=sha, paths=paths)
                                             for sha, paths in sorted(duplicates.items()) if len(paths) > 1])
    (HERE / 'scope.json').write_text(json.dumps(output, indent=2) + '\n')
    (HERE / 'scope_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    with (HERE / 'scope.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['path', 'native_size', 'x2_size', 'route_hint', 'batch_hint', 'disposition', 'sha256'])
        for row in records:
            writer.writerow([row['id'], row['native_size'], row['x2_size'], row['route_hint'], row['batch_hint'],
                             row['disposition'], row['sha256']])
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
