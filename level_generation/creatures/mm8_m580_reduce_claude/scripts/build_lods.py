"""work/pad45_lod0.glb -> work/pad45_lods.glb with LOD1-3 and shadow LODs, the same profile as
mm8_m580_claude/scripts/build_lods.py (shared 0.5 / 0.18 / 0.06, 4 influences). Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
generate(P / 'work/pad45_lod0.glb', P / 'work/pad45_lods.glb', 'Turtle', max_influences=4)
