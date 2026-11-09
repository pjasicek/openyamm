import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene;objects=[bpy.data.objects['Body'],bpy.data.objects['BowAsset']];inv=r.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();report={}
def bounds():
 lo=Vector((1e6,1e6,1e6));hi=-lo
 for ob in objects:
  ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
  co=np.array([tuple(ob.matrix_world@v.co)for v in m.vertices]);ev.to_mesh_clear();lo=Vector(np.minimum(lo,co.min(0)));hi=Vector(np.maximum(hi,co.max(0)))
 return lo,hi
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];nf=int(a.frame_range[1]);loc=[];corr=[0.]*(nf+1)
 for f in range(nf+1):sc.frame_set(f);loc.append(r.pose.bones['B_Pelvis'].location.copy())
 for tick in range(nf*4+1):
  f=tick/4;sc.frame_set(int(f),subframe=f-int(f));lo,hi=bounds();dz=max(0.,.00035-lo.z)
  if lo.z>=.0001:dz=0.
  for j in {int(f),min(nf,math.ceil(f))}:corr[j]=max(corr[j],dz)
 assert max(corr)<.004,('Unexpected new floor failure',a.name,max(corr))
 for f,l in enumerate(loc):
  b=r.pose.bones['B_Pelvis'];b.location=l+inv@Vector((0,0,corr[f]));b.keyframe_insert('location',frame=f)
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 floor=99;heights=[]
 for tick in range(nf*4+1):
  f=tick/4;sc.frame_set(int(f),subframe=f-int(f));lo,hi=bounds();floor=min(floor,lo.z);heights.append(hi.z-lo.z)
 assert floor>=-1e-5,(a.name,floor)
 report[a.name]={'root_clearance_correction_max_m':max(corr),'floor_min_m':floor,'height_range_m':[min(heights),max(heights)]};print('FINAL FLOOR',a.name,report[a.name])
a=bpy.data.actions['Walking'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];feet={s:[]for s in 'LR'}
for f in range(25):
 sc.frame_set(f)
 for s in 'LR':feet[s].append((r.pose.bones[f'B_{s}_Foot'].head-r.pose.bones['B_Pelvis'].head).y)
stride=2*np.mean([max(v)-min(v)for v in feet.values()]);height=np.mean(report['Standing']['height_range_m']);scale=256*.699997/height
(P/'work/final_floor.json').write_text(json.dumps(report,indent=2));(P/'work/calibration.json').write_text(json.dumps({'native_standing_opaque_height_px':256,'native_scale':.699997,'target_height_world':256*.699997,'standing_height_m':height,'model_scale':scale,'stride_length_m':stride,'run_threshold_world':scale*2.4,'native_speeds':[140,150,160]},indent=2));print('CALIBRATION',height,scale,stride)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
