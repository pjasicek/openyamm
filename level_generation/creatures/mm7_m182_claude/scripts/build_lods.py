"""Colour LODs 1/2, 1/4, 1/8 and merged shadow LODs (Blender): export/mm7_m182_prepared.glb -> export/mm7_m182_lods.glb."""
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate
generate(P / 'export/mm7_m182_prepared.glb', P / 'export/mm7_m182_lods.glb', 'Body', ratios=(.5, .25, .125), max_influences=4)
