"""Reduce each runtime material while preserving helmet horns, soles and weapon tips."""
import bpy,sys,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));import build_actor_lods as L
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_uv.blend'));body=bpy.data.objects['Body'];prop=bpy.data.objects['Crossbow']
co=np.array([v.co[:] for v in body.data.vertices]);piece=np.array([x.value for x in body.data.attributes['piece'].data]);points=[]
for pid in (19,20,12,14):
 c=co[piece==pid]
 if pid in (19,20):points.extend([c[np.argmax(c[:,2])],c[np.argmin(c[:,0])],c[np.argmax(c[:,0])]])
 else:
  sole=c[c[:,2]<c[:,2].min()+.01];points.extend([sole[np.argmin(sole[:,1])],sole[np.argmax(sole[:,1])]])
pc=np.array([v.co[:] for v in prop.data.vertices]);points.extend([pc[np.argmin(pc[:,0])],pc[np.argmax(pc[:,0])],pc[np.argmax(pc[:,1])]])
bpy.ops.wm.read_factory_settings(use_empty=True)
L.generate(P/'export/mm8_m632_runtime_lod0.glb',P/'export/mm8_m632_lods.glb','DarkDwarf',ratios=(.5,.25,.125),max_influences=8,protected_points=[tuple(x) for x in points])
(P/'review/lod_protected_points.json').write_text(json.dumps([x.tolist() for x in points],indent=2))

