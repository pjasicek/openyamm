"""Signed anatomical elbow/forearm and standing sole audit at 48 Hz."""
import bpy,json,math
import numpy as np
from mathutils import Vector
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_master.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene
rest={s:[r.data.bones['B_'+s+'_'+n].head_local.copy() for n in ['UpperArm','Forearm','Hand']] for s in 'RL'}
report={};co=np.array([tuple(v.co) for v in b.data.vertices]);feet={}
for s,sign in [('R',-1),('L',1)]:
 ids=np.where((co[:,2]<.14)&(co[:,0]*sign>0))[0];mid=np.median(co[ids,1]);feet[s]=[ids[co[ids,1]>=mid],ids[co[ids,1]<mid]]
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows={s:[] for s in 'RL'};sole=[]
 for f in sorted(set(np.arange(float(a.frame_range[0]),float(a.frame_range[1]),sc.render.fps/48).tolist()+[float(a.frame_range[1])])):
  sc.frame_set(int(f),subframe=float(f-int(f)))
  for s in 'RL':
   un,fn,hn=['B_'+s+'_'+n for n in ['UpperArm','Forearm','Hand']];U,F,H=[r.pose.bones[n].head for n in [un,fn,hn]];up=(F-U).normalized();fo=(H-F).normalized();ru=(rest[s][1]-rest[s][0]).normalized();bend=Vector((0,-1,0));bend=(bend-ru*bend.dot(ru)).normalized();rot=r.pose.bones[un].matrix.to_3x3()@r.data.bones[un].matrix_local.to_3x3().inverted();normal=(rot@(ru.cross(bend))).normalized();forward=normal.cross(up).normalized();signed=math.degrees(math.atan2(fo.dot(forward),fo.dot(up)));off=math.degrees(math.asin(max(-1,min(1,fo.dot(normal)))))
   ax=(r.data.bones[fn].matrix_local.inverted()@r.data.bones[hn].head_local).normalized();q=r.pose.bones[fn].matrix_basis.to_quaternion();tw=(2*math.atan2(Vector(q[1:]).dot(ax),q.w)+math.pi)%(2*math.pi)-math.pi
   rows[s].append([float(f/sc.render.fps),signed,off,math.degrees(tw)])
  if a.name in ['Standing','Fidget']:
   e=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();p=np.array([tuple(v.co) for v in m.vertices]);e.to_mesh_clear();sole.append([float(min(p[g,2])) for fs in feet.values() for g in fs])
 rr={}
 for s,x in rows.items():
  x=np.array(x);rr[s]={'flex_min':float(x[:,1].min()),'flex_max':float(x[:,1].max()),'off_plane_max':float(abs(x[:,2]).max()),'forearm_roll_max':float(abs(x[:,3]).max()),'worst_flex_time':float(x[x[:,1].argmin(),0])}
 if sole:rr['soles_heel_toe_z_range_m']=[np.min(sole,axis=0).tolist(),np.max(sole,axis=0).tolist()]
 report[a.name]=rr
(P/'review/elbow_gate.json').write_text(json.dumps(report,indent=2));print('ELBOW',json.dumps(report))

for v in report.values():
 for side in "RL":
  assert v[side]["flex_min"] >= -5 and v[side]["off_plane_max"] < 1 and v[side]["forearm_roll_max"] <= 90
 if "soles_heel_toe_z_range_m" in v:assert max(abs(x) for row in v["soles_heel_toe_z_range_m"] for x in row) < .01
