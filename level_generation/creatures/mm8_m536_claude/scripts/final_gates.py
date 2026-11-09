"""Half-frame contact, ground-clearance, skin and motion checks on the assembled editable creature."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
me=body.data;co=np.array([v.co[:] for v in me.vertices]);pa=np.array([a.value for a in me.attributes['part'].data]);names={g.index:g.name for g in body.vertex_groups};ew=np.array([e.vertices[:] for e in me.edges]);el=np.linalg.norm(co[ew[:,1]]-co[ew[:,0]],axis=1)
weights=np.array([[sum(g.weight for g in v.groups if names[g.group].startswith('B_'+sd+'_')) for sd in ['L','R']] for v in me.vertices])
def volume(mask):
 bm=bmesh.new();bm.from_mesh(me);attr=bm.verts.layers.int.new('source');bm.verts.ensure_lookup_table()
 for v in bm.verts:v[attr]=v.index
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if not mask[v.index]],context='VERTS')
 boundary=[e for e in bm.edges if e.is_boundary];bmesh.ops.holes_fill(bm,edges=boundary,sides=0);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.verts.index_update();verts=[v[attr] for v in bm.verts];faces=[[v.index for v in f.verts] for f in bm.faces];bm.free();return verts,faces
vols={'torso':volume((pa==0)&(weights.max(1)<.5)),'L':volume((pa==0)&(weights[:,0]>.55)),'R':volume((pa==0)&(weights[:,1]>.55))}
for o in bpy.data.objects:
 if o.type=='MESH':
  for v in o.data.vertices:
   ws=[g.weight for g in v.groups if g.weight>1e-6];assert ws and len(ws)<=4 and abs(sum(ws)-1)<1e-4,(o.name,v.index,ws)
def coords(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();c=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();return c
probes=['B_'+sd+'_'+n for sd in ['L','R'] for n in ['Hand']+[f'Finger{f}{s}' for f in range(5) for s in ['', '1','2']]];report={};violations=[];motion_names=['B_Head','B_L_UpperArm','B_L_Forearm','B_L_Hand','B_R_UpperArm','B_R_Forearm','B_R_Hand'];direction=Vector((.391,.672,.628)).normalized()
for action in bpy.data.actions:
 rig.animation_data.action=action;lo,hi=action.frame_range;mins={n:1e9 for n in ['Body','FlameTail','FlaskRemains']};stretch=[];motion=[];penetration=0.;hits=0
 for frame in sorted(set(np.arange(lo,hi,.5).tolist()+[float(hi)])):
  sc.frame_set(int(frame),subframe=frame%1);c=coords(body);d=np.linalg.norm(c[ew[:,1]]-c[ew[:,0]],axis=1)/np.maximum(el,1e-8);mask=(el>1e-4)&(pa[ew[:,0]]==0)&(pa[ew[:,1]]==0);stretch.append([float(np.percentile(d[mask],99)),float(d[mask].max())]);motion.append([list(rig.pose.bones[n].matrix.to_quaternion()) for n in motion_names])
  for n in mins:
   v=c if n=='Body' else coords(bpy.data.objects[n]);mins[n]=min(mins[n],float(v[:,2].min()))
  if action.name in ['Death','Dead']:continue
  trees={n:BVHTree.FromPolygons(c[ids].tolist(),fs,all_triangles=True) for n,(ids,fs) in vols.items()}
  for n in probes:
   p=rig.pose.bones[n].matrix.translation;side=n.split('_')[1]
   for other in ['torso','R' if side=='L' else 'L']:
    tree=trees[other];near,normal,idx,dist=tree.find_nearest(p)
    if near is None or (p-near).dot(normal)>=-.012:continue
    q=p.copy();crossings=0
    for _ in range(30):
     hit,_,_,length=tree.ray_cast(q,direction)
     if hit is None:break
     crossings+=1;q=hit+direction*.00001
    if crossings%2:
     hits+=1;penetration=max(penetration,dist)
     if len(violations)<40:violations.append({'clip':action.name,'frame':float(frame),'probe':n,'inside':other,'depth_m':dist})
 motion=np.array(motion);dots=np.abs(np.sum(motion[1:]*motion[:-1],axis=2));steps=2*np.arccos(np.clip(dots,-1,1));report[action.name]={'samples':len(motion),'min_z':mins,'stretch_p99_max':np.max(stretch,axis=0).tolist(),'contact_hits':hits,'deepest_contact_m':penetration,'maximum_joint_step_deg':float(np.degrees(steps).max()),'maximum_step_at':[float(np.unravel_index(np.argmax(steps),steps.shape)[0]/2+1),motion_names[np.unravel_index(np.argmax(steps),steps.shape)[1]]],'max_step_change_deg':float(np.degrees(np.abs(np.diff(steps,axis=0))).max()) if len(steps)>1 else 0}
 print(action.name,report[action.name],flush=True)
(P/'review/final_gates.json').write_text(json.dumps({'clips':report,'contact_examples':violations,'method':'Closed posed torso and opposing arm shells; 12 mm contact tolerance, digit/hand joint probes; 60 Hz sampling'},indent=2))
assert all(min(v['min_z'].values())>=-.01 for v in report.values()),'Geometry below floor'
assert all(v['contact_hits']==0 for v in report.values()),'Hand/torso or opposite-arm penetration'
assert all(v['stretch_p99_max'][0]<2.05 and v['stretch_p99_max'][1]<4.5 for v in report.values()),'Stretch gate'
