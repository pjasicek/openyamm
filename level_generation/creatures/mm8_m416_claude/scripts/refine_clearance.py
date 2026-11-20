"""Small clearance offsets retain the measured two-hand prop relation."""
from pathlib import Path
import bpy,sys,math,json
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/all_motion.blend'));r=bpy.data.objects['Rig'];scene=bpy.context.scene
names=[p.name for p in r.pose.bones]
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
report={}
for a in list(bpy.data.actions):
 if not a.use_fake_user:continue
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];end=int(a.frame_range[1]);raw=[]
 for f in range(end+1):scene.frame_set(f);raw.append({p.name:p.matrix_basis.copy() for p in r.pose.bones})
 poses=[];checks=[]
 for f,pose in enumerate(raw):
  r.animation_data.action=None
  for n,m in pose.items():r.pose.bones[n].matrix_basis=m
  bpy.context.view_layer.update();t=f/30;contact=0;raise_w=0
  if a.name=='Attack':raise_w=smooth(t/.65)*(1-smooth((t-1.2)/.5));contact=smooth((t-.12)/.48)*(1-smooth((t-1.25)/.30))
  if a.name=='Fidget':phase=math.sin(math.pi*f/end)**2;contact=smooth((phase-.12)/.5);raise_w=.5*phase
  dz=.045*(1-raise_w)
  if a.name=='Death':dz*=1-smooth(f/6)
  R=armik.W(r,'B_R_Hand').copy();L=armik.W(r,'B_L_Hand').copy()
  target=R.translation+Vector((0,0,dz));armik.solve(r,'R',target,hand_rot=R.to_3x3().normalized())
  free=.045 if a.name!='Running' else 0
  if a.name=='Death':free=.06*(1-smooth((f-10)/12))
  target=L.translation+Vector((free*(1-contact),-.015*(1-contact) if free else 0,dz*contact));armik.solve(r,'L',target,hand_rot=L.to_3x3().normalized())
  if a.name=='Death':
   hand=r.pose.bones['B_R_Hand'];swing,twist=armik.split_swing_twist(hand.rotation_quaternion,Vector((0,1,0)));angle=min(swing.angle,2*math.pi-swing.angle);deg=math.degrees(angle)
   if deg>45:
    limited=45+10*math.tanh((deg-45)/10);weight=smooth(f/5);limited=deg*(1-weight)+limited*weight
    hand.rotation_quaternion=Quaternion((1,0,0,0)).slerp(swing,limited/deg)@Quaternion((0,1,0),twist);bpy.context.view_layer.update()
  checks.append({s:armik.wrist_cost(r,s,armik.W(r,f'B_{s}_Hand').to_3x3().normalized()) for s in 'RL'});poses.append({n:r.pose.bones[n].rotation_quaternion.copy() for n in ['B_R_UpperArm','B_R_Forearm','B_R_Hand','B_L_UpperArm','B_L_Forearm','B_L_Hand']})
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];previous={}
 for f,pose in enumerate(poses):
  for n,q in pose.items():
   if n in previous and q.dot(previous[n])<0:q=-q
   previous[n]=q.copy();r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
 report[a.name]={s:{'swing_max':max(x[s][0] for x in checks),'twist_max':max(abs(x[s][1]) for x in checks)} for s in 'RL'}
 print('REFINED',a.name,report[a.name],flush=True)
r.animation_data.action=None;(P/'work/refined_arm_checks.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/all_motion_clear.blend'))
