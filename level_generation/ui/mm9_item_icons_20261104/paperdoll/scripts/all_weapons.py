"""Every MM9 weapon, missile weapon and shield in the hand with the new icons and the proposed grips
(runtime/equip_anchors.tsv), the way the game composites the character screen:

- main-hand weapons: the grip point on the doll type's main-hand anchor, the fingers over it (two-handed weapons and
  spears hold the left hand on the shaft);
- shields: the left hand closed, the grip point at that hand plus the doll type's shield offset;
- bows and crossbows: centred on the doll type's bow point (the grip is not used).

    python3 scripts/all_weapons.py [item id ...]     writes review/weapons/<id>.jpg (all five dolls side by side)
"""
import csv
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import outfit as O

PROJECT = O.PROJECT
OUT = PROJECT / 'review/weapons'
ICONS = PROJECT / 'work/_all_weapons_x2'
DESIGNS = {item: entry['design_id'] for entry in O.json.loads((O.ICON_PROJECT / 'designs.json').read_text())
           for item in entry['item_ids']}
ROWS = {int(row[0]): row for row in O.preview.read_tsv(O.TABLES / 'doll_types.txt')[1:]
        if len(row) > 27 and row[0].strip().isdigit()}
BOW_POINT = {doll_type: O.preview.legacy_point(row, 24) for doll_type, row in ROWS.items()}
SHIELD_OFFSET = {doll_type: O.preview.legacy_point(row, 26) for doll_type, row in ROWS.items()}
ANCHORS = {int(row['Item #']): row for row in csv.DictReader((PROJECT / 'runtime/equip_anchors.tsv').open(),
                                                             delimiter='\t')}


def icon_root():
    ICONS.mkdir(parents=True, exist_ok=True)
    for item_id in ANCHORS:
        Image.open(O.ICON_PROJECT / f'items/{DESIGNS[item_id]}/icon_a_x2.png').save(ICONS / f'mm9_item_{item_id}.png')
    return O.preview.AssetIndex([(ICONS, 2)] + O.preview.declared_icon_roots())


def render(assets, doll_type, item_id):
    row = O.MM9_ROWS[item_id]
    stat, skill = row['Equip Stat'], row['Skill Group']
    grip = ANCHORS[item_id]
    equip_x, equip_y = int(grip['New X']), int(grip['New Y'])
    doll, kind = O.DOLLS[doll_type], O.DOLL_TYPES[doll_type]
    layer = lambda name: O.layer(assets, name)      # noqa: E731
    canvas = layer(doll.background_asset).crop((0, 0, O.preview.PAPERDOLL_WIDTH * O.SCALE,
                                                O.preview.PAPERDOLL_HEIGHT * O.SCALE))
    icon = layer(row['Pic File'])
    if stat == 'Missile' and skill == 'Bow':
        # the bow is drawn behind the body, centred on the bow point
        bow = BOW_POINT[doll_type]
        O.paste(canvas, icon, (bow[0] - icon.width // (2 * O.SCALE), bow[1] - icon.height // (2 * O.SCALE)))
        O.paste(canvas, layer(doll.body_asset), (doll.body_x, doll.body_y))
        O.paste(canvas, layer(doll.right_hand_open_asset), kind.right_hand_open)
        O.paste(canvas, layer(doll.left_hand_open_asset), kind.left_hand_fingers)
        return canvas
    O.paste(canvas, layer(doll.body_asset), (doll.body_x, doll.body_y))
    if stat == 'Shield':
        O.paste(canvas, layer(doll.right_hand_open_asset), kind.right_hand_open)
        O.paste(canvas, layer(doll.left_hand_closed_asset), kind.left_hand_closed)
        shield = SHIELD_OFFSET[doll_type]
        point = (kind.left_hand_closed[0] + shield[0] - equip_x, kind.left_hand_closed[1] + shield[1] - equip_y)
        O.paste(canvas, icon, point)
        return canvas
    two_handed = stat == 'Weapon2' or skill == 'Spear'
    O.paste(canvas, layer(doll.right_hand_hold_asset), kind.right_hand_closed)
    if not two_handed:
        O.paste(canvas, layer(doll.left_hand_open_asset), kind.left_hand_fingers)
    fingers = layer(doll.right_hand_fingers_asset)
    anchor_x = kind.right_hand_fingers[0] + round(fingers.width / O.SCALE * 0.5)
    anchor_y = kind.right_hand_closed[1] + O.MAIN_HAND_OFFSET[doll_type][1]
    O.paste(canvas, icon, (anchor_x - equip_x, anchor_y - equip_y))
    O.paste(canvas, fingers, kind.right_hand_fingers)
    if two_handed:
        O.paste(canvas, layer(doll.left_hand_hold_asset), O.LEFT_HOLD_POINT[doll_type])
    return canvas


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assets = icon_root()
    ids = [int(value) for value in sys.argv[1:]] or sorted(ANCHORS)
    for item_id in ids:
        cells = [render(assets, doll_type, item_id).convert('RGB') for doll_type in O.DOLL_NAMES]
        sheet = Image.new('RGB', (sum(cell.width for cell in cells), cells[0].height + 18), (20, 20, 20))
        for index, cell in enumerate(cells):
            sheet.paste(cell, (index * cell.width, 18))
        row = ANCHORS[item_id]
        ImageDraw.Draw(sheet).text((4, 3), f"{item_id} {row['Name']} ({row['Equip Stat']}, {row['Skill Group']}) "
                                           f"grip {row['New X']},{row['New Y']}", fill=(255, 220, 120))
        sheet = sheet.resize((sheet.width // 2, sheet.height // 2), Image.Resampling.LANCZOS)
        sheet.save(OUT / f'{item_id}.jpg', quality=86)
    print(len(ids), 'sheets in', OUT)


if __name__ == '__main__':
    main()
