import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_finished.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene;me=body.data
co=np.array([tuple(v.co)for v in me.vertices]);part=np.array([a.value for a in me.attributes['piece'].data]);cloth=np.array([a.value for a in me.attributes['cloth'].data]);edges=np.array([e.vertices[:]for e in me.edges]);lengths=np.linalg.norm(co[edges[:,1]]-co[edges[:,0]],axis=1);valid=lengths>.002
# Continuous skirt shell, excluding decorative feather islands. Open hem candidates are excluded geometrically.
faces=[]
for f in me.polygons:
 ids=list(f.vertices)
 if all(part[i]==0 and (cloth[i] or (abs(co[i,0])<.23 and .99<co[i,2]<1.32)) for i in ids):
  pts=co[ids];n=np.cross(pts[1]-pts[0],pts[2]-pts[0]);rad=pts.mean(0)*np.array([1,1,0]);faces.append(tuple(ids if np.dot(n,rad)>0 else ids[::-1]))
centres=np.array([co[list(f)].mean(0)for f in faces]);legids=np.where((part==1)&(co[:,2]>.45))[0];report={}
for role in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];worst={'mm':0};ratios={};maxedge={}
 for frame in np.arange(a.frame_range[0],a.frame_range[1]+.001,sc.render.fps/48):
  sc.frame_set(int(frame),subframe=float(frame%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();c=np.array([tuple(v.co)for v in mesh.vertices]);ev.to_mesh_clear();tree=BVHTree.FromPolygons([Vector(v)for v in c],faces)
  for i in legids:
   hit,n,j,d=tree.find_nearest(Vector(c[i]));signed=(Vector(c[i])-hit).dot(n)
   if signed<=0 or centres[j,2]<.605:continue
   if signed*1000>worst['mm']:worst={'mm':signed*1000,'seconds':float(frame/sc.render.fps),'vertex':int(i),'surface_face':int(j),'point':c[i].tolist(),'surface':list(hit),'rest_surface_z':float(centres[j,2])}
  lens=np.linalg.norm(c[edges[:,1]]-c[edges[:,0]],axis=1);r=lens/np.maximum(lengths,1e-9)
  for p in set(part.tolist()):
   mask=(part[edges[:,0]]==p)&valid
   if mask.any():
    ix=np.where(mask)[0][np.argmax(r[mask])]
    if r[ix]>ratios.get(p,0):ratios[p]=float(r[ix]);maxedge[p]={'vertices':edges[ix].tolist(),'seconds':float(frame/sc.render.fps),'rest_m':float(lengths[ix]),'posed_m':float(lens[ix])}
 report[role]={'cloth_penetration':worst,'edge_ratio_by_piece':ratios,'worst_edges':maxedge};print(role,worst,'edges',sorted(ratios.items(),key=lambda kv:-kv[1])[:6],flush=True)
(P/'review/cloth/finished_geometry_audit.json').write_text(json.dumps(report,indent=2));assert len(report)==9
