"""Compare evaluated arm/wing surface intersections before and after the native attack correction."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];report={};unchanged={}
for revision,file in [('before','work/attack_v3/animations_before.blend'),('after','work/animations.blend'),('export','export/mm6_gar_lod0.glb')]:
 if revision=='export':
  bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P/file));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');obj=bpy.data.objects['Gargoyle']
 else:
  bpy.ops.wm.open_mainfile(filepath=str(P/file));rig=bpy.data.objects['Rig'];obj=bpy.data.objects['Body']
 scene=bpy.context.scene
 def action_signature(action):
  return [(fc.data_path,fc.array_index,[(round(k.co.x,6),round(k.co.y,6)) for k in fc.keyframe_points]) for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
 for name in ([] if revision=='export' else ['Flight','Hit','Death','Dead']):
  signature=sorted(action_signature(bpy.data.actions[name]))
  if revision=='before':unchanged[name]=signature
  else:
   diffs=[(a,b) for a,b in zip(unchanged[name],signature) if a!=b]
   # Matrix decomposition changes unit scales by less than one part per million.
   assert len(signature)==len(unchanged[name])
   for a,b in zip(unchanged[name],signature):
    assert a[:2]==b[:2] and len(a[2])==len(b[2])
    assert np.allclose(a[2],b[2],rtol=0,atol=.00001),f'Unexpected change to {name}: {a[:2]}'
 rest=np.array([obj.matrix_world@v.co for v in obj.data.vertices]);obj.data.calc_loop_triangles();faces=[tuple(t.vertices) for t in obj.data.loop_triangles]
 def weight(terms):return np.array([sum(g.weight for g in v.groups if any(s in obj.vertex_groups[g.group].name for s in terms)) for v in obj.data.vertices])
 wing=weight(['W_']);wing_faces=[f for f in faces if min(wing[list(f)])>.45]
 masks={};arm_faces={}
 for sd in ['L','R']:
  shoulder=np.array(rig.matrix_world@rig.data.bones[f'B_{sd}_UpperArm'].head_local);aw=weight([f'B_{sd}_UpperArm',f'B_{sd}_Forearm',f'B_{sd}_Hand',f'B_{sd}_Finger']);away=np.linalg.norm(rest-shoulder,axis=1)>.12
  arm_faces[sd]=[f for f in faces if min(aw[list(f)])>.55 and all(away[list(f)])]
  masks[sd]=np.where((weight([f'B_{sd}_Forearm',f'B_{sd}_Hand',f'B_{sd}_Finger'])>.8)&(wing<.01))[0]
  assert len(arm_faces[sd])>500 and len(masks[sd])>300
 act=next(a for a in bpy.data.actions if a.name=='Attack' or a.name.endswith('|Attack'));rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];duration=float(act.frame_range[1])/scene.render.fps;assert duration>1;rows=[]
 for t in sorted(set([i/120 for i in range(math.ceil(duration*120))]+[duration])):
  f=t*scene.render.fps;scene.frame_set(math.floor(f),subframe=f%1);ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[obj.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();w=BVHTree.FromPolygons(co,wing_faces,all_triangles=True,epsilon=0);row={'time':t}
  for sd in ['L','R']:
   a=BVHTree.FromPolygons(co,arm_faces[sd],all_triangles=True,epsilon=0);pairs=w.overlap(a)
   clearance=min(w.find_nearest(co[int(i)])[3] for i in masks[sd]);row[sd]={'intersecting_triangle_pairs':len(pairs),'minimum_forearm_hand_clearance_m':clearance,'wrist':list(rig.matrix_world@rig.pose.bones[f'B_{sd}_Hand'].head)}
  rows.append(row)
 report[revision]={'duration':duration,'samples':len(rows),'maximum_intersecting_pairs':max(r[sd]['intersecting_triangle_pairs'] for r in rows for sd in ['L','R']),'minimum_forearm_hand_clearance_m':min(r[sd]['minimum_forearm_hand_clearance_m'] for r in rows for sd in ['L','R']),'worst_frame':max(rows,key=lambda r:sum(r[sd]['intersecting_triangle_pairs'] for sd in ['L','R'])),'samples_detail':rows}
 print('ARM_WING_CLEARANCE',revision,{k:v for k,v in report[revision].items() if k not in ['samples_detail','worst_frame']},flush=True)
rows=report['after']['samples_detail'];reach=min(rows,key=lambda r:r['R']['wrist'][1]);report['impact_review']={'event_seconds':.75,'maximum_right_wrist_forward_reach_seconds':reach['time'],'interpretation':'Impact at maximum forward reach, within one authored 60 Hz sample; lateral follow-through continues across the front.'};assert abs(reach['time']-.75)<=1/60
report['unchanged_clips']=['Flight','Hit','Death','Dead'];(P/'work/attack_v4/wing_clearance.json').write_text(json.dumps(report,indent=2))
assert report['before']['maximum_intersecting_pairs']>0,'The regression check must detect the reported defect'
assert report['after']['maximum_intersecting_pairs']==0,'Arm still intersects a wing'
assert report['after']['minimum_forearm_hand_clearance_m']>.02,'Too little room between forearm/hand and wing'

assert report['export']['maximum_intersecting_pairs']==0,'Exported arm still intersects wing'
assert report['export']['minimum_forearm_hand_clearance_m']>.02
