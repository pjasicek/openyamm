#!/usr/bin/env python3
"""Copy and downscale the existing game art used by the solo action HUD mockups into art/ and fonts/.

Every image here is an existing OpenYAMM asset (assets_dev, assets_source or an earlier UI study); nothing is
generated. The two gameplay captures come from tours/background.yml and are converted by --captures.
"""

import argparse
import shutil
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ICONS = ROOT / 'assets_dev/engine/icons_x2'
SOURCE_ICONS = ROOT / 'assets_source/engine/icons_x2'
MENUS = ROOT / 'assets_dev/engine/hud_x2/menus'
SPELLS = ROOT / 'level_generation/ui/combat_orders_20261108/art/spells'
FONTS = ROOT / 'assets_dev/engine/fonts/truetype'

# (source, published name, longest side or None)
ART = [
    (ICONS / 'pc03-01.png', 'face_pc03.png', None),
    (MENUS / 'omenu_frame.png', 'omenu_frame.png', None),
    (MENUS / 'omenu_button_small_default.png', 'omenu_button_small.png', None),
    (MENUS / 'omenu_button_small_hover.png', 'omenu_button_small_hover.png', None),
    (MENUS / 'omenu_keycap.png', 'omenu_keycap.png', None),
    (MENUS / 'omenu_seal.png', 'omenu_seal.png', None),
    (SOURCE_ICONS / 'obsidian_party_endcap_socket.png', 'endcap_socket.png', 400),
    (SOURCE_ICONS / 'obsidian_party_endcap_compact.png', 'endcap_compact.png', 400),
    (SOURCE_ICONS / 'obsidian_hud_portrait_rim_normal.png', 'portrait_rim.png', None),
    (SOURCE_ICONS / 'obsidian_hud_portrait_rim_selected.png', 'portrait_rim_selected.png', None),
    (SOURCE_ICONS / 'obsidian_hud_selection_diamond.png', 'selection_diamond.png', None),
    (SOURCE_ICONS / 'obsidian_hud_status_plate.png', 'status_plate.png', None),
    (SOURCE_ICONS / 'obsidian_enemy_health_frame.png', 'enemy_health_frame.png', None),
    (SOURCE_ICONS / 'obsidian_skills_surface.png', 'skills_surface.png', None),
    (SOURCE_ICONS / 'obsidian_personal_buffs.png', 'personal_buffs.png', 128),
    (SOURCE_ICONS / 'obsidian_frame_tl.png', 'frame_tl.png', None),
    (SOURCE_ICONS / 'obsidian_frame_top.png', 'frame_top.png', None),
    (SOURCE_ICONS / 'obsidian_frame_left.png', 'frame_left.png', None),
    (ICONS / 'item178.png', 'item_cure_wounds.png', 128),
    (ICONS / 'item177.png', 'item_magic_potion.png', 128),
    (ICONS / 'item199.png', 'item_scroll.png', 128),
    (ICONS / 'lshield1.png', 'item_kite_shield.png', 160),
    (ICONS / 'lshield2.png', 'item_tower_shield.png', 160),
    (ICONS / '7item115.png', 'item_boots.png', 160),
    (ICONS / 'item004.png', 'item_sword.png', 300),
    (ICONS / '7item024.png', 'item_axe.png', 300),
    (ICONS / '7item043.png', 'item_longbow.png', 300),
]
BUFFS = ['sbs02a', 'sbs07a', 'sbf05a', 'sbe05a', 'sbl08a', 'sbl09a', 'sbv02a', 'sba02a', 'sbb07a', 'sba06a',
         'sbs03a', 'sbdk07a', 'sbf08a', 'sba10a', 'combat', 'sbl06a', 'sbm03a', 'sbb09a']
