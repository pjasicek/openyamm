"""Keep the source rig and actions; reduce the face without destructive edge collapse."""
from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parents[2]/'tools'))
import build_actor_lods as lod
lod.generate(p/'export/mm8_m540_runtime_lod0.glb',p/'export/mm8_m540_lods.glb','OgreMage',ratios=(.5,.25,.125),max_influences=8)
runpy.run_path(str(p/'scripts/reduce_head_lods.py'),run_name='__main__')
