"""Correct two measured reduced-mesh contacts at the actual failing poses."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as s
cfg=json.loads((P/'gates.json').read_text());g=s.Glb(P/'export/mm6_jak1.glb');meshes=s.load_meshes(g);report=s.Report(cfg);props=s.load_props(cfg,P,g,report);rows=[]
for level,t,file in [(3,.125,'lod3_reduced01.blend')]:
 m=meshes[level];a=next(a for n,a,lo,hi in g.clips()if n=='Death');pose=g.pose(a,np.array([t]))[0];co=m.posed(pose)
 if level==3:
  surface=s.Surface(m,np.ones(len(m.rest),bool)).build(co);pm=props[0]['meshes'][level];pp=s.transform(pose[g.names['Staff']]@np.linalg.inv(s.C),pm.rest);dist,faces=surface.signed(pp);i=int(np.argmin(dist));hit,n,fi,d=surface.tree.find_nearest(Vector(pp[i]));ids=m.weld_first[surface.faces[fi]];delta=-np.array(n)*(float(-dist[i])+.001);assert np.linalg.norm(delta)<.009
 else:
  m.find_components();cloth=next(m.components==c for c in np.unique(m.components)if .5<m.rest[m.components==c,2].min()<.8 and 1<m.rest[m.components==c,2].max()<1.2 and np.ptp(m.rest[m.components==c,0])>.4);f=m.faces[cloth[m.faces].all(1)];tri=m.rest[f];n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);r=tri.mean(1);r[:,2]=0;r/=np.maximum(np.linalg.norm(r,axis=1)[:,None],1e-12);f=f[(n*r).sum(1)>.25];tree=BVHTree.FromPolygons(co.tolist(),f.tolist());hit,n,fi,d=tree.find_nearest(Vector(co[107]));ids=[107];delta=-np.array(n)*.0015
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/reduction'/file));body=bpy.data.objects['Jackalman'];rig=bpy.data.objects['Rig'];a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc=bpy.context.scene;f=t*sc.render.fps;sc.frame_set(int(f),subframe=float(f-int(f)));names={v.index:v.name for v in body.vertex_groups};me=body.data;rest=np.array([v.co[:]for v in me.vertices]);selected=set()
 for i in ids:
  distance=np.linalg.norm(rest-m.rest[i],axis=1);assert distance.min()<1e-5,(level,i,distance.min());selected.update(np.flatnonzero(distance<1e-5).tolist())
 for i in selected:
  v=me.vertices[i];pairs=[(np.array(rig.pose.bones[names[q.group]].matrix@rig.data.bones[names[q.group]].matrix_local.inverted()),q.weight)for q in v.groups if names[q.group]in rig.pose.bones];matrix=sum(mat*w for mat,w in pairs)/sum(w for mat,w in pairs);v.co+=Vector(np.linalg.solve(matrix[:3,:3],delta))
 me.update();me.normals_split_custom_set([(0,0,0)]*len(me.loops));rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2/reduction'/file));rows.append({'lod':level,'clip':'Death','time':t,'runtime_vertices':list(map(int,ids)),'source_vertices':sorted(selected),'delta_m':delta.tolist()})
(P/'review/round2/reduction/final_contact_corrections_2.json').write_text(json.dumps(rows,indent=2));print(rows,flush=True)
