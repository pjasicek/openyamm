"""G1: measure local overhead strike candidates with the current staff stand-in before selecting a motion."""
import bpy,json,math,sys,os
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/winged_hands.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;scene.render.fps=48;rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
rest={b.name:b.matrix_local.copy() for b in rig.data.bones};grip=json.loads((P/'work/grip_pose.json').read_text());M=Matrix.Rotation(math.pi/2,4,'X');M.translation=Vector(grip['R']['center_bind']);socket=rest['B_R_Hand'].inverted()@M
names=[f'B_{sd}_{part}' for sd in 'LR' for part in ['UpperArm','Forearm','Hand']];TURN=Matrix.Rotation(math.pi,4,'Z');out={}
for file,picks in [('1Hand',['MaceAttackR1','MaceAttackR2','MaceAttackR3','SwordAttackR1','SwordAttackR2','SwordAttackR3']),('Armed',['ArmedIdle','ArmedIdleAlert1','ArmedIdlePistolL'])]:
 old_o=set(bpy.data.objects);old_a=set(bpy.data.actions);bpy.ops.import_scene.gltf(filepath=str(ROOT/'anim_library/humanoid_set'/f'{file}.glb'));added=set(bpy.data.objects)-old_o;actions=set(bpy.data.actions)-old_a;src=next(o for o in added if o.type=='ARMATURE');src.animation_data_create()
 for track in src.animation_data.nla_tracks:track.mute=True
 for pick in picks:
  action=next(a for a in actions if a.name.split('@')[-1].split('|')[-1]==pick);src.animation_data.action=action
  if action.slots:src.animation_data.action_slot=action.slots[0]
  start,end=action.frame_range;duration=(end-start)/48;rows=[]
  for t in np.linspace(0,duration,math.ceil(duration*48)+1):
   f=start+t*48;scene.frame_set(math.floor(f),subframe=f%1)
   for pb in rig.pose.bones:pb.matrix_basis.identity()
   bpy.context.view_layer.update()
   for n in names:
    pb=rig.pose.bones[n];R=(TURN@src.matrix_world@src.pose.bones[n].matrix).to_3x3().normalized().to_4x4();R.translation=pb.head;pb.matrix=R;bpy.context.view_layer.update()
   H=rig.pose.bones['B_R_Hand'].matrix;tip=(H@socket)@Vector((0,0,.765));head=rig.pose.bones['B_Head'].head;L=rig.pose.bones['B_L_Hand'].matrix
   gunM=Matrix.Rotation(math.pi/2,4,'X');gunM.translation=Vector(grip['L']['center_bind']);barrel=(L@rest['B_L_Hand'].inverted()@gunM).to_3x3()@Vector((0,-1,0))
   rows.append({'time':float(t),'tip':list(tip),'hand':list(H.translation),'head_z':head.z,'gun_direction':list(barrel.normalized())})
  z=np.array([r['tip'][2] for r in rows]);tt=np.array([r['time'] for r in rows]);vz=np.diff(z)/np.diff(tt);peak=int(z.argmax());down=peak+int(vz[peak:].argmin()) if peak<len(vz) else int(vz.argmin())
  out[pick]={'source':f'anim_library/humanoid_set/{file}.glb','duration_s':duration,'tip_peak_m':float(z[peak]),'peak_time_s':float(tt[peak]),'down_speed_m_s':float(vz[down]),'down_time_s':float((tt[down]+tt[down+1])/2),'down_tip_forward_m':-rows[down]['tip'][1],'max_hand_above_head_m':max(r['hand'][2]-r['head_z'] for r in rows),'gun_ready_direction':rows[0]['gun_direction'],'samples':rows}
  print(pick,{k:v for k,v in out[pick].items() if k!='samples'},flush=True)
 for o in added:bpy.data.objects.remove(o,do_unlink=True)
 for a in actions:bpy.data.actions.remove(a)
(P/'review/motion_probe_feedback.json').write_text(json.dumps(out,indent=2)+'\n')
sys.stdout.flush();sys.stderr.flush();os._exit(0)
