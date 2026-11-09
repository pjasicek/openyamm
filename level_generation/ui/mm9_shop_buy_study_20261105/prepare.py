#!/usr/bin/env python3
"""Prepare the MM9 Buy view study: stock data, frame backdrop, live-room crops, icons and fonts.

Reads the checked-in MM9 vendor tables and item tables, a native Obsidian house-dialogue capture and the
Thjorgard City review captures. Writes everything the browser page needs next to this script.
"""

import csv
import json
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
ASSETS = OUT / 'assets'

MM9_TABLES = ROOT / 'assets_dev/worlds/mm9/data_tables'
ENGINE_TABLES = ROOT / 'assets_dev/engine/data_tables'
FRAME_CAPTURE = ROOT / 'level_generation/ui/obsidian_curved_portraits_20260929/native/overlay_arcs/images/house-topic.png'
SOURCE_ICONS = ROOT / 'assets_source/engine/icons_x2'
MM9_MERCHANT_BACKGROUND = ROOT / 'mm9/extracted/LOCALART/LOCALART/INTERFACESCREENS/MERCHANT/MERCHANTBG.pcx'
ROOM_CAPTURES = ROOT / 'level_generation/projects/mm9r_thjorgardcity/review/v03'

# Media rectangle of the 4:3 house screen in the 1600x900 stage (the house video area).
MEDIA = (213, 54, 1077, 688)

# Vendors shown in the study: one per stock profile plus the worst padding cases.
VENDORS = [
    ('30005', '32-i10_armor_shop.png'),
    ('30010', '33-i11_weapon_shop.png'),
    ('30017', '27-i05_general_store.png'),
    ('30015', '28-i06_apothecary.png'),
    ('30020', '29-i07_library.png'),
    ('30012', '26-i04_magic_shop.png'),
    ('30136', '26-i04_magic_shop.png'),
    ('30142', '28-i06_apothecary.png'),
    ('30340', '33-i11_weapon_shop.png'),
]

SHELF_ASSETS = ['wepntabl', 'armory', 'genshelf', 'magshelf']
FONT_SOURCES = {
    'arrus.ttf': ROOT / 'level_generation/ui/obsidian_overlays_20260928/assets/fonts/openyamm_arrus_faithful.ttf',
    'create.ttf': ROOT / 'level_generation/ui/obsidian_overlays_20260928/assets/fonts/openyamm_create_faithful.ttf',
    'smallnum.ttf': ROOT / 'level_generation/ui/obsidian_overlays_20260928/assets/fonts/openyamm_smallnum_faithful.ttf',
    'comic.ttf': ROOT / 'level_generation/ui/obsidian_overlays_20260928/assets/fonts/openyamm_comic_faithful.ttf',
    'lucida.ttf': ROOT / 'level_generation/ui/obsidian_overlays_20260928/assets/fonts/openyamm_lucida_faithful.ttf',
    'fondamento.ttf': ROOT / 'level_generation/ui/hud_overlay_study_20260927/assets/fonts/Fondamento-Regular.ttf',
}


def loadItems(path):
    items = {}
    header = None
    for line in path.read_text(encoding='utf-8', errors='replace').split('\n'):
        cells = line.split('\t')
        if header is None:
            if cells[0].startswith('Item'):
                header = cells
            continue
        if cells and cells[0].strip().isdigit():
            items[int(cells[0])] = dict(zip(header, cells))
    return items


def loadEnchantNames(path):
    names = [None]
    for index, line in enumerate(path.read_text(encoding='utf-8', errors='replace').split('\n')):
        cells = line.split('\t')
        if index < 3 or len(cells) < 2 or not cells[1].strip():
            continue
        names.append(cells[1].strip())
    return names


def cellSize(item, iconPath):
    width = item.get('inventory_width', '')
    height = item.get('inventory_height', '')
    if width.isdigit() and height.isdigit():
        return int(width), int(height)
    with Image.open(iconPath) as image:
        return max(1, round(image.width / 2 / 32)), max(1, round(image.height / 2 / 32))


def findIcon(picture):
    for folder in ('assets_dev/worlds/mm9/icons_x2', 'assets_dev/engine/icons_x2'):
        candidate = ROOT / folder / f'{picture.lower()}.png'
        if candidate.exists():
            return candidate
        candidate = ROOT / folder / f'{picture}.png'
        if candidate.exists():
            return candidate
    raise FileNotFoundError(picture)


