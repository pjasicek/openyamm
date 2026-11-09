import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_equipped.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
act=bpy.data.actions['Death'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows=[]
for f in np.arange(0,109.001,.25):
 sc.frame_set(int(f),subframe=float(f%1));angle=-9*math.exp(-.5*((f-81)/7)**2)
 q=rig.pose.bones['B_Neck'].rotation_quaternion.copy()@Quaternion(Vector((0,1,0)),math.radians(angle));rows.append((float(f),q))
for f,q in rows:b=rig.pose.bones['B_Neck'];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
rows=[];inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
for f in np.arange(0,109.001,.25):
 sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min((body.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
 rows.append((float(f),rig.pose.bones['B_Pelvis'].location.copy()+inv@Vector((0,0,.002-low))))
for f,loc in rows:b=rig.pose.bones['B_Pelvis'];b.location=loc;b.keyframe_insert('location',frame=f)
from g6_head_clearance import Clearance
C=Clearance(body);report={}
for name in ['Standing','Walking','Running','Attack','Hit','Death','Fidget']:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];head=[];props={k:[] for k in ['SwordMesh','ScabbardMesh']}
 for f in np.arange(0,float(act.frame_range[1])+.001,.5):
  sc.frame_set(int(f),subframe=float(f%1));head.append((float(f),C.measure()[0]))
  for n,vals in props.items():
   ob=bpy.data.objects[n];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();vals.append(min((ob.matrix_world@v.co).z for v in m.vertices));ev.to_mesh_clear()
 report[name]={'head_depth_cm':max(x[1] for x in head)*100,'head_worst_frame':max(head,key=lambda x:x[1])[0],'prop_min_z_cm':{k:min(v)*100 for k,v in props.items()}}
 print('FINAL_CONTACT',name,report[name])
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_complete.blend'))
(P/'review/equipped_contacts.json').write_text(json.dumps(report,indent=2)+'\n')
