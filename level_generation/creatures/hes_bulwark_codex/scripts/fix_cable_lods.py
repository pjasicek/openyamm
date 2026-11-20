import sys,copy
from pathlib import Path
import bpy,numpy as np
P=Path('level_generation/creatures/hes_bulwark_codex').resolve();sys.path[:0]=[str(P.parents[2]/'tools'),str(P.parent/'claude_shared/floor')]
from build_actor_lods import generate
from glb_pose import Glb
g=Glb(P/'work/lod_repair/export/hes_bulwark.glb');node=next(n for n in g.json['nodes'] if n.get('name')=='Bulwark_Cables');mesh=g.json['meshes'][node['mesh']];mesh.pop('extras')
points=np.concatenate([g.accessor(p['attributes']['POSITION']) for p in mesh['primitives']]);protected=[(float(x),float(-z),float(y)) for x,y,z in points if y<.015]
g.write(P/'work/cable_lod_input.glb')
generate(P/'work/cable_lod_input.glb',P/'work/cable_lod_revised.glb','Bulwark_Cables',ratios=(.5,.40,.30),max_influences=2,protected_points=protected)
g=Glb(P/'work/cable_lod_revised.glb');d=g.json;node=next(n for n in d['nodes'] if n.get('name')=='Bulwark_Cables');mesh=d['meshes'][node['mesh']]
extensions={p['material']:copy.deepcopy(p.get('extensions',{})) for p in mesh['primitives']}
for mi in mesh['extras']['openyamm_lods']:
 for p in d['meshes'][mi]['primitives']:p['extensions']=extensions[p['material']]
used=set()
for n in d['nodes']:
 if 'mesh' in n:
  used.add(n['mesh']);e=d['meshes'][n['mesh']].get('extras',{});used.update(e.get('openyamm_lods',[]));used.update(e.get('openyamm_shadow_lods',[]))
remap={old:new for new,old in enumerate(sorted(used))};d['meshes']=[d['meshes'][i] for i in sorted(used)]
for n in d['nodes']:
 if 'mesh'in n:n['mesh']=remap[n['mesh']]
for m in d['meshes']:
 for key in ('openyamm_lods','openyamm_shadow_lods'):
  if key in m.get('extras',{}):m['extras'][key]=[remap[i] for i in m['extras'][key]]
g.write(P/'work/bulwark_final_lods.glb')
