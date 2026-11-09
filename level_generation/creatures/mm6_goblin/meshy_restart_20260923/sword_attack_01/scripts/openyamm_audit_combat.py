import bpy,json,math,traceback
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/sword_attack_01');s=bpy.data.scenes['Goblin - Sword and Native Attack'];bpy.context.window.scene=s;r=s.objects['Goblin_Combat_Rig'];m=s.objects['Goblin_Combat_Body'];blade=s.objects['Corsair blade'];faces=[list(p.vertices) for p in m.data.polygons];r.animation_data.action=bpy.data.actions['MM6_Goblin_Attack'];r.animation_data.action_slot=r.animation_data.action.slots[0];samples=[];prev={};start={};end={}
for f in [1+i*.5 for i in range(37)]:
 s.frame_set(int(f),subframe=f-int(f));dg=bpy.context.evaluated_depsgraph_get();em=m.evaluated_get(dg);eb=blade.evaluated_get(dg);co=[em.matrix_world@v.co for v in em.data.vertices];bc=[eb.matrix_world@v.co for v in eb.data.vertices];tree=BVHTree.FromPolygons(co,faces,all_triangles=False);hits=[]
 for edge in eb.data.edges:
  a,b=[bc[i] for i in edge.vertices];delta=b-a
  if delta.length>.000001:
   hit,n,idx,dist=tree.ray_cast(a,delta.normalized(),delta.length)
   if hit is not None:hits.append({'body_face':idx,'point':list(hit)})
 maxstep=(0,None)
 for name in ['mixamorig:RightArm','mixamorig:RightForeArm','mixamorig:RightHand','mixamorig:LeftArm','mixamorig:LeftForeArm']:
  q=r.pose.bones[name].matrix.to_quaternion()
  if name in prev:
   ang=math.degrees(q.rotation_difference(prev[name]).angle);ang=min(ang,360-ang)
   if ang>maxstep[0]:maxstep=(ang,name)
  prev[name]=q.copy()
 if f==1:start={pb.name:pb.matrix.copy() for pb in r.pose.bones}
 if f==19:end={pb.name:pb.matrix.copy() for pb in r.pose.bones}
 samples.append({'frame':f,'blade_body_intersections':hits,'largest_arm_world_rotation_step_degrees':maxstep,'body_min_z':min(v.z for v in co)})
report={'attack_samples':samples,'largest_arm_step_degrees':max(x['largest_arm_world_rotation_step_degrees'][0] for x in samples),'blade_intersection_frames':[x['frame'] for x in samples if x['blade_body_intersections']],'attack_return_max_joint_distance_m':max((start[n].translation-end[n].translation).length for n in start),'attack_return_max_rotation_difference_deg':max(min(math.degrees(start[n].to_quaternion().rotation_difference(end[n].to_quaternion()).angle),360-math.degrees(start[n].to_quaternion().rotation_difference(end[n].to_quaternion()).angle)) for n in start),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in s.objects if o.type=='MESH'),'bones':len(r.data.bones)}
(OUT/'combat_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='attack_samples'}));s.frame_set(4)
