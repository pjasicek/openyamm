import bpy,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
o=bpy.data.objects['BoneDragon'];rig=bpy.data.objects['BoneDragon_Rig'];sc=bpy.context.scene
co=np.array([v.co[:] for v in o.data.vertices]);edges=np.array([e.vertices[:] for e in o.data.edges]);restlen=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1);report={}
for name in ('Fly','Attack'):
 rig.animation_data.action=bpy.data.actions[name];rows=[]
 for f in (0,6,12,18,24):
  sc.frame_set(f);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(c[edges[:,0]]-c[edges[:,1]],axis=1)/np.maximum(restlen,1e-8)
  for e in np.argsort(ratio)[-30:]:rows.append(dict(frame=f,ratio=float(ratio[e]),edge=edges[e].tolist(),positions=co[edges[e]].tolist(),weights=[{o.vertex_groups[g.group].name:round(g.weight,4) for g in o.data.vertices[i].groups} for i in edges[e]]))
 report[name]=rows
(P/'review/pilot_edge_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({n:sorted(r,key=lambda x:x['ratio'],reverse=True)[:4] for n,r in report.items()},indent=2))
(P/'review/viewer').mkdir(exist_ok=True)
for ob in sc.objects:ob.select_set(ob in (o,rig))
bpy.ops.export_scene.gltf(filepath=str(P/'review/viewer/pilot.glb'),use_selection=True,export_format='GLB',export_yup=True,export_skins=True,export_animations=True,export_animation_mode='ACTIONS',export_frame_range=False,export_materials='NONE')
