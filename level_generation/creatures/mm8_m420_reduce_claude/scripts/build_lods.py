"""work/d73_lod0.glb -> work/d73_lods_raw.glb with LOD1-3 and shadow LODs (tools/build_actor_lods.py, about the
installed ratios 0.5 / 0.25 / 0.125 of LOD0, 4 influences). The peg is restored afterwards by preserve_peg_lods.py.
Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
generate(P / 'work/d73_lod0.glb', P / 'work/d73_lods_raw.glb', 'PirateMage', ratios=(.5, .25, .125), max_influences=4)
