"""Dresses a doll in a whole outfit (armour, helm, belt, boots and a weapon) the way the game composites the
character screen, for three sources: the new MM9 art, the current MM9 art and the MM7/MM8 reference items.

    python3 scripts/outfit.py           writes review/outfits/*.jpg and review/outfits/index.json

Layer order and placement follow the engine (GameplayPartyOverlayRenderer, GameplayScreenRuntime and character.yml):
background, body (60), right hand holding or open and left hand open (65), armour and helm (66), boots and belt (67),
main-hand weapon (70), right-hand fingers and, for a two-handed weapon or a spear, the left hand holding it (75).
Worn pieces use the runtime file suffixes and their complex_item_pictures points; the weapon hangs from its Equip X/Y
at the doll type's main-hand anchor. All doll-type Y values are negated, as CharacterDollTable does.
"""
import csv
import json
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[1]
ICON_PROJECT = PROJECT.parent
ROOT = PROJECT.parents[3]
sys.path.insert(0, str(ROOT / 'tools/mm9_import_discovery'))
import render_paperdoll_equipment_preview as preview  # noqa: E402

OUT = PROJECT / 'review/outfits'
TABLES = preview.ENGINE_TABLE_ROOT
MM9_TABLES = preview.MM9_TABLE_ROOT
SCALE = preview.PHYSICAL_SCALE
DOLL_NAMES = {0: 'Human male', 1: 'Human female', 2: 'Minotaur', 3: 'Troll', 4: 'Dwarf'}
OUTFITS = {
    'A': {'Armor': 10102, 'Helm': 10123, 'Belt': 10152, 'Boots': 10126, 'weapon': 10009},
    'B': {'Armor': 10113, 'Helm': 10125, 'Belt': 10153, 'Boots': 10132, 'weapon': 10074},
    # full pass (2026-11-05): two more outfits from the new pieces
    'C': {'Armor': 10111, 'Helm': 10124, 'Belt': 10154, 'Boots': 10131, 'weapon': 10009},
    'D': {'Armor': 10115, 'Helm': 10203, 'Belt': 10208, 'Boots': 10233, 'weapon': 10074},
}
WEAPONS = [10009, 10074, 10061, 10039, 10079]
Z = {'Armor': 66, 'Helm': 66, 'Boots': 67, 'Belt': 67}
ORDER = ['Armor', 'Boots', 'Helm', 'Belt']           # character.yml order inside equal z


def rows(path, encoding='utf-8'):
    table = list(csv.reader(path.open(encoding=encoding, newline=''), delimiter='\t'))
    header = next(index for index, row in enumerate(table) if row and row[0] == 'Item #')
    return {int(row[0]): dict(zip(table[header], row)) for row in table[header + 1:] if row and row[0].isdigit()}


ENGINE_ROWS = rows(TABLES / 'items.txt', 'cp1252')
MM9_ROWS = rows(MM9_TABLES / 'items.txt')
PIECES = yaml.safe_load((PROJECT / 'pieces.yml').read_text())['pieces']
PIECE_BY_ID = {piece['id']: (key, piece) for key, piece in PIECES.items()}
ENGINE_POINTS = preview.read_complex_picture_offsets(TABLES / 'complex_item_pictures.txt')
MM9_POINTS = preview.read_complex_picture_offsets(MM9_TABLES / 'complex_item_pictures.txt')
DOLLS = preview.representative_dolls(preview.read_character_dolls(TABLES / 'character_data.txt'))
DOLL_TYPES = preview.read_doll_types(TABLES / 'doll_types.txt')
MAIN_HAND_OFFSET = {int(row[0]): preview.legacy_point(row, 22) for row in preview.read_tsv(TABLES / 'doll_types.txt')[1:]
                    if len(row) > 23 and row[0].strip().isdigit()}
LEFT_HOLD_POINT = {int(row[0]): preview.legacy_point(row, 16) for row in preview.read_tsv(TABLES / 'doll_types.txt')[1:]
                   if len(row) > 23 and row[0].strip().isdigit()}
NEW_ANCHORS = yaml.safe_load((ICON_PROJECT / 'review/doll_grip/anchors_new.yml').read_text())['items']


def new_weapon_root():
    """The new x2 weapon icons under their Pic File names (one folder, tier 2)."""
    folder = PROJECT / 'work/_weapons_x2'
    folder.mkdir(parents=True, exist_ok=True)
    for item_id in WEAPONS:
        Image.open(ICON_PROJECT / f'items/{item_id}/icon_a_x2.png').save(folder / f'mm9_item_{item_id}.png')
    return folder


def assets_for(source):
    roots = preview.declared_icon_roots()
    if source == 'new':
        fitted = [(PROJECT / 'work' / key / 'fitted', 2) for key in PIECES]
        roots = [(new_weapon_root(), 2)] + [root for root in fitted if root[0].is_dir()] + roots
    return preview.AssetIndex(roots)


def worn(source, slot, item_id):
    """(icon name, equip stat, points per doll type) of the outfit's piece for a source."""
    if source == 'reference':
        reference = PIECE_BY_ID[item_id][1]['reference']
        return ENGINE_ROWS[reference]['Pic File'], ENGINE_POINTS[reference]
    if source == 'new':
        reference = PIECE_BY_ID[item_id][1]['reference']
        return MM9_ROWS[item_id]['Pic File'], ENGINE_POINTS[reference]      # the canvases are the reference's
    return MM9_ROWS[item_id]['Pic File'], MM9_POINTS[item_id]


