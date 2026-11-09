"""Prepares the per-item Codex inputs of the MM9 inventory icon trial: the original MM9 PCX without its 3 px gold
frame (x8, nearest), an upright copy for diagonal weapons, and a sheet of MM7/MM8 x2 icons of the same family as
the style reference. Usage: python3 -I prep.py"""
import json
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
PCX = os.path.join(REPO, 'mm9/extracted/ART/ART/INVENTORYICONS')
ICONS = os.path.join(REPO, 'assets_dev/engine/icons_x2')

# Family -> MM7/MM8 style references (engine icons_x2) and the x2 target canvas the result is fitted into.
FAMILIES = {
    'ring': (['item139', 'item140', 'item145', 'item144'], (64, 60)),
    'helm': (['item112', 'item113', 'item111', 'item110'], (132, 136)),
    'chain': (['item090', 'item093', 'item092', 'item091'], (200, 206)),
    'plate': (['item096', 'item097', 'item098', 'item253'], (204, 206)),
    'belt': (['item117', 'item118', 'item120', 'item121'], (136, 52)),
    'sword': (['item001', 'item011', 'item014', 'item018'], (84, 316)),
    'axe': (['item033', 'item034', 'item035', 'item032'], (116, 284)),
    'crossbow': (['item063', 'item064', 'item065', 'item061'], (136, 312)),
    'polearm': (['item047', 'item048', 'item049', 'item046'], (144, 564)),
    'flail': (['item067', 'item068', 'item070', 'item066'], (136, 330)),
}

ITEMS = [
    (10158, 'Pearl Ring', 'ring', 'RingPearl.pcx'),
    (10210, 'Soulband', 'ring', 'Ringsoulband.pcx'),
    (10123, 'Dragon Helm', 'helm', 'DragonHelm.pcx'),
    (10125, "Jarl's Helm", 'helm', 'JarlHelm.pcx'),
    (10102, 'Chedian Chain', 'chain', 'ChehDianChain.pcx'),
    (10113, 'Thjoradric Plate', 'plate', 'ThjoradricPlate.pcx'),
    (10152, "Soldier's Belt", 'belt', 'BeltSoldiers.pcx'),
    (10153, 'Regal Belt', 'belt', 'BeltRegal.pcx'),
    (10012, 'Mercenary Sword', 'sword', 'BladeMercenary.pcx'),
    (10039, 'Storm Axe', 'axe', 'Axestorm.pcx'),
    (10055, 'Thjoradric Arbalest', 'crossbow', 'XbowArbalest.pcx'),
    (10064, 'Regimental Halberd', 'polearm', 'HalberdReg.pcx'),
    (10074, 'War Star', 'flail', 'FlailWarStar.pcx'),
]
DIAGONAL = {'sword', 'axe', 'crossbow', 'polearm', 'flail'}


def find_pcx(name):
    for f in os.listdir(PCX):
        if f.lower() == name.lower():
            return os.path.join(PCX, f)
    raise SystemExit('missing ' + name)


def style_sheet(names, path):
    images = [Image.open(os.path.join(ICONS, n + '.png')).convert('RGBA') for n in names]
    scale = min(1.0, 600 / max(i.height for i in images))
    images = [i.resize((round(i.width * scale), round(i.height * scale)), Image.LANCZOS) for i in images]
    w = sum(i.width for i in images) + 40 * (len(images) + 1)
    h = max(i.height for i in images) + 80
    sheet = Image.new('RGBA', (w, h), (96, 96, 96, 255))
    x = 40
    for i in images:
        sheet.alpha_composite(i, (x, 40 + (h - 80 - i.height) // 2))
        x += i.width + 40
    sheet.convert('RGB').save(path)


def main():
    manifest = []
    for item_id, name, family, pcx in ITEMS:
        folder = os.path.join(HERE, 'items', str(item_id))
        os.makedirs(folder, exist_ok=True)
        src = Image.open(find_pcx(pcx)).convert('RGB').crop((3, 3, 61, 61))
        src.resize((464, 464), Image.NEAREST).save(os.path.join(folder, 'source_pcx.png'))
        if family in DIAGONAL:
            # MM9 draws weapons bottom-left to top-right; rotate 45 degrees counter-clockwise to stand it upright.
            big = src.resize((464, 464), Image.LANCZOS)
            pad = Image.new('RGB', (680, 680), (0, 0, 0))
            pad.paste(big, (108, 108))
            pad.rotate(45, Image.BICUBIC).save(os.path.join(folder, 'source_upright.png'))
        style_sheet(FAMILIES[family][0], os.path.join(folder, 'style_reference.png'))
        manifest.append({'item_id': item_id, 'name': name, 'family': family, 'pcx': pcx,
                         'style_refs': FAMILIES[family][0], 'target_x2': FAMILIES[family][1]})
    with open(os.path.join(HERE, 'items.json'), 'w') as f:
        json.dump(manifest, f, indent=1)


main()
