"""Blender: the isle props project's review renders (its scripts/review.py: LOD0 front, three-quarter, side,
behind-above, below and each LOD three-quarter, back faces culled) for this project's GLBs -> review/<prop>/*.png.
Usage: blender --background --python review.py -- [prop ...]"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(HERE, '..', 'mm9_isleofashes_claude', 'scripts', 'review.py')
sys.path.insert(0, os.path.dirname(SCRIPT))
import blib  # noqa: E402

blib.HERE, blib.WORK, blib.TEX = HERE, os.path.join(HERE, 'work'), os.path.join(HERE, 'textures')
with open(SCRIPT) as stream:
    exec(compile(stream.read(), SCRIPT, 'exec'), {'__file__': SCRIPT, '__name__': '__main__'})
