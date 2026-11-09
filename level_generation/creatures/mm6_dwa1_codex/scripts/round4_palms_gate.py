"""Protect the accepted palm side, finger curl and wrist/axe frame on every clip."""
import bpy,json,sys,math,numpy as np,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROLES=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'];traces={}
for label,path in [('accepted',P/'work/round4_before/work/export_reimport.blend'),('reduced',P/'work/export_reimport.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;traces[label]={}
 for role in ROLES:
  act=bpy.data.actions[role];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];rows=[]
  for t in np.arange(0,float(act.frame_range[1])/scene.render.fps+1e-6,1/48):
   f=t*scene.render.fps;scene.frame_set(int(f),subframe=f%1);row={}
   for sd in 'LR':
    hand=rig.pose.bones[f'B_{sd}_Hand'];w=hand.head;i=rig.pose.bones[f'B_{sd}_Finger1'].head;p=rig.pose.bones[f'B_{sd}_Finger4'].head
    normal=(i-w).cross(p-w).normalized();curl=[]
    for digit in [1,2,3,4]:
     a,b,c=[rig.pose.bones[f'B_{sd}_Finger{digit}{s}'].head for s in ['', '1','2']]
     curl.append(math.degrees((b-a).angle(c-b)))
    row[sd]={'palm_plane_normal':list(normal),'finger_curl_degrees':curl,'hand_frame':np.array(hand.matrix).tolist()}
   row['axe_in_hand']=np.array(rig.pose.bones['B_R_Hand'].matrix.inverted()@rig.pose.bones['Axe'].matrix).tolist();rows.append(row)
  traces[label][role]=rows
report={}
for role in ROLES:
 old,new=traces['accepted'][role],traces['reduced'][role];assert len(old)==len(new)
 err=max(abs(np.array(a[sd]['hand_frame'])-b[sd]['hand_frame']).max()for a,b in zip(old,new)for sd in 'LR')
 normal=max(np.linalg.norm(np.array(a[sd]['palm_plane_normal'])-b[sd]['palm_plane_normal'])for a,b in zip(old,new)for sd in 'LR')
 curl=max(abs(np.array(a[sd]['finger_curl_degrees'])-b[sd]['finger_curl_degrees']).max()for a,b in zip(old,new)for sd in 'LR')
 grip=max(abs(np.array(a['axe_in_hand'])-b['axe_in_hand']).max()for a,b in zip(old,new))
 report[role]={'samples':len(new),'palm_normal_delta':float(normal),'finger_curl_max_delta_deg':float(curl),'hand_frame_max_delta':float(err),'axe_grip_frame_max_delta':float(grip),'pass':bool(max(err,normal,curl,grip)<1e-4)}
out={'runtime_sha256':hashlib.sha256((P/'export/mm6_dwa1.glb').read_bytes()).hexdigest(),'sample_hz':48,'method':'Anatomical palm planes, all four finger curls, full wrist frames and axe-in-hand frame compared to the user-accepted round 3 pose on every clip. Accepted palm side and grip are preserved; this is not a new pose authoring pass.','clips':report,'pass':all(x['pass']for x in report.values())}
(P/'review/round4/palms_gate.json').write_text(json.dumps(out,indent=2)+'\n');assert out['pass'];print('PALMS',out['pass'])

