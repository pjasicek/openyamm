"""48 Hz world-space angular acceleration on upper arms, forearms and wrists."""
import bpy,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];source=P/globals().get('INPUT','work/round1_lod0.blend')
if source.suffix=='.glb':
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source))
else:bpy.ops.wm.open_mainfile(filepath=str(source))
r=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene;fps=sc.render.fps/sc.render.fps_base;out={}
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];times=np.arange(0,a.frame_range[1]/fps+1e-6,1/48);qs={f'B_{s}_{n}':[] for s in 'RL' for n in ['UpperArm','Forearm','Hand']}
 for t in times:
  f=t*fps;sc.frame_set(int(f),subframe=f%1)
  for n in qs:qs[n].append((r.matrix_world@r.pose.bones[n].matrix).to_quaternion())
 rows={}
 for n,q in qs.items():
  v=[]
  for p,c in zip(q,q[1:]):
   d=c@p.inverted()
   if d.w<0:d.negate()
   axis,angle=d.to_axis_angle();v.append(np.array(axis)*angle*48)
  acceleration=np.linalg.norm(np.diff(v,axis=0),axis=1)*48*180/math.pi;i=int(acceleration.argmax());rows[n]={'max_deg_s2':float(acceleration[i]),'time':float(times[i+1]),'pass':float(acceleration[i])<=20000}
 out[a.name]={'bones':rows,'pass':all(x['pass'] for x in rows.values())};print('ACCELERATION',a.name,max(x['max_deg_s2'] for x in rows.values()),out[a.name]['pass'],flush=True)
(P/globals().get('REPORT','review/round1/acceleration_gate.json')).write_text(json.dumps({'limit_deg_s2':20000,'method':'World rotation-vector velocity differences at 48 Hz; shared gates threshold.','clips':out,'pass':all(x['pass'] for x in out.values())},indent=2))
