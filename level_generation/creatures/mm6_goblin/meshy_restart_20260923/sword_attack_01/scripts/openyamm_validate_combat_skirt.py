import bpy,json,math,traceback
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/sword_attack_01');s=bpy.data.scenes['Goblin - Sword and Native Attack'];bpy.context.window.scene=s;arm=s.objects['Goblin_Combat_Rig'];mesh=s.objects['Goblin_Combat_Body'];strips=json.loads((OUT/'strips.json').read_text());legs=set(i for c in [x for x in json.loads((OUT/'body_components.json').read_text()) if x['n']>100 and x['max'][2]<.95 and x['min'][2]<.01] for i in c['ids']);base=[mesh.matrix_world@v.co for v in mesh.data.vertices];bodyfaces=[list(p.vertices) for p in mesh.data.polygons if all(i in legs for i in p.vertices) and all(.40<base[i].z<1.08 for i in p.vertices)]
for st in strips:
 ids=set(st['ids']);st['faces']=[list(p.vertices) for p in mesh.data.polygons if all(i in ids for i in p.vertices)];st['ids_low']=[i for i in ids if base[i].z<st['pivot'][2]-.025];st['faces_low']=[f for f in st['faces'] if sum(base[i].z for i in f)/len(f)<st['pivot'][2]-.025]
jobs=[];report={}
for key in ['Idle','Walk','Run','Attack','GripRest']:
 a=bpy.data.actions['MM6_Goblin_'+key];lo,hi=a.frame_range;frames=[lo+i*.5 for i in range(round((hi-lo)*2)+1)];report[key]={'samples':len(frames),'minimum_clearance_m':1,'worst_frame':None,'worst_strip':None,'penetrating_samples':0};jobs.extend((key,f) for f in frames)
def step():
 try:
  bpy.context.window.scene=s
  if not jobs:
   (OUT/'motion_clearance_report.json').write_text(json.dumps(report,indent=2));(OUT/'validation_done.txt').write_text('complete');return None
  key,f=jobs.pop(0);a=bpy.data.actions['MM6_Goblin_'+key];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];s.frame_set(int(f),subframe=f-int(f));ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());co=[ev.matrix_world@v.co for v in ev.data.vertices];bvh=BVHTree.FromPolygons(co,bodyfaces,all_triangles=True);hip=arm.pose.bones['mixamorig:Hips'];D=hip.matrix@hip.bone.matrix_local.inverted();r=report[key]
  for st in strips:
   points=[co[i] for i in st['ids_low']]
   for face in st['faces_low']:
    points.append(sum((co[i] for i in face),Vector())/len(face))
    for j in range(len(face)):
     if (base[face[j]].z+base[face[(j+1)%len(face)]].z)/2<st['pivot'][2]-.025:points.append((co[face[j]]+co[face[(j+1)%len(face)]])/2)
   outward=D.to_quaternion()@Vector(st['radial'])
   for q in points:
    loc,n,idx,d=bvh.find_nearest(q)
    if loc is None:continue
    if (q-loc).dot(n)<0:
     rh,rn,ri,rd=bvh.ray_cast(q,outward,.6)
     if rh is not None and rn.dot(outward)>0:d=-d
    if d<r['minimum_clearance_m']:r.update(minimum_clearance_m=d,worst_frame=f,worst_strip=st['name'])
    if d<-.0005:r['penetrating_samples']+=1
  (OUT/'validation_progress.txt').write_text(key+' '+str(f)+' remaining '+str(len(jobs)));return .01
 except Exception:(OUT/'validation_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print('Checking',len(jobs),'whole and half-frame poses for skirt/thigh penetration')
