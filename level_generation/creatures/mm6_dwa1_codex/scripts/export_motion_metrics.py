import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget'];groups={'arms':[f'B_{s}_{n}'for s in'LR'for n in ['UpperArm','Forearm']],'hands':['B_L_Hand','B_R_Hand'],'twist':[f'B_{s}_{n}Twist'for s in'LR'for n in ['UpperArm','Forearm']],'fingers':[],'legs':[f'B_{s}_{n}'for s in'LR'for n in ['Thigh','Calf','Foot']],'trunk':['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']}
report={}
for tag,file in [('source','source_clips.blend'),('production','export_reimport.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work'/file));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;groups['fingers']=[b.name for b in rig.pose.bones if 'Finger'in b.name];report[tag]={}
 for n in roles:
  a=bpy.data.actions[n];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];prev=None;worst={g:0. for g in groups};floor=[];height=[];feet={s:[]for s in'LR'}
  for f in np.arange(float(a.frame_range[0]),float(a.frame_range[1])+1e-5,scene.render.fps/48):
   scene.frame_set(int(f),subframe=float(f-int(f)));cur={b.name:(rig.matrix_world@b.matrix).to_quaternion()for b in rig.pose.bones}
   if prev:
    for g,ns in groups.items():
     for bn in ns:
      if bn in cur and bn in prev:
       d=math.degrees(prev[bn].rotation_difference(cur[bn]).angle);worst[g]=max(worst[g],min(d,360-d))
   prev=cur
   if tag=='production':
    ob=bpy.data.objects['Body'];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();zs=[(ob.matrix_world@v.co).z for v in m.vertices];ev.to_mesh_clear();floor.append(min(zs));height.append(max(zs)-min(zs))
    for s in'LR':feet[s].append(tuple(rig.pose.bones[f'B_{s}_Foot'].head))
  report[tag][n]={'max_deg_per_48hz_step':worst,'duration_s':float(a.frame_range[1]-a.frame_range[0])/scene.render.fps}
  if floor:report[tag][n].update({'floor_min_max':[min(floor),max(floor)],'body_height_min_median_max':[min(height),float(np.median(height)),max(height)],'stride_length_m':[float(np.ptp(np.array(feet[s])[:,1])*2)for s in'LR']})
  print('METRICS',tag,n,report[tag][n],flush=True)
for n in roles:
 a=report['production'][n]['max_deg_per_48hz_step'];b=report['source'][n]['max_deg_per_48hz_step'];limits={g:b['hands'if g=='fingers'else'arms'if g=='twist'else g]+10 for g in a};report['production'][n]['trace_flags']=[g for g,v in a.items()if v>limits[g]]
(P/'review/motion_metrics_exported.json').write_text(json.dumps(report,indent=2))
