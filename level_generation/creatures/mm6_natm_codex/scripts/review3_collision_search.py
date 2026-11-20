"""Find feasible anatomical two-hand impact poses around the native lunge target."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3_key_baseline/runtime_lod0.blend'));C.activate('Attack',34/48);r=bpy.data.objects['Rig'];snapshot={b.name:b.matrix_basis.copy()for b in r.pose.bones};r.animation_data.action=None
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
 return sorted(out,key=lambda row:row[0])[:5]
# The shared evaluator is an authoring objective here; acceptance still uses the unmodified runner.
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as Shared
config=json.loads((P/'gates.json').read_text());glb=Shared.Glb(P/'export/mm6_natm.glb');mesh=Shared.load_meshes(glb)[0];Shared.configure_mesh(mesh,config,Shared.Report(config));prop_mesh={}
for name in ['spear','buckler']:prop_mesh[name]=Shared.load_meshes(Shared.Glb(P/f'export/mm6_natm_{name}.glb'))[0]
solid=Shared.Surface(mesh,mesh.solid);spear_surface=Shared.Surface(mesh,mesh.solid&~mesh.regions['hand_L']&~mesh.regions['hand_R'])
base_twist=r.pose.bones['B_L_ForearmTwist'].matrix_basis.copy()
def contacts(R,L):
 for sd,item in [('R',R),('L',L)]:
  sides[sd].apply(item[1]);fb=r.data.bones[f'B_{sd}_Forearm'];hb=r.data.bones[f'B_{sd}_Hand'];ub=r.data.bones[f'B_{sd}_UpperArm'];ax=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(r.pose.bones[fb.name].matrix.inverted()@r.pose.bones[hb.name].matrix).to_quaternion();rr=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();tw=IK.swing_twist_deg(rel@rr.inverted(),ax)[1]
  if sd=='R':r.pose.bones['B_R_ForearmTwist'].rotation_quaternion=Quaternion(ax,math.radians(max(-80,min(80,.6*tw))))
  else:r.pose.bones['B_L_ForearmTwist'].matrix_basis=base_twist
  ax=(ub.matrix_local.inverted()@fb.head_local).normalized();tw=IK.swing_twist_deg(r.pose.bones[ub.name].rotation_quaternion,ax)[1];r.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_quaternion=Quaternion(ax,math.radians(-.5*tw))
 bpy.context.view_layer.update();pose=glb.rest.copy()
 for bone in r.pose.bones:
  if bone.name in glb.names:pose[glb.names[bone.name]]=np.array(bone.matrix)
 points=mesh.posed(pose);values={}
 for sd in 'LR':values[sd]=Shared.penetration(mesh.surfaces[sd].build(points),points[mesh.contact_samples[sd]])[0]
 for name,node,surface in [('spear','Spear',spear_surface),('buckler','Buckler',solid)]:
  prop=Shared.transform(pose[glb.names[node]]@np.linalg.inv(Shared.C),prop_mesh[name].rest);values[name]=Shared.penetration(surface.build(points),prop)[0]
 return values
results=[]
for x in [-.20,-.25,-.30,-.35,-.40]:
 for y in [-.55,-.65,-.75,-.85,-.95]:
  for z in [.70,.80,.90,1.00,1.10,1.20]:
   G=Vector((x,y,z));right=solutions('R',G)
   if not right:continue
   for spacing in [.16,.10,-.10,-.16]:
    left=solutions('L',G+axis*spacing)
    if not left:continue
    for R in right:
     for L in left:
      collision=contacts(R,L);score=(G-Vector((-.245,-.75,1.03))).length*100+R[0]+L[0]+max(collision.values())*1000
      results.append((score,G.copy(),spacing,R,L,collision))
 print('COLLISION_SEARCH_X',x,'pairs',len(results),'best',min((v[0]for v in results),default=None),flush=True)
results.sort(key=lambda row:row[0]);output=[]
for score,G,spacing,R,L,collision in results[:30]:
 row={'score':score,'grip':list(G),'spacing':spacing,'metrics':{'R':R[2],'L':L[2]},'collision_objective_mm':collision,'bones':{}}
 for sd,sol in [('R',R[1]),('L',L[1])]:
  sides[sd].apply(sol)
  for part in ['UpperArm','Forearm','Hand']:n=f'B_{sd}_{part}';row['bones'][n]=list(r.pose.bones[n].rotation_quaternion)
 output.append(row)
(P/'work/round3_collision_impacts.json').write_text(json.dumps(output,indent=2));print('BEST_COLLISION_FIT',output[:1],flush=True)
