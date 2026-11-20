from pathlib import Path
import bpy,sys
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'))
from build_actor_lods import generate
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(p/'export/mm8_m472_prepared.glb',p/'export/mm8_m472_lods.glb','Necromancer',ratios=(.5,.25,.125))
