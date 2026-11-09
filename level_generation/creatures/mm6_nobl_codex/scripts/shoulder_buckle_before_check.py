"""Check shipped shoulder coverage and rigid belt/medallion attachment through all clips."""
import bpy,numpy as np,json
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];out=p/'review/shoulder_buckle_20261011'
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v13.blend'));o=bpy.data.objects['Body']
pv=np.zeros(len(o.data.vertices),np.int32);o.data.attributes['piece'].data.foreach_get('value',pv)
co=np.array([v.co[:] for v in o.data.vertices]);kd=KDTree(len(co))
for i,c in enumerate(co):kd.insert(Vector(c),i)
kd.balance()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/'review/shoulder_buckle_20261011/before/mm6_nobl.glb'))
r=next(o for o in bpy.data.objects if o.type=='ARMATURE');o=next(o for o in bpy.data.objects if o.type=='MESH' and o.parent==r);sc=bpy.context.scene
mapping=np.array([kd.find(o.matrix_world@v.co)[1] for v in o.data.vertices]);rest=co[mapping];pieces=pv[mapping]
probes=np.flatnonzero((pieces==1)&(rest[:,2]>1.34)&(rest[:,2]<1.405)&(abs(rest[:,0])>.115)&(abs(rest[:,0])<.215)&(rest[:,1]<-.055))
probes=np.array([next(i for i in probes if mapping[i]==v) for v in np.unique(mapping[probes])])
cf=[list(f.vertices) for f in o.data.polygons if all(pieces[i]==0 for i in f.vertices) and rest[list(f.vertices),2].mean()>1.2]
belt=np.flatnonzero(np.isin(pieces,[10,11,18]));pelvis=r.pose.bones['B_Pelvis'];chest=r.pose.bones['B_Spine2']
report={};maximum_attachment_error=0
for a in [bpy.data.actions['Walking']]:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows=[]
 for f in np.arange(a.frame_range[0],a.frame_range[1]+1e-5,sc.render.fps/120):
  sc.frame_set(int(f),subframe=float(f%1));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();P=[o.matrix_world@v.co for v in me.vertices]
  tree=BVHTree.FromPolygons(P,cf);D=(chest.matrix@chest.bone.matrix_local.inverted()).to_3x3();direction=(D@Vector((0,-1,0))).normalized()
  gaps=[];misses=0
  for i in probes:
   start=P[int(i)]-direction*.15;t=0;hits=[]
   for _ in range(10):
    hit,n,j,d=tree.ray_cast(start+direction*t,direction,.30-t)
    if hit is None:break
    t+=d;hits.append(t);t+=.0001
   if hits:gaps.append((max(hits)-.15)*1000)
   else:misses+=1
  D=pelvis.matrix@pelvis.bone.matrix_local.inverted();I=D.inverted()
  err=max((I@P[int(i)]-Vector(rest[i])).length for i in belt)*1000;maximum_attachment_error=max(maximum_attachment_error,err)
  rows.append({'seconds':float(f/sc.render.fps),'minimum_shoulder_gap_mm':min(gaps) if gaps else None,'misses':misses,'attachment_error_mm':err})
  ev.to_mesh_clear()
 report[a.name]=rows
 print('SHOULDER_GATE',a.name,'gap',min(x['minimum_shoulder_gap_mm'] for x in rows if x['minimum_shoulder_gap_mm'] is not None),'misses',max(x['misses'] for x in rows),'attachment_mm',max(x['attachment_error_mm'] for x in rows),flush=True)
(out/'before_export_gate.json').write_text(json.dumps({'probe_source_vertices':mapping[probes].tolist(),'maximum_attachment_error_mm':maximum_attachment_error,'clips':report},indent=1))
