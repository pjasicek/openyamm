"""Keep the off-hand approach outside the torso and haft, then seat the fixed grip."""
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/'scripts/review3_collision_search.py').read_text().split('results=[]')[0].replace('round3_key_baseline/','').replace('34/48','42/48').replace('import arm_ik as IK','import arm_ik as IK;import importlib;importlib.reload(IK)')
exec(compile(s,str(P/'scripts/review3_collision_search.py'),'exec'))
rows=[];worlds=[]
for f in range(109):
 C.activate('Attack',f/48);rows.append({b.name:b.matrix_basis.copy()for b in r.pose.bones});worlds.append({b.name:b.matrix.copy()for b in r.pose.bones})
r.animation_data.action=None;side=sides['L'];h=r.data.bones['B_L_Hand'];ax=h.matrix_local.to_3x3().inverted()@(sum((r.data.bones[f'B_L_Finger{i}'].head_local for i in range(5)),Vector())/5-h.head_local).normalized();options=[];relL=worlds[42]['Spear'].inverted()@worlds[42]['B_L_Hand']
for f in range(28,43):
 for n,m in rows[f].items():r.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
 right=sides['R'];rhR=r.pose.bones['B_R_Hand'].matrix.to_3x3();GR=r.pose.bones['B_R_Hand'].matrix@right.grip_hand
 if 34<f<42:GR+=Vector((0,.060,.040))*math.sin(math.pi*(f-34)/8)**2
 rs=right.pose_anatomical(GR,rhR,r.pose.bones['B_R_Forearm'].head-r.pose.bones['B_R_UpperArm'].head);right.apply(rs);R=(0,rs,{})
 if f>=37:
  G=r.pose.bones['Spear'].matrix@Vector((0,0,-.16));rh=(r.pose.bones['Spear'].matrix@relL).to_3x3()
 else:
  G=r.pose.bones['B_L_Hand'].matrix@side.grip_hand;rh=r.pose.bones['B_L_Hand'].matrix.to_3x3();amount=max(0,min(1,(f-28)/9));amount=amount*amount*(3-2*amount)
  target_rh=(r.pose.bones['Spear'].matrix@relL).to_quaternion();rh=rh.to_quaternion().slerp(target_rh,amount).to_matrix()
  target=r.pose.bones['Spear'].matrix@Vector((0,0,-.16))+rh@Vector((0,0,.07*(1-amount)));G=G.lerp(target,amount)

 S0=r.pose.bones['B_L_UpperArm'].head.copy();pole=r.pose.bones['B_L_Forearm'].head-S0;u=(G-rh@side.grip_hand-S0).normalized();parent=r.pose.bones['B_L_Clavicle'].matrix.to_3x3()@side.rel['Arm'];spear_surface=Shared.Surface(mesh,mesh.solid&~mesh.regions['hand_R']&(~mesh.regions['hand_L']if f>=37 else np.ones(len(mesh.rest),bool)));opts=[]
 for deg in range(-12,13,2):
  sol=side.pose_anatomical(G,rh,Quaternion(u,math.radians(deg))@pole);sw,tw=IK.swing_twist_deg(((sol['Rf']@side.rel['Hand']).inverted()@rh).to_quaternion(),ax);upper=IK.swing_twist_deg((parent.inverted()@sol['Ra']).to_quaternion(),side.uA)[1];c=contacts(R,(0,sol,{}));cost=1000*sum(max(0,v-1.8)**2 for v in c.values())+.2*deg*deg + (1000*deg*deg if f in [28,42] else 0)+1000*sum(max(0,v-lim)**2 for v,lim in [(sw,66),(abs(tw),84),(abs(upper),84),(sol['miss']*1000 if f>=37 else 0,.5)])
  opts.append({'cost':cost,'pole_delta_deg':deg,'objective_mm':c,'miss_mm':sol['miss']*1000,'q':np.array(list(sol['Ra'].to_quaternion())),'row':{b.name:b.matrix_basis.copy()for b in r.pose.bones}})
 options.append(opts);print('ENTRY_OPTIONS',f,min(o['cost']for o in opts),flush=True)
cost=np.array([o['cost']for o in options[0]]);backs=[]
for i in range(1,len(options)):
 prev=options[i-1];cur=options[i];q0=np.array([o['q']for o in prev]);q1=np.array([o['q']for o in cur]);angle=np.degrees(2*np.arccos(np.clip(abs(q0@q1.T),0,1)));transition=angle*angle*2;values=cost[:,None]+transition;back=np.argmin(values,axis=0);cost=np.array([o['cost']for o in cur])+values[back,np.arange(len(cur))];backs.append(back)
ids=[int(np.argmin(cost))]
for back in reversed(backs):ids.append(int(back[ids[-1]]))
ids.reverse();author=[]
angles=np.array([opts[i]['pole_delta_deg'] for opts,i in zip(options,ids)],float)
for _ in range(2):angles=np.convolve(np.pad(angles,2),np.array([1,4,6,4,1])/16,'valid')
angles[0]=angles[-1]=0
for k,(f,opts,i) in enumerate(zip(range(28,43),options,ids)):
 selected=opts[i]
 # Slerp neighbouring anatomical solutions at the smoothed pole angle.
 j=max(0,min(len(opts)-2,int((angles[k]+12)//2)));t=(angles[k]-(-12+j*2))/2
 row=dict(selected['row'])
 for n,m in row.items():
  if n.startswith('B_L_') and any(part in n for part in ['UpperArm','Forearm','Hand']):
   q=opts[j]['row'][n].to_quaternion().slerp(opts[j+1]['row'][n].to_quaternion(),t);v=q.to_matrix().to_4x4();v.translation=m.translation;row[n]=v
 rows[f]=row;author.append({'frame':f,'filtered_pole_deg':angles[k],**{k:selected[k]for k in ['cost','pole_delta_deg','objective_mm','miss_mm']}})
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f in range(28,43):
  for n,m in rows[f].items():
   if not any(n.startswith(f'B_{sd}_{part}')for sd in 'LR'for part in ['UpperArm','Forearm','Hand']):continue
   b=r.pose.bones[n];b.matrix_basis=m;b.keyframe_insert('rotation_quaternion',frame=f,group=n)
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
(P/'review/round3_entry_clearance.json').write_text(json.dumps(author,indent=2));print('ENTRY_SELECTED',author,flush=True)
