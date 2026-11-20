"""Author shortest world-space hand paths through the approved native key poses."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
s=(P/'scripts/review3_collision_search.py').read_text().split('results=[]')[0].replace('round3_key_baseline/','').replace("34/48","42/48")
s=s.replace('import arm_ik as IK','import arm_ik as IK;import importlib;importlib.reload(IK)')
exec(compile(s,str(P/'scripts/review3_collision_search.py'),'exec'))
import reduction_common as C,common
rows=[];worlds=[]
for f in range(109):
 C.activate('Attack',f/48);rows.append({b.name:b.matrix_basis.copy()for b in r.pose.bones});worlds.append({b.name:b.matrix.copy()for b in r.pose.bones})
r.animation_data.action=None
keys=[0,21,42,60,108];data={}
for sd in 'LR':
 data[sd]={}
 for f in keys:
  H=worlds[f][f'B_{sd}_Hand'];S=worlds[f][f'B_{sd}_UpperArm'].translation;data[sd][f]=(H@ sides[sd].grip_hand-S,H.to_quaternion())
# Fixed two-hand frame from the collision-free impact.
relL=worlds[42]['Spear'].inverted()@worlds[42]['B_L_Hand']
last={sd:worlds[0][f'B_{sd}_Forearm'].translation-worlds[0][f'B_{sd}_UpperArm'].translation for sd in 'LR'}
previous={};poses=[];author=[];lastroll={"R":0,"L":0}
def smooth(t):return t*t*(3-2*t)
def candidates(sd,G,Rh):
 side=sides[sd];S=r.pose.bones[f'B_{sd}_UpperArm'].head;u=(G-Rh@side.grip_hand-S).normalized();parent=r.pose.bones[f'B_{sd}_Clavicle'].matrix.to_3x3()@side.rel['Arm'];h=r.data.bones[f'B_{sd}_Hand'];axis=h.matrix_local.to_3x3().inverted()@(sum((r.data.bones[f'B_{sd}_Finger{i}'].head_local for i in range(5)),Vector())/5-h.head_local).normalized();out=[]
 for roll in ([0]+[sign*x for x in range(15,181,15)for sign in [-1,1]] if sd=='R'else[0]):
  rr=roll*math.sin(math.pi*t)**2;rh=Quaternion(Rh@side.axis_hand,math.radians(rr)).to_matrix()@Rh
  for deg in [0]+[sign*x for x in range(5,181,5)for sign in [-1,1]]:
   sol=side.pose_anatomical(G,rh,Quaternion(u,math.radians(deg))@last[sd]);rel=(sol['Rf']@side.rel['Hand']).inverted()@rh;sw,tw=IK.swing_twist_deg(rel.to_quaternion(),axis);upper=IK.swing_twist_deg((parent.inverted()@sol['Ra']).to_quaternion(),side.uA)[1];flex=math.degrees((sol['E']-sol['S']).angle(sol['W']-sol['E']))
   if sd=='L'and sw>62:
    relq=rel.to_quaternion().slerp(Quaternion(),(sw-62)/sw);rh_fixed=(sol['Rf']@side.rel['Hand'])@relq.to_matrix();sol['Rh']=rh_fixed;sw,tw=IK.swing_twist_deg(relq,axis)
   score=100*sum(max(0,v-lim)**2 for v,lim in [(sw,64),(abs(tw),80),(abs(upper),80),(flex,145),(sol['miss']*1000,1)])+.01*deg*deg+.002*rr*rr+.03*(rr-lastroll[sd])**2
   out.append((score,sol,{'swing':sw,'twist':tw,'upper':upper,'flex':flex,'shaft_roll':rr}))
 return sorted(out,key=lambda x:x[0])[:8]
for f,row in enumerate(rows):
 for n,m in row.items():r.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
 if 60<f<108:
  a,b=(21,42)if f<42 else(60,108);t=smooth((f-a)/(b-a));cands={}
  for sd in 'L':
   ga,qa=data[sd][a];gb,qb=data[sd][b];S=r.pose.bones[f'B_{sd}_UpperArm'].head;G=S+ga.lerp(gb,t);Rh=qa.slerp(qb,t).to_matrix()
   # Clear the chest on entry and uncross the off hand ahead of the body during recovery.
   arc=math.sin(math.pi*t)**2;G+=Vector(((-.08 if sd=='R'else .20)*arc,-.14*arc,0))
   if sd=='L'and f>60:
    G+=Vector((.20,-.25,.13))*math.sin(math.pi*math.sqrt(t))**2
    G.x+=.15*smooth(min(1,(f-60)/8))*(1-smooth(max(0,min(1,(f-75)/33))))
   cands[sd]=candidates(sd,G,Rh)
  rr=(0,dict(Ra=r.pose.bones['B_R_UpperArm'].matrix.to_3x3(),Rf=r.pose.bones['B_R_Forearm'].matrix.to_3x3(),Rh=r.pose.bones['B_R_Hand'].matrix.to_3x3(),S=r.pose.bones['B_R_UpperArm'].head.copy(),E=r.pose.bones['B_R_Forearm'].head.copy(),W=r.pose.bones['B_R_Hand'].head.copy()),{})
  best=None
  for ll in cands['L']:
   c=contacts(rr,ll);score=ll[0]+200*sum(max(0,v-1.0)**2 for v in c.values())
   if best is None or score<best[0]:best=(score,rr,ll,c)
   if max(c.values())<=1:break
  _,rr,ll,c=best;contacts(rr,ll);last['L']=ll[1]['E']-ll[1]['S']
  author.append({'frame':f,'score':best[0],'contacts':c,'R':rr[2],'L':ll[2]})
 else:
  for sd in 'LR':last[sd]=r.pose.bones[f'B_{sd}_Forearm'].head-r.pose.bones[f'B_{sd}_UpperArm'].head
 if f>88:
  blend=smooth(min(1,(f-88)/20))
  for part in ['UpperArm','Forearm','Hand','UpperArmTwist','ForearmTwist']:
   n='B_L_'+part;r.pose.bones[n].rotation_quaternion=r.pose.bones[n].rotation_quaternion.slerp(row[n].to_quaternion(),blend)
 bpy.context.view_layer.update();poses.append({b.name:b.matrix_basis.copy()for b in r.pose.bones})
 if f%12==0:print('WORLD_PATH',f,author[-1]if author else '',flush=True)
for sweep in range(2):
 original=[dict(row)for row in poses]
 for f in range(61,108):
  for part in ['UpperArm','Forearm','Hand','UpperArmTwist']:
   n='B_L_'+part;ref=original[f][n].to_quaternion();total=np.zeros(4)
   for delta,weight in [(-2,1),(-1,4),(0,6),(1,4),(2,1)]:
    q=original[max(60,min(108,f+delta))][n].to_quaternion()
    if ref.dot(q)<0:q.negate()
    total+=np.array(q)*weight
   q=Quaternion(total);q.normalize();m=q.to_matrix().to_4x4();m.translation=original[f][n].translation;poses[f][n]=m
(P/'review/round3_left_recovery_authoring.json').write_text(json.dumps(author,indent=2))
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];a.use_frame_range=True;a.frame_start=0;a.frame_end=108;r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];previous={}
 for f,row in enumerate(poses):
  for n,m in row.items():
   b=r.pose.bones[n];b.matrix_basis=m;q=b.rotation_quaternion
   if n in previous and previous[n].dot(q)<0:q.negate()
   previous[n]=q.copy();b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f,group=n)
   if n=='B_Pelvis':b.keyframe_insert('location',frame=f,group=n)
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
 if level==0:
  bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'));common.workbench_clay(bpy.context.scene)
  for f in []:
   C.activate('Attack',f/48);common.render_views(str(P/f'review/round3_motion/recovery_{f:02}'),.9,2.9,views=('front','left','three_quarter'),resolution=(650,750),target=(0,-.25))
