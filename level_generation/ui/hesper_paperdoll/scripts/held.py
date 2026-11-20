"""Preview held weapons and emitters on the dolls with the engine's placement rules (GameplayScreenRuntime::
resolveCharacterEquipmentRenderRect): a main-hand weapon's Equip X/Y point goes on the right hand's fingers anchor
(their x centre, the hold point's y plus the doll's main-hand offset), under the fingers layer; a shield (an emitter)
puts its point on the left closed hand plus the doll's shield offset. Native items preview with their own table
values, Hesper items with grips.yml.

    python3 scripts/held.py <output.png> <item id> [...]
"""
import csv
import sys

import yaml
from PIL import Image, ImageDraw

import dolls as D

GRIPS = yaml.safe_load((D.PROJECT / 'grips.yml').read_text())['grips']
ICONS_X2 = D.ROOT / 'design/kreegan_world/art/item_icons/x2'


def draft_items():
    rows = csv.reader(D.ROOT.joinpath('design/kreegan_world/data/items.txt').open(), delimiter='\t')
    return {int(row[0]): row for row in rows if row and row[0].isdigit()}


def turned(icon, grip):
    """A gun's icon and grip as the doll holds it (grips.yml `up`: a quarter turn counter-clockwise; `out`: mirrored;
    logical pixels)."""
    if len(grip) < 3:
        return icon, tuple(grip)
    width = icon.width // D.SCALE
    if grip[2] == 'up':
        return icon.transpose(Image.Transpose.ROTATE_90), (grip[1], width - grip[0])
    return icon.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (width - grip[0], grip[1])


def held_item(item_id):
    """(icon at physical scale, equip stat, equip point)."""
    if item_id in GRIPS:
        row = draft_items()[item_id]
        icon, grip = turned(Image.open(ICONS_X2 / f'{row[1]}.png').convert('RGBA'), GRIPS[item_id])
        return icon, row[4], grip
    rows = csv.reader(D.TABLES.joinpath('items.txt').open(encoding='latin-1'), delimiter='\t')
    row = next(row for row in rows if row and row[0] == str(item_id))
    return D.layer(row[1]), row[4], (int(row[14]), int(row[15]))


def render(item_id, doll_type):
    icon, stat, (equip_x, equip_y) = held_item(item_id)
    doll = D.DOLLS[doll_type]
    kind = D.DOLL_TYPES[doll_type]
    canvas = D.doll(doll_type, weapon=stat != 'Shield')
    rows = list(csv.reader(D.TABLES.joinpath('doll_types.txt').open(), delimiter='\t'))
    row = next(r for r in rows if r and r[0] == str(doll_type))
    main_offset = (int(row[22]), -int(row[23]))
    shield = (int(row[26]), -int(row[27]))
    if stat == 'Shield':
        point = (kind.left_hand_closed[0] + shield[0] - equip_x, kind.left_hand_closed[1] + shield[1] - equip_y)
        canvas.alpha_composite(icon, D.preview.physical(point))
        return canvas
    fingers = D.layer(doll.right_hand_fingers_asset)
    anchor_x = kind.right_hand_fingers[0] + round(fingers.width / D.SCALE / 2) if fingers else \
        kind.right_hand_closed[0] + main_offset[0]
    anchor_y = kind.right_hand_closed[1] + main_offset[1]
    canvas.alpha_composite(icon, D.preview.physical((anchor_x - equip_x, anchor_y - equip_y)))
    if fingers is not None:
        canvas.alpha_composite(fingers, D.preview.physical(kind.right_hand_fingers))
    return canvas


def main():
    output, *ids = sys.argv[1:]
    cells = [[render(int(item_id), doll_type) for doll_type in range(5)] for item_id in ids]
    width, height = D.WIDTH // 2, D.HEIGHT // 2
    sheet = Image.new('RGB', (width * 5, (height + 14) * len(cells)), (28, 28, 30))
    draw = ImageDraw.Draw(sheet)
    for row_index, (item_id, row) in enumerate(zip(ids, cells)):
        draw.text((4, row_index * (height + 14)), item_id, fill='white')
        for column, image in enumerate(row):
            sheet.paste(image.resize((width, height), Image.Resampling.LANCZOS).convert('RGB'),
                        (column * width, row_index * (height + 14) + 14))
    sheet.save(output)


if __name__ == '__main__':
    main()