def weapon(source, item_id):
    """(icon name, Equip X, Equip Y, two-handed) for a source; the reference source shows the new weapon."""
    row = MM9_ROWS[item_id]
    two_handed = row['Equip Stat'] == 'Weapon2' or row['Skill Group'] == 'Spear'
    if source == 'old':
        return row['Pic File'], int(row['Equip X']), int(row['Equip Y']), two_handed
    anchor = NEW_ANCHORS[int(row['x_mm9_raw_item_id'])]['equip_anchor']
    return row['Pic File'], anchor[0], anchor[1], two_handed


def layer(assets, name):
    path = assets.find(name)
    return None if path is None else preview.load_layer(path, color_key=True, tier=assets.tier(path))


def paste(canvas, image, point):
    """alpha_composite at a logical point; the part outside the canvas (a tall weapon above the frame) is cut off."""
    if image is None:
        return
    x, y = point[0] * SCALE, point[1] * SCALE
    left, top = max(0, -x), max(0, -y)
    if left < image.width and top < image.height:
        canvas.alpha_composite(image.crop((left, top, image.width, image.height)), (x + left, y + top))


def render(source, doll_type, slots, weapon_id):
    """One doll in the outfit (a dict slot -> item id) holding weapon_id (or empty-handed)."""
    assets = ASSETS[source]
    doll, kind = DOLLS[doll_type], DOLL_TYPES[doll_type]
    canvas = layer(assets, doll.background_asset).crop((0, 0, preview.PAPERDOLL_WIDTH * SCALE,
                                                        preview.PAPERDOLL_HEIGHT * SCALE))
    held = weapon(source, weapon_id) if weapon_id else None
    paste(canvas, layer(assets, doll.body_asset), (doll.body_x, doll.body_y))
    if held:
        paste(canvas, layer(assets, doll.right_hand_hold_asset), kind.right_hand_closed)
    else:
        paste(canvas, layer(assets, doll.right_hand_open_asset), kind.right_hand_open)
    if not (held and held[3]):
        paste(canvas, layer(assets, doll.left_hand_open_asset), kind.left_hand_fingers)
    missing = []
    for slot in sorted(slots, key=lambda s: (Z[s], ORDER.index(s))):
        if not kind.can_equip.get(slot, False):
            continue
        icon, points = worn(source, slot, slots[slot])
        item = preview.Item(id=slots[slot], icon_name=icon, name='', equip_stat=slot, source='mm9')
        name, path, suffix = preview.resolve_item_asset(item, doll_type, held is not None, 'runtime', assets)
        if path is None or suffix == '' or (source == 'new' and PROJECT not in path.parents):
            missing.append(f'{slot} {icon}')
            continue
        paste(canvas, preview.load_layer(path, color_key=True, tier=assets.tier(path)), points[doll_type])
    if held:
        icon, equip_x, equip_y, two_handed = held
        fingers = layer(assets, doll.right_hand_fingers_asset)
        anchor_x = kind.right_hand_fingers[0] + round(fingers.width / SCALE * 0.5)
        anchor_y = kind.right_hand_closed[1] + MAIN_HAND_OFFSET[doll_type][1]
        paste(canvas, layer(assets, icon), (anchor_x - equip_x, anchor_y - equip_y))
        paste(canvas, fingers, kind.right_hand_fingers)
        if two_handed:
            paste(canvas, layer(assets, doll.left_hand_hold_asset), LEFT_HOLD_POINT[doll_type])
    return canvas.convert('RGB'), missing


ASSETS = {}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for source in ('new', 'old', 'reference'):
        ASSETS[source] = assets_for(source)
    index = {'outfits': [], 'weapons': []}
    for doll_type in DOLL_NAMES:
        for outfit, slots in OUTFITS.items():
            worn_slots = {slot: value for slot, value in slots.items() if slot != 'weapon'}
            for source in ('new', 'old', 'reference'):
                for pose, weapon_id in (('empty', None), ('weapon', slots['weapon'])):
                    image, missing = render(source, doll_type, worn_slots, weapon_id)
                    name = f'outfit{outfit}_t{doll_type}_{source}_{pose}.jpg'
                    image.save(OUT / name, quality=90)
                    index['outfits'].append({'file': name, 'outfit': outfit, 'doll_type': doll_type,
                                             'source': source, 'pose': pose, 'missing': missing})
        for weapon_id in WEAPONS:
            for source in ('new', 'old'):
                image, _ = render(source, doll_type, {}, weapon_id)
                name = f'weapon{weapon_id}_t{doll_type}_{source}.jpg'
                image.save(OUT / name, quality=90)
                index['weapons'].append({'file': name, 'weapon': weapon_id, 'doll_type': doll_type, 'source': source})
    (OUT / 'index.json').write_text(json.dumps(index, indent=1) + '\n')
    problems = [entry for entry in index['outfits'] if entry['missing']]
    print(len(index['outfits']), 'outfit renders,', len(index['weapons']), 'weapon renders;',
          len(problems), 'with missing pieces')
    for entry in problems[:12]:
        print('  missing', entry['file'], entry['missing'])


if __name__ == '__main__':
    main()
