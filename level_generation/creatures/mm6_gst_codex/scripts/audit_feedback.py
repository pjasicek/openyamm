"""Measure the requested attack keys, visible wrist bends and the claw impact speed."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;D=json.loads((P/'work/rig.json').read_text());r.animation_data.action=bpy.data.actions['Attack'];frames=np.arange(1,85.01,.5);tips=[];angles={'L':[],'R':[]};keys={}
for frame in frames:
 sc.frame_set(int(frame),subframe=frame%1)
 for sd in ['L','R']:
  fore=r.pose.bones['B_'+sd+'_Forearm'].matrix.translation;hand=r.pose.bones['B_'+sd+'_Hand'].matrix.translation;H=r.pose.bones['B_'+sd+'_Hand'].matrix@r.data.bones['B_'+sd+'_Hand'].matrix_local.inverted();palm=H@Vector(D['digits'][sd+'2']['pts'][0]);angles[sd].append(math.degrees((hand-fore).angle(palm-hand)))
 digit=D['digits']['R2'];n=digit['bones'][-1];tips.append(list(r.pose.bones[n].matrix@r.data.bones[n].matrix_local.inverted()@Vector(digit['pts'][-1])))
 if frame-1 in [0,12,24,36,44,56,70,84]:keys[str(int(frame-1))]={n:list(r.pose.bones[n].matrix.translation) for n in ['B_Pelvis','B_Head','B_R_Hand','B_L_Hand']}
velocity=np.linalg.norm(np.diff(tips,axis=0),axis=1)*120;times=(frames[1:]-1-.25)/60;window=(times>.40)&(times<.933);peak=int(np.flatnonzero(window)[np.argmax(velocity[window])]);out={'revision':'v2','key_positions':keys,'max_visible_wrist_bend_deg':{k:max(v) for k,v in angles.items()},'claw_impact_time_s':float(times[peak]),'claw_impact_speed_m_s':float(velocity[peak]),'duration':1.4}
assert max(max(v) for v in angles.values())<46,out
(P/'review/feedback_v2/attack_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
