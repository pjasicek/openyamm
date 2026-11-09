"""The character screen's jewellery panel (character.yml CharacterDollJewelryOverlayPanel) filled with MM9 gauntlets,
amulets and rings, beside panels of MM6, MM7 and MM8 jewellery, drawn the way the engine draws them
(GameplayScreenRuntime::resolveCharacterEquipmentRenderRect):

- gauntlets: from the cell's top-left plus the item's complex_item_pictures point (MM9: runtime/complex_item_pictures.txt,
  centred; MM6-MM8: none) plus any item_visuals.txt placement, then shrunk about the centre by the jewellery scale;
- amulets and rings: centred in the cell, shrunk by the jewellery scale.

    python3 scripts/jewelry.py        writes review/jewelry/panel_<name>.jpg and review/jewelry/index.json
"""
import csv
import json

from PIL import Image, ImageDraw

import mm9_paperdoll as M

P = M.P
D = P.D
OUT = P.PROJECT / 'review/jewelry'
ICON_PROJECT = M.ICON_PROJECT
PANEL = (176, 345)
CELLS = {'Gauntlets': (21, 68, 40, 72), 'Amulet': (112, 68, 40, 72), 'Ring1': (21, 177, 40, 40),
         'Ring2': (69, 177, 40, 40), 'Ring3': (117, 177, 40, 40), 'Ring4': (21, 225, 40, 40),
         'Ring5': (69, 225, 40, 40), 'Ring6': (117, 225, 40, 40)}
BORDER, FILL, BACK = (0x77, 0x69, 0x53), (0x1b, 0x21, 0x17), (0x1d, 0x1b, 0x18)
S = D.SCALE
MM9_GAUNTLETS = [10133, 10134, 10135, 10136, 10137, 10138, 10139, 10140, 10141, 10206, 10227, 10237, 10365]
MM9_AMULETS = [10160, 10161, 10162, 10163, 10164, 10213, 10214, 10215, 10216, 10217, 10218, 10228]
MM9_RINGS = [10155, 10156, 10157, 10158, 10159, 10209, 10210, 10211, 10212, 10222, 10232, 10235]
REFERENCES = {'MM8': (128, 147, [137, 138, 139, 140, 144, 145]), 'MM7': (912, 932, [922, 923, 925, 927, 929, 931]),
              'MM6': (1712, 1732, [1722, 1723, 1724, 1725, 1726, 1731])}


def visuals():
    """item_visuals.txt (engine): jewellery scales and doll type 0 gauntlet placements of the MM6-MM8 items."""
    scale, placement = {}, {}
    rows = csv.reader((D.ROOT / 'assets_dev/engine/data_tables/item_visuals.txt').open(), delimiter='\t')
    for row in rows:
        if row and row[0] == 'inventory':
            scale[int(row[1])] = float(row[9])
        elif row and row[0] == 'placement' and row[2] == '0' and row[3] == 'Gauntlets':
            placement[int(row[1])] = (int(row[4]), int(row[5]))
    return scale, placement


SCALE, PLACEMENT = visuals()
POINTS = {int(row[1]): (int(row[4]), int(row[5])) for row in
          csv.reader((P.RUNTIME / 'complex_item_pictures.txt').open(), delimiter='\t') if row and row[0].isdigit()}


def mm9_icon(item_id):
    designs = json.loads((ICON_PROJECT / 'designs.json').read_text())
    design = next(entry['design_id'] for entry in designs if item_id in entry['item_ids'])
    return Image.open(ICON_PROJECT / f'items/{design}/icon_a_x2.png').convert('RGBA')


def panel(title, gauntlet, amulet, rings):
    """gauntlet/amulet/rings: (image at x2, item id, source)."""
    canvas = Image.new('RGBA', (PANEL[0] * S, PANEL[1] * S), BACK + (255,))
    draw = ImageDraw.Draw(canvas)
    for x, y, w, h in CELLS.values():
        draw.rectangle(((x - 1) * S, (y - 1) * S, (x + w + 1) * S - 1, (y + h + 1) * S - 1), fill=BORDER)
        draw.rectangle((x * S, y * S, (x + w) * S - 1, (y + h) * S - 1), fill=FILL)
    for cell, entry in [('Gauntlets', gauntlet), ('Amulet', amulet)] + [(f'Ring{n + 1}', r) for n, r in enumerate(rings)]:
        if entry is None:
            continue
        image, item_id = entry
        x, y, w, h = CELLS[cell]
        rect_w, rect_h = image.width / S, image.height / S
        if cell == 'Gauntlets':
            point = POINTS.get(item_id, (0, 0))
            extra = PLACEMENT.get(item_id, (0, 0))
            left, top = x + point[0] + extra[0], y + point[1] + extra[1]
        else:
            left, top = x + (w - rect_w) / 2, y + (h - rect_h) / 2
        scale = SCALE.get(item_id, 1.0)
        left += rect_w * (1 - scale) / 2
        top += rect_h * (1 - scale) / 2
        size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
        canvas.alpha_composite(image.resize(size, Image.Resampling.LANCZOS), (round(left * S), round(top * S)))
    draw.text((6, 6), title, fill=(235, 220, 190))
    return canvas.convert('RGB')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    for world, (gauntlet, amulet, rings) in REFERENCES.items():
        layer = lambda item_id: D.layer(D.ENGINE_ITEMS[item_id].icon_name)       # noqa: E731
        image = panel(f'{world} reference', (layer(gauntlet), gauntlet), (layer(amulet), amulet),
                      [(layer(r), r) for r in rings])
        image.save(OUT / f'panel_{world}.jpg', quality=90)
        index.append({'file': f'panel_{world}.jpg', 'title': f'{world} reference', 'items': [gauntlet, amulet] + rings})
    for number, gauntlet in enumerate(MM9_GAUNTLETS):
        amulet = MM9_AMULETS[number % len(MM9_AMULETS)]
        rings = [MM9_RINGS[(number * 6 + k) % len(MM9_RINGS)] for k in range(6)]
        image = panel(f'MM9 {number + 1}', (mm9_icon(gauntlet), gauntlet), (mm9_icon(amulet), amulet),
                      [(mm9_icon(r), r) for r in rings])
        name = f'panel_mm9_{number + 1:02d}.jpg'
        image.save(OUT / name, quality=90)
        index.append({'file': name, 'title': f'MM9 {number + 1}', 'items': [gauntlet, amulet] + rings})
    (OUT / 'index.json').write_text(json.dumps(index, indent=1) + '\n')
    print(len(index), 'panels')


if __name__ == '__main__':
    main()
