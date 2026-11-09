from pathlib import Path
import bpy,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilots_fitted.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data;names=[g.name for g in body.vertex_groups];pv=[x.value for x in me.attributes['piece'].data]
report=json.loads((p/'review/pilot_contacts.json').read_text())['clips']
for role,rows in report.items():
 for kind,row in rows.items():
  if row['depth_m']<.002:continue
  a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=row['frame'];bpy.context.scene.frame_set(int(f),subframe=f-int(f))
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=np.array([tuple(v.co) for v in em.vertices]);ev.to_mesh_clear();pt=Vector(row['point'])
  def own(v):return sum(e.weight for e in me.vertices[v].groups if names[e.group].startswith('B_'+('R' if kind=='wand' else 'L')+'_') and any(x in names[e.group] for x in ['Clavicle','UpperArm','Forearm','Hand','Finger']))>.2
  fs=[f for f in me.polygons if all(pv[i] in (0,2,3,4) and (kind in ['cape','loin'] or not own(i)) for i in f.vertices)]
  tree=BVHTree.FromPolygons(co.tolist(),[tuple(f.vertices) for f in fs]);loc,n,idx,d=tree.find_nearest(pt);tri=fs[idx];near=int(np.argmin(np.linalg.norm(co-np.array(pt),axis=1)));bones={}
  for v in tri.vertices:
   for e in me.vertices[v].groups:bones[names[e.group]]=bones.get(names[e.group],0)+e.weight/len(tri.vertices)
  print('CONTACT_DETAIL',role,kind,row,'sample_rest',list(me.vertices[near].co),'sample_weights',[(names[e.group],round(e.weight,3)) for e in me.vertices[near].groups if e.weight>.02],'skin_closest',list(loc),'skin_weights',sorted(bones.items(),key=lambda x:-x[1])[:6],flush=True)
