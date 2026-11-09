from pathlib import Path
import bpy,sys,json,math,numpy as np
from mathutils import Vector,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/hands.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
common.workbench_clay(sc);report={}
for act in bpy.data.actions:
 if not act.use_fake_user:continue
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];record={}
 for f in np.arange(act.frame_range[0],act.frame_range[1]+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1))
  for sd in 'LR':
   fa=rig.pose.bones['B_'+sd+'_ForearmTwist'];hand=rig.pose.bones['B_'+sd+'_Hand']
   axis=(fa.bone.matrix_local.inverted()@hand.bone.head_local).normalized();rel=(fa.matrix.inverted()@hand.matrix).to_quaternion();rest=(fa.bone.matrix_local.inverted()@hand.bone.matrix_local).to_quaternion();dq=rel@rest.inverted()
   v=Vector((dq.x,dq.y,dq.z));proj=axis*v.dot(axis);tw=Quaternion((dq.w,*proj)).normalized();swing=dq@tw.inverted()
   vals={'wrist_swing':min(swing.angle,2*math.pi-swing.angle)*180/math.pi,'wrist_twist':min(tw.angle,2*math.pi-tw.angle)*180/math.pi,'forearm_twist':min(fa.rotation_quaternion.angle,2*math.pi-fa.rotation_quaternion.angle)*180/math.pi}
   for k,value in vals.items():
    key=sd+'_'+k
    if value>record.get(key,{}).get('degrees',-1):record[key]={'degrees':value,'frame':float(f)}
 report[act.name]=record
for act,frame in [('Standing',0),('Attack',30),('Running',12)]:
 a=bpy.data.actions[act];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(frame)
 for sd in 'LR':
  ctr=(rig.pose.bones['B_'+sd+'_Hand'].head+rig.pose.bones['B_'+sd+'_Finger2'].head)/2
  common.render_views(str(p/'review/animation'/f'hand_{act}_{sd}'),ctr.z,.40,target=(ctr.x,ctr.y),views=('front','back','left','right'),resolution=(640,640))
(p/'review/wrist_gates.json').write_text(json.dumps(report,indent=2)+'\n');print('WRIST',json.dumps(report))
