"""Dense subframe rotation, shaft/body intersection and skin deformation checks."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;C=np.array([v.co[:] for v in me.vertices]);PA=np.array([a.value for a in me.attributes['part'].data]);E=np.array([e.vertices[:] for e in me.edges]);EL=np.linalg.norm(C[E[:,1]]-C[E[:,0]],axis=1);hands=np.isin(PA,[1,6]);mask=hands[E[:,0]]&hands[E[:,1]]&(EL>.002);faces=[tuple(f.vertices) for f in me.polygons if PA[f.vertices[0]] not in [6,10]];D=json.loads((P/'work/rig.json').read_text());out={};sc=bpy.context.scene
for a in bpy.data.actions:
 r.animation_data.action=a;lo,hi=a.frame_range;maxstretch=0.;minfloor=1e9;maxstep=0.;worst=None;prev=None;hits=[];first=None;growth=0
 for frame in np.arange(lo,hi+.001,.5):
  sc.frame_set(int(frame),subframe=frame%1);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();c=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();minfloor=min(minfloor,float(c[:,2].min()));lens=np.linalg.norm(c[E[mask,1]]-c[E[mask,0]],axis=1);maxstretch=max(maxstretch,float((lens/EL[mask]).max()));growth=max(growth,float((lens-EL[mask]).max()));current={n:r.pose.bones[n].matrix.to_quaternion() for n in D['bones']}
  if prev:
   step,bn=max((math.degrees(2*math.acos(min(1,abs(q.dot(prev[n]))))),n) for n,q in current.items())
   if step>maxstep:maxstep=step;worst={'bone':bn,'time_s':(frame-lo)/60}
  prev=current
  if int(frame*2)%2==0 and a.name not in ['Death','Dead']:
   tree=BVHTree.FromPolygons([Vector(v) for v in c],faces);tm=r.pose.bones['Trident'].matrix;origin=tm.translation;axis=tm.to_3x3()@Vector((0,1,0));offsets=[Vector(),tm.to_3x3()@Vector((.013,0,0)),tm.to_3x3()@Vector((-.013,0,0)),tm.to_3x3()@Vector((0,0,.013)),tm.to_3x3()@Vector((0,0,-.013))];casts=[tree.ray_cast(origin-axis*.83+offset,axis,2.40) for offset in offsets];h=next((c for c in casts if c[0] is not None),casts[0])
   if h[0] is not None:hits.append({'time_s':(frame-lo)/60,'position':list(h[0])})
  if first is None:first=c.copy()
 out[a.name]={'samples':int((hi-lo)*2+1),'half_frame_hand_edge_stretch_max':maxstretch,'hand_edge_growth_max_m':growth,'min_z_m':minfloor,'max_world_rotation_half_frame_deg':maxstep,'worst_rotation':worst,'shaft_body_intersections':hits,'endpoint_surface_delta_m':float(np.linalg.norm(c-first,axis=1).max())};print(a.name,out[a.name],flush=True)
(P/'review/reduced_dense_audit.json').write_text(json.dumps(out,indent=2))
assert all(v['max_world_rotation_half_frame_deg']<(12 if n in ('Attack','Cast') else 25) for n,v in out.items()),'Rotation continuity'
assert all(not v['shaft_body_intersections'] for v in out.values()),'Shaft/body intersection'
assert all(v['half_frame_hand_edge_stretch_max']<4.5 for v in out.values()),'Hand skin stretch'
assert all(v['min_z_m']>0 for n,v in out.items() if n not in ['Death','Dead']),'Floor contact'
