"""Fit measured hand frames/finger chains and rebuild their skin weights on the new hands."""
import bpy,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/bound_body.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
fit=json.loads((P/'work/round2/fingers_fit.json').read_text());oldj=json.loads((P/'work/round2/finger_joints.json').read_text());oldrig=json.loads((P/'work/round2/previous_rig.json').read_text())
labels=['thumb','index','middle','ring','pinky'];correct={};FJ={};transforms={}
# The first separated small component is the pinky in this palm-forward mesh. Order by anatomical thumb end.
for sd in 'LR':
 correct[sd]={labels[k]:fit[sd][labels[4-k]] for k in range(5)}
 correct[sd]['verts']={labels[k]:fit[sd]['verts'][labels[4-k]]for k in range(5)}
 joints={}
 for k in range(5):
  oldnames=[f'B_{sd}_Finger{4-k}']
  while True:
   children=[b.name for b in rig.data.bones if b.parent and b.parent.name==oldnames[-1]]
   if not children:break
   oldnames.append(children[0])
  names=[f'B_{sd}_Finger{k}']
  while True:
   children=[b.name for b in rig.data.bones if b.parent and b.parent.name==names[-1]]
   if not children:break
   names.append(children[0])
  for a,b in zip(names,oldnames):joints[a]=np.array(oldj[sd][b])
  joints[names[-1]+'_tip']=np.array(oldj[sd][oldnames[-1]+'_tip'])
 wr=np.array(rig.data.bones[f'B_{sd}_Hand'].head_local)
 def basis(f,t):
  f=f/np.linalg.norm(f);t=t-f*(t@f);t/=np.linalg.norm(t);return np.column_stack([f,t,np.cross(f,t)])
 fm=joints[f'B_{sd}_Finger2']-wr;tm=joints[f'B_{sd}_Finger1']-joints[f'B_{sd}_Finger4']
 fo=np.array(oldrig[f'B_{sd}_Finger2']['head'])-wr;to=np.array(oldrig[f'B_{sd}_Finger1']['head'])-np.array(oldrig[f'B_{sd}_Finger4']['head'])
 Q=basis(fo,to)@basis(fm,tm).T;k=float(np.linalg.norm(fo)/np.linalg.norm(fm));A=Q*k;transforms[sd]=(wr,A)
 FJ[sd]={n:(wr+A@(v-wr)).tolist()for n,v in joints.items()}
 for name in labels:correct[sd][name]=[(wr+A@(np.array(v)-wr)).tolist()for v in correct[sd][name]]
correct_path=P/'work/round2/fingers_fit_aligned.json';correct_path.write_text(json.dumps(correct,indent=2))
(P/'work/round2/finger_joints_aligned.json').write_text(json.dumps(FJ,indent=2))
pv=[a.value for a in body.data.attributes['piece'].data]
for v in body.data.vertices:
 sd='L'if v.co.x>0 else'R';wr,A=transforms[sd];amount=1. if pv[v.index]in[3,4] else 0.
 if pv[v.index]==1:
  handgi=body.vertex_groups[f'B_{sd}_Hand'].index;amount=sum(g.weight for g in v.groups if g.group==handgi)
 if amount:
  p=np.array(v.co);v.co=p*(1-amount)+(wr+A@(p-wr))*amount
# Keep body/arm bones and Club socket unchanged; refit only the measured digit chains.
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for sd in 'LR':
 for k in range(5):
  names=[f'B_{sd}_Finger{k}']
  while True:
   children=[b.name for b in rig.data.edit_bones if b.parent and b.parent.name==names[-1]]
   if not children:break
   names.append(children[0])
  for j,n in enumerate(names):
   eb=rig.data.edit_bones[n];start=Vector(FJ[sd][n]);end=Vector(FJ[sd][names[j+1]]if j+1<len(names)else FJ[sd][n+'_tip'])
   old=Matrix(oldrig[n]['matrix']).to_3x3();oldseg=Vector(oldrig[n]['tail'])-Vector(oldrig[n]['head']);Q=oldseg.rotation_difference(end-start);R=Q.to_matrix()@old
   eb.head=start;eb.tail=end;eb.align_roll(R.col[2])
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2/hands_fitted.blend'))
s=(P/'scripts/finger_weights.py').read_text().replace("'work', 'finger_joints.json'","'work', 'round2', 'finger_joints_aligned.json'").replace("'work', 'fingers_fit.json'","'work', 'round2', 'fingers_fit_aligned.json'")
sys.argv=['finger_weights.py','--',str(P/'work/round2/hands_fitted.blend'),str(P/'work/round2/rigged.blend')]
exec(compile(s,str(P/'scripts/finger_weights.py'),'exec'),{'__name__':'__main__','__file__':str(P/'scripts/finger_weights.py')})
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/rigged.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
common.workbench_clay(bpy.context.scene)
for role,t in [('Standing',0),('Attack',.8125),('Death',1.4),('Running',.2)]:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=t*30;bpy.context.scene.frame_set(int(f),subframe=f%1)
 common.render_views(str(P/'review/round2'/('rigged_'+role)),.85,2.2,views=('front','left','three_quarter'),resolution=(600,900))
 for sd in 'LR':
  c=rig.pose.bones[f'B_{sd}_Hand'].head
  common.render_views(str(P/'review/round2'/f'hand_{role}_{sd}'),c.z,.38,views=('front','left'),target=(c.x,c.y),resolution=(500,500))
