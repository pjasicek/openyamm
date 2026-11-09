import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_jak1_runtime_lod0.glb'));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');body=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.parent is rig and 'Staff' in o.vertex_groups);scene=bpy.context.scene;g=body.vertex_groups['Staff'].index;ids=[v.index for v in body.data.vertices if not any(e.group==g and e.weight>.5 for e in v.groups)];report={}
for ac in bpy.data.actions:
 rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];rows=[];height=[]
 for f in np.arange(0,float(ac.frame_range[1])+.001,30/48):
  scene.frame_set(int(f),subframe=float(f-int(f)));a=rig.matrix_world@rig.pose.bones['B_Pelvis'].head;b=rig.matrix_world@rig.pose.bones['B_Neck'].head;rows.append([f/30,a.z,math.degrees((b-a).angle(Vector((0,0,1))))])
  if ac.name=='Standing':
   ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();zz=[(body.matrix_world@me.vertices[i].co).z for i in ids];height.append(max(zz)-min(zz));ev.to_mesh_clear()
 report[ac.name]={'pelvis_height_m':[min(r[1]for r in rows),max(r[1]for r in rows)],'trunk_lean_deg':[min(r[2]for r in rows),max(r[2]for r in rows)],'samples':rows}
 if height:report[ac.name]['body_height_m']=float(np.median(height))
assert len(report)==8
(P/'review/posture.json').write_text(json.dumps(report,indent=2));print('POSTURE',{k:{n:v for n,v in d.items()if n!='samples'}for k,d in report.items()},flush=True)
