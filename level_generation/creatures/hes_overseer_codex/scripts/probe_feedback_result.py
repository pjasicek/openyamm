"""Check the requested low-ready flight and overhead smash on the assembled candidate."""
import bpy,json,sys,os,math,importlib.util
from pathlib import Path
import numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/overseer_assembly.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;out={}
for name,duration in [('Overseer_Flight',3),('Overseer_AttackRanged',1.2),('Overseer_AttackMelee',2.4)]:
 a=bpy.data.actions[name];rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
 rows=[]
 for t in sorted(set([*np.arange(0,duration,1/48),duration])):
  f=t*48;scene.frame_set(math.floor(f),subframe=f%1)
  tip=rig.pose.bones['CollarRod'].matrix@Vector((0,0,.588));gun=(rig.pose.bones['PulsePistol'].matrix.to_3x3()@Vector((0,-1,0))).normalized();head=rig.pose.bones['B_Head'].head;hand=rig.pose.bones['B_R_Hand'].head
  rows.append({'time':float(t),'rod_tip':list(tip),'gun_direction':list(gun),'hand_above_head':hand.z-head.z})
 z=np.array([r['rod_tip'][2] for r in rows]);tt=np.array([r['time'] for r in rows]);v=np.diff(z)/np.diff(tt);peak=int(z.argmax());down=peak+int(v[peak:].argmin()) if peak<len(v) else int(v.argmin())
 out[name]={'gun_max_z':max(r['gun_direction'][2] for r in rows),'gun_max_forward':max(-r['gun_direction'][1] for r in rows),'windup_peak_s':float(tt[peak]),'rod_peak_z':float(z[peak]),'drop_after_peak_m':float(z[peak]-z[peak:].min()),'downstroke_peak_s':float((tt[down]+tt[down+1])/2),'downstroke_velocity_m_s':float(v[down]),'max_hand_above_head_m':max(r['hand_above_head'] for r in rows),'samples':rows}
 print(name,{k:v for k,v in out[name].items() if k!='samples'},flush=True)
assert out['Overseer_Flight']['gun_max_z']<-.75,'Flight pistol is not lowered'
assert out['Overseer_AttackRanged']['gun_max_forward']>.7,'Ranged clip never aims forward'
assert out['Overseer_AttackMelee']['max_hand_above_head_m']>0,'Melee hand never reaches overhead'
assert out['Overseer_AttackMelee']['drop_after_peak_m']>.8,'Melee lacks a downward smash'
# Sample the exported runtime interpolation between authored frames as well as at the firing anchors.
spec=importlib.util.spec_from_file_location('gates',P.parent/'claude_shared/gates/run_gates.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
glb=g.Glb(P/'work/overseer_body_lod0.glb');clip=next(a for n,a,_,_ in glb.clips() if n=='Overseer_AttackRanged')
times=np.unique(np.r_[np.arange(0,1.2,1/192),.35,.45,.53,.73,.85,1.2]);poses=glb.pose(clip,times);M=poses[:,glb.names['PulsePistol']];direction=g.unit(-M[:,:3,1]);release=int(np.flatnonzero(times==.45)[0]);hold=(times>=.35)&(times<=.45);shot=(times>=.35)&(times<=.85)
angle=g.angle(direction,direction[release]);speed=g.angle(direction[:-1],direction[1:])/np.diff(times)
shoulder=poses[:,glb.names['B_L_UpperArm'],:3,3];relative=M[:,:3,3]-shoulder
metrics={'glb_sha256':glb.sha256,'sampling_hz':192,'aim_forward_error_deg':float(g.angle(direction[hold],[0,-1,0]).max()),'aim_hold_drift_deg':float(angle[hold].max()),'recoil_excursion_deg':float(angle[shot].max()),'recoil_rise_deg':float(np.degrees(np.arcsin(direction[shot,2])).max()-np.degrees(np.arcsin(direction[release,2]))),'grip_travel_relative_shoulder_m':float(np.linalg.norm(relative[shot]-relative[release],axis=1).max()),'max_muzzle_speed_deg_s':float(speed.max()),'end_muzzle_z':float(direction[-1,2])}
muzzle=poses[:,glb.names['Socket_Muzzle'],:3,3];head=poses[:,glb.names['B_Head'],:3,3]
metrics['muzzle_above_head_joint_m']=float((muzzle[hold,2]-head[hold,2]).max())
assert -.10<metrics['muzzle_above_head_joint_m']<.20,metrics
assert metrics['aim_forward_error_deg']<6,metrics
assert metrics['aim_hold_drift_deg']<.5,metrics
assert 8<metrics['recoil_rise_deg']<11 and 9<metrics['recoil_excursion_deg']<11,metrics
assert metrics['grip_travel_relative_shoulder_m']<.025,metrics
assert metrics['max_muzzle_speed_deg_s']<450 and metrics['end_muzzle_z']<-.75,metrics
out['ranged_export_check']=metrics
print('RANGED_EXPORTED_CHECK',metrics,flush=True)
(P/'review/feedback_motion.json').write_text(json.dumps(out,indent=2)+'\n')
sys.stdout.flush();sys.stderr.flush();os._exit(0)
