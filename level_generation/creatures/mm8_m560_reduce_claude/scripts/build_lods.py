"""work/r55_lod0.glb -> export/mm8_m560.glb with LOD1-3 and shadow LODs, as mm8_m560_claude/scripts/build_lods.py
(build_actor_lods default ratios 0.5 / 0.18 / 0.06, 4 influences). Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
generate(P / 'work/r55_lod0.glb', P / 'export/mm8_m560.glb', 'Wyvern', max_influences=4)
