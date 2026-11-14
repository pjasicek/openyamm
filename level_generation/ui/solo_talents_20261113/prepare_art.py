#!/usr/bin/env python3
"""Copy the existing game art the solo talent study uses into art/ and fonts/. Nothing here is generated.

Sources: the solo HUD study's prepared art (icons, frame9), the Obsidian tab buttons and skills surface from
assets_source, the native Skills page capture of the approved overlay collection (the 4:3 character screen the talent
page sits in) and the game's TrueType fonts."""

import shutil
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HUD = ROOT / 'level_generation/ui/solo_action_hud_20261113'
OVERLAYS = ROOT / 'level_generation/ui/obsidian_overlays_20260928'
SOURCE_ICONS = ROOT / 'assets_source/engine/icons_x2'

ICONS = ['item_sword', 'item_axe', 'item_boots', 'item_tower_shield', 'item_kite_shield', 'item_longbow',
         'spell_shrapmetal', 'spell_icebolt', 'spell_paralyze', 'spell_incinerate', 'spell_curepoison',
         'spell_regeneration', 'spell_heal', 'spell_fireball', 'spell_lightningbolt', 'spell_haste', 'spell_bless',
         'spell_stoneskin', 'buff_sbf08a', 'buff_sba02a', 'buff_sbb09a', 'buff_sbv02a', 'buff_sba10a', 'buff_sbs03a',
         'buff_sbl08a', 'buff_sbs07a', 'frame9', 'face_pc03', 'omenu_frame', 'selection_diamond']


def main():
    art = HERE / 'art'
    fonts = HERE / 'fonts'
    art.mkdir(exist_ok=True)
    fonts.mkdir(exist_ok=True)
    for name in ICONS:
        shutil.copy2(HUD / 'art' / f'{name}.png', art / f'{name}.png')
    for state in ('normal', 'hover', 'selected', 'disabled'):
        shutil.copy2(SOURCE_ICONS / f'obsidian_button_tab_{state}.png', art / f'tab_{state}.png')
    surface = Image.open(SOURCE_ICONS / 'obsidian_skills_surface.png').convert('RGB')
    surface.save(art / 'skills_surface.jpg', quality=90)
    # The native Skills page at 1600 x 900 (Obsidian overlay revision 03): the frame, paperdoll and portrait row.
    capture = Image.open(OVERLAYS / 'previews/r03/skills-some-available.png').convert('RGB')
    capture.save(art / 'character_screen.jpg', quality=92)
    for name in ('fondamento_regular.ttf', 'openyamm_arrus_faithful.ttf', 'openyamm_lucida_faithful.ttf',
                 'openyamm_smallnum_faithful.ttf', 'fondamento_ofl.txt'):
        shutil.copy2(HUD / 'fonts' / name, fonts / name)
    shutil.copy2(OVERLAYS / 'assets/fonts/openyamm_create_faithful.ttf', fonts / 'openyamm_create_faithful.ttf')


if __name__ == '__main__':
    main()
