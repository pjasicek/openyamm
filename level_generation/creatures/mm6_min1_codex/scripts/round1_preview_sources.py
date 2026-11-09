import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_sources.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene
r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0)
A=r.pose.bones['B_R_Hand'].matrix.inverted()@r.pose.bones['Axe'].matrix
G={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'RL'}
common.workbench_clay(sc);sc.view_settings.view_transform='Standard'
D=P/'review/round1/sources';D.mkdir(exist_ok=True)
for nm in ['DownSlashplant','PowerSlashplant','AxeDownplant']:
 a=bpy.data.actions[nm];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for i in range(7):
  f=a.frame_range[1]*i/6;sc.frame_set(int(f),subframe=f%1);snap={n:pb.matrix_basis.copy() for n,pb in r.pose.bones.items()};r.animation_data.action=None
  for n,m in snap.items():r.pose.bones[n].matrix_basis=m
  for s in 'RL':
   for n,q in G[s]['finger_local'].items():r.pose.bones[n].rotation_quaternion=q
  bpy.context.view_layer.update();r.pose.bones['Axe'].matrix=r.pose.bones['B_R_Hand'].matrix@A;bpy.context.view_layer.update()
  common.render_views(str(D/f'{nm}_{i}'),1,3.8,views=['front','left','three_quarter'],resolution=(300,360))
  r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
