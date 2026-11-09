import bpy,json,math,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from timing import phase
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_master.blend'));rig=bpy.data.objects['Rig'];ob=bpy.data.objects['Jackalman'];sc=bpy.context.scene;names={g.index:g.name for g in ob.vertex_groups};dom=[names[max(v.groups,key=lambda g:g.weight).group]if v.groups else '' for v in ob.data.vertices];thumb=[v.index for v in ob.data.vertices if dom[v.index].startswith('B_R_Finger0')];tp=[tuple(p.vertices)for p in ob.data.polygons if any(i in thumb for i in p.vertices)];st=[v.index for v in ob.data.vertices if dom[v.index]=='Staff'];rest=np.array([v.co[:]for v in ob.data.vertices]);edges=np.array([e.vertices[:]for e in ob.data.edges if any(i in thumb for i in e.vertices)]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1);grip=json.loads((P/'work/grip_pose.json').read_text())['finger_local'];q0=Quaternion(grip['B_R_Finger0']);pb=rig.pose.bones['B_R_Finger0'];a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
def at(t):
 f=phase('Death',float(t))*sc.render.fps;sc.frame_set(int(f),subframe=f-int(f))
def smooth(u):u=max(0,min(1,u));return u*u*(3-2*u)
results=[]
for xyz in [(1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,0,1),(0,1,1),(1,-1,0),(1,0,-1),(0,1,-1)]:
 for deg in [-90,-60,-45,-30,30,45,60,90]:
  q1=Quaternion(Vector(xyz).normalized(),math.radians(deg))@q0;worst=0;stretch=0
  for t in np.arange(.12,.53,1/48):
   at(t);u=smooth((t-.12)/.13);v=smooth((t-.35)/.15);pb.rotation_quaternion=q0.slerp(q1,u).slerp(Quaternion().slerp(q0,.45),v);bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.empty((len(me.vertices),3),np.float32);me.vertices.foreach_get('co',co.ravel());ev.to_mesh_clear();stretch=max(stretch,float(np.max(np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)/np.maximum(length,1e-9))));tree=BVHTree.FromPolygons(co.tolist(),tp)
   for i in st:
    loc,n,fi,d=tree.find_nearest(Vector(co[i]),.03)
    if loc is not None and (Vector(co[i])-loc).dot(n)<-.7*d:worst=max(worst,d)
   if worst>.0021 or stretch>4.5:break
  row={'axis':xyz,'angle_deg':deg,'depth_m':worst,'max_edge_stretch':stretch,'target_quaternion':list(q1)};results.append(row)
  if worst<=.002 and stretch<=4.5:print('PASS THUMB',row,flush=True)
valid=[r for r in results if r['depth_m']<=.002 and r['max_edge_stretch']<=4.5];(P/'work/thumb_release_candidates.json').write_text(json.dumps(results,indent=2));assert valid,sorted(results,key=lambda r:r['depth_m'])[:5];best=min(valid,key=lambda r:(abs(r['angle_deg']),r['max_edge_stretch']));(P/'work/thumb_release.json').write_text(json.dumps(best,indent=2));print('BEST',best,flush=True)
a=bpy.data.actions['Dead'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0);ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();hi=sorted([(v.co.z,dom[v.index],v.index)for v in me.vertices if dom[v.index]!='Staff'],reverse=True)[:20];print('CORPSE HIGH',hi,flush=True)
