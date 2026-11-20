"""Seat the off hand before the forward drive, with a fixed physical grip frame."""
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/'scripts/review3_collision_search.py').read_text().split('results=[]')[0].replace('round3_key_baseline/','').replace('34/48','42/48').replace('import arm_ik as IK','import arm_ik as IK;import importlib;importlib.reload(IK)')
exec(compile(s,str(P/'scripts/review3_collision_search.py'),'exec'))
rows={};worlds={}
for f in [39,40,41,42]:
 C.activate('Attack',f/48);rows[f]={b.name:b.matrix_basis.copy()for b in r.pose.bones};worlds[f]={b.name:b.matrix.copy()for b in r.pose.bones}
r.animation_data.action=None;rel=worlds[42]['Spear'].inverted()@worlds[42]['B_L_Hand'];side=sides['L'];h=r.data.bones['B_L_Hand'];axis=h.matrix_local.to_3x3().inverted()@(sum((r.data.bones[f'B_L_Finger{i}'].head_local for i in range(5)),Vector())/5-h.head_local).normalized();selected={};report=[]
for f in [40,41]:
 candidates=[]
 for dy in [0,.005,.010,.015]:
  for n,m in rows[f].items():r.pose.bones[n].matrix_basis=m
  for n,q in lg['finger_local'].items():r.pose.bones[n].rotation_quaternion=Quaternion(q)
  bpy.context.view_layer.update();right=sides['R'];hr=r.pose.bones['B_R_Hand'];G=hr.matrix@right.grip_hand+Vector((0,dy,dy/2));rr=right.pose_anatomical(G,hr.matrix.to_3x3(),r.pose.bones['B_R_Forearm'].head-r.pose.bones['B_R_UpperArm'].head);right.apply(rr);sp=r.pose.bones['Spear'].matrix.copy();Rh=(sp@rel).to_3x3();G=sp@Vector((0,0,-.16));S0=r.pose.bones['B_L_UpperArm'].head;u=(G-Rh@side.grip_hand-S0).normalized();pole=worlds[42]['B_L_Forearm'].translation-worlds[42]['B_L_UpperArm'].translation;parent=r.pose.bones['B_L_Clavicle'].matrix.to_3x3()@side.rel['Arm']
  for deg in range(-20,21,2):
   sol=side.pose_anatomical(G,Rh,Quaternion(u,math.radians(deg))@pole);c=contacts((0,rr,{}),(0,sol,{}));sw,tw=IK.swing_twist_deg(((sol['Rf']@side.rel['Hand']).inverted()@Rh).to_quaternion(),axis);roll=IK.swing_twist_deg((parent.inverted()@sol['Ra']).to_quaternion(),side.uA)[1];cost=1000*sum(max(0,v-1.5)**2 for v in c.values())+1000*sum(max(0,v-lim)**2 for v,lim in [(sw,68),(abs(tw),88),(abs(roll),88),(sol['miss']*1000,.3)])+.1*deg*deg+10000*dy*dy
   row={b.name:b.matrix_basis.copy()for b in r.pose.bones}
   for n in ['B_L_UpperArm','B_L_Forearm','B_L_Hand']:
    for end in [39,42]:cost+=.2*math.degrees(row[n].to_quaternion().rotation_difference(rows[end][n].to_quaternion()).angle)**2
   candidates.append((cost,row,{'frame':f,'dy':dy,'pole':deg,'contacts':c,'miss_mm':sol['miss']*1000,'wrist':[sw,tw],'upper_roll':roll}))
 cost,row,receipt=min(candidates,key=lambda x:x[0]);selected[f]=row;report.append(receipt);print('SEATED_GRIP',cost,receipt,flush=True)
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 # Restore the original smooth finger closure before seating.
 for f in range(35,40):
  t=(f-27)/15;rr=1/3;close=.5*t*t/(rr*(1-rr))if t<rr else 1-.5*(1-t)**2/(rr*(1-rr))if t>1-rr else(t-rr/2)/(1-rr)
  for n,q in lg['finger_local'].items():
   b=r.pose.bones[n];b.rotation_quaternion=Matrix(D['standing_basis'][n]).to_quaternion().slerp(Quaternion(q),close);b.keyframe_insert('rotation_quaternion',frame=f,group=n)
 for f,row in selected.items():
  for n,m in row.items():
   if not any(n.startswith(f'B_{sd}_{part}')for sd in 'LR'for part in ['UpperArm','Forearm','Hand','Finger']):continue
   b=r.pose.bones[n];b.matrix_basis=m;b.keyframe_insert('rotation_quaternion',frame=f,group=n)
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
(P/'review/round3_seated_grip.json').write_text(json.dumps(report,indent=2))
