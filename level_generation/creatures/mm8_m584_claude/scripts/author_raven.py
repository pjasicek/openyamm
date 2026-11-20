"""Raven Man flight and two-handed overhead chop over the selected local source motions."""
from pathlib import Path
import bpy,sys,math,json
import numpy as np
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
import armik,common,grip_dp
bpy.ops.wm.open_mainfile(filepath=str(P/'work/assembled_rig.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sc.render.fps=30
names=[b.name for b in rig.data.bones]
G={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'LR'}
GC={s:Vector(G[s]['handle_centre_hand_local']) for s in 'LR'}
GA={s:Vector(G[s]['handle_axis_hand_local']) for s in 'LR'}
def action(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def reset():
 action(None)
 for b in rig.pose.bones:b.matrix_basis=Matrix()
 bpy.context.view_layer.update()
def snap():return {b.name:b.matrix_basis.copy() for b in rig.pose.bones}
def put(p):
 action(None)
 for n,m in p.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def sample(a,f):
 reset();action(a);sc.frame_set(int(f),subframe=f-int(f));return snap()
def smooth(x):
 x=max(0,min(1,x));return x*x*(3-2*x)
def blend(a,b,w):
 out={}
 for n in a:
  la,qa,sa=a[n].decompose();lb,qb,sb=b[n].decompose()
  if qa.dot(qb)<0:qb=-qb
  out[n]=Matrix.LocRotScale(la.lerp(lb,w),qa.slerp(qb,w),sa.lerp(sb,w))
 return out
def rotate(n,axis,deg):
 m=armik.W(rig,n);t=m.translation.copy();m=Matrix.Rotation(math.radians(deg),4,axis)@m;m.translation=t
 armik.set_world(rig,n,m)
def curve(keys,t):
 ts=np.array([a[0] for a in keys]);vs=np.array([a[1] for a in keys],float)
 if t<=ts[0]:return vs[0]
 if t>=ts[-1]:return vs[-1]
 i=int(np.searchsorted(ts,t)-1);h=ts[i+1]-ts[i];u=(t-ts[i])/h
 slopes=np.zeros_like(vs);slopes[1:-1]=(vs[2:]-vs[:-2])/(ts[2:]-ts[:-2])[:,None]
 return (2*u**3-3*u*u+1)*vs[i]+(u**3-2*u*u+u)*h*slopes[i]+(-2*u**3+3*u*u)*vs[i+1]+(u**3-u*u)*h*slopes[i+1]
reset();rest=snap();restW={n:armik.W(rig,n).copy() for n in names}
def leg(sd,t,lean=0):
 th,ca,ft=[f'B_{sd}_{b}' for b in ('Thigh','Calf','Foot')]
 for n in (th,ca,ft,f'B_{sd}_Toe0'):rig.pose.bones[n].matrix_basis=Matrix()
 bpy.context.view_layer.update()
 H=armik.W(rig,th).translation.copy();K=armik.W(rig,ca).translation.copy();A=armik.W(rig,ft).translation.copy()
 target=restW[ft].translation+Vector((0,.10+lean*.002,.13+.02*math.sin(math.tau*t+(0 if sd=='L' else 1.5))))
 l1=(K-H).length;l2=(A-K).length;d=target-H;dist=min(d.length,(l1+l2)*.995);u=d.normalized()
 front=Vector((0,-1,0));v=(front-u*front.dot(u)).normalized()
 c=max(-1,min(1,(l1*l1+dist*dist-l2*l2)/(2*l1*dist)))
 kn=H+l1*(u*c+v*math.sqrt(1-c*c))
 for n,child,tgt in ((th,ca,kn),(ca,ft,H+u*dist)):
  m=armik.W(rig,n);cur=armik.W(rig,child).translation-m.translation
  q=cur.normalized().rotation_difference((tgt-m.translation).normalized())
  armik.set_world(rig,n,armik.rot_world(m,q.to_matrix()@m.to_3x3().normalized()))
 rf=Matrix.Rotation(math.radians(28+3*math.sin(math.tau*t)),3,'X')@restW[ft].to_3x3()
 armik.set_world(rig,ft,armik.rot_world(armik.W(rig,ft),rf))
def settle_leg(side,w):
 th,ca,ft=[f'B_{side}_{x}' for x in ('Thigh','Calf','Foot')]
 H=armik.W(rig,th).translation.copy();K=armik.W(rig,ca).translation.copy();A=armik.W(rig,ft).translation.copy()
 foot_before=armik.W(rig,ft).to_quaternion()
 direction=Vector((.12 if side=='L' else -.12,1,0)).normalized()
 target=H+direction*min(.70,(A-H).length);target.z=.21
 target=A.lerp(target,w);target.z=max(target.z,.21);u=(target-H).normalized();l1=(K-H).length;l2=(A-K).length;dist=min((target-H).length,(l1+l2)*.995)
 up=Vector((0,0,1));v=(up-u*up.dot(u)).normalized();c=max(-1,min(1,(l1*l1+dist*dist-l2*l2)/(2*l1*dist)))
 kn=H+l1*(u*c+v*math.sqrt(1-c*c))
 for n,child,tgt in ((th,ca,kn),(ca,ft,H+u*dist)):
  m=armik.W(rig,n);q=(armik.W(rig,child).translation-m.translation).normalized().rotation_difference((tgt-m.translation).normalized())
  armik.set_world(rig,n,armik.rot_world(m,q.to_matrix()@m.to_3x3().normalized()))
 m=armik.W(rig,ft);R=Matrix.Rotation(math.atan2(direction.x,-direction.y),3,'Z')@restW[ft].to_3x3()
 armik.set_world(rig,ft,armik.rot_world(m,foot_before.slerp(R.to_quaternion(),w).to_matrix()))
 b=rig.pose.bones[f'B_{side}_Toe0'];b.rotation_mode='QUATERNION';b.rotation_quaternion=b.rotation_quaternion.slerp(Quaternion(),w)
 bpy.context.view_layer.update()

def wings(t,fold=0,falling=False):
 fold_weight=fold;fold=0
 for side,sg in (('L',1),('R',-1)):
  phase=math.tau*t-math.pi/2;upfold=((1-math.sin(phase))/2)**3;downfold=((1+math.sin(phase))/2)**3
  for n in names:
   if n.startswith((f'Wing_{side}_',f'Feather_{side}_')):rig.pose.bones[n].matrix_basis=Matrix()
  bpy.context.view_layer.update()
  D=armik.W(rig,'B_Spine2').to_3x3()@restW['B_Spine2'].to_3x3().inverted()
  ay=D@Vector((0,1,0)) if falling else 'Y';az=D@Vector((0,0,1)) if falling else 'Z'
  rotate(f'Wing_{side}_Root',ay,sg*(17+32*math.sin(phase))*(1-fold))
  rotate(f'Wing_{side}_Root',az,sg*(5*math.cos(phase)+72*fold))
  rotate(f'Wing_{side}_Arm',ay,sg*(3*math.sin(phase-.3)+42*fold))
  rotate(f'Wing_{side}_Fore',ay,sg*(3*math.sin(phase-.6)+20*upfold-65*fold))
  rotate(f'Wing_{side}_Fore',az,sg*60*(upfold+downfold))
  rotate(f'Wing_{side}_Hand',ay,sg*(3*math.sin(phase-.9)+15*upfold+42*fold))
  for i in range(10):
   b=rig.pose.bones[f'Feather_{side}_P{i:02d}']
   b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion((0,1,0),math.radians(sg*(7*math.sin(phase-.8)+i*.5)*(1-fold)))
  bpy.context.view_layer.update()
  if fold_weight:
   T=Matrix.Rotation(math.radians(-sg*15),3,'Z')@Matrix.Rotation(math.pi/2,3,'X')
   for part in ('Root','Arm','Fore','Hand'):
    n=f'Wing_{side}_{part}';m=armik.W(rig,n)
    target=T@restW[n].to_3x3()
    if part in ('Root','Arm','Fore','Hand'):
     direction=Vector((sg*.13,.07,-.02)) if part=='Root' else Vector((sg*.30,.10,-.08))
     if part=='Fore':direction=Vector((sg*.39,.10,-.14))
     if part=='Hand':direction=Vector((sg*.77,.15,-.08))
     target=(target@Vector((0,1,0))).rotation_difference(direction.normalized()).to_matrix()@target
    q=m.to_quaternion().slerp(target.to_quaternion(),fold_weight)
    armik.set_world(rig,n,armik.rot_world(m,q.to_matrix()))
   for i in range(8):rotate(f'Feather_{side}_S{i:02d}','Z',-sg*18*fold_weight)
def fingers(opening=0):
 for s in 'LR':
  for n,q in G[s]['finger_local'].items():
   b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion(q).slerp(Quaternion(),opening)
 bpy.context.view_layer.update()
def write(name,poses):
 a=bpy.data.actions.new(name);a.use_fake_user=True;action(a);prev={}
 for f,p in enumerate(poses):
  for n,m in p.items():
   loc,q,scale=m.decompose();b=rig.pose.bones[n];b.rotation_mode='QUATERNION'
   if n in prev and prev[n].dot(q)<0:q=-q
   prev[n]=q.copy();b.rotation_quaternion=q;b.location=loc;b.scale=(1,1,1)
   b.keyframe_insert('rotation_quaternion',frame=f)
   b.keyframe_insert('location',frame=f)
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1;action(None)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 return a
src={n:bpy.data.actions['Source'+n] for n in ('Idle','Attack','Hit','Death')}
initial={n:sample(a,0) for n,a in src.items()}
base=initial['Idle'].copy()
for n in ('B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head'):base[n]=rest[n].copy()
carryC=Vector((-.22,-.36,1.25));carryA=Vector((-.80,-.10,.60)).normalized()
keysC=[(0,list(carryC)),(.20,[-.15,-.22,1.50]),(.36,[-.25,-.35,1.55]),(.50,[-.15,-.46,1.16]),(.64,[-.15,-.43,1.08]),(.88,[-.22,-.40,1.27]),(1.30,list(carryC))]
keysA=[(0,list(carryA)),(.20,[-.4,.3,.86]),(.36,[-.15,.4,.90]),(.50,[-.1,-.94,.35]),(.64,[-.2,-.92,.05]),(.88,[-.6,-.4,.69]),(1.30,list(carryA))]
stats={};results={}
for name,dur in (('Standing',2),('Walking',2),('Attack',1.3),('Hit',.7333333333),('Death',1.5)):
 frames=[];count=round(dur*30)+1
 for f in range(count):
  t=f/30
  if name in ('Standing','Walking'):
   pose=sample(src['Idle'],f);pose=blend(base,pose,.32);put(pose)
  elif name=='Attack':
   pose=sample(src['Attack'],50*t/dur);put(blend(base,pose,.65*max(0,math.sin(math.pi*t/dur))**.65))
  elif name=='Hit':
   pose=sample(src['Hit'],20*t/dur);put(blend(base,pose,max(0,math.sin(math.pi*t/dur))**.45))
  else:
   pose=blend(results['Standing'][0],rest,smooth((t-.25)/.8));put(pose)
  # Remove the source guard's sideways stance; retain its change through the action.
  kind='Idle' if name in ('Standing','Walking') else name
  amplitude=.32 if kind=='Idle' else (.55*max(0,math.sin(math.pi*t/dur))**.65 if kind=='Attack' else .40)
  for n in ('B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head'):
   q0=initial[kind][n].to_quaternion();q1=pose[n].to_quaternion()
   delta=q1@q0.inverted()
   if delta.w<0:delta=-delta
   b=rig.pose.bones[n];b.rotation_mode='QUATERNION'
   if name=='Death':b.rotation_quaternion=Quaternion().slerp(delta,smooth(t/.22))
   elif n=='B_Pelvis':b.rotation_quaternion=Quaternion()
   else:
    angle=min(delta.angle,math.radians(16 if 'Spine' in n else 10))
    b.rotation_quaternion=Quaternion(delta.axis,angle*amplitude)
  if name=='Death':
   rig.pose.bones['B_Pelvis'].location=pose['B_Pelvis'].to_translation()-initial['Death']['B_Pelvis'].to_translation()
  bpy.context.view_layer.update()
  if name=='Death':
   # A controlled forward fall keeps the broad feather wings clear of the body and floor.
   pitch=float(curve([(0,[0]),(.18,[-7]),(.45,[22]),(.78,[68]),(1.12,[90]),(1.5,[90])],t)[0])
   T=Matrix.Rotation(math.radians(pitch),3,'X')
   root=armik.W(rig,'B_Pelvis')
   root.translation=Vector((0,0,float(curve([(0,[1.062]),(.18,[1.075]),(.45,[.92]),(.78,[.48]),(1.12,[.20]),(1.5,[.20])],t)[0])))
   armik.set_world(rig,'B_Pelvis',root)
   for n in ('B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head'):
    m=armik.W(rig,n);yaw=(75 if n=='B_Head' else 35 if n=='B_Neck' else 0)*smooth((t-.40)/.65)
    curl=8*math.sin(math.pi*min(1,t/1.12)) if 'Spine' in n else 0
    target=T@Matrix.Rotation(math.radians(curl),3,'X')@Matrix.Rotation(math.radians(yaw),3,'Z')@restW[n].to_3x3()
    armik.set_world(rig,n,armik.rot_world(m,target))
  if name!='Death':
   p=rig.pose.bones['B_Pelvis'];p.location=base['B_Pelvis'].to_translation()+Vector((0,0,.016*math.sin(math.tau*t)))
   bpy.context.view_layer.update()
   lean=7 if name=='Walking' else 0
   rotate('B_Pelvis','X',lean)
   for side in 'LR':leg(side,t,lean)
  wings(t,smooth((t-.28)/.85) if name=='Death' else 0,name=='Death')
  fingers(smooth((t-.60)/.15) if name=='Death' else 0)
  C=Vector(curve(keysC,t)) if name=='Attack' else carryC.copy()
  A=Vector(curve(keysA,t)).normalized() if name=='Attack' else carryA.copy()
  if name=='Death':
   # Follow the chest until the hands release the weapon.
   chest=armik.W(rig,'B_Spine2')@restW['B_Spine2'].inverted()
   C=chest@C;A=(chest.to_3x3()@A).normalized()
  else:C.z+=.016*math.sin(math.tau*t)
  frames.append({'snap':snap(),'unfitted':snap(),'C':C,'dir':A,'t':t})
 print('BODY',name,len(frames),flush=True)
 # Fit both arms to the same shaft; choose roll/elbow globally, then refine the palm-centre target.
 choices={}
 for side in 'RL':
  for fr in frames:
   fr['centre']=fr['C']-fr['dir']*(.24 if side=='L' else 0)
   R=armik.hand_rot(GA[side],fr['dir'],180 if side=='R' else 0)
   fr['wrist']=fr['centre']-R@GC[side]
  path=grip_dp.solve(rig,side,frames,GA[side],GC[side],stats.get('Standing',{}).get('arms',{}).get(side,[None])[0] if name in ('Walking','Attack','Hit') else None)
  poses=[];metrics=[]
  for fr,p in zip(frames,path):
   wrist=fr['centre']-armik.hand_rot(GA[side],fr['dir'],p['psi'])@GC[side]
   sw,tw=armik.apply_arm(rig,side,fr['snap'],wrist,GA[side],fr['dir'],p['phi'],p['psi'])
   fr['snap']=snap()
   err=(armik.W(rig,f'B_{side}_Hand')@GC[side]-fr['centre']).length
   metrics.append({'swing':sw,'twist':tw,'grip_error_m':err,'phi':float(p['phi']),'psi':float(p['psi']),'time':fr['t'],'centre':list(fr['centre']),'shoulder':list(armik.W(rig,f'B_{side}_UpperArm').translation)})
  choices[side]=metrics
  print('ARM',name,side,'swing',max(x['swing'] for x in metrics),'error',max(x['grip_error_m'] for x in metrics),flush=True)
 final=[];release=None;launch=None
 for fr in frames:
  put(fr['snap']);t=fr['t']
  if name=='Death' and t>.60:
   w=smooth((t-.60)/.25)
   for side in 'LR':
    for part in ('Clavicle','UpperArm','Forearm','Hand'):
     n=f'B_{side}_{part}';rig.pose.bones[n].matrix_basis=blend(fr['snap'],fr['unfitted'],w)[n]
   fingers(smooth((t-.60)/.15))
   bpy.context.view_layer.update()
  # Keep the blade face readable in carry; turn its cutting plane into the chop.
  A=fr['dir'];normal=Vector((0,-1,0)).lerp(Vector((1,0,0)),max(0,math.sin(math.pi*t/dur)) if name=='Attack' else 0)
  normal=(normal-A*normal.dot(A)).normalized()
  m=Matrix((A.cross(normal),A,normal)).transposed().to_4x4()
  m.translation=fr['C'] if name=='Death' else armik.W(rig,'B_R_Hand')@GC['R'];armik.set_world(rig,'Polearm',m)
  if name=='Death':
   # The rigid polearm becomes a dropped attachment after release; its node is baked in the actor clip.
   if t>=.333333 and release is None:release=armik.W(rig,'Polearm').copy()
   if release is not None:
    elapsed=t-.333333
    if t<=.600001:
     m=armik.W(rig,'Polearm');m.translation+=fr['dir']*(.48*smooth((t-.333333)/.266667));launch=m.copy()
    else:
     if launch is None:launch=release.copy()
     elapsed=t-.60;side=-1 if launch.translation.x<0 else 1
     target=Vector((side*1.0,-.45,.022))
     position=launch.translation.lerp(target,smooth(elapsed/.20))
     position.z=launch.translation.z*(1-smooth((elapsed-.15)/.60))+.022*smooth((elapsed-.15)/.60)
     end=Matrix((Vector((0,-side,0)),Vector((side,0,0)),Vector((0,0,1)))).transposed().to_quaternion()
     m=Matrix.LocRotScale(position,launch.to_quaternion().slerp(end,smooth((elapsed-.15)/.30)),Vector((1,1,1)))
    m_prop=m.copy();armik.set_world(rig,'Polearm',m)
   # Ground the body as it settles; open feather surfaces are evaluated separately.
   ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
   ids=[v.index for v in body.data.vertices if body.data.attributes['piece'].data[v.index].value==0 and sum(g.weight for g in v.groups if 'Spine' in body.vertex_groups[g.group].name)>.5]
   low=min(mesh.vertices[i].co.z for i in ids);ev.to_mesh_clear()
   m=armik.W(rig,'B_Pelvis');m.translation.z-=low*smooth((t-.55)/.65);armik.set_world(rig,'B_Pelvis',m)
   settle=smooth((t-.65)/.65)
   if settle:
    for side in 'LR':
     settle_leg(side,settle)
     shoulder=armik.W(rig,f'B_{side}_UpperArm').translation.copy()
     sign=1 if side=='L' else -1
     wrist=Vector((sign*.30,-.72,.12));pole=Vector((sign*.50,-.65,.15))
     old=armik.W(rig,f'B_{side}_Hand').translation.copy()
     armik.solve(rig,side,old.lerp(wrist,settle),pole=pole)
     n=f'B_{side}_Hand';m=armik.W(rig,n)
     restrel=restW[f'B_{side}_Forearm'].to_3x3().inverted()@restW[n].to_3x3()
     target=armik.W(rig,f'B_{side}_Forearm').to_3x3()@restrel
     armik.set_world(rig,n,armik.rot_world(m,m.to_quaternion().slerp(target.to_quaternion(),settle).to_matrix()))
   # Correct residual fingertip/face floor contacts after the limbs settle.
   ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
   low=min(v.co.z for v in mesh.vertices if body.data.attributes['piece'].data[v.index].value<1000)
   ev.to_mesh_clear()
   if low<0:
    m=armik.W(rig,'B_Pelvis');m.translation.z-=low;armik.set_world(rig,'B_Pelvis',m)
   if release is not None:armik.set_world(rig,'Polearm',m_prop)
  final.append(snap())
 write(name,final);results[name]=final;stats[name]={'duration':(count-1)/30,'arms':choices}
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/authored_partial.blend'))
 (P/'work/motion_fit.json').write_text(json.dumps(stats,indent=2)+'\n')
 print('WROTE',name,flush=True)
write('Dead',[results['Death'][-1]]*31)
for a in list(bpy.data.actions):
 if a.name.startswith('Source'):bpy.data.actions.remove(a)
action(bpy.data.actions['Standing']);sc.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/authored.blend'))
(P/'work/motion_fit.json').write_text(json.dumps(stats,indent=2)+'\n')
assert all(max(m['grip_error_m'] for s in a['arms'].values() for m in s)<.025 for n,a in stats.items() if n!='Death'), 'Unreachable two-hand grip; inspect motion_fit.json'
