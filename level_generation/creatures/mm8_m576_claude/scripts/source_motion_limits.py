"""Measure the selected library motions and retain extreme poses for deformation review."""
import bpy,math,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];root=p.parents[2]
roles={row['role'].replace('Attack_body','Attack'):(row['path'].removeprefix('anim_library/'),None) for row in json.loads((p/'motion_selection.json').read_text())['selected_sources']}
roles['Hit']=('humanoid_set/Unarmed.glb','UnarmedGetHitF1')
result={}
for role,(file,clip) in roles.items():
 path=root/'anim_library'/file;bpy.ops.wm.read_factory_settings(use_empty=True)
 if path.suffix=='.fbx':bpy.ops.import_scene.fbx(filepath=str(path))
 else:bpy.ops.import_scene.gltf(filepath=str(path))
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene
 if clip:
  a=next(a for a in bpy.data.actions if a.name.split('@')[-1].split('|')[-1]==clip);rig.animation_data.action=a
  if a.slots:rig.animation_data.action_slot=a.slots[0]
 else:a=rig.animation_data.action
 fps=sc.render.fps/sc.render.fps_base;f0,f1=a.frame_range;duration=(f1-f0)/fps
 names={n.split(':')[-1]:n for n in rig.pose.bones.keys()}
 chains={}
 for side,sd in [('Left','L'),('Right','R')]:
  keys=[side+x for x in ('Arm','ForeArm','Hand','HandMiddle1')] if not clip else [f'B_{sd}_{x}' for x in ('UpperArm','Forearm','Hand','Finger2')]
  chains[sd]=[names[k] for k in keys]
 selected=[n for chain in chains.values() for n in chain[:3]]+[n for n in names.values() if 'Spine' in n or 'Neck' in n]
 quats={n:[] for n in selected};angles={sd:[] for sd in chains};times=np.linspace(0,duration,int(round(duration*48))+1)
 for t in times:
  f=f0+t*fps;sc.frame_set(math.floor(f),subframe=f-math.floor(f))
  for n in selected:quats[n].append((rig.matrix_world@rig.pose.bones[n].matrix).to_quaternion())
  for sd,ns in chains.items():
   pts=[rig.matrix_world@rig.pose.bones[n].head for n in ns];segs=[b-a for a,b in zip(pts[:-1],pts[1:])]
   angles[sd].append([math.degrees(segs[0].angle(segs[1])),math.degrees(segs[1].angle(segs[2]))])
 rr={}
 for n,qs in quats.items():
  steps=[];vel=[];rest=(rig.matrix_world@rig.data.bones[n].matrix_local).to_quaternion();swing=[]
  for q in qs:
   delta=q@rest.inverted();swing.append(math.degrees(min(delta.angle,2*math.pi-delta.angle)))
  for i,(qa,qb) in enumerate(zip(qs[:-1],qs[1:])):
   dq=qb@qa.inverted()
   if dq.w<0:dq.negate()
   axis,angle=dq.to_axis_angle();steps.append(math.degrees(angle));vel.append(np.array(axis)*angle/(times[i+1]-times[i]))
  acc=np.linalg.norm(np.diff(vel,axis=0),axis=1)/np.diff(times)[:-1]*180/math.pi
  rr[n]={'max_rotation_from_rest_deg':max(swing),'extreme_time_s':float(times[np.argmax(swing)]),'max_step_deg_48hz':max(steps),'max_acceleration_deg_s2':float(acc.max())}
 for sd,vals in angles.items():
  vals=np.array(vals)
  for i,label in enumerate(('elbow_flex','wrist_bend')):rr[sd+'_'+label]={'min_deg':float(vals[:,i].min()),'max_deg':float(vals[:,i].max()),'extreme_time_s':float(times[vals[:,i].argmax()])}
 assert duration>0 and all(np.isfinite(v) for row in rr.values() for v in row.values())
 result[role]={'path':str(path.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'clip':clip,'duration_s':duration,'bones':rr}
 print('SOURCE_ROM',role,round(duration,3),rr['R_elbow_flex'],rr['R_wrist_bend'])
(p/'review/source_motion_limits.json').write_text(json.dumps(result,indent=2)+'\n')
