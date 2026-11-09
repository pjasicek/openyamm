"""work/r57fix_lod0.glb (reduced, head/neck/shoulder fix) -> work/r57fix_lods.glb with LOD1-3 and shadow LODs, the same ratios and influence budget as
mm8_m448_claude/scripts/build_lods.py (0.5 / 0.25 / 0.125, 4 influences). Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
generate(P / 'work/r57fix_lod0.glb', P / 'work/r57fix_lods.glb', 'Ratman', ratios=(.5, .25, .125), max_influences=4)
