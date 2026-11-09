"""Read native animation, equipment-registration and Arcomage bindings for the frozen manifest."""
import collections
import csv
import re

from finalize_classification import ROOT, digest


def rows(name, path=None):
    path = path or ROOT / 'assets_dev/engine/data_tables' / name
    return [dict(source=path.relative_to(ROOT).as_posix(), line=i,
                 fields=line.split('\t')) for i, line in enumerate(path.read_text(errors='replace').splitlines(), 1)]


def load():
    items = collections.defaultdict(lambda: collections.defaultdict(list))
    for path in [ROOT / 'assets_dev/engine/data_tables/items.txt',
                 *sorted((ROOT / 'assets_dev/worlds').glob('*/data_tables/items.txt'))]:
        namespace = path.parent.parent.relative_to(ROOT / 'assets_dev').as_posix()
        for line, text in enumerate(path.read_text(errors='replace').splitlines(), 1):
            fields = text.split('\t')
            if len(fields) >= 16 and fields[0].isdigit() and fields[1]:
                items[namespace][fields[1].lower()].append(dict(source=path.relative_to(ROOT).as_posix(), line=line,
                    item_id=int(fields[0]), name=fields[2], equip_stat=fields[4], skill_group=fields[5],
                    native_equip_xy=fields[14:16]))
    icons = collections.defaultdict(list)
    for row in rows('icon_frame_data.txt'):
        fields = row['fields']
        if len(fields) < 5 or not fields[2].isdigit():
            continue
        icons[fields[1].lower()].append(dict(source=row['source'], line=row['line'], animation=fields[0],
            frame_length_raw=int(fields[2]), animation_length_raw=int(fields[3]),
            frame_ticks=int(fields[2]) * 8, animation_ticks=int(fields[3]) * 8, flags=int(fields[4], 0)))
    portraits = collections.defaultdict(list)
    for row in rows('portrait_frame_data.txt'):
        fields = row['fields']
        if len(fields) < 5 or not fields[0].isdigit():
            continue
        portraits[int(fields[1])].append(dict(source=row['source'], line=row['line'],
            expression_id=int(fields[0]), texture_index=int(fields[1]), frame_length_raw=int(fields[2]),
            animation_length_raw=int(fields[3]), frame_ticks=int(fields[2]) * 8,
            animation_ticks=int(fields[3]) * 8, flags=int(fields[4], 0)))
    complex_items = collections.defaultdict(list)
    for name in ['complex_item_pictures.txt', 'complex_item_picture_offsets.txt']:
        paths = [ROOT / 'assets_dev/engine/data_tables' / name,
                 *sorted((ROOT / 'assets_dev/worlds').glob('*/data_tables/' + name))]
        for path in paths:
            for row in rows(name, path):
                fields = row['fields']
                if len(fields) > 1 and fields[0].isdigit() and fields[1].isdigit():
                    complex_items[int(fields[1])].append(row)
    dolls = {int(r['fields'][0]): r for r in rows('doll_types.txt') if r['fields'][0].isdigit()}
    cards_path = ROOT / 'assets_dev/engine/data_tables/arcomage_cards.txt'
    cards = list(csv.DictReader(cards_path.read_text().splitlines(), delimiter='\t'))
    by_slot = collections.defaultdict(list)
    for card in cards:
        by_slot[int(card['slot'])].append(dict(id=int(card['id']), name=card['name'], slot=int(card['slot'])))
    return dict(items=items, icons=icons, portraits=portraits, complex_items=complex_items, dolls=dolls, cards=by_slot,
                cards_source=cards_path.relative_to(ROOT).as_posix(), cards_sha256=digest(cards_path))


def attach(target, metadata):
    name = target['runtime_name']
    if name in metadata['icons']:
        target['animation_table_frames'] = metadata['icons'][name]
    match = re.fullmatch(r'(?:[678])?pc\d+-(\d+)', name)
    if target['treatment'] == 'player_portrait_frames':
        assert target['frame'], f'Unbound player portrait: {name}'
        target['portrait_expression_frames'] = metadata['portraits'].get(target['frame']['ordinal'], [])
        target['portrait_timing_rule'] = ('Expression selection, not one constant frame rate. Raw duration * 8 ticks; '
            'HasMore=1 advances through following table rows and animation_ticks sets the loop. Unlisted texture '
            'indices remain conservatively retained legacy frames, without an invented active expression.')
    if re.fullmatch(r'ira-[1-4]_\d+', name):
        family, ordinal = name.rsplit('_', 1)
        count = {'ira-1': 10, 'ira-2': 10, 'ira-3': 9, 'ira-4': 11}[family]
        target['frame'] = dict(family=family, ordinal=int(ordinal), first_frame=1, last_frame=count,
                               frame_milliseconds=100, unhovered_frame=1,
                               source='game/ui/GameplayPartyOverlayRenderer.cpp:journalMainIconTextureName')
    if target['treatment'] in {'paperdoll_parts', 'fitted_equipment_variants', 'inventory_items'}:
        base = re.sub(r'v\d+[ab]?$', '', name) if target['treatment'] == 'fitted_equipment_variants' else name
        item_namespace = target['namespace'] if target['namespace'] in metadata['items'] else 'engine'
        item_rows = metadata['items'][item_namespace].get(base, [])
        ids = {int(u['item_id']) for u in target['usages'] if str(u.get('item_id', '')).isdigit()}
        ids.update(r['item_id'] for r in item_rows)
        anchors = [row for item_id in sorted(ids) for row in metadata['complex_items'].get(item_id, [])]
        target['equipment_registration'] = dict(item_ids=sorted(ids), item_definitions=item_rows,
            complex_picture_and_override_rows=anchors,
            doll_types=list(metadata['dolls'].values()) if target['treatment'] != 'inventory_items' else [],
            selector='game/gameplay/GameplayScreenRuntime.cpp:resolveEquippedItemHudTextureName',
            placement='game/gameplay/GameplayScreenRuntime.cpp:resolveCharacterEquipmentRenderRect',
            rule='Preserve the canvas origin. vN uses doll type N-1; armor vNa is alternate hand pose, cloak '
                 'uses the alternate suffix and some doll types share v1. Keep table offsets in native logical '
                 'units; only image pixels double. Do not independently fit pieces to their opaque bounds.')
    if target['treatment'] == 'registered_arcomage_atlas':
        target['atlas'] = dict(card_slots=dict(metadata['cards']), source=metadata['cards_source'],
            source_sha256=metadata['cards_sha256'], columns=10, card_native_size=[96, 128], cards_top=220,
            reconstruction='Paste registered regions at twice their source xy into the full 1920x5000 canvas. '
                           'Font regions use the deterministic font pipeline; uniform unused regions retain their '
                           'exact source color. Review all joins and render active source rectangles before acceptance.')