DEBUFFS = ['slow', 'stun', 'fear', 'paralyze', 'dark_grasp']
SPELL_ART = ['fireball', 'firebolt', 'lightningbolt', 'heal', 'curepoison', 'icebolt', 'sunray', 'regeneration',
             'shrapmetal', 'stoneskin', 'flyingfist', 'haste', 'bless', 'heroism', 'powercure', 'mindblast',
             'spiritlash', 'toxiccloud', 'turnundead', 'lifedrain', 'dragonbreath', 'incinerate', 'harm', 'lightbolt',
             'dayofthegods', 'paralyze', 'slow']
FONT_FILES = ['fondamento_regular.ttf', 'openyamm_arrus_faithful.ttf', 'openyamm_lucida_faithful.ttf',
              'openyamm_smallnum_faithful.ttf', 'alegreya_variable.ttf', 'fondamento_ofl.txt', 'alegreya_ofl.txt']


def copyScaled(source: Path, target: Path, longest):
    image = Image.open(source).convert('RGBA')
    if longest and max(image.size) > longest:
        image.thumbnail((longest, longest), Image.LANCZOS)
    image.save(target, optimize=True)


def captures(clean: Path, hud: Path):
    """The clean capture becomes the background; the HUD capture gives the native top bar, minimap and buff panels."""
    art = HERE / 'art'
    Image.open(clean).convert('RGB').save(art / 'bg_goblins.jpg', quality=90)
    native = Image.open(hud).convert('RGBA')
    native.convert('RGB').save(art / 'native_today.jpg', quality=90)
    native.crop((0, 0, 559, 48)).save(art / 'native_topbar.png')
    x0, y0, x1, y1 = 1336, 4, 1580, 268
    scale = 4
    mask = Image.new('L', ((x1 - x0) * scale, (y1 - y0) * scale), 0)
    draw = ImageDraw.Draw(mask)
    for cx, cy, r in ((1456, 150, 107.5), (1367, 218, 13), (1545, 218, 13)):
        draw.ellipse(((cx - x0 - r) * scale, (cy - y0 - r) * scale, (cx - x0 + r) * scale, (cy - y0 + r) * scale),
                     fill=255)
    draw.rounded_rectangle(((1401 - x0) * scale, (9 - y0) * scale, (1511 - x0) * scale, (37 - y0) * scale),
                           radius=6 * scale, fill=255)
    minimap = native.crop((x0, y0, x1, y1))
    minimap.putalpha(mask.resize(minimap.size, Image.LANCZOS))
    minimap.save(art / 'native_minimap.png')
    panels = native.crop((6, 60, 216, 159))
    mask = Image.new('L', panels.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle((0, 0, 98, 98), fill=255)
    draw.rectangle((111, 0, 209, 98), fill=255)
    panels.putalpha(mask)
    panels.save(art / 'native_herobuffs.png')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--captures', nargs=2, metavar=('CLEAN', 'HUD'), help='clean and HUD gameplay captures')
    args = parser.parse_args()
    (HERE / 'art').mkdir(exist_ok=True)
    (HERE / 'fonts').mkdir(exist_ok=True)
    for source, name, longest in ART:
        copyScaled(source, HERE / 'art' / name, longest)
    for name in ('endcap_socket.png', 'endcap_compact.png'):
        endcap = Image.open(HERE / 'art' / name)
        endcap.crop(endcap.getchannel('A').point(lambda a: 255 if a > 8 else 0).getbbox()).save(HERE / 'art' / name)
    for buff in BUFFS:
        copyScaled(SOURCE_ICONS / f'obsidian_buff_{buff}.png', HERE / 'art' / f'buff_{buff}.png', 128)
    for debuff in DEBUFFS:
        copyScaled(SOURCE_ICONS / f'obsidian_debuff_{debuff}.png', HERE / 'art' / f'debuff_{debuff}.png', 128)
    for spell in SPELL_ART:
        copyScaled(SPELLS / f'{spell}.png', HERE / 'art' / f'spell_{spell}.png', 128)
    for font in FONT_FILES:
        shutil.copyfile(FONTS / font, HERE / 'fonts' / font)
    if args.captures:
        captures(Path(args.captures[0]), Path(args.captures[1]))


if __name__ == '__main__':
    main()
