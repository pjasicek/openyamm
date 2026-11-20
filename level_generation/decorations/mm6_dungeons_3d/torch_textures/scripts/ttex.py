"""Helpers of the torch texture pass: materials from torch_textures/textures/ (the shared CC0 PBR sets made by
make_textures.py), falling back to the torch batch's helpers (../../torches/scripts/tlib.py: project flames, props
textures) for the rest, and tlib's COLOR_0 tint to the native sprite's measured colours."""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTURES = os.path.join(HERE, 'textures')
sys.path.insert(0, os.path.join(HERE, '..', 'torches', 'scripts'))
import tlib  # noqa: E402

pl = tlib.pl
u = tlib.u
tint = tlib.tint
flame_material = tlib.flame_material


def material(name, texture, alpha=False, extras=None):
    """pl.material from torch_textures/textures/<texture>_*.png when the set is there, else tlib.material."""
    if not os.path.exists(os.path.join(TEXTURES, f'{texture}_basecolor.png')):
        return tlib.material(name, texture, alpha=alpha, extras=extras)
    previous = pl.TEX
    pl.TEX = TEXTURES
    try:
        return pl.material(name, texture, alpha=alpha, extras=extras)
    finally:
        pl.TEX = previous
