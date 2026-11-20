"""Complete Guardian reactions and fall around the accepted pilot hunch, preserving source timing."""
from pathlib import Path
import bpy,sys,json,math,ast,numpy as np
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'));import common,armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots_fitted.blend'));scene=bpy.context.scene;scene.render.fps=30;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];names=[b.name for b in rig.data.bones]
tree=ast.parse((P/'scripts/author_pilots.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'action','reset','current','apply','write','turn','surface','path'}],type_ignores=[]),'pilot_helpers','exec'),globals())
def sample(a,f):
 action(a);scene.frame_set(int(f),subframe=f%1);return current()
ST=sample(bpy.data.actions['Standing'],0);SW={n:armik.W(rig,n).copy() for n in names};co=np.array([tuple(v.co) for v in body.data.vertices]);feet=np.flatnonzero((co[:,2]<.12)&(abs(co[:,0])<.5));parts=np.array([v.value for v in body.data.attributes['piece'].data]);F=json.loads(scene['guardian_claws'])
action(None);before=set(bpy.data.objects);acts=set(bpy.data.actions);bpy.ops.import_scene.gltf(filepath=str(P.parent/'mm6_ogr_claude/export/mm6_ogr.glb'));new=set(bpy.data.objects)-before;src=next(o for o in new if o.type=='ARMATURE');sn=[n for n in names if n in src.pose.bones and 'Finger' not in n and 'Twist' not in n];sources={}
for name in ('Hit','Death'):
 a=next(a for a in set(bpy.data.actions)-acts if a.name.split('|')[-1].split('@')[-1].split('.')[0]==name);src.animation_data.action=a;src.animation_data.action_slot=a.slots[0];f0,f1=a.frame_range;N=round(f1-f0);rows=[]
 for f in range(N+1):
  scene.frame_set(int(f0+f),subframe=(f0+f)%1);rows.append({n:(src.matrix_world@src.pose.bones[n].matrix).copy() for n in sn})
 sources[name]=rows
for o in new:bpy.data.objects.remove(o,do_unlink=True)
for a in set(bpy.data.actions)-acts:bpy.data.actions.remove(a)
def smooth(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
report={};out={}
# The Ogre falls sideways. Reorient its measured lean/descent progression to the native Guardian's backward fall.
for name,rows in sources.items():
 N=len(rows)-1;poses=[];floor=[]
 if name=='Death':
  angles=[]
  for row in rows:
   D=row['B_Pelvis'].to_quaternion()@rows[0]['B_Pelvis'].to_quaternion().inverted();up=D@Vector((0,0,1));angles.append(math.acos(float(np.clip(up.z,-1,1))))
  progress=np.maximum.accumulate(angles);progress=np.convolve(np.pad(progress,(1,1),mode='edge'),[.25,.5,.25],mode='valid');progress=(progress-progress[0])/(progress[-1]-progress[0])
 for f,row in enumerate(rows):
  apply(ST)
  if name=='Hit':
   w=min(smooth(f/5),smooth((N-f)/5))
   for n in sn:
    if n=='B_Pelvis' or any(x in n for x in ('Thigh','Calf','Foot','Toe','Twist')):continue
    D=row[n].to_quaternion()@rows[0][n].to_quaternion().inverted()
    if D.w<0:D=-D
    D=Quaternion().slerp(D,.4*w);m=armik.W(rig,n);armik.set_world(rig,n,armik.rot_world(m,D.to_matrix()@SW[n].to_3x3().normalized()))
   rig.pose.bones['Jaw'].rotation_quaternion=Quaternion((1,0,0),math.radians(-3+5*math.sin(math.pi*f/N)**2))
  else:
   u=float(progress[f]);R=Matrix.Rotation(-math.pi/2*u,3,'X');m=armik.W(rig,'B_Pelvis');m=armik.rot_world(m,R@SW['B_Pelvis'].to_3x3().normalized());m.translation=SW['B_Pelvis'].translation+Vector((0,.30*u,(row['B_Pelvis'].translation.z-rows[0]['B_Pelvis'].translation.z)*.75));armik.set_world(rig,'B_Pelvis',m)
   turn('B_Spine',(1,0,0),-4*math.sin(math.pi*u));forward=R@Vector((0,-1,0))
   for sd,sign in [('L',1),('R',-1)]:turn(f'B_{sd}_UpperArm',forward,sign*50*smooth(u/.8))
   rig.pose.bones['Jaw'].rotation_quaternion=Quaternion((1,0,0),math.radians(-3+10*math.sin(math.pi*u)**2))
  bpy.context.view_layer.update();v=surface();low=float(v[:,2].min() if name=='Death' else v[feet,2].min());m=armik.W(rig,'B_Pelvis');m.translation.z-=low;armik.set_world(rig,'B_Pelvis',m);floor.append(low);poses.append(current())
 poses[0]=ST
 if name=='Hit':poses[-1]=ST
 out[name]=poses;report[name]={'duration':N/30,'source':'Completed MM6 Ogre '+name,'adaptation':'Measured Ogre lean/descent timing reoriented backward; native spread arms and upturned feet.' if name=='Death' else 'Ogre recoil about the Guardian hunch','floor_before':[min(floor),max(floor)]}
poses=[];N=19
for f in range(N+1):
 apply(ST);u=f/N;env=math.sin(math.pi*u)**2;turn('B_Spine',(1,0,0),7*env);turn('B_Spine2',(1,0,0),3*env);turn('B_Head',(1,0,0),-7*env)
 for sd,sign in [('R',-1),('L',1)]:turn(f'B_{sd}_UpperArm',(0,-1,0),sign*5*env)
 rig.pose.bones['Jaw'].rotation_quaternion=Quaternion((1,0,0),math.radians(-3+17*env));bpy.context.view_layer.update();poses.append(current())
poses[0]=ST;poses[-1]=ST;out['Fidget']=poses;report['Fidget']={'duration':N/30,'source':'Native shoulder lift and jaw roar, fitted hunch; 19-frame sampling of 0.625-second evidence.'}
for name,poses in out.items():write(name,poses)
FA=.6;UA=.5;tree=ast.parse((P.parent/'mm6_natm_claude/scripts/twist_bones.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'twist_about','bake_twist'}],type_ignores=[]),'twist_bake','exec'),globals())
for name in out:bake_twist(bpy.data.actions[name])
# Recheck the actual twist-deformed body floor before freezing its corpse endpoint.
for name in out:
 a=bpy.data.actions[name];poses=[]
 step=.25 if name=='Death' else 1
 for f in np.arange(0,a.frame_range[1]+.001,step):
  pose=sample(a,float(f));apply(pose);v=surface();low=float(v[:,2].min() if name=='Death' else v[feet,2].min());m=armik.W(rig,'B_Pelvis');m.translation.z-=low;armik.set_world(rig,'B_Pelvis',m);poses.append(current())
 write(name,poses)
 if step!=1:
  a=bpy.data.actions[name]
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for k in fc.keyframe_points:k.co.x*=step;k.handle_left.x*=step;k.handle_right.x*=step
  a.frame_end*=step
end=sample(bpy.data.actions['Death'],bpy.data.actions['Death'].frame_range[1]);write('Dead',[end,end]);write('Dying',[end,end]);reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/full_actions.blend'));(P/'review/full_actions.json').write_text(json.dumps(report,indent=2)+'\n');print('FULL_ACTIONS',report,flush=True)
common.workbench_clay(scene);outdir=P/'review/full_actions';outdir.mkdir(exist_ok=True)
for name in ('Hit','Fidget','Death'):
 a=bpy.data.actions[name];action(a);N=int(a.frame_range[1])
 for f in sorted(set([0,round(N*.25),round(N*.5),round(N*.75),N])):
  scene.frame_set(f);common.render_views(str(outdir/f'{name}_{f:03d}'),.95,3,views=('front','left','three_quarter'),resolution=(650,650))
