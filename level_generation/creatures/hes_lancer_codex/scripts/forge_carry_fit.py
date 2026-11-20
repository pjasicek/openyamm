"""Fit the library's low maul carry to the broad apron without changing the planted body or grip."""
import bpy,sys,os,runpy,math,json
from pathlib import Path
import numpy as np
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];S=P/'scripts';sys.path.insert(0,str(S));import armik
src=P/'work/forge_before_carry.blend';sys.argv=['gates.py','--',str(src),'forge_carry_masks'];g=runpy.run_path(str(S/'gates.py'),run_name='__main__');r=g['rig'];sc=bpy.context.scene;report={}
assert r.data.bones['Thunder_Maul'].parent.name=='B_R_Hand'
for role in ('Standing','Walking','Running','Attack','Hit','Fidget','Cast'):
 a=bpy.data.actions['Forge_'+role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];frames=[];sides='R' if role=='Cast' else 'LR';bone_names=[f'B_{s}_{n}' for s in sides for n in ('UpperArm','Forearm','Hand','UpperArmTwist','ForearmTwist')]+['Thunder_Maul']
 for f in np.arange(a.frame_range[0],a.frame_range[1]+.001,.5):
  sc.frame_set(int(f),subframe=float(f%1));frames.append((float(f),{b.name:b.matrix_basis.copy() for b in r.pose.bones}))
 accepted=None
 for amount in (.08,.06,.04,.02):
  keys=[];maximum={'reach':0,'wrist':0,'arm':0,'hand':0};bad=None
  for f,snapshot in frames:
   sc.frame_set(int(f),subframe=f%1)
   for n,m in snapshot.items():r.pose.bones[n].matrix_basis=m
   bpy.context.view_layer.update();chest=armik.W(r,'B_Spine2');turn=chest@r.data.bones['B_Spine2'].matrix_local.inverted();hands={s:armik.W(r,f'B_{s}_Hand').copy() for s in sides};fade=float(np.clip((chest.translation.z+.10-max(h.translation.z for h in hands.values()))/.2,0,1));delta=turn.to_3x3()@Vector((0,-amount,amount*.5))*fade;weapon=armik.W(r,'Thunder_Maul').copy();twists={}
   for side,h in hands.items():
    fore,hand,upper=[r.data.bones[f'B_{side}_{n}'] for n in ('Forearm','Hand','UpperArm')]
    def twist():
     ax=(upper.matrix_local.inverted()@fore.head_local).normalized();_,ut=armik.split_swing_twist(r.pose.bones[upper.name].matrix_basis.to_quaternion(),ax);bx=(fore.matrix_local.inverted()@hand.head_local).normalized();rel=(r.pose.bones[fore.name].matrix.inverted()@r.pose.bones[hand.name].matrix).to_quaternion();rr=(fore.matrix_local.inverted()@hand.matrix_local).to_quaternion();_,ft=armik.split_swing_twist(rel@rr.inverted(),bx);return ax,bx,ut,ft
    ax,bx,ou,of=twist();uq=r.pose.bones[f'B_{side}_UpperArmTwist'].rotation_quaternion.copy();fq=r.pose.bones[f'B_{side}_ForearmTwist'].rotation_quaternion.copy();pole=armik.W(r,f'B_{side}_Forearm').translation.copy();reach=armik.solve(r,side,h.translation+delta,pole,h.to_3x3());maximum['reach']=max(maximum['reach'],reach)
    twists[side]=(ax,bx,ou,of,uq,fq)
   weapon.translation+=delta;armik.set_world(r,'Thunder_Maul',weapon)
   if role=='Cast':
    hand=r.data.bones['B_R_Hand'];fore=r.data.bones['B_R_Forearm'];axis=(hand.matrix_local.to_3x3().inverted()@(hand.head_local-fore.head_local)).normalized();b=r.pose.bones[hand.name];swing,tw=armik.split_swing_twist(b.matrix_basis.to_quaternion(),axis)
    if swing.w<0:swing=-swing
    b.rotation_quaternion=Quaternion(swing.axis,min(swing.angle,math.radians(59)))@Quaternion(axis,tw);bpy.context.view_layer.update()
   for side in sides:
    fore,hand,upper=[r.data.bones[f'B_{side}_{n}'] for n in ('Forearm','Hand','UpperArm')];ax,bx,ou,of,uq,fq=twists[side];_,nu=armik.split_swing_twist(r.pose.bones[upper.name].matrix_basis.to_quaternion(),ax);rel=(r.pose.bones[fore.name].matrix.inverted()@r.pose.bones[hand.name].matrix).to_quaternion();rr=(fore.matrix_local.inverted()@hand.matrix_local).to_quaternion();_,nf=armik.split_swing_twist(rel@rr.inverted(),bx);r.pose.bones[f'B_{side}_UpperArmTwist'].rotation_quaternion=Quaternion(ax,-.5*math.remainder(nu-ou,2*math.pi))@uq;r.pose.bones[f'B_{side}_ForearmTwist'].rotation_quaternion=Quaternion(bx,.5*math.remainder(nf-of,2*math.pi))@fq;bpy.context.view_layer.update();pts=g['coords']();e=g['edges'];stretch=np.linalg.norm(pts[e[:,0]]-pts[e[:,1]],axis=1)/np.maximum(g['L0'],1e-6);maximum['wrist']=max(maximum['wrist'],armik.wrist_cost(r,side,armik.W(r,hand.name).to_3x3())[0]);maximum['arm']=max(maximum['arm'],float(np.percentile(stretch[g['ef'][side]],99)));maximum['hand']=max(maximum['hand'],float(stretch[g['hf'][side]].max()))
   if maximum['reach']>.998 or maximum['wrist']>60 or maximum['arm']>2.05 or maximum['hand']>4.5:bad=(f,maximum.copy());break
   keys.append((f,{n:r.pose.bones[n].matrix_basis.copy() for n in bone_names}))
  print('CARRY_FIT',role,amount,'FAIL' if bad else 'PASS',bad or maximum,flush=True)
  if not bad:accepted=(amount,keys,maximum);break
 assert accepted is not None,(role,'no carry fit')
 amount,keys,maximum=accepted;previous={}
 for f,pose in keys:
  for n,m in pose.items():
   b=r.pose.bones[n];q=m.to_quaternion()
   if n in previous and q.dot(previous[n])<0:q=-q
   previous[n]=q.copy();b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
 report[role]={'forward_m':amount,'up_m':amount*.5,'maxima':maximum};bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_carry_fit.blend'));(P/'review/forge_carry_fit.json').write_text(json.dumps(report,indent=2)+'\n')
sys.stdout.flush();os._exit(0)
