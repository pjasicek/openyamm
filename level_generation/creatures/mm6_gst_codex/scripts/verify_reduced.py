"""Dense half-frame anatomical and contact checks on the selected ghost animation master."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;C=np.array([v.co[:] for v in me.vertices]);PA=np.array([a.value for a in me.attributes['part'].data]);E=np.array([e.vertices[:] for e in me.edges]);EL=np.linalg.norm(C[E[:,1]]-C[E[:,0]],axis=1);hands=np.isin(PA,[1,3,4,5,6,8,9,11,12,15]);fingers=np.isin(PA,[1,3,5,8,9,11,12,15]);mask=hands[E[:,0]]&hands[E[:,1]]&(EL>.001);cloth_faces=[list(f.vertices) for f in me.polygons if all(PA[v]==0 for v in f.vertices)];D=json.loads((P/'work/rig.json').read_text());out={};sc=bpy.context.scene
for a in bpy.data.actions:
 r.animation_data.action=a;lo,hi=a.frame_range;maxstretch=0;minfloor=1e9;maxstep=0.;worst=None;prev=None;minclear=1e9;rootfirst=None;last=None
 for frame in np.arange(lo,hi+.001,.5):
  sc.frame_set(int(frame),subframe=frame%1);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();c=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();minfloor=min(minfloor,float(c[:,2].min()));maxstretch=max(maxstretch,float((np.linalg.norm(c[E[mask,1]]-c[E[mask,0]],axis=1)/EL[mask]).max()));current={n:r.pose.bones[n].matrix.to_quaternion() for n in D['bones']}
  if prev:
   step,bn=max((math.degrees(2*math.acos(min(1,abs(q.dot(prev[n]))))),n) for n,q in current.items())
   if step>maxstep:maxstep=step;worst={'bone':bn,'time_s':(frame-lo)/60}
  prev=current
  if a.name in ['Attack','Standing','Walking','Running','Hit','Fidget'] and int(frame*2)%4==0:
   tree=BVHTree.FromPolygons([Vector(v) for v in c],cloth_faces,all_triangles=True)
   # Open ragged cloth has no reliable interior sign; report exact surface distances and visually review near contacts.
   for v in c[np.where(fingers)[0][::3]]:minclear=min(minclear,tree.find_nearest(Vector(v))[3])
  if rootfirst is None:rootfirst=c.copy()
  last=c
 out[a.name]={'samples':int((hi-lo)*2+1),'half_frame_hand_edge_stretch_max':maxstretch,'min_z_m':minfloor,'max_world_rotation_half_frame_deg':maxstep,'worst_rotation':worst,'finger_cloth_min_distance_m':None if minclear==1e9 else minclear,'endpoint_surface_delta_m':float(np.linalg.norm(last-rootfirst,axis=1).max())}
 print(a.name,out[a.name],flush=True)
 assert minfloor>-.001 and maxstretch<1.65,(a.name,minfloor,maxstretch)
 assert maxstep<30,(a.name,maxstep)
(P/'review/animation_dense_reduced_audit.json').write_text(json.dumps(out,indent=2))