def statLine(item):
    equip = item.get('Equip Stat', '')
    mod1 = item.get('Mod1', '').strip()
    mod2 = item.get('Mod2', '').strip()
    if equip in ('Weapon', 'Weapon2', 'Weapon1or2', 'Missile'):
        bonus = f' + {mod2}' if mod2 not in ('', '0') else ''
        return f'Damage {mod1}{bonus}'
    if equip in ('Armor', 'Shield', 'Helm', 'Belt', 'Gauntlets', 'Boots', 'Cloak'):
        try:
            total = int(mod1 or 0) + int(mod2 or 0)
        except ValueError:
            return ''
        return f'Armor {total}' if total else ''
    if equip == 'LearnSkill':
        return 'Teaches the skill'
    if equip == 'Book':
        return 'Spellbook'
    return ''


TYPE_NAMES = {
    'Weapon': 'Weapon', 'Weapon2': 'Two-handed weapon', 'Weapon1or2': 'Weapon', 'Missile': 'Missile weapon',
    'Armor': 'Armour', 'Shield': 'Shield', 'Helm': 'Helm', 'Belt': 'Belt', 'Gauntlets': 'Gauntlets',
    'Boots': 'Boots', 'Cloak': 'Cloak', 'Ring': 'Ring', 'Amulet': 'Amulet', 'Misc': 'Reagent',
    'LearnSkill': 'Skill book', 'Book': 'Spellbook', 'Bottle': 'Potion', 'Reagent': 'Reagent',
}

# MM9's own merchant filter tabs (MERCHANT-COORDS.txt), plus Books for spellbooks and skill books.
CATEGORY = {
    'Weapon': 'Weapons', 'Weapon2': 'Weapons', 'Weapon1or2': 'Weapons', 'Missile': 'Weapons',
    'Armor': 'Armor', 'Shield': 'Armor', 'Helm': 'Armor', 'Belt': 'Armor', 'Cloak': 'Armor',
    'Gauntlets': 'Gloves/Boots', 'Boots': 'Gloves/Boots', 'Ring': 'Jewelry', 'Amulet': 'Jewelry',
    'LearnSkill': 'Books', 'Book': 'Books',
}


def prepareData():
    items = loadItems(ENGINE_TABLES / 'items.txt')
    items.update(loadItems(MM9_TABLES / 'items.txt'))
    standardNames = loadEnchantNames(ENGINE_TABLES / 'standard_item_enchants.txt')
    specialNames = loadEnchantNames(ENGINE_TABLES / 'special_item_enchants.txt')
    vendors = {row['vendor_id']: row for row in csv.DictReader(
        open(MM9_TABLES / 'vendors.txt', encoding='utf-8'), delimiter='\t')}
    stock = list(csv.DictReader(open(MM9_TABLES / 'vendor_stock.txt', encoding='utf-8'), delimiter='\t'))

    usedItems = {}
    outVendors = []
    for vendorId, roomCapture in VENDORS:
        vendor = vendors[vendorId]
        lanes = {}
        for lane in ('standard', 'special'):
            pages = {}
            for row in stock:
                if row['vendor_id'] != vendorId or row['lane'] != lane:
                    continue
                pages.setdefault(int(row['page']), []).append(row)
            lanes[lane] = []
            for pageIndex in sorted(pages):
                slots = []
                for row in sorted(pages[pageIndex], key=lambda r: int(r['slot'])):
                    itemId = int(row['item_id'])
                    item = items[itemId]
                    usedItems[itemId] = item
                    standardId = int(row['standard_enchant_id'])
                    specialId = int(row['special_enchant_id'])
                    name = item['Name']
                    enchantText = ''
                    if specialId:
                        enchantName = specialNames[specialId]
                        name = f'{enchantName} {name}' if enchantName.endswith("'") else f'{name} {enchantName}'
                        enchantText = enchantName
                    elif standardId:
                        power = int(row['standard_enchant_power'])
                        name = f"{name} {standardNames[standardId]}"
                        enchantText = f'{standardNames[standardId]} +{power}'
                    slots.append({'item': itemId, 'name': name, 'enchant': enchantText})
                lanes[lane].append(slots)
        outVendors.append({
            'id': vendorId,
            'name': vendor['name'],
            'location': vendor['location'],
            'profile': vendor['profile'],
            'type': vendor['source_type'],
            'merchandise': vendor['merchandise'],
            'merchantBase': float(vendor['merchant_base']),
            'restockDays': int(vendor['restock_days']),
            'room': f'assets/room_{Path(roomCapture).stem.split("-", 1)[1]}.jpg',
            'lanes': lanes,
        })

    outItems = {}
    for itemId, item in usedItems.items():
        iconSource = findIcon(item['Pic File'])
        iconName = iconSource.stem.lower()
        target = ASSETS / 'icons' / f'{iconName}.png'
        if not target.exists():
            with Image.open(iconSource) as image:
                image.save(target, optimize=True)
        width, height = cellSize(item, iconSource)
        with Image.open(iconSource) as image:
            iconWidth, iconHeight = image.size
        equip = item.get('Equip Stat', '')
        outItems[itemId] = {
            'name': item['Name'],
            'value': int(item['Value']),
            'equip': equip,
            'typeName': TYPE_NAMES.get(equip, equip),
            'category': CATEGORY.get(equip, 'Potions/Misc'),
            'skill': item.get('Skill Group', ''),
            'stat': statLine(item),
            'icon': f'assets/icons/{iconName}.png',
            'iconSize': [iconWidth, iconHeight],
            'cells': [width, height],
            'notes': item.get('Notes', '').strip('"')[:220],
        }

    payload = {'vendors': outVendors, 'items': outItems}
    (OUT / 'data.js').write_text('window.SHOP_DATA = ' + json.dumps(payload, indent=1) + ';\n', encoding='utf-8')


