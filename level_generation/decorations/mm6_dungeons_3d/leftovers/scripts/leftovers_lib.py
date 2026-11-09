"""Helpers for the leftover MM6 dungeon decorations (corpses, rocks, trees, flowers): the outdoor props library
(read only, through ../../scripts/dungeon_lib.py) redirected so that everything a build writes (textures, work files,
renders) lands in this batch folder. Materials resolve textures here first, then in the dungeon project's
textures/, then in the outdoor props textures (read only)."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import dungeon_lib as dl  # noqa: E402

pl = dl.pl
units = dl.units
TEXTURES = os.path.join(HERE, 'textures')
WORK = os.path.join(HERE, 'work')
REVIEW = os.path.join(HERE, 'review')
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
X2 = os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2')
MODELS = os.path.join(REPO, 'assets_dev', 'worlds', 'mm6', 'models')
SEARCH = [TEXTURES, dl.TEXTURES, dl.PROPS_TEXTURES]
for path in (TEXTURES, WORK, REVIEW):
    os.makedirs(path, exist_ok=True)


def redirect():
    """Point the props library's writable roots at this folder (call after importing any copied outdoor module
    that writes to pl.TEX / pl.PROPS)."""
    pl.PROPS = HERE
    pl.TEX = TEXTURES


def material(name, texture, alpha=False, extras=None):
    """pl.material from the first search folder holding <texture>_basecolor.png."""
    folder = next((p for p in SEARCH if os.path.exists(os.path.join(p, f'{texture}_basecolor.png'))), None)
    if folder is None:
        raise FileNotFoundError(texture)
    saved = pl.TEX
    pl.TEX = folder
    try:
        return pl.material(name, texture, alpha=alpha, extras=extras)
    finally:
        pl.TEX = saved


redirect()
