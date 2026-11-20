import bpy,numpy as np,json,os
from pathlib import Path
from mathutils import Vector,geometry
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/os.environ.get('GATE_BLEND','work/textured.blend')));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=b.data;sc=bpy.context.scene;pv=np.array([v.value for v in me.attributes['piece'].data]);co=np.array([v.co[:] for v in me.vertices]);me.calc_loop_triangles();tri=[tuple(t.vertices) for t in me.loop_triangles]
sets={}
for sd,sign in [('L',1),('R',-1)]:
 elbow=np.array(r.data.bones[f'B_{sd}_Forearm'].head_local);axis=np.array(r.data.bones[f'B_{sd}_Hand'].head_local)-elbow;axis/=np.linalg.norm(axis);t=(co-elbow)@axis
 ids=(pv==0)&(co[:,0]*sign>.24)&(co[:,2]>1.0);end=float(np.percentile(t[ids],96));wall=[f for f in tri if all(ids[i] and t[i]<end-.008 for i in f)];skin=[f for f in tri if all(pv[i]==(2 if sd=='L' else 3) for i in f)];sets[sd+'_sleeve']=(wall,skin)
sets['coat']=([f for f in tri if all(pv[i]==0 and abs(co[i,0])<.25 and .815<co[i,2]<1.12 for i in f)],[f for f in tri if all(pv[i] in [1,5,6,10,11] for i in f)])
def intersections(a,z):
 out=[]
 for T,U in [(a,z),(z,a)]:
  for x,y in zip(T,T[1:]+T[:1]):
   d=y-x
   if d.length<1e-8:continue
   hit=geometry.intersect_ray_tri(*U,d.normalized(),x,True)
   if hit is not None and .00001<(hit-x).dot(d.normalized())<d.length-.00001:out.append(hit)
 return out
report={}
for act in bpy.data.actions:
 if not act.use_fake_user:continue
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];row={k:{'crossing_pairs':0,'worst_penetration_mm':0.} for k in sets};count=0
 for f in sorted(set(list(np.arange(0,float(act.frame_range[1])+.00001,30/48))+[float(act.frame_range[1])])):
  sc.frame_set(int(f),subframe=f%1);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();P=[v.co.copy() for v in em.vertices];ev.to_mesh_clear();count+=1
  for name,(cloth,skin) in sets.items():
   ct=BVHTree.FromPolygons(P,cloth,all_triangles=True);st=BVHTree.FromPolygons(P,skin,all_triangles=True)
   for ci,si in ct.overlap(st):
    C=[P[i] for i in cloth[ci]];S=[P[i] for i in skin[si]]
    if not intersections(C,S):continue
    # Signed distance is measured against the real cloth wall, after exact edge/triangle crossing confirms it.
    normal=(C[1]-C[0]).cross(C[2]-C[0]).normalized();ds=[(x-C[0]).dot(normal) for x in S];depth=max(0.,-min(ds))*1000
    if depth<=.1:continue
    row[name]['crossing_pairs']+=1
    if depth>row[name]['worst_penetration_mm']:row[name].update(worst_penetration_mm=float(depth),frame=float(f),cloth_triangle=cloth[ci],skin_triangle=skin[si])
 row['samples_48hz']=count;row['pass']=all(row[k]['worst_penetration_mm']<=2. for k in sets);report[act.name]=row;print('CLOTH_SURFACE',act.name,row,flush=True)
(p/os.environ.get('CLOTH_REPORT','review/cloth_surface_gate.json')).write_text(json.dumps({'method':'48 Hz exact surface crossings, BVH broadphase then finite-edge/triangle intersections, signed endpoint distance to actual cloth walls; opening caps and below-hem exits excluded. This open coat needs surface crossings rather than whole-robe containment; proximal forearms correctly remain inside sleeve volumes.','clips':report},indent=2))
