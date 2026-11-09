"""Keep the source walk and planted sole path; remove the folded swing-foot orientation."""
import bpy,numpy as np,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));bpy.ops.wm.open_mainfile(filepath=str(p/'work/round2_motion.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
pv=np.array([a.value for a in body.data.attributes['piece'].data]);points={s:[rig.data.bones['B_'+s+'_Foot'].matrix_local.inverted()@v.co for v in body.data.vertices if pv[v.index]==part] for s,part in [('R',101),('L',102)]}
names=[b.name for b in rig.pose.bones];old=bpy.data.actions['Walking'];frames=[];feet=[];floors=[]
rig.animation_data.action=old;rig.animation_data.action_slot=old.slots[0]
for f in range(97):
 scene.frame_set(f);frames.append({n:rig.pose.bones[n].matrix_basis.copy() for n in names});feet.append({s:rig.pose.bones['B_'+s+'_Foot'].matrix.copy() for s in 'LR'});floors.append({s:min((feet[-1][s]@v).z for v in points[s]) for s in 'LR'})
stand=bpy.data.actions['Standing'];rig.animation_data.action=stand;rig.animation_data.action_slot=stand.slots[0];scene.frame_set(0);rot={}
for s in 'LR':
 M=rig.pose.bones['B_'+s+'_Foot'].matrix;D=M@rig.data.bones['B_'+s+'_Foot'].matrix_local.inverted();axis=D.to_3x3()@Vector((0,-1,0));yaw=math.atan2(axis.x,-axis.y);rot[s]=Matrix.Rotation(-yaw,3,'Z')@M.to_3x3()
old.name='Walking_before_sole_refine';old.use_fake_user=False;out=bpy.data.actions.new('Walking');out.use_fake_user=True;out.use_frame_range=True;out.frame_start=0;out.frame_end=96
report=[]
for f,d in enumerate(frames):
 rig.animation_data.action=None
 for n,m in d.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
 for s in 'LR':
  up,lo,foot=[rig.pose.bones['B_'+s+'_'+n] for n in ['Thigh','Calf','Foot']];M=rot[s].to_4x4();M.translation=feet[f][s].translation;floor=.004+.58*max(0,floors[f][s]-.004);M.translation.z+=floor-min((M@v).z for v in points[s])
  A=up.head.copy();W=M.translation.copy();pole=lo.head-A;L1=(rig.data.bones[lo.name].head_local-rig.data.bones[up.name].head_local).length;L2=(rig.data.bones[foot.name].head_local-rig.data.bones[lo.name].head_local).length;d=W-A;dist=min(d.length,(L1+L2)*.999);u=d.normalized();pole=(pole-u*pole.dot(u)).normalized();q=(L1*L1+dist*dist-L2*L2)/(2*dist);E=A+u*q+pole*math.sqrt(max(0,L1*L1-q*q));W=A+u*dist
  for pb,target,child in [(up,E,lo),(lo,W,foot)]:
   R=(child.head-pb.head).normalized().rotation_difference((target-pb.head).normalized()).to_matrix()@pb.matrix.to_3x3();N=R.to_4x4();N.translation=pb.head;pb.matrix=N;bpy.context.view_layer.update()
  M.translation=W;foot.matrix=M;bpy.context.view_layer.update();report.append({'time':f/120,'side':s,'sole_mm':min((foot.matrix@v).z for v in points[s])*1000,'knee_deg':math.degrees((lo.head-up.head).angle(foot.head-lo.head))})
 rig.animation_data.action=out
 for pb in rig.pose.bones:
  pb.rotation_mode='QUATERNION';pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f);pb.keyframe_insert('scale',frame=f)
bpy.data.actions.remove(old)
import normalize_keys_r2
(p/'work/round2_gait_refine.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/round2_gait.blend'));print('GAIT_REFINED',min(x['sole_mm'] for x in report),max(x['sole_mm'] for x in report),max(x['knee_deg'] for x in report),flush=True)
