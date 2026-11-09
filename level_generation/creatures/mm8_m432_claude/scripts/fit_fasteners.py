"""Fit each rigid fastener to the blended weights of its nearest underlying surface."""
import bpy,sys,json
import numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_assembled.blend'));o=bpy.data.objects['Body'];me=o.data
co=np.array([v.co[:] for v in me.vertices]);piece=np.array([x.value for x in me.attributes['piece'].data]);names=[g.name for g in o.vertex_groups];w=np.zeros((len(co),len(names)))
for v in me.vertices:
 for e in v.groups:w[v.index,e.group]=e.weight
host=np.where(piece<12)[0];tree=KDTree(len(host))
for i in host:tree.insert(co[i],int(i))
tree.balance();report={}
faces=[tuple(f.vertices) for f in me.polygons if all(piece[i]<12 for i in f.vertices)];surface=BVHTree.FromPolygons([v.co for v in me.vertices],faces)
for part in sorted(set(piece)):
 if part<12:continue
 ids=np.where(piece==part)[0];centre=co[ids].mean(0);point,normal,face,distance=surface.find_nearest(Vector(centre));local=co[ids]-centre
 values,vectors=np.linalg.eigh(local.T@local);axis=Vector(vectors[:,0]);direction=Vector(centre)-point
 if axis.dot(direction)<0:axis=-axis
 if values[0]<values[1]*.4:local=np.array([axis.rotation_difference(normal)@Vector(v) for v in local])
 normal_array=np.array(normal);bottom=float((local@normal_array).min());target=np.array(point)+normal_array*(.0005-bottom);co[ids]=local+target
 for i in ids:me.vertices[int(i)].co=co[i]
 near=[tree.find(co[i]) for i in ids];weights=w[[j for _,j,_ in near]].mean(0);weights/=weights.sum();order=np.argsort(weights)[-4:];weights[np.setdiff1d(np.arange(len(weights)),order)]=0;weights/=weights.sum()
 for g in o.vertex_groups:g.remove(ids.tolist())
 for j in np.where(weights>1e-6)[0]:o.vertex_groups[int(j)].add(ids.tolist(),float(weights[j]),'REPLACE')
 report[int(part)]={'rest_translation_mm':float(np.linalg.norm(target-centre)*1000),'gap_mm':float(np.mean([d for _,_,d in near])*1000),'weights':{names[j]:float(weights[j]) for j in np.where(weights>1e-6)[0]}}
assert len(report)>20
(P/'work/fastener_fit.json').write_text(json.dumps(report,indent=1));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_hardware.blend'));print('FASTENERS',len(report))
