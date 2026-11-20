"""work/r75_lod0.glb -> work/r75_lods.glb with LOD1-3 and shadow LODs: the m432 project's builder settings
(tools/build_actor_lods.py defaults 0.5 / 0.18 / 0.06; skinning limited to 4 influences like the installed body),
on the body alone (the sword stays the separate installed attachment). Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
generate(P / 'work/r75_lod0.glb', P / 'work/r75_lods.glb', 'M432', ratios=(.5, .18, .06), max_influences=4)
