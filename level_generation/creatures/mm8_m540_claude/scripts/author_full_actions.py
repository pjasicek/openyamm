"""Complete the Mage set with Ogre recoil/fall and native wand inspection."""
from pathlib import Path
import bpy,sys,os,runpy,ast,math,json,numpy as np
from mathutils import Vector,Quaternion,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
import common,armik
os.environ['SOURCE_TURN_DEG']='0'
s=p/'scripts/retarget.py';ogre=p.parent/'mm6_ogr_claude/export/mm6_ogr.glb'
sys.argv=[str(s),'--',str(p/'work/pilots_fitted.blend'),str(p/'work/full_sources.blend'),f'{ogre}:Hit:HitSource',f'{ogre}:Death:DeathSource']
runpy.run_path(str(s),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_sources.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];wand=bpy.data.objects['Wand'];scene=bpy.context.scene
scene.render.fps=30;names=[b.name for b in rig.data.bones]
tree=ast.parse((p/'scripts/author_pilots.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'set_act','sample','apply','current','write','turn','path','arm'}],type_ignores=[]),'pilot_helpers','exec'),globals())
g=json.loads((p/'work/grip_pose.json').read_text());axis=Vector(g['handle_axis_hand_local'])
ST=sample(bpy.data.actions['Standing'],0)
def smooth(x):
 x=float(np.clip(x,0,1));return x*x*(3-2*x)
def points(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();P=np.array([tuple(obj.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();return P
pv=np.array([x.value for x in body.data.attributes['piece'].data]);feet=np.isin(pv,[3,4])
report={};out={}
for name,fi,fo in [('Hit',3,6),('Death',6,0)]:
 a=bpy.data.actions[name+'Source'];N=int(a.frame_range[1]);first=sample(a,0);poses=[]
 for f in range(N+1):
  raw=sample(a,f);pose={}
  for n,(q,l) in raw.items():
   if name=='Hit':
    if n=='B_Pelvis' or any(k in n for k in ('Thigh','Calf','Foot','Toe')):q,l=ST[n]
    else:q,l=(q@first[n][0].inverted())@ST[n][0],ST[n][1]
   if name=='Hit':
    gain=.12 if n in ('B_Head','B_Neck') else .30 if any(k in n for k in ('Clavicle','UpperArm','Forearm','Hand')) else .55
    q=ST[n][0].slerp(q if ST[n][0].dot(q)>=0 else -q,gain)
   elif name=='Death' and any(k in n for k in ('Clavicle','UpperArm','Forearm','Hand','Head','Neck')):
    gain=.10 if n in ('B_Head','B_Neck') else .25 if 'Clavicle' in n else .65
    q=ST[n][0].slerp(q if ST[n][0].dot(q)>=0 else -q,gain)
   if any(k in n for k in ('Finger','Wand','Cape','Loin')):q,l=ST[n]
   w=min(smooth(f/fi),smooth((N-f)/fo) if fo else 1)
   if ST[n][0].dot(q)<0:q=-q
   pose[n]=(ST[n][0].slerp(q,w),ST[n][1].lerp(l,w))
  apply(pose)
  if name=='Death':
   # Spread the falling arms away from the rising knees, in the chest's frame.
   forward=(rig.pose.bones['B_Spine2'].matrix@rig.data.bones['B_Spine2'].matrix_local.inverted()).to_3x3()@Vector((0,-1,0))
   for side,sign in [('L',1),('R',-1)]:turn(f'B_{side}_UpperArm',forward,sign*20*smooth(f/8))
   # The held wand follows the falling arm; retain the fitted wrist and finger grip.
   for side in 'RL':rig.pose.bones[f'B_{side}_Hand'].rotation_quaternion=ST[f'B_{side}_Hand'][0]
   for k in range(3):rig.pose.bones[f'Cape{k}'].rotation_quaternion=ST[f'Cape{k}'][0]
   rig.pose.bones['LoinFront'].rotation_quaternion=ST['LoinFront'][0].slerp(Quaternion(),smooth(f/N))
  bpy.context.view_layer.update();poses.append(current())
 poses[0]=ST
 if name=='Hit':poses[-1]=ST
 out[name]=poses;report[name]={'source':'completed MM6 Ogre '+name,'duration_seconds':N/30}
apply(ST);ready=armik.W(rig,'B_R_Hand').translation.copy();up=armik.W(rig,'B_R_Hand').to_3x3()@axis
poses=[];last=None;checks=[];N=45
for f in range(N+1):
 t=f/30;envelope=math.sin(math.pi*f/N)**2;apply(ST)
 for bone,angle in [('B_Spine',4),('B_Spine1',4),('B_Head',8)]:turn(bone,(1,0,0),angle*envelope)
 right=path(t,[(0,ready),(.45,(-.34,-.30,1.08)),(.85,(-.34,-.30,1.08)),(1.15,(-.35,-.28,.96)),(1.5,ready)])
 direction=path(t,[(0,up),(.45,(.12,-.06,.99)),(.85,(.12,-.06,.99)),(1.5,up)]).normalized()
 last,c=arm('R',right,direction,last);checks.append(c);poses.append(current())
poses[0]=ST;poses[-1]=ST;out['Fidget']=poses
report['Fidget']={'source':'native bend and wand inspection, fitted Mage IK','duration_seconds':N/30,'max_wrist_swing':max(c['swing'] for c in checks)}
for name,poses in out.items():write(name,poses)
FA=UA=.5;tree=ast.parse((p/'scripts/twist_bones.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'twist_about','bake_twist'}],type_ignores=[]),'twist_bake','exec'),globals())
for name in out:bake_twist(bpy.data.actions[name])
for name in out:
 a=bpy.data.actions[name];poses=[sample(a,f) for f in range(int(a.frame_range[1])+1)];lows=[]
 for pose in poses:
  apply(pose);P=points(body);lows.append(float(min(P[:,2].min(),points(wand)[:,2].min()) if name=='Death' else P[feet,2].min()))
 for f,pose in enumerate(poses):
  apply(pose);root=rig.pose.bones['B_Pelvis'];m=root.matrix.copy();m.translation.z-=lows[f];root.matrix=m;bpy.context.view_layer.update();poses[f]=current()
 if name!='Death':poses[0]=ST;poses[-1]=ST
 write(name,poses);report[name]['floor_before_m']=[min(lows),max(lows)]
death=bpy.data.actions['Death'];end=sample(death,death.frame_range[1]);write('Dead',[end for _ in range(31)])
for name in ('HitSource','DeathSource','CastSource'):
 if name in bpy.data.actions:bpy.data.actions.remove(bpy.data.actions[name])
set_act(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_actions.blend'))
(p/'review/full_actions.json').write_text(json.dumps(report,indent=2)+'\n');print('FULL_ACTIONS',report,flush=True)
common.workbench_clay(scene)
for name in ['Hit','Death','Fidget']:
 a=bpy.data.actions[name];set_act(a);N=int(a.frame_range[1])
 for f in sorted(set([0,round(N*.25),round(N*.5),round(N*.75),N])):
  scene.frame_set(f);common.render_views(str(p/f'review/full_actions/{name}_{f:03d}'),.85,2.5,views=('front','left','back'),resolution=(480,600))
