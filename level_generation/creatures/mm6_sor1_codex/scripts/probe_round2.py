import bpy,json,math,numpy as np,sys
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(p/'review/round2/baseline/work/production_master.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
import arm_solver as sol
out={}
for s in 'LR':
 a=sol.Side('B_'+s+'_');print('REST',s,'hinge',list(a.hinge_local()),'upper',list(a.uA),'fore',list(a.uF),flush=True)
 out[s]={}
 for role in ['Standing','Walking','Attack','Cast','Hit','Fidget','Death','Dead']:
  rig.animation_data.action=None
  for pb in rig.pose.bones:pb.matrix_basis.identity()
  act=bpy.data.actions[role];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];v=[]
  for f in np.arange(0,act.frame_range[1]+.001,scene.render.fps/48):
   scene.frame_set(int(f),subframe=float(f%1));U,F,H=[rig.pose.bones['B_'+s+'_'+n] for n in ['UpperArm','Forearm','Hand']]
   u=(F.head-U.head).normalized();ff=(H.head-F.head).normalized();h=(U.matrix.to_3x3()@a.hinge_local()).normalized();bend=math.degrees(math.atan2(h.dot(u.cross(ff)),u.dot(ff)))
   v.append(bend)
  out[s][role]=[min(v),max(v)]
print('ELBOW_BASELINE',json.dumps(out),flush=True)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
for z in [.05,.30,.50,.70,.90,1.05,1.15,1.30,1.40]:
 vv=[v.co for v,a in zip(body.data.vertices,body.data.attributes['piece'].data) if a.value in [0,100] and abs(v.co.z-z)<.035 and abs(v.co.x)<.31]
 if vv: print('WIDTH',z,min(v.x for v in vv),max(v.x for v in vv),min(v.y for v in vv),max(v.y for v in vv),flush=True)
for s in 'LR':
 for n in ['Clavicle','UpperArm','Forearm','Hand']:
  b=rig.data.bones['B_'+s+'_'+n];print('JOINT',b.name,list(b.head_local),flush=True)
(p/'work/round2_probe.json').write_text(json.dumps(out,indent=2))
