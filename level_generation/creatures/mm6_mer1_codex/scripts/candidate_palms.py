import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];args=sys.argv[sys.argv.index('--')+1:];tag=args[1];bpy.ops.wm.open_mainfile(filepath=str(P/args[0]));r=bpy.data.objects['Rig'];s=bpy.context.scene;g=json.loads((P/'work/grip_pose.json').read_text());M=r.data.bones['B_R_Hand'].matrix_local;K=sum((r.data.bones[f'B_R_Finger{i}'].head_local for i in[1,2,3,4]),Vector())/4;D=(K-M.translation).normalized();A=(M.to_3x3()@Vector(g['handle_axis_hand_local'])).normalized();v=M@Vector(g['handle_centre_hand_local'])-K;v-=A*v.dot(A);v-=D*v.dot(D);n=v.normalized();norm={'R':M.to_3x3().inverted()@n};n.x=-n.x;norm['L']=r.data.bones['B_L_Hand'].matrix_local.to_3x3().inverted()@n
report={}
for role in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows=[]
 for t in np.arange(0,float(a.frame_range[1])/30+.0001,1/48):
  f=t*30;s.frame_set(int(f),subframe=float(f%1));row=[float(t)]
  for sd in 'LR':
   n=(r.pose.bones[f'B_{sd}_Hand'].matrix.to_3x3()@norm[sd]).normalized();want=Vector((-1 if sd=='L'else 1,0,0));row.append(math.degrees(n.angle(want)))
  rows.append(row)
 ar=np.array(rows);report[role]={'angle_towards_body_deg_min':ar[:,1:].min(0).tolist(),'max':ar[:,1:].max(0).tolist()};print('PALM',role,report[role],flush=True)
(P/'review'/f'{tag}_palms.json').write_text(json.dumps(report,indent=2));(P/'work/palm_normals.json').write_text(json.dumps({sd:list(v)for sd,v in norm.items()},indent=2))
