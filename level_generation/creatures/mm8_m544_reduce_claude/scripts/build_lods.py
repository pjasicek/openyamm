"""work/r60_lod0.glb -> work/r60_lods.glb with LOD1-3 and shadow LODs, the same ratios and influence budget as
mm8_m544_claude/scripts/build_lods.py (0.5 / 0.25 / 0.125, 4 influences); floor contacts of every clip
(floor_contacts.py: hoof soles, the Death/Dead body) and the rest-pose bounding extremes (horn tip, tail tip, ear
tips: LOD3 otherwise lost 7 mm of horn; Cyclops lesson) are protected. Usage: blender -b -P build_lods.py"""
from pathlib import Path
import json
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
from mathutils import Vector  # noqa: E402
contacts = [Vector(p) for p in json.load(open(P / 'work/floor_contacts.json'))]
contacts += [Vector(p) for p in json.load(open(P / 'work/extremes.json'))]
generate(P / 'work/r60_lod0.glb', P / 'work/r60_lods.glb', 'Unicorn', ratios=(.5, .25, .125), max_influences=4,
         protected_points=contacts)
