"""Existing Blender LOD builder; far levels are subsequently rebuilt by the repair.py route."""
import sys,bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import generate
for n in ['egg_cluster','brood_sac','ganglion']:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 generate(P/'export'/('hes_'+n+'_lod0.glb'),P/'work'/('hes_'+n+'_initial_lods.glb'),'BroodBody',ratios=(.8,.6,.4),max_influences=4)
