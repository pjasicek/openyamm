"""Prepares the full MM9 icon pass: one design per distinct source PCX (items sharing a PCX share the icon). For each
design it writes items/<id>/source_pcx.png (frame removed, x8 nearest), source_upright.png for diagonal weapons,
style_reference.png (four MM6-MM8 x2 icons of the family) and briefs/<id>.md, and lists everything in designs.json.
Designs whose folder already has paint_a.png are skipped, and an existing brief is never overwritten.
Usage: python3 -I prep_all.py"""
import csv
import json
import os
import yaml
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
PCX = os.path.join(REPO, 'mm9/extracted/ART/ART/INVENTORYICONS')
ICONS = os.path.join(REPO, 'assets_dev/engine/icons_x2')
ITEMS = os.path.join(REPO, 'assets_dev/worlds/mm9/data_tables/items.txt')
OLD_NOTES = os.path.join(REPO, 'tools/mm9_import_discovery/mm9_item_generated_art.yml')

UPRIGHT = 'Perfectly vertical, functional end at the top, grip or butt at the bottom, seen flat from the side.'
# family: (style references, x2 fit box, diagonal source, view rule)
FAMILIES = {
    'sword': (['item001', 'item011', 'item014', 'item018'], (84, 316), True, UPRIGHT + ' Point at the top.'),
    'sword2h': (['item006', 'item007', 'item008', 'item010'], (96, 390), True, UPRIGHT + ' Point at the top.'),
    'dagger': (['item021', 'item023', 'item026', 'item028'], (84, 246), True, UPRIGHT + ' Point at the top.'),
    'throwing': (['item022', 'item026', 'item032', 'item031'], (110, 250), True,
                 UPRIGHT + ' Keep the source\'s grouping if it shows several pieces together (for example a fan of'
                 ' blades), arranged upright.'),
    'axe': (['item033', 'item034', 'item035', 'item032'], (116, 284), True, UPRIGHT + ' Head at the top.'),
    'axe2h': (['item036', 'item037', 'item039', 'item040'], (142, 520), True, UPRIGHT + ' Head at the top.'),
    'bow': (['item056', 'item057', 'item058', 'item060'], (128, 398), True,
            'Perfectly vertical bow seen flat from the side, string straight down one side, grip at mid-height, like'
            ' the reference bows.'),
    'crossbow': (['item063', 'item064', 'item065', 'item061'], (140, 316), True,
                 'Vertical, prod/bow at the top spread horizontally, stock running straight down to the butt at the'
                 ' bottom, seen from directly above like the reference crossbows.'),
    'firearm': (['item063', 'item064', 'item065', 'item061'], (100, 360), True,
                'Perfectly vertical, muzzle at the top, stock/butt at the bottom, seen flat from the side.'),
    'spear': (['item042', 'item043', 'item044', 'item045'], (100, 572), True,
              UPRIGHT + ' Head at the top. Long shaft: the whole weapon is about five times taller than its widest'
              ' point; the head takes only the top fifth.'),
    'halberd': (['item046', 'item047', 'item048', 'item049'], (144, 564), True,
                UPRIGHT + ' Head at the top. Long shaft: the whole weapon is about five times taller than its widest'
                ' point; the head takes only the top fifth.'),
    'mace': (['item066', 'item068', 'item076', 'item077'], (130, 336), True, UPRIGHT + ' Head at the top.'),
    'hammer': (['item071', 'item072', 'item073', 'item075'], (122, 304), True, UPRIGHT + ' Head at the top.'),
    'hammer2h': (['item075', 'item070', 'item078', 'item074'], (142, 480), True, UPRIGHT + ' Head at the top.'),
    'flail': (['item067', '7item054', 'item066', 'item068'], (140, 324), True,
              'Like the reference flails: the handle stands vertical with its grip at the bottom and the chain'
              ' attachment at its TOP; the chain(s) hang DOWN from the top of the handle under gravity, alongside the'
              ' handle, so the striking head(s) hang near the lower half beside the handle. Never point the chain'
              ' or head upward. Seen flat from the side.'),
    'staff': (['item079', 'item080', 'item081', 'item082'], (120, 576), True, UPRIGHT + ' Head/ornament at the top.'),
    'shield': (['item099', 'item102', 'item106', 'item108'], (204, 300), False,
               'Straight front view of the shield face, upright and symmetric, like the reference shields.'),
    'helm': (['item112', 'item113', 'item111', '6helm2'], (132, 136), False,
             'Straight front view, perfectly symmetric, upright, like the reference helms. Empty, no head.'),
    'armor': (['item090', 'item093', 'item096', 'item085'], (204, 206), False,
              'MM8-style three-quarter view like the reference armours: the empty garment turned about 30 degrees so'
              ' its front faces toward the viewer\'s left, the near (right) shoulder larger, the far side and armhole'
              ' receding on the image right; camera slightly above chest height so the hollow inside of the neck'
              ' opening and the far armhole are visible. Torso piece only as the source shows it. No body, no stand.'),
    'boots': (['item132', 'item133', 'item134', 'item135'], (132, 148), False,
              'A pair of boots side by side, upright, seen from the side and slightly front, toes pointing to the'
              ' viewer\'s left, like the reference boots.'),
    # gauntlets: 68x128 (34x64 logical) keeps the glove inside the jewellery panel's 40x72 cell with a margin, as MM7's
    # 61-63 px gloves do (2026-11-05; was 86x142, which touched the cell's edge)
    'gauntlets': (['item127', 'item128', 'item129', 'item130'], (68, 128), False,
                  'A single glove/gauntlet standing upright, fingers at the top, cuff at the bottom, seen from the'
                  ' back of the hand, like the reference gauntlets.'),
    'belt': (['item117', 'item118', 'item120', 'item121'], (136, 52), False,
             'The front half of the belt seen straight from the front as a wide, gently curved horizontal band (a'
             ' shallow smile-shaped arc), buckle or clasp at the centre, like the reference belts.'),
    'ring': (['item139', 'item140', 'item145', 'item144'], (64, 60), False,
             'Straight from the front with only a slight downward tilt, the setting at top centre, the band symmetric'
             ' below it, like the reference rings.'),
    'amulet': (['item147', 'item148', 'item149', 'item150'], (72, 110), False,
               'The pendant hanging vertically, seen straight from the front, symmetric, with only a short loop or'
               ' bail of its chain at the top (no long chain), like the reference amulets.'),
    'book': (['item207', '7item191', 'book3', 'item275'], (144, 128), False,
             'A closed book lying in a three-quarter view from slightly above, front cover facing the viewer, like the'
             ' reference books.'),
    'scroll': (['item199', '7item182', 'scroll5', 'item265'], (140, 72), False,
               'Presented like the reference scrolls: a rolled scroll lying horizontally, or an open sheet/letter seen'
               ' from the front, whichever the source shows.'),
    'key': (['item224', '7item205', 'keys1', 'keyring'], (64, 124), False,
            'Hanging vertically, bow (handle) at the top and bit at the bottom, seen flat from the front, like the'
            ' reference keys.'),
    'bottle': (['item162', 'item267', '7item259', 'item280'], (72, 124), False,
               'Upright, seen straight from the front at eye level, like the reference bottles and jars.'),
    'misc': (['7item259', 'statuet1', 'keg', 'item269'], (128, 128), False,
             'The object in its natural resting orientation, seen from the front or a gentle three-quarter view'
             ' slightly from above, like the reference quest items.'),
}


