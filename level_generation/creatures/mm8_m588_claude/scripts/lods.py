import bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import generate,read_glb,accessor_bytes
import numpy as np
source=P/'export/boulder_prepared.glb';d,b=read_glb(source)
pr=d['meshes'][next(n['mesh'] for n in d['nodes'] if n.get('name')=='Body')]['primitives'][0]
pos=np.frombuffer(accessor_bytes(d,b,pr['attributes']['POSITION']),dtype='<f4').reshape(-1,3)
# Preserve the rest-pose basal contacts; glTF +Y is Blender +Z.
protected=[(float(x),-float(z),float(y)) for x,y,z in pos if y<.02]
bpy.ops.wm.read_factory_settings(use_empty=True)
generate(source,P/'export/boulder_lods.glb','Body',ratios=(.5,.25,.125),max_influences=1,protected_points=protected)
