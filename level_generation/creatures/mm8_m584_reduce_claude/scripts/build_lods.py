"""work/r80_lod0.glb -> export/mm8_m584.glb with LOD1-3 and shadow LODs, the settings of the production project
(mm8_m584_claude/scripts/lods.py: 0.5 / 0.25 / 0.125, 8 influences), then scripts/preserve_wing_lods.py puts the
4,024 wing/feather triangles back whole into every LOD (feather shells open gaps under any collapse).
Usage: blender -b -P build_lods.py && python3 scripts/preserve_wing_lods.py (Blender's Python has no PIL)"""
from pathlib import Path
import sys
import bpy
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(P / 'work/r80_lod0.glb', P / 'export/mm8_m584.glb', 'Body', ratios=(.5, .25, .125), max_influences=8)
