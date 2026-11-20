import bpy,sys,runpy,math
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v4.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
with bpy.data.libraries.load(str(P/'work/extra_sources.blend'),link=False) as (src,dst):dst.actions=['Running','Death']
for a in dst.actions:a.use_fake_user=True
r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0);base={p.name:p.matrix_basis.copy() for p in r.pose.bones};r.animation_data.action=None
rows=[]
for f in range(37):
 for n,m in base.items():r.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update();t=f/36
 for sd,c in [('R',.30),('L',.65)]:
  u=max(0,1-abs(t-c)/.18);bump=math.sin(u*math.pi/2)**2
  for name,deg in [(f'B_{sd}_Thigh',-15),(f'B_{sd}_Calf',30),(f'B_{sd}_Foot',-15)]:
   M=armik.W(r,name);tr=M.translation.copy();M=Matrix.Rotation(math.radians(deg*bump),4,'X')@M;M.translation=tr;armik.set_world(r,name,M)
 for name,deg in [('B_Neck',-5),('B_Head',-4)]:
  M=armik.W(r,name);tr=M.translation.copy();M=Matrix.Rotation(math.radians(deg*math.sin(2*math.pi*t)**2),4,'X')@M;M.translation=tr;armik.set_world(r,name,M)
 rows.append({p.name:p.matrix_basis.copy() for p in r.pose.bones})
a=bpy.data.actions.new('Fidget');a.use_fake_user=True;r.animation_data.action=a
for f,row in enumerate(rows):
 for n,m in row.items():
  pb=r.pose.bones[n];pb.matrix_basis=m;pb.rotation_mode='QUATERNION';pb.keyframe_insert('rotation_quaternion',frame=f)
  if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
a.use_frame_range=True;a.frame_start=0;a.frame_end=36
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_motion.blend'))
sys.argv=['run_fit.py','--',str(P/'work/rig_motion.blend'),str(P/'work/rig_motion.blend')];runpy.run_path(str(P/'scripts/run_fit.py'),run_name='__main__')
sys.argv=['foot_level.py','--',str(P/'work/rig_motion.blend'),str(P/'work/rig_motion.blend'),'Walking:const','Death:until=18'];runpy.run_path(str(P/'scripts/foot_level.py'),run_name='__main__')
