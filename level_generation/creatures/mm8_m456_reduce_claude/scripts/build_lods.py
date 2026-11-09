"""work/r76_lod0.glb -> work/r76_lods_raw.glb with LOD1-3 and shadow LODs (tools/build_actor_lods.py, 4 influences).
Ratios 0.44 / 0.19 / 0.075 (production 0.46 / 0.21 / 0.075). The knee rows restored afterwards
(refine_knee_lods.py) add a near-fixed number of faces per level, and the shared gates cap LOD1/2/3 at 0.55 / 0.25 /
0.10 of LOD0; on the smaller LOD0 the production ratios gave 0.553 / 0.260. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
generate(P / 'work/r76_lod0.glb', P / 'work/r76_lods_raw.glb', 'DragonHunter', ratios=(.44, .19, .075), max_influences=4)
