import bpy,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_jak1_runtime_lod0.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');ob=next(o for o in bpy.data.objects if o.type=='MESH' and o.parent is rig);rig.animation_data.action=bpy.data.actions['Death'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];names={g.index:g.name for g in ob.vertex_groups}
for t in [.1,.125,.15,.166667,.1875,.208333,.25,.29,.333333]:
 f=t*bpy.context.scene.render.fps;bpy.context.scene.frame_set(int(f),subframe=f-int(f));ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();inv=(rig.matrix_world@rig.pose.bones['Staff'].matrix).inverted();rows=[]
 for v in me.vertices:
  rv=ob.data.vertices[v.index]
  if not rv.groups:continue
  dom=names[max(rv.groups,key=lambda g:g.weight).group]
  if not dom.startswith(('B_R_Hand','B_R_Finger')):continue
  q=inv@ob.matrix_world@v.co
  if abs(q.z)<.075:rows.append((round((q.x*q.x+q.y*q.y)**.5,5),dom,v.index))
 ev.to_mesh_clear();print('RELEASE',t,sorted(rows)[:5],flush=True)
