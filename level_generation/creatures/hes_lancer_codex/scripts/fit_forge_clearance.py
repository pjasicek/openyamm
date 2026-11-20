"""Measure elbow-plane and common grip translation choices on the preserved hammer stroke."""
import bpy,sys,runpy,math,json,os
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];S=P/'scripts';sys.path.insert(0,str(S));import armik
src=P/'work/forge_review_base.blend'
sys.argv=['gates.py','--',str(src),'forge_probe_masks'];skin=runpy.run_path(str(S/'gates.py'),run_name='__main__')
sys.argv=['armour_gate.py','--',str(src),'forge_probe_masks',str(S/'armour_forge.json')];g=runpy.run_path(str(S/'armour_gate.py'),run_name='__main__');r=g['rig'];body=g['body'];sc=bpy.context.scene

def helpers(side):
 fore,hand,upper=[r.data.bones[f'B_{side}_{n}'] for n in ('Forearm','Hand','UpperArm')]
 ax=(upper.matrix_local.inverted()@fore.head_local).normalized();_,tw=armik.split_swing_twist(r.pose.bones[upper.name].matrix_basis.to_quaternion(),ax);r.pose.bones[f'B_{side}_UpperArmTwist'].rotation_quaternion=Quaternion(ax,-.5*tw)
 ax=(fore.matrix_local.inverted()@hand.head_local).normalized();rel=(r.pose.bones[fore.name].matrix.inverted()@r.pose.bones[hand.name].matrix).to_quaternion();rr=(fore.matrix_local.inverted()@hand.matrix_local).to_quaternion();_,tw=armik.split_swing_twist(rel@rr.inverted(),ax);r.pose.bones[f'B_{side}_ForearmTwist'].rotation_quaternion=Quaternion(ax,.5*tw)
 cl=r.data.bones[f'B_{side}_Clavicle'];pa=r.data.bones[f'B_{side}_Pauldron'];rest=cl.matrix_local.to_3x3().inverted()@upper.matrix_local.to_3x3().col[1];posed=r.pose.bones[cl.name].matrix.to_3x3().inverted()@r.pose.bones[upper.name].matrix.to_3x3().col[1];q=rest.rotation_difference(posed);q=Quaternion(q.axis,min(q.angle*.8,math.radians(60))) if q.angle>1e-6 else Quaternion();rb=cl.matrix_local.to_3x3().inverted()@pa.matrix_local.to_3x3();r.pose.bones[pa.name].rotation_quaternion=(rb.inverted()@q.to_matrix()@rb).to_quaternion();bpy.context.view_layer.update()

