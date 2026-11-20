#!/usr/bin/env python3
"""Copy the existing game art the talent tree v2 mockups use into art/ and fonts/. Nothing here is generated.

Sources: the first Talents study (solo_talents_20261113: fonts, Obsidian tab buttons, skills surface, frame9), the solo
HUD study's icons, its end-cap socket (the round socket becomes the keystone socket) and seal, the native Skills page
capture of the approved overlay collection (revision 03, cropped to its 4:3 frame at 1024 x 768) and the Lich portrait
pc27-01 standing in for the Death Knight (Lich King)."""

import shutil
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STUDY = ROOT / 'level_generation/ui/solo_talents_20261113'
HUD = ROOT / 'level_generation/ui/solo_action_hud_20261113'
OVERLAYS = ROOT / 'level_generation/ui/obsidian_overlays_20260928'

ICONS = ['item_sword', 'item_axe', 'item_boots', 'item_tower_shield', 'item_longbow', 'item_kite_shield',
         'spell_shrapmetal', 'spell_icebolt', 'spell_paralyze', 'spell_incinerate', 'spell_curepoison',
         'spell_flyingfist', 'spell_lightbolt', 'spell_lightningbolt', 'spell_lifedrain', 'spell_stoneskin',
         'spell_toxiccloud', 'spell_heroism', 'spell_dayofthegods', 'spell_heal', 'spell_harm', 'spell_haste',
         'buff_sbf08a', 'buff_sba02a', 'buff_sbb09a', 'buff_sbv02a', 'buff_sba10a', 'buff_sbs03a', 'buff_sbl08a',
         'buff_sbm03a', 'buff_sba06a', 'buff_sbe05a', 'debuff_dark_grasp']


def main():
    art = HERE / 'art'
    fonts = HERE / 'fonts'
    art.mkdir(exist_ok=True)
    fonts.mkdir(exist_ok=True)
    for name in ICONS:
        icon = Image.open(HUD / 'art' / f'{name}.png').convert('RGBA')
        icon.thumbnail((96, 96), Image.LANCZOS)
        icon.save(art / f'{name}.png', optimize=True)
    for state in ('normal', 'hover', 'selected', 'disabled'):
        shutil.copy2(STUDY / 'art' / f'tab_{state}.png', art / f'tab_{state}.png')
    Image.open(STUDY / 'art/skills_surface.jpg').convert('RGB').save(art / 'skills_surface.jpg', quality=88)
    # frame9 at half size: the CSS border-image slice is 82 instead of 164.
    Image.open(STUDY / 'art/frame9.png').resize((292, 292), Image.LANCZOS).save(art / 'frame9.png', optimize=True)
    # The native Skills page (1600 x 900, 4:3 frame from x 200) cropped and scaled to 1024 x 768.
    capture = Image.open(OVERLAYS / 'previews/r03/skills-some-available.png').convert('RGB')
    capture.crop((200, 0, 1400, 900)).resize((1024, 768), Image.LANCZOS).save(art / 'character_screen.jpg', quality=88)
    # The round socket of the basebar end cap, the keystone socket.
    socket = Image.open(HUD / 'art/endcap_socket.png').convert('RGBA').crop((0, 112, 116, 228))
    mask = Image.new('L', socket.size, 0)
    ImageDraw.Draw(mask).ellipse((1, 1, 115, 115), fill=255)
    socket.putalpha(ImageChops.multiply(socket.split()[3], mask))
    socket.save(art / 'socket.png', optimize=True)
    shutil.copy2(HUD / 'art/omenu_seal.png', art / 'seal.png')
    shutil.copy2(ROOT / 'assets_dev/engine/icons_x2/pc27-01.png', art / 'portrait_lich.png')
    for name in ('fondamento_regular.ttf', 'openyamm_arrus_faithful.ttf', 'openyamm_lucida_faithful.ttf',
                 'openyamm_smallnum_faithful.ttf', 'openyamm_create_faithful.ttf', 'fondamento_ofl.txt'):
        shutil.copy2(STUDY / 'fonts' / name, fonts / name)


if __name__ == '__main__':
    main()
