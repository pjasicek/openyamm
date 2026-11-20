"""Blender: the Anskram Keep's review step (its scripts/review.py, which runs the isle props project's review renders:
LOD0 front, three-quarter, side, behind-above, below and each LOD three-quarter, back faces culled) for this
project's GLBs -> review/<prop>/*.png. Usage: blender --background --python review.py -- [prop ...]"""
import os

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(SCRIPTS, '..', '..', 'mm9_anskramkeep_claude', 'scripts', 'review.py')
with open(SCRIPT) as stream:
    exec(compile(stream.read(), SCRIPT, 'exec'), {'__file__': os.path.join(SCRIPTS, 'review.py'), '__name__': '__main__'})
