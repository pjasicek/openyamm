"""Refit the off-hand elbow around the torso while retaining its seated power grip."""
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/'scripts/review3_collision_search.py').read_text().split('results=[]')[0].replace('round3_key_baseline/','').replace('34/48','42/48')
exec(compile(s,str(P/'scripts/review3_collision_search.py'),'exec'))
R=(0,dict(Ra=r.pose.bones['B_R_UpperArm'].matrix.to_3x3(),Rf=r.pose.bones['B_R_Forearm'].matrix.to_3x3(),Rh=r.pose.bones['B_R_Hand'].matrix.to_3x3(),S=r.pose.bones['B_R_UpperArm'].head.copy(),E=r.pose.bones['B_R_Forearm'].head.copy(),W=r.pose.bones['B_R_Hand'].head.copy()),{})
side=sides['L'];G=r.pose.bones['Spear'].matrix@Vector((0,0,-.16));rh=r.pose.bones['B_L_Hand'].matrix.to_3x3();S0=r.pose.bones['B_L_UpperArm'].head.copy();pole=r.pose.bones['B_L_Forearm'].head-S0;u=(G-rh@side.grip_hand-S0).normalized();parent=r.pose.bones['B_L_Clavicle'].matrix.to_3x3()@side.rel['Arm'];h=r.data.bones['B_L_Hand'];ax=h.matrix_local.to_3x3().inverted()@(sum((r.data.bones[f'B_L_Finger{i}'].head_local for i in range(5)),Vector())/5-h.head_local).normalized();out=[]
for deg in range(-90,91,2):
 sol=side.pose_anatomical(G,rh,Quaternion(u,math.radians(deg))@pole);sw,tw=IK.swing_twist_deg(((sol['Rf']@side.rel['Hand']).inverted()@rh).to_quaternion(),ax);upper=IK.swing_twist_deg((parent.inverted()@sol['Ra']).to_quaternion(),side.uA)[1];c=contacts(R,(0,sol,{}));score=max(c.values())*1000+abs(deg)+100*sum(max(0,v-lim)**2 for v,lim in [(sw,65),(abs(tw),80),(abs(upper),80)]);out.append((score,deg,sol,c,[sw,tw,upper]))
out.sort(key=lambda x:x[0]);score,deg,sol,c,metrics=out[0];contacts(R,(0,sol,{}));row={'elbow_pole_delta_deg':deg,'objective_mm':c,'wrist_swing_roll_upper_roll':metrics,'bones':{f'B_L_{n}':list(r.pose.bones[f'B_L_{n}'].rotation_quaternion)for n in ['UpperArm','Forearm','Hand']}};(P/'work/round3_impact_left_refit.json').write_text(json.dumps(row,indent=2));print('LEFT_IMPACT_REFIT',row,flush=True)
