"""work/g78_lod0.glb -> export/mm8_m412_lods.glb (or argv[1]) with LOD1-3 and shadow LODs: the creature's own builder
(../mm8_m412_claude/scripts/build_lods.py: 0.46 / 0.18 / 0.06, then knee bend rows restored by knee_cuts.py lods),
LOD1 base ratio REA_LOD1 (default 0.42: the knee rows add ~850 faces and the shared gate caps LOD1 at 55 %).
Usage: blender -b -P build_lods.py [-- <out.glb>]"""
import os
from pathlib import Path
import sys
P = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import generate  # noqa: E402
out = Path(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv else P / 'export/mm8_m412_lods.glb'
generate(P / 'work/g78_lod0.glb', out, 'Pirate', ratios=(float(os.environ.get('REA_LOD1', '0.42')), .18, .06))
