"""Helpers for the MM6 dungeon decorations: the outdoor props library (../../mm6_new_sorpigal_3d/props/scripts,
read only) with materials found in this project's textures/ first and the props textures second."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROPS_SCRIPTS = os.path.join(HERE, '..', 'mm6_new_sorpigal_3d', 'props', 'scripts')
sys.path.insert(0, os.path.abspath(PROPS_SCRIPTS))
import props_lib as pl  # noqa: E402

TEXTURES = os.path.join(HERE, 'textures')
PROPS_TEXTURES = pl.TEX
UNITS_PER_METRE = 81.7


def units(value):
    """Map units (the native sprite's world units) to Blender metres."""
    return value / UNITS_PER_METRE


def material(name, texture, alpha=False, extras=None):
    """pl.material from textures/<texture>_basecolor.png here when present, else from the props textures."""
    local = os.path.exists(os.path.join(TEXTURES, f'{texture}_basecolor.png'))
    pl.TEX = TEXTURES if local else PROPS_TEXTURES
    try:
        return pl.material(name, texture, alpha=alpha, extras=extras)
    finally:
        pl.TEX = PROPS_TEXTURES
