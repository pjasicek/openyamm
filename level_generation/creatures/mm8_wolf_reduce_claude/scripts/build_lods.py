"""work/r55_lod0.glb -> export/mm8_wolf.glb with LOD1-3 and shadow LODs, the installed wolf's ratios
(14,201 / 7,100 / 3,550 / 1,767: 0.5 / 0.25 / 0.125) and 4 influences. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
generate(P / 'work/r55_lod0.glb', P / 'export/mm8_wolf.glb', 'Wolf', ratios=(.5, .25, .125), max_influences=4)