def prepareFrame():
    frame = Image.open(FRAME_CAPTURE).convert('RGB')
    # Replace the right panel (title, portrait, name, topics) with the clean runtime sidebar art at its layout size:
    # DialogueEventDialog is 172x368 logical at the top right of the 640x480 frame, drawn here at 1.875x.
    with Image.open(SOURCE_ICONS / 'obsidian_house_sidebar.png') as sidebar:
        sidebar = sidebar.convert('RGBA').resize((323, 690), Image.LANCZOS)
        frame.paste(sidebar, (1077, 0), sidebar)
    frame.save(ASSETS / 'frame.jpg', quality=92)



def prepareRooms():
    for _, capture in VENDORS:
        target = ASSETS / f'room_{Path(capture).stem.split("-", 1)[1]}.jpg'
        if target.exists():
            continue
        with Image.open(ROOM_CAPTURES / capture) as image:
            image.convert('RGB').crop(MEDIA).save(target, quality=88)


def prepareShelvesAndFonts():
    with Image.open(SOURCE_ICONS / 'obsidian_reading_surface.png') as surface:
        surface.convert('RGB').resize((960, 720), Image.LANCZOS).save(ASSETS / 'reading_surface.jpg', quality=88)
    for name in ('button_close_normal', 'button_close_hover', 'button_close_pressed'):
        shutil.copyfile(SOURCE_ICONS / f'obsidian_{name}.png', ASSETS / f'{name}.png')
    for name in SHELF_ASSETS:
        with Image.open(ROOT / 'assets_dev/engine/icons_x2' / f'{name}.png') as image:
            image.convert('RGB').save(ASSETS / f'shelf_{name}.jpg', quality=88)
    for target, source in FONT_SOURCES.items():
        shutil.copyfile(source, ASSETS / 'fonts' / target)
    shutil.copyfile(ROOT / 'level_generation/ui/hud_overlay_study_20260927/assets/fonts/fondamento-OFL.txt',
                    ASSETS / 'fonts' / 'fondamento-OFL.txt')


def prepareNineSlice():
    """Compose the eight carved frame slices into one image for CSS border-image (164-pixel borders)."""
    sheet = Image.new('RGBA', (584, 584), (0, 0, 0, 0))
    placements = {
        'frame_tl': (0, 0), 'frame_top': (164, 0), 'frame_tr': (420, 0),
        'frame_left': (0, 164), 'frame_right': (420, 164),
        'frame_bl': (0, 420), 'frame_bottom': (164, 420), 'frame_br': (420, 420),
    }
    for name, position in placements.items():
        with Image.open(SOURCE_ICONS / f'obsidian_{name}.png') as piece:
            sheet.paste(piece.convert('RGBA'), position)
    sheet.save(ASSETS / 'frame9.png', optimize=True)
    for name in placements:
        (ASSETS / f'{name}.png').unlink(missing_ok=True)


def prepareOriginalMerchantScreen():
    with Image.open(MM9_MERCHANT_BACKGROUND) as image:
        image.convert('RGB').save(ASSETS / 'mm9_merchantbg.jpg', quality=88)


def main():
    (ASSETS / 'icons').mkdir(parents=True, exist_ok=True)
    (ASSETS / 'fonts').mkdir(parents=True, exist_ok=True)
    prepareData()
    prepareFrame()
    prepareRooms()
    prepareShelvesAndFonts()
    prepareNineSlice()
    prepareOriginalMerchantScreen()


if __name__ == '__main__':
    main()
