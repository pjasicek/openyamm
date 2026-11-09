"""Fit a safe off-hand thumb release against the actual, bounded grip geometry."""
import bpy,json,sys,runpy,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from timing import phase
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_master.blend'));rig=bpy.data.objects['Rig'];ob=bpy.data.objects['Jackalman'];sc=bpy.context.scene
names={g.index:g.name for g in ob.vertex_groups};dom=[names[max(v.groups,key=lambda g:g.weight).group]if v.groups else''for v in ob.data.vertices];st=[v.index for v in ob.data.vertices if dom[v.index]=='Staff'];matrix=rig.data.bones['Staff'].matrix_local;inv=matrix.inverted()
def smooth(u):u=max(0,min(1,u));return u*u*(3-2*u)
# Undo the trial's additive thickening, then build up only undersized shaft surfaces.
for i in st:
 v=ob.data.vertices[i];q=inv@v.co;r=math.hypot(q.x,q.y);extra=sum(a*smooth((.09-abs(q.z-c))/.035)for c,a in [(0,.0034),(.29,.006)]);base=max(0,r-extra);new=base
 for c,target in [(0,.016),(.29,.017)]:new+=max(0,target-base)*smooth((.09-abs(q.z-c))/.035)
 if r>1e-7:q.x*=new/r;q.y*=new/r
 v.co=matrix@q
a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=phase('Attack',.8)*sc.render.fps;sc.frame_set(int(f),subframe=f-int(f))
G=json.loads((P/'work/grip_pose_left.json').read_text())['finger_local'];q0=Quaternion(G['B_L_Finger0']);pb=rig.pose.bones['B_L_Finger0'];thumb=[v.index for v in ob.data.vertices if dom[v.index].startswith('B_L_Finger0')];tp=[tuple(p.vertices)for p in ob.data.polygons if any(i in thumb for i in p.vertices)];rest=np.array([v.co[:]for v in ob.data.vertices]);edges=np.array([e.vertices[:]for e in ob.data.edges if any(i in thumb for i in e.vertices)]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1);staffinv=(rig.matrix_world@rig.pose.bones['Staff'].matrix).inverted();rows=[]
for axis in [(1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,0,1),(0,1,1),(1,-1,0),(1,0,-1),(0,1,-1)]:
 for degree in [-90,-60,-45,-30,30,45,60,90]:
  q1=Quaternion(Vector(axis).normalized(),math.radians(degree))@q0;worst=0;stretch=0;radius=0
  for u in np.linspace(0,1,13):
   pb.rotation_quaternion=q0.slerp(q1,float(u));bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.empty((len(me.vertices),3),np.float32);me.vertices.foreach_get('co',co.ravel());ev.to_mesh_clear();stretch=max(stretch,float(np.max(np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)/np.maximum(length,1e-9))));tree=BVHTree.FromPolygons(co.tolist(),tp)
   for i in st:
    loc,n,fi,d=tree.find_nearest(Vector(co[i]),.03)
    if loc is not None and (Vector(co[i])-loc).dot(n)<-.7*d:worst=max(worst,d)
   local=[staffinv@Vector(co[i])for i in thumb];radius=min(math.hypot(v.x,v.y)for v in local)
   if worst>.002 or stretch>4.5:break
  row={'axis':axis,'degrees':degree,'depth_m':worst,'max_edge_stretch':stretch,'end_radius_m':radius,'quaternion':list(q1)};rows.append(row)
valid=[r for r in rows if r['depth_m']<=.002 and r['max_edge_stretch']<=4.5 and r['end_radius_m']>.04];(P/'work/left_thumb_candidates.json').write_text(json.dumps(rows,indent=2));assert valid,sorted(rows,key=lambda r:r['depth_m'])[:5];best=min(valid,key=lambda r:(abs(r['degrees']),r['max_edge_stretch']));(P/'work/left_thumb_open.json').write_text(json.dumps(best,indent=2));print('LEFT THUMB ARC',best,flush=True)
for file in ['textured_master','production_body','animated_master']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{file}.blend'));rig=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc=bpy.context.scene;sc.frame_set(0);idle={n:rig.pose.bones[n].rotation_quaternion.copy()for n in G if n.startswith('B_L_Finger0')}
 for f in range(int(a.frame_range[1])+1):
  t=f/sc.render.fps;entry=t/.4;leave=(t-1.2)/.4;reach=min(smooth(entry/.72),1-smooth((leave-.28)/.72));curl=min(smooth((entry-.72)/.28),1-smooth(leave/.28))
  for n,q in idle.items():
   closed=Quaternion(G[n]);opened=Quaternion(best['quaternion'])if n=='B_L_Finger0'else closed;target=opened.slerp(closed,curl);pb=rig.pose.bones[n];pb.rotation_quaternion=q.slerp(target,smooth(reach/.5));pb.keyframe_insert('rotation_quaternion',frame=f)
 bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/{file}.blend'))
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
