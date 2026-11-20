import bpy,json,math,traceback
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/rig_review_01/skirt_clearance');s=bpy.data.scenes['Goblin - Skirt Clearance v3'];bpy.context.window.scene=s;arm=s.objects['Goblin_SkirtClearance_Rig'];mesh=s.objects['Goblin_SkirtClearance_10577'];strips=json.loads((OUT/'strips.json').read_text());garment=set(i for p in json.loads((OUT/'components.json').read_text()) for i in p['ids']);coords=[mesh.matrix_world@v.co for v in mesh.data.vertices]
legs=set(i for c in json.loads((OUT/'body_components.json').read_text())[1:3] for i in c['ids'])
bodyfaces=[list(p.vertices) for p in mesh.data.polygons if all(i in legs for i in p.vertices) and all(.40<coords[i].z<1.08 and abs(coords[i].x)<.29 for i in p.vertices)]
# Surface samples include triangle edges and centers, not just garment vertices.
for strip in strips:
 ids=set(strip['ids']);points=[coords[i] for i in ids]
 for p in mesh.data.polygons:
  if all(i in ids for i in p.vertices):
   vs=[coords[i] for i in p.vertices];points.append(sum(vs,Vector())/len(vs))
   for i in range(len(vs)):points.append((vs[i]+vs[(i+1)%len(vs)])/2)
 unique={tuple(round(c,6) for c in v):v for v in points if v.z<strip['pivot'][2]-.025};strip['samples']=list(unique.values())
def signed_clearance(bvh,points,xf,outward):
 worst=1.
 for p in points:
  q=xf@p;hit,n,idx,d=bvh.find_nearest(q)
  if hit is not None:
   inside=False
   if (q-hit).dot(n)<0:
    rh,rn,ri,rd=bvh.ray_cast(q,outward,.6);inside=rh is not None and rn.dot(outward)>0
   worst=min(worst,-d if inside else d)
 return worst
def hinge(strip,angle):
 origin=Vector(strip['pivot']);return Matrix.Translation(origin)@Quaternion(Vector(strip['axis']),angle).to_matrix().to_4x4()@Matrix.Translation(-origin)
keys=['Idle_3','Walking','Running','Right_Hand_Sword_Slash','restpose'];jobs=[];results={};margin=.003
for key in keys:
 a=bpy.data.actions['Goblin_Skirt_'+key];jobs.extend((key,f) for f in range(math.floor(a.frame_range[0]),math.ceil(a.frame_range[1])+1));results[key]=[]
def step():
 try:
  bpy.context.window.scene=s
  if not jobs:
   (OUT/'clearance_solution.json').write_text(json.dumps(results,indent=2));(OUT/'clearance_done.txt').write_text('complete');return None
  key,f=jobs.pop(0);a=bpy.data.actions['Goblin_Skirt_'+key];arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];s.frame_set(f);bpy.context.view_layer.update();ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());deformed=[ev.matrix_world@v.co for v in ev.data.vertices];bvh=BVHTree.FromPolygons(deformed,bodyfaces,all_triangles=True);hip=arm.pose.bones['mixamorig:Hips'];D=hip.matrix@hip.bone.matrix_local.inverted();angles=[];clearances=[]
  for strip in strips:
   best=(-10,0);found=False
   for deg in range(0,86,2):
    val=signed_clearance(bvh,strip['samples'],D@hinge(strip,math.radians(deg)),D.to_quaternion()@Vector(strip['radial']))
    if val>best[0]:best=(val,deg)
    if val>=margin:found=True;break
   angle=deg if found else best[1];angles.append(angle);clearances.append(val if found else best[0])
  results[key].append({'frame':f,'degrees':angles,'clearances':clearances});(OUT/'clearance_progress.txt').write_text(key+' '+str(f)+' remaining '+str(len(jobs)))
  if len(jobs)%30==0:(OUT/'clearance_solution.json').write_text(json.dumps(results))
  return .01
 except Exception:(OUT/'clearance_error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print('Sampling',len(jobs),'frames and',len(bodyfaces),'body triangles for independent skirt-strip clearance')
