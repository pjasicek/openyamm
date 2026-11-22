#!/usr/bin/env python3
"""Reference images for the Codex calls (README.md). Writes refs/layout_<face>.png: MM9's Town Portal page
(tpchedian.png) on MM9's empty table, widened to the 1536x1024 image size, with its map replaced by the face's world
board painting (level_generation/xeen_art/mu1_world/raw/<face>_v2.png) as the layout of the new map; and copies the
existing continent cards for the new-game card."""
import shutil
from pathlib import Path

from PIL import Image

W = Path(__file__).resolve().parent
ROOT = W.parents[2]
PAGE = ROOT / 'assets_dev/worlds/mm9/icons_x2/tpchedian.png'
TABLE = ROOT / 'level_generation/ui/mm9_town_portal_20261108/raw/table_wood_v2.png'
BOARD = ROOT / 'level_generation/xeen_art/mu1_world/raw'
CARDS = ROOT / 'assets_dev/engine/hud_x2/menus'
# tpchedian's map inside its inner red border
MAP = (121, 117, 1018, 822)

for face in ('cloudside', 'darkside'):
    page = Image.open(PAGE).convert('RGB')
    board = Image.open(BOARD / f'{face}_v2.png').convert('RGB')
    page.paste(board.resize((MAP[2] - MAP[0], MAP[3] - MAP[1]), Image.LANCZOS), MAP[:2])
    canvas = Image.open(TABLE).convert('RGB').resize((1536, 1024), Image.LANCZOS)
    # only the frame and its shadow, so that the two tables do not show a seam
    canvas.paste(page.crop((18, 0, 1124, 892)), (128 + 18, 32))
    canvas.save(W / 'refs' / f'layout_{face}.png')
for name in ('chedian', 'jadame', 'enroth'):
    Image.open(CARDS / f'omenu_continent_{name}.png').convert('RGB').save(W / 'refs' / f'card_{name}.png')
shutil.copy(BOARD / 'cloudside_v2.png', W / 'refs' / 'board_cloudside.png')
# the loading pages' style reference (MM7's first loading page)
Image.open(ROOT / 'assets_dev/engine/icons_x2/7load1.png').convert('RGB').save(W / 'refs' / 'style_7load1.png')