# Per-design x2 fit boxes where the family box would misstate the object's size (bucklers are smaller than shields).
BOX_OVERRIDES = {10142: (136, 168), 10143: (150, 186),
                 # wide-guard swords: the default width made them shorter than every MM6-MM8 sword
                 10175: (100, 316), 10176: (100, 316),
                 # Blackpowder hangs behind the body at the bow point: no taller than MM crossbows, or its muzzle shows over the head
                 10188: (80, 240)}


def family_of(row):
    equip, skill, pcx = row[4], row[5], row[36].split('/')[-1].lower()
    if equip == 'Weapon':
        if skill == 'Mace':
            return 'flail' if pcx.startswith('flail') else 'hammer' if 'hammer' in pcx else 'mace'
        return {'Sword': 'sword', 'Dagger': 'dagger', 'Axe': 'axe'}[skill]
    if equip == 'Weapon2':
        if skill == 'Spear':
            return 'spear' if pcx.startswith('spear') else 'halberd'
        return {'Sword': 'sword2h', 'Axe': 'axe2h', 'Mace': 'hammer2h', 'Staff': 'staff'}[skill]
    if equip == 'Missile':
        if skill == 'Throwing':
            return 'throwing'
        return 'firearm' if pcx.startswith('blackpowder') else 'crossbow' if pcx.startswith('xbow') else 'bow'
    simple = {'Armor': 'armor', 'Helm': 'helm', 'Boots': 'boots', 'Gauntlets': 'gauntlets', 'Belt': 'belt',
              'Ring': 'ring', 'Amulet': 'amulet', 'Shield': 'shield', 'LearnSkill': 'book'}
    if equip in simple:
        return simple[equip]
    if 'key' in pcx and 'book' not in pcx:
        return 'key'
    if 'book' in pcx or 'manuscript' in pcx:
        return 'book'
    if equip == 'Mscroll' or 'scroll' in pcx or 'writ' in pcx or 'letter' in pcx:
        return 'scroll'
    if 'amulet' in pcx:
        return 'amulet'
    if 'shield' in pcx:
        return 'shield'
    if 'potion' in pcx or 'elixir' in pcx:
        return 'bottle'
    return 'misc'


