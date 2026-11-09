"""work/r76_lod0.glb -> export/mm8_m568_lods.glb with LOD1-3 and shadow LODs: the same ratios and influence budget as
mm8_m568_claude/scripts/build_lods.py (0.5 / 0.25 / 0.125, 4 influences), on the body alone (the polearm stays a
separate installed attachment). Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
generate(P / 'work/r76_lod0.glb', P / 'export/mm8_m568_lods.glb', 'Body', ratios=(.5, .25, .125), max_influences=4)
