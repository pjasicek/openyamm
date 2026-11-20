import bpy,bmesh,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/skirt_rebuild_01')
s=bpy.data.scenes['Goblin - Rebuilt Skirt and Belt v2'];bpy.context.window.scene=s
src=next(o for o in s.objects if o.name.startswith('SkirtStudy_Source200K'));old=next(o for o in s.objects if o.name.startswith('Goblin200K_ClothingShellRemoved'))
for o in s.objects:
 if o.name.startswith(('Goblin200K_ClothingShellRemoved','Goblin_InnerWaist_Band','Goblin_HiddenUpperThigh')):o.hide_render=True;o.hide_set(True)
plain=next(o for o in s.objects if o.name.startswith('Goblin_InnerWaist_Band')).data.materials[0]
body=src.copy();body.data=src.data.copy();body.name='Goblin_CleanWaistCut';s.collection.objects.link(body);body.hide_render=False;body.hide_set(False)
bm=bmesh.new();bm.from_mesh(body.data)
for z in [-.235,.213]:
 geom=[v for v in bm.verts if abs(v.co.x)<.30]+[e for e in bm.edges if all(abs(v.co.x)<.30 for v in e.verts)]+[f for f in bm.faces if all(abs(v.co.x)<.30 for v in f.verts)]
 bmesh.ops.bisect_plane(bm,geom=geom,dist=1e-7,plane_co=(0,0,z),plane_no=(0,0,1),clear_inner=False,clear_outer=False)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if abs(f.calc_center_median().x)<.30 and -.23500001<f.calc_center_median().z<.21299999],context='FACES')
loops=[]
for z in [-.235,.213]:
 edges=[e for e in bm.edges if e.is_boundary and all(abs(v.co.z-z)<1e-5 for v in e.verts)]
 adj={}
 for e in edges:
  a,b=e.verts;adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
 remaining=set(adj)
 while remaining:
  first=next(iter(remaining));ring=[];cur=first;prev=None
  while cur not in ring:
   ring.append(cur);remaining.discard(cur);opts=[v for v in adj[cur] if v!=prev]
   if not opts:break
   prev,cur=cur,opts[0]
  if len(ring)>8:loops.append((z,[v.co.copy() for v in ring]))
bm.to_mesh(body.data);bm.free();body.data.update()
created=[]
for idx,(z,ring) in enumerate(loops):
 center=sum(ring,Vector())/len(ring);ring.sort(key=lambda p:math.atan2(p.y-center.y,p.x-center.x))
 # Keep the actual cut ring unchanged; loft inward through the covered hip area.
 if z<0:levels=[(z,1.,0),(-.17,1.012,-.003),(-.07,1.018,-.008),(.09,.97,-.020)]
 else:levels=[(z,1.,0),(.17,.97,0),(.07,1.0,0),(-.05,.90,0)]
 vs=[];fs=[];N=len(ring)
 for h,scale,shift in levels:
  for p in ring:
   v=center+(p-center)*scale;v.z=h
   if z<0:v.x+=shift*(1 if center.x>0 else -1)
   vs.append(v[:])
 for k in range(len(levels)-1):
  for j in range(N):
   face=[k*N+j,k*N+(j+1)%N,(k+1)*N+(j+1)%N,(k+1)*N+j]
   if z>0:face.reverse()
   fs.append(face)
 me=bpy.data.meshes.new('Fitted covered anatomy');me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new('Goblin_CoveredAnatomy_'+str(idx),me);s.collection.objects.link(ob);me.materials.append(plain)
 for p in me.polygons:p.use_smooth=True
 created.append(ob)
# Preserve original pouch exterior in a separately clipped copy, close its hidden cut surfaces.
pouch=src.copy();pouch.data=src.data.copy();pouch.name='Goblin_PreservedPouch';s.collection.objects.link(pouch);pouch.hide_render=False;pouch.hide_set(False)
bm=bmesh.new();bm.from_mesh(pouch.data)
for co,no,outer in [((-.198,0,0),(1,0,0),True),((0,0,-.039),(0,0,1),False),((0,0,.130),(0,0,1),True),((0,-.11,0),(0,1,0),False),((0,.145,0),(0,1,0),True)]:
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=co,plane_no=no,clear_outer=outer,clear_inner=not outer)
bound=[e for e in bm.edges if e.is_boundary]
if bound:bmesh.ops.holes_fill(bm,edges=bound,sides=0)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(pouch.data);bm.free();pouch.data.update()
report={'body_triangles_after_clean_cut':sum(len(p.vertices)-2 for p in body.data.polygons),'cut_loops':[{'z':z,'vertices':len(ring)} for z,ring in loops],'covered_anatomy_triangles':sum(len(p.vertices)-2 for o in created for p in o.data.polygons),'pouch_triangles':sum(len(p.vertices)-2 for p in pouch.data.polygons)}
(ROOT/'body_join_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
# Render one corrected view now, leaving material bake connected.
cam=s.camera;cam.location=(0,-4,0);cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(ROOT/'front_baked_v3.png');bpy.ops.render.render(write_still=True)
