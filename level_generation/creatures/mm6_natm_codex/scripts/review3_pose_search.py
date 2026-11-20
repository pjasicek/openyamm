"""Find feasible anatomical two-hand impact poses around the native lunge target."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));C.activate('Attack',34/48);r=bpy.data.objects['Rig'];snapshot={b.name:b.matrix_basis.copy()for b in r.pose.bones};r.animation_data.action=None
for n,m in snapshot.items():r.pose.bones[n].matrix_basis=m
bpy.context.view_layer.update();import arm_ik as IK
sides={s:IK.Side(s)for s in 'LR'};lg=json.loads((P/'work/round3_left_grip.json').read_text());sides['L'].grip_hand=Vector(lg['handle_centre_hand_local']);axis=Vector((0,-1,0));D=json.loads((P/'work/round3_pose_reference.json').read_text());world={n:Matrix(v)for n,v in D['standing'].items()};ref={}
for sd in 'RL':
 h=world[f'B_{sd}_Hand'].to_3x3();ax=Vector(IK.GDATA['handle_axis_hand_local']if sd=='R'else lg['handle_axis_hand_local']);ref[sd]=(h@ax).rotation_difference(axis).to_matrix()@h
def solutions(sd,G):
 side=sides[sd];S=r.pose.bones[f'B_{sd}_UpperArm'].head;parent=r.pose.bones[f'B_{sd}_Clavicle'].matrix.to_3x3()@side.rel['Arm'];finger=(sum((r.data.bones[f'B_{sd}_Finger{i}'].head_local for i in range(5)),Vector())/5-r.data.bones[f'B_{sd}_Hand'].head_local).normalized();finger=r.data.bones[f'B_{sd}_Hand'].matrix_local.to_3x3().inverted()@finger;out=[]
 for roll in range(-180,180,30):
  rh=Quaternion(axis,math.radians(roll)).to_matrix()@ref[sd];u=(G-rh@side.grip_hand-S).normalized()
  for pd in range(-180,180,15):
   sol=side.pose_anatomical(G,rh,Quaternion(u,math.radians(pd))@Vector((1 if sd=='L'else-1,0,-.3)));rel=(sol['Rf']@side.rel['Hand']).inverted()@rh;sw,tw=IK.swing_twist_deg(rel.to_quaternion(),finger);upper=IK.swing_twist_deg((parent.inverted()@sol['Ra']).to_quaternion(),side.uA)[1];flex=math.degrees((sol['E']-sol['S']).angle(sol['W']-sol['E']))
   if sw<=65 and abs(tw)<=80 and abs(upper)<=80 and flex<=145 and sol['miss']<.001:
    cost=sw+abs(tw)*.2+abs(upper)*.1;out.append((cost,sol,{'swing':sw,'twist':tw,'upper':upper,'flex':flex}))
 return sorted(out,key=lambda row:row[0])[:2]
results=[]
for x in [-.20,-.25,-.30,-.35,-.40]:
 for y in [-.55,-.65,-.75,-.85,-.95]:
  for z in [.80,.90,1.00,1.10,1.20,1.30]:
   G=Vector((x,y,z));right=solutions('R',G)
   if not right:continue
   for spacing in [.10,.16,-.10]:
    left=solutions('L',G+axis*spacing)
    if not left:continue
    score=(G-Vector((-.245,-.75,1.03))).length*100+right[0][0]+left[0][0]
    results.append((score,G,spacing,right[0],left[0]))
 print('SEARCH_X',x,'feasible',len(results),flush=True)
results.sort(key=lambda row:row[0]);output=[]
for score,G,spacing,R,L in results[:20]:
 row={'score':score,'grip':list(G),'spacing':spacing,'metrics':{'R':R[2],'L':L[2]},'bones':{}}
 for sd,sol in [('R',R[1]),('L',L[1])]:
  sides[sd].apply(sol)
  for part in ['UpperArm','Forearm','Hand']:n=f'B_{sd}_{part}';row['bones'][n]=list(r.pose.bones[n].rotation_quaternion)
 output.append(row)
(P/'work/round3_feasible_impacts.json').write_text(json.dumps(output,indent=2));print('FEASIBLE',output[:1],flush=True)
