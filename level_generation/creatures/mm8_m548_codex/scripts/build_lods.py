import sys,bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import generate
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(P/'export/mm8_m548_prepared.glb',P/'export/mm8_m548.glb','CrystalDragon',ratios=(.5,.25,.125),max_influences=4)