def find_pcx(name):
    for f in os.listdir(PCX):
        if f.lower() == name.lower():
            return os.path.join(PCX, f)
    raise SystemExit('missing ' + name)


def style_sheet(names, path):
    images = [Image.open(os.path.join(ICONS, n.lower() + '.png')).convert('RGBA') for n in names]
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


def canvas_size(family):
    box = FAMILIES[family][1]
    return '1024x1536' if box[1] > box[0] * 1.6 else '1536x1024' if box[0] > box[1] * 1.6 else '1024x1024'


def main():
    old = yaml.safe_load(open(OLD_NOTES))['items']
    rows = list(csv.reader(open(ITEMS, encoding='latin-1'), delimiter='\t'))[1:]
    order = list(FAMILIES)
    rows = [r for r in rows if len(r) > 36]
    rows.sort(key=lambda r: (order.index(family_of(r)), int(r[0])))
    designs = {}
    for r in rows:
        pcx = r[36].split('/')[-1].lower()
        if pcx not in designs:
            designs[pcx] = {'design_id': int(r[0]), 'name': r[2], 'family': family_of(r), 'pcx': r[36],
                            'item_ids': [], 'names': [], 'notes': r[16].strip()}
        designs[pcx]['item_ids'].append(int(r[0]))
        if r[2] not in designs[pcx]['names']:
            designs[pcx]['names'].append(r[2])
    out = []
    for pcx, d in designs.items():
        family = d['family']
        refs, box, diagonal, view = FAMILIES[family]
        d['target_x2'] = list(BOX_OVERRIDES.get(d['design_id'], box))
        d['style_refs'] = refs
        out.append(d)
        folder = os.path.join(HERE, 'items', str(d['design_id']))
        os.makedirs(folder, exist_ok=True)
        if os.path.exists(os.path.join(folder, 'paint_a.png')):
            continue
        src = Image.open(find_pcx(pcx)).convert('RGB')
        # 64x64 inventory pictures carry a 3 px gold frame; the odd larger picture (the 200x200 basket) has none.
        src = src.crop((3, 3, 61, 61)) if src.size == (64, 64) else src
        src.resize((464, 464), Image.NEAREST if src.width < 464 else Image.LANCZOS).save(os.path.join(folder, 'source_pcx.png'))
        if diagonal:
            big = src.resize((464, 464), Image.LANCZOS)
            pad = Image.new('RGB', (680, 680), (0, 0, 0))
            pad.paste(big, (108, 108))
            pad.rotate(45, Image.BICUBIC).save(os.path.join(folder, 'source_upright.png'))
        style_sheet(refs, os.path.join(folder, 'style_reference.png'))
        raw = d['design_id'] - 10000
        old_note = ' '.join(old[raw]['prompt'].split()) if raw in old else ''
        lines = [f'# Item {d["design_id"]} {d["name"]} ({family}). Folder: items/{d["design_id"]}. '
                 f'Size {canvas_size(family)}.',
                 'Deliverable: ONE candidate only, `paint_a.png` (ignore the "two candidates" line of COMMON.md;'
                 ' record it in generation_runs.json the same way).',
                 'Repaint exactly the object shown in source_pcx.png: same parts, proportions, colours, materials'
                 ' and ornaments. Study the source closely before painting and keep every distinctive detail;'
                 ' do not substitute a generic item of this kind.',
                 f'VIEW: {view}']
        if len(d['names']) > 1:
            lines.append('This picture is shared by: ' + ', '.join(d['names'][:6]) + '.')
        if d['notes']:
            lines.append(f'MM9 description (context only, not text to draw): {d["notes"][:400]}')
        if old_note:
            lines.append('Design notes from an earlier pass (their view, size and transparency instructions are'
                         f' superseded by this brief): {old_note[:600]}')
        brief = os.path.join(HERE, 'briefs', f'{d["design_id"]}.md')
        if not os.path.exists(brief):  # never overwrite: briefs may carry hand-written corrections
            with open(brief, 'w') as f:
                f.write('\n'.join(lines) + '\n')
    with open(os.path.join(HERE, 'designs.json'), 'w') as f:
        json.dump(out, f, indent=1)
    from collections import Counter
    print(len(out), 'designs', Counter(d['family'] for d in out))


main()
