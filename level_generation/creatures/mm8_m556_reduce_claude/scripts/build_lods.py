"""work/r85_lod0.glb -> work/mm8_m556_lods.glb with LOD1-3 and shadow LODs: the installed body's ratios
(0.5 / 0.18 / 0.06 of LOD0, the build's default; 4 influences after reduction as in mm8_m556_claude). The sword and
shield stay separate installed attachments. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
generate(P / 'work/r85_lod0.glb', P / 'work/mm8_m556_lods.glb', 'Wasp', ratios=(.5, .18, .06), max_influences=4)
