"""work/r84_lod0.glb -> export/mm8_m628_lods.glb with LOD1-3 and shadow LODs: the installed build's ratios, influence
budget and protected contacts (../mm8_m628/scripts/build_lods.py: 0.5 / 0.25 / 0.125, 4 influences; finger tips,
soles and bow nocks from ../mm8_m628/export/lods.json; contacts the reduction removed are simply not found).
Usage: blender -b -P build_lods.py"""
import json
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
points = [tuple(p) for p in json.loads((P.parent / 'mm8_m628/export/lods.json').read_text())['protected_points']]
generate(P / 'work/r84_lod0.glb', P / 'export/mm8_m628_lods.glb', 'SkeletonArcher', ratios=(.5, .25, .125),
         max_influences=4, protected_points=points)
