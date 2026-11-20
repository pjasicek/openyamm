import sys,json
from pathlib import Path
import bpy,numpy as np
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P.parents[2]/'tools'),str(P.parent/'claude_shared/floor')]
from build_actor_lods import generate
from glb_pose import Glb
source=P/'export/hes_bulwark_lod0.glb'
for name,dest in [('Bulwark',P/'work/body_initial_lods.glb'),('Bulwark_Cables',P/'work/hes_bulwark_initial_lods.glb')]:
    g=Glb(source);node=next(n for n in g.json['nodes'] if n.get('name')==name)
    points=np.concatenate([g.accessor(p['attributes']['POSITION']) for p in g.json['meshes'][node['mesh']]['primitives']])
    low=points[points[:,1]<.015];protected=[(float(x),float(-z),float(y)) for x,y,z in low]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    generate(source,dest,name,ratios=(.5,.25,.125),max_influences=2 if name.endswith('Cables') else 1,protected_points=protected)
    (P/f'review/geometry/{name}_initial_lods.json').write_text((dest.parent/'lods.json').read_text())
    source=dest
