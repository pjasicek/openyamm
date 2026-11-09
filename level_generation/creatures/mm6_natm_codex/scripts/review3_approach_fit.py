"""Fit a smooth free-hand approach envelope against the shared collision evaluator."""
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=(P/'scripts/review3_collision_search.py').read_text().split('results=[]')[0].replace('round3_key_baseline/','').replace('34/48','42/48').replace('import arm_ik as IK','import arm_ik as IK;import importlib;importlib.reload(IK)')
exec(compile(s,str(P/'scripts/review3_collision_search.py'),'exec'))
side=sides['L'];rows={};base={};names=['B_L_UpperArm','B_L_Forearm','B_L_Hand'];h=r.data.bones['B_L_Hand'];axis=h.matrix_local.to_3x3().inverted()@(sum((r.data.bones[f'B_L_Finger{i}'].head_local for i in range(5)),Vector())/5-h.head_local).normalized()
for f in range(30,45):
 C.activate('Attack',f/48);rows[f]={b.name:b.matrix_basis.copy()for b in r.pose.bones};base[f]=(r.pose.bones['B_L_Hand'].matrix@side.grip_hand,r.pose.bones['B_L_Hand'].matrix.to_3x3(),r.pose.bones['B_L_Forearm'].head-r.pose.bones['B_L_UpperArm'].head)
r.animation_data.action=None;spear_surface=Shared.Surface(mesh,mesh.solid&~mesh.regions['hand_R']);counter=0

def evaluate(params,save=False):
 global counter
 cost=.08*float(params@params);result={};metrics=[];quats={f:{n:rows[f][n].to_quaternion()for n in names}for f in rows}
 for f in range(33,42):
  for n,m in rows[f].items():r.pose.bones[n].matrix_basis=m
  bpy.context.view_layer.update();G,Rh,pole=base[f];G=G.copy();Rh=Rh.copy();u=math.sin(math.pi*(f-32)/10)
  G+=Vector(params[:3])*.001*u
  rot=Vector(params[3:6])*math.pi/180*u
  if rot.length>0:Rh=Quaternion(rot.normalized(),rot.length).to_matrix()@Rh
  S=r.pose.bones['B_L_UpperArm'].head;direction=(G-Rh@side.grip_hand-S).normalized();sol=side.pose_anatomical(G,Rh,Quaternion(direction,math.radians(params[6]*u))@pole)
  rr=(0,dict(Ra=r.pose.bones['B_R_UpperArm'].matrix.to_3x3(),Rf=r.pose.bones['B_R_Forearm'].matrix.to_3x3(),Rh=r.pose.bones['B_R_Hand'].matrix.to_3x3(),S=r.pose.bones['B_R_UpperArm'].head.copy(),E=r.pose.bones['B_R_Forearm'].head.copy(),W=r.pose.bones['B_R_Hand'].head.copy()),{})
  contact=contacts(rr,(0,sol,{}));sw,tw=IK.swing_twist_deg(((sol['Rf']@side.rel['Hand']).inverted()@Rh).to_quaternion(),axis);parent=r.pose.bones['B_L_Clavicle'].matrix.to_3x3()@side.rel['Arm'];upper=IK.swing_twist_deg((parent.inverted()@sol['Ra']).to_quaternion(),side.uA)[1]
  cost+=1000*sum(max(0,v-1.5)**2 for v in contact.values())+1000*sum(max(0,v-lim)**2 for v,lim in [(sw,68),(abs(tw),88),(abs(upper),88)])
  quats[f]={n:r.pose.bones[n].rotation_quaternion.copy()for n in names};result[f]={b.name:b.matrix_basis.copy()for b in r.pose.bones};metrics.append({'frame':f,'contacts':contact,'wrist':[sw,tw],'upper_roll':upper})
 for n in names:
  vectors=[]
  for f in range(30,44):
   q=quats[f][n].inverted()@quats[f+1][n]
   if q.w<0:q.negate()
   vectors.append(np.array(q.axis)*math.degrees(q.angle))
  steps=np.linalg.norm(vectors,axis=1);acc=np.linalg.norm(np.diff(vectors,axis=0),axis=1)*48*48
  cost+=1000*sum(np.maximum(steps-24,0)**2)+sum(np.maximum(acc-18000,0)**2)*.001
 counter+=1
 if save:return cost,result,metrics
 return cost
best=np.zeros(7);score=evaluate(best);rng=np.random.default_rng(7)
for step in [12,7,3,1]:
 for sweep in range(3):
  changed=False
  for k in range(7):
   for sign in [-1,1]:
    q=best.copy();q[k]+=sign*step
    if abs(q[k])>(60 if k<3 else 30):continue
    value=evaluate(q)
    if value<score:best,score=q,value;changed=True
  print('APPROACH_FIT',step,sweep,score,best.tolist(),flush=True)
  if not changed:break
score,result,metrics=evaluate(best,True);print('APPROACH_FINAL',score,best.tolist(),metrics,flush=True)
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f,row in result.items():
  for n,m in row.items():
   if not any(n.startswith('B_L_'+part)for part in ['UpperArm','Forearm','Hand']):continue
   b=r.pose.bones[n];b.matrix_basis=m;b.keyframe_insert('rotation_quaternion',frame=f,group=n)
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
(P/'review/round3_approach_fit.json').write_text(json.dumps({'parameters':best.tolist(),'objective':score,'evaluations':counter,'frames':metrics},indent=2,default=float))
