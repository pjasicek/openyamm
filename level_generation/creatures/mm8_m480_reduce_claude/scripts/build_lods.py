"""work/r78_lod0.glb -> work/r78_lods.glb with colour and shadow LOD1-3: the ratios and influence budget of
mm8_m480_claude's own build (tools/build_actor_lods.py, 0.5 / 0.25 / 0.125, 4 influences). Run under Blender."""
import sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
generate(P / 'work/r78_lod0.glb', P / 'work/r78_lods.glb', 'TrollPeasant', ratios=(.5, .25, .125), max_influences=4)
