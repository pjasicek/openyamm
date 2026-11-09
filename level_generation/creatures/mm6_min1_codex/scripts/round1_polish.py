import bpy,sys,json,math,runpy
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import round1_fit as F
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_high.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;F.r=r;F.body=b;F.sc=sc
F.apply(F.sample(bpy.data.actions['Standing'],0));pts=F.coords();A=F.M('Axe')@F.restb['Axe'].inverted();axis=np.array(A.to_3x3()@Vector((0,0,1)));origin=np.array(A.translation);mat={g.index:np.array(r.pose.bones[g.name].matrix@r.data.bones[g.name].matrix_local.inverted())[:3,:3] for g in b.vertex_groups if g.name in r.pose.bones};hand={g.index for g in b.vertex_groups if g.name.startswith('B_R_') and ('Hand' in g.name or 'Finger' in g.name)};count=0
for v in b.data.vertices:
 if sum(g.weight for g in v.groups if g.group in hand)>.5:
  d=pts[v.index]-origin;d-=axis*(d@axis);d=d/np.linalg.norm(d)*.00018;skin=sum(g.weight*mat[g.group] for g in v.groups if g.group in mat);assert abs(np.linalg.det(skin))>.01;v.co+=Vector(np.linalg.solve(skin,d));count+=1
print('PALM clearance 0.18 mm',count,flush=True)
# Keep the existing visible swing height while reducing the toe-down pitch to a hoof's modest roll.
for role in ['Walking','Running']:
 a=bpy.data.actions[role];rows=[];stats=[]
 for f in range(int(a.frame_range[1])+1):
  F.apply(F.sample(a,f));before={s:float(F.coords()[F.sole[s],2].min()) for s in 'RL'}
  for s in 'RL':
   foot=F.M(f'B_{s}_Foot');p=F.coords()[F.sole[s]];n=np.linalg.svd(p-p.mean(0))[2][-1];n=n if n[2]>0 else -n;tilt=math.acos(min(1,float(n[2])));delta=Vector(n).rotation_difference(Vector((0,0,1)));fraction=max(0,(tilt-math.radians(12))/max(tilt,1e-6));rot=delta.slerp(type(delta)(),1-fraction).to_matrix()@foot.to_3x3();F.leg(s,foot.translation,rot);foot=F.M(f'B_{s}_Foot');foot.translation.z+=before[s]-float(F.coords()[F.sole[s],2].min());F.leg(s,foot.translation,rot)
  rows.append(F.snapshot())
 for f,row in enumerate(rows):
  F.apply(row);r.animation_data.action=a
  for s in 'RL':
   for n in ['Thigh','Calf','Foot']:
    pb=r.pose.bones[f'B_{s}_{n}'];pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
  r.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_polished.blend'))
runpy.run_path(str(P/'scripts/round1_cloth.py'),run_name='__main__',init_globals={'INPUT':'work/round1_polished.blend'})
sys.argv=['g','--','work/round1_clothed.blend'];runpy.run_path(str(P/'scripts/rig_gates_48.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round1_precision.py'),run_name='__main__')
