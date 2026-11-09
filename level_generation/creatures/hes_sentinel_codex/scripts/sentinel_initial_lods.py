"""Initial 50/25/12.5 percent LOD chain, followed by the shared far-LOD texture repair."""
import sys,bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import generate
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(P/'export/hes_sentinel_lod0.glb',P/'work/hes_sentinel_initial_lods.glb','Sentinel',ratios=(.5,.25,.125),max_influences=2)