# A small fitted carry correction retains the library strike's timing and direction.
a=bpy.data.actions['Forge_Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
C={s:Vector(json.loads((P/f'work/grip_pose_{"R" if s=="R" else "L_tun"}.json').read_text())['handle_centre_hand_local']) for s in 'LR'}
frames=[];knots=[(0,0,0),(3,0,0),(8,0,-.1),(12,-15,-.2),(19,-15,-.22),(22,-20,-.22),(25,-30,-.10),(28,-30,0),(34,-30,0),(43,-15,0),(53,0,0),(60,0,0)]
def curve(f,col):
 for l,h in zip(knots,knots[1:]):
  if l[0]<=f<=h[0]:
   t=(f-l[0])/(h[0]-l[0]);t=t*t*(3-2*t);return l[col]*(1-t)+h[col]*t
 return 0
for frame in np.arange(0,float(a.frame_range[1])+.001,.5):
 sc.frame_set(int(frame),subframe=float(frame%1));snap={b.name:b.matrix_basis.copy() for b in r.pose.bones};hands={s:armik.W(r,f'B_{s}_Hand').copy() for s in 'LR'};centres={s:hands[s]@C[s] for s in 'LR'};centre=(centres['L']+centres['R'])/2;gun=armik.W(r,'Thunder_Maul').copy();axis=gun.to_3x3().col[1].normalized()
 torso=r.pose.bones['B_Spine2'].matrix.to_3x3()@r.data.bones['B_Spine2'].matrix_local.to_3x3().inverted();front=torso@Vector((0,-1,0));front.z=0;front.normalize();pitchaxis=Vector((0,0,1)).cross(front).normalized();q=Quaternion(pitchaxis,math.radians(curve(frame,1)));offset=front*curve(frame,2)
 targetgun=(q.to_matrix()@gun.to_3x3()).to_4x4();targetgun.translation=centre+q@(gun.translation-centre)+offset
 frames.append(dict(frame=float(frame),snap=snap,hands=hands,centres=centres,centre=centre,q=q,axis=q@axis,offset=offset,gun=targetgun))
r.animation_data.action=None
states=[(phi,roll) for phi in range(-105,106,15) for roll in range(-45,46,15)];zero=states.index((0,0));all_chosen={};report={}
for side in 'LR':
 table=[];nms=[f'B_{side}_{n}' for n in ('UpperArm','Forearm','Hand','UpperArmTwist','ForearmTwist','Pauldron')]
 armids=np.array([i for i in g['ARMV'] if g['DOM'][i].startswith('B_'+side+'_')],int)
 skip=g['HIDFK']|{j for j,f in enumerate(g['BFK']) if not (g['DOM'][f[0]].startswith('B_'+side+'_') or g['DOM'][f[0]] in ('B_Head','B_Neck','Bone_025'))}
 for f,fr in enumerate(frames):
  for n,m in fr['snap'].items():r.pose.bones[n].matrix_basis=m
  bpy.context.view_layer.update();h=fr['hands'][side];u=armik.W(r,f'B_{side}_UpperArm').translation.copy();e=armik.W(r,f'B_{side}_Forearm').translation.copy();original={n:r.pose.bones[n].matrix_basis.copy() for n in nms};rows=[]
  stationary={n:g['ev'](bpy.data.objects['Arm_'+n])[0] for n in ('chest','breast_L','breast_R','back','crest')}
  strees={n:BVHTree.FromPolygons(v.tolist(),g['pfaces']['Arm_'+n]) for n,v in stationary.items()}
  bounds={n:(v.min(0),v.max(0)) for n,v in stationary.items()}
  for phi,roll in states:
   if (fr['frame']<=2 or fr['frame']>=53) and (phi or roll):rows.append({'cost':1e10});continue
   for n,m in original.items():r.pose.bones[n].matrix_basis=m
   bpy.context.view_layer.update();hr=Quaternion(fr['axis'],math.radians(roll)).to_matrix()@fr['q'].to_matrix()@h.to_3x3().normalized();target=fr['centre']+fr['q']@(fr['centres'][side]-fr['centre'])+fr['offset']-hr@C[side];pole=u+Quaternion((h.translation-u).normalized(),math.radians(phi))@(e-u)
   reach=armik.solve(r,side,target,pole,hr);helpers(side);sw,tw=armik.wrist_cost(r,side,hr)
   if reach>.995 or sw>60:rows.append({'cost':1e10});continue
   points,_=g['ev'](body);edges=skin['edges'];st=np.linalg.norm(points[edges[:,0]]-points[edges[:,1]],axis=1)/np.maximum(skin['L0'],1e-6);p99=float(np.percentile(st[skin['ef'][side]],99));tree=BVHTree.FromPolygons(points.tolist(),g['BFK']);dep=0;who=''
   for name in ('chest','crest','breast_'+side):
    ob=bpy.data.objects['Arm_'+name];pp=stationary[name][g['BASE_PLATE'][ob.name]];d,_=g['inside_closed'](tree,pp,1.2,skip)
    lo,hi=bounds[name];near=armids[np.all((points[armids]>lo-.01)&(points[armids]<hi+.01),axis=1)]
    if len(near):d=max(d,g['inside_closed'](strees[name],points[near])[0])
    if d>dep:dep=d;who=name
   for name in ():
    ob=bpy.data.objects['Arm_'+name];pp=g['ev'](ob)[0];d,_=g['inside_closed'](tree,pp[g['BASE_PLATE'][ob.name]],1.2,g['HIDFK']);lo,hi=pp.min(0),pp.max(0)
    for other,pt in strees.items():
     olo,ohi=bounds[other]
     if np.any(lo>ohi) or np.any(hi<olo):continue
     d=max(d,g['inside_closed'](pt,pp[g['PV'][ob.name]])[0])
    if d>dep:dep=d;who=name
   ht=BVHTree.FromPolygons(points.tolist(),skin['bodyf'][side]);hand=skin['inside'](ht,points[skin['handv'][side]])[0]
   cost=1e6*max(0,dep-.002)+1e6*max(0,p99-1.97)+1e7*hand+.001*phi*phi+.001*roll*roll
   rows.append(dict(cost=cost,phi=phi,roll=roll,depth=dep,part=who,p99=p99,wrist=sw,hand=hand,pose={n:r.pose.bones[n].matrix_basis.copy() for n in nms},target=target,world_q=[list(armik.W(r,f'B_{side}_{part}').to_quaternion()) for part in ('UpperArm','Forearm','Hand')]))
  assert min(x['cost'] for x in rows)<1e9,('No wrist/reach solution',side,f)
  table.append(rows)
  if f%5==0:
   best=min(rows,key=lambda x:x['cost']);print('FORGE_FIT_FRAME',side,f,{k:round(v,4) if isinstance(v,float) else v for k,v in best.items() if k not in ('pose','target','world_q')},flush=True)
 cost=np.array([x['cost'] for x in table[0]]);backs=[]
 for prev,rows in zip(table,table[1:]):
  qa=np.array([x.get('world_q',[[1,0,0,0]]*3) for x in prev]);qb=np.array([x.get('world_q',[[1,0,0,0]]*3) for x in rows]);dot=np.abs(np.einsum('ikc,jkc->ijk',qa,qb));degrees=np.degrees(2*np.arccos(np.clip(dot,0,1)));transition=4*np.sum(degrees**2*np.array([.5,.3,.2]),axis=2)
  choices=cost[:,None]+transition;back=choices.argmin(0);cost=choices[back,np.arange(len(states))]+np.array([x['cost'] for x in rows]);backs.append(back)
 index=zero;path=[index]
 for back in reversed(backs):index=int(back[index]);path.append(index)
 path.reverse();chosen=[rows[i] for rows,i in zip(table,path)];assert all('pose' in x for x in chosen)
 all_chosen[side]=chosen;report[side]=[{k:v for k,v in x.items() if k not in ('pose','target','world_q')} for x in chosen];print('FORGE_PATH',side,'max depth',max(x['depth'] for x in chosen),'max p99',max(x['p99'] for x in chosen),flush=True)
r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];previous={}
for f,fr in enumerate(frames):
 fn=fr['frame'];sc.frame_set(int(fn),subframe=fn%1)
 for side in 'LR':
  for n,m in all_chosen[side][f]['pose'].items():r.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
 for side in 'LR':assert (armik.W(r,f'B_{side}_Hand').translation-all_chosen[side][f]['target']).length<1e-5
 armik.set_world(r,'Thunder_Maul',fr['gun'])
 for n in [f'B_{s}_{n}' for s in 'LR' for n in ('UpperArm','Forearm','Hand','UpperArmTwist','ForearmTwist','Pauldron')]+['Thunder_Maul']:
  b=r.pose.bones[n];m=b.matrix_basis.copy();q=m.to_quaternion()
  if n in previous and q.dot(previous[n])<0:q=-q
  previous[n]=q.copy();b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('rotation_quaternion',frame=fn);b.keyframe_insert('location',frame=fn)
r.animation_data.action=None;out=P/'work/forge_fitted.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out));(P/'review/forge_clearance_fit.json').write_text(json.dumps(report,indent=2)+'\n')
for name,args in [('gates.py',[out,'forge_fitted','Forge_Attack']),('armour_gate.py',[out,'forge_fitted',S/'armour_forge.json','Forge_Attack']),('equipment_gate.py',[out,'forge','Forge_Attack']),('render_review.py',['forge_fitted.blend','Forge_Attack','12','front'])]:
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(S/name),run_name='__main__')
sys.stdout.flush();os._exit(0)
