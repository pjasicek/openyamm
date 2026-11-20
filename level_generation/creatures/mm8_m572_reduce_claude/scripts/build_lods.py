"""work/r60_lod0.glb -> export/mm8_m572.glb with LOD1-3 and shadow LODs, the same ratios and influence budget as
mm8_m572_claude/scripts/build_lods.py (0.5 / 0.25 / 0.125, 4 influences); the Death/Dead floor contacts (floor_contacts.py) are protected. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
import json  # noqa: E402
from mathutils import Vector  # noqa: E402
contacts = [Vector(p) for p in json.load(open(P / 'work/floor_contacts.json'))]
generate(P / 'work/r60_lod0.glb', P / 'export/mm8_m572.glb', 'Body', ratios=(.5, .25, .125), max_influences=4,
         protected_points=contacts)
