from pathlib import Path
import sys,bpy
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'))
import build_actor_lods as lod
bpy.ops.wm.read_factory_settings(use_empty=True)
lod.generate(p/'export/mm8_m460_runtime_lod0.glb',p/'export/mm8_m460_lods.glb','Cleric',ratios=(.5,.25,.125),max_influences=8)
