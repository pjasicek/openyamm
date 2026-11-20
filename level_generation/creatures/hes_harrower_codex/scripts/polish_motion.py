"""Smooth fitted arm rolls; choose a continuous counter-twist on the existing helper bones."""
from pathlib import Path
import sys,math,json
import bpy,numpy as np
from mathutils import Quaternion
def gaussian_filter1d(a,sigma,axis=0,mode='nearest'):
 radius=int(math.ceil(3*sigma));k=np.exp(-.5*(np.arange(-radius,radius+1)/sigma)**2);k/=k.sum()
 return np.stack([np.convolve(np.pad(a[:,i],radius,mode='edge'),k,mode='valid') for i in range(a.shape[1])],axis=1)
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/guard_high.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
base=np.array([v.co[:] for v in body.data.vertices]);edges=np.array([e.vertices[:] for e in body.data.edges]);length=np.linalg.norm(base[edges[:,0]]-base[edges[:,1]],axis=1)
gi={g.index:g.name for g in body.vertex_groups}
mask={s:np.array([sum(g.weight for g in v.groups if gi[g.group].startswith('B_'+s+'_') and any(x in gi[g.group] for x in ('UpperArm','Forearm')))>0.3 for v in body.data.vertices]) for s in 'LR'}
ef={s:mask[s][edges[:,0]]&mask[s][edges[:,1]] for s in 'LR'}
def posed():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();C=np.empty(len(me.vertices)*3);me.vertices.foreach_get('co',C);ev.to_mesh_clear();return C.reshape(-1,3)
report={}
for act in [a for a in bpy.data.actions if a.name.startswith('Harrower_') and not a.name.endswith('_Dead')]:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];frames=list(range(int(act.frame_range[1])+1))
 armnames=[b.name for b in rig.pose.bones if b.name.startswith('B_') and any(x in b.name for x in ('UpperArm','Forearm','Hand')) and 'Twist' not in b.name]
 Q={n:[] for n in armnames}
 for f in frames:
  sc.frame_set(f)
  for n in armnames:
   q=rig.pose.bones[n].rotation_quaternion.copy()
   if Q[n] and q.dot(Quaternion(Q[n][-1]))<0:q=-q
   Q[n].append(list(q))
 sigma=1.6 if 'Attack' in act.name else .7
 for n in armnames:
  A=np.array(Q[n]);S=gaussian_filter1d(A,sigma,axis=0,mode='nearest');S/=np.linalg.norm(S,axis=1)[:,None]
  S[0]=A[0];S[-1]=A[-1]
  pb=rig.pose.bones[n]
  for f,q in enumerate(S):pb.rotation_quaternion=Quaternion(q);pb.keyframe_insert('rotation_quaternion',frame=f)
 # Use one constant gain per side and clip, selected from the actual shared skin's stretch.
 gains=np.array([0.,.25,.5,.75,1.]);scores={s:np.zeros(len(gains)) for s in 'LR'}
 for f in frames[::2]:
  sc.frame_set(f)
  for sd in 'LR':
   ub=rig.data.bones[f'B_{sd}_UpperArm'];fb=rig.data.bones[f'B_{sd}_Forearm'];axis=(ub.matrix_local.inverted()@fb.head_local).normalized()
   _,tw=armik.split_swing_twist(rig.pose.bones[ub.name].matrix_basis.to_quaternion(),axis)
   helper=rig.pose.bones[f'B_{sd}_UpperArmTwist']
   for i,gain in enumerate(gains):
    helper.rotation_quaternion=Quaternion(axis,-gain*tw);bpy.context.view_layer.update();C=posed();ratio=np.linalg.norm(C[edges[:,0]]-C[edges[:,1]],axis=1)/np.maximum(length,1e-6)
    scores[sd][i]=max(scores[sd][i],np.percentile(ratio[ef[sd]],99))
 selected={s:float(gains[np.argmin(scores[s])]) for s in 'LR'}
 for f in frames:
  sc.frame_set(f)
  for sd in 'LR':
   ub=rig.data.bones[f'B_{sd}_UpperArm'];fb=rig.data.bones[f'B_{sd}_Forearm'];hb=rig.data.bones[f'B_{sd}_Hand'];axis=(ub.matrix_local.inverted()@fb.head_local).normalized()
   _,tw=armik.split_swing_twist(rig.pose.bones[ub.name].matrix_basis.to_quaternion(),axis)
   pb=rig.pose.bones[f'B_{sd}_UpperArmTwist'];pb.rotation_quaternion=Quaternion(axis,-selected[sd]*tw);pb.keyframe_insert('rotation_quaternion',frame=f)
   axis=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion();rest=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion()
   _,tw=armik.split_swing_twist(rel@rest.inverted(),axis);pb=rig.pose.bones[f'B_{sd}_ForearmTwist'];pb.rotation_quaternion=Quaternion(axis,.6*tw);pb.keyframe_insert('rotation_quaternion',frame=f)
 report[act.name]={'upper_twist_gain':selected,'p99_by_gain':{s:scores[s].tolist() for s in 'LR'}};print('POLISH',act.name,report[act.name],flush=True)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
(P/'review/polish.json').write_text(json.dumps(report,indent=2)+'\n');bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/guard_polished.blend'))
