"""work/r35_lod0.glb -> work/r35_lods.glb with LOD1-3 and shadow LODs, the same ratios and influence budget as
build_lods.py (0.5 / 0.25 / 0.125, 4 influences); the floor contacts of every clip (floor_contacts.py: spike tips,
corpse) are protected. Then shrink_shadow_lods.py and carry_variants.py (build_export.sh).
Usage: blender -b -P lod_chain.py"""
from pathlib import Path
import json
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
from mathutils import Vector  # noqa: E402
contacts = [Vector(p) for p in json.load(open(P / 'work/floor_contacts.json'))]
generate(P / 'work/r35_lod0.glb', P / 'work/r35_lods.glb', 'Robot', ratios=(.5, .25, .125), max_influences=4,
         protected_points=contacts)
