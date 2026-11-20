import bpy,json,sys
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import generate
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(P/'export/raven_prepared.glb',P/'export/raven_lods.glb','Body',ratios=(.5,.25,.125),max_influences=8)

# Thin feather shells lose coverage under global collapse; retain their authored silhouette.
exec(compile((P/'scripts/preserve_wing_lods.py').read_text(), str(P/'scripts/preserve_wing_lods.py'), 'exec'))
