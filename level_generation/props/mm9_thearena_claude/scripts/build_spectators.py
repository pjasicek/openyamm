"""Blender: builds the Arena spectators' decoration GLBs (work/<prop>_export.glb, work/<prop>_meta.json) with Sturmford
City's build (../mm9_sturmfordcity_claude/scripts/build.py: POSES models posed in their library animation at its first
key before baking, one material per skin, opaque people, LODs from 1000 triangles), run here on the spectator table
(scripts/spectators.py) with this project's directories.
Usage: blender --background --factory-startup --python scripts/build_spectators.py -- [prop ...]"""
import os
import sys

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS)
import props_table  # noqa: E402,F401
import spectators  # noqa: E402

# PeasantMS1's native ABC LODs collapse the feet and the head to spikes in the seated pose (review 2026-11-05):
# its LOD1/LOD2 are collapse decimations of LOD0 instead (Sturmford's build decimates when it is given no native LOD).
DECIMATED_LODS = {'peasantms1alisten', 'peasantms1blisten'}

sys.modules['props_table'] = spectators
SCRIPT = os.path.join(str(spectators.STURMFORD), 'scripts', 'build.py')
with open(SCRIPT) as stream:
    source = stream.read()
assert source.rstrip().endswith('\nmain()')
ns = {'__file__': os.path.join(SCRIPTS, 'build_spectators.py'), '__name__': 'sturmford_build'}
exec(compile(source.rstrip()[:-len('main()')], SCRIPT, 'exec'), ns)
_lod_sources = ns['lod_sources']
ns['lod_sources'] = lambda prop: _lod_sources(prop)[:1] if prop in DECIMATED_LODS else _lod_sources(prop)
ns['main']()
