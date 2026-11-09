"""Import and measure the original Smart Topology body without changing its anatomy."""
from pathlib import Path
import json
import sys
import bpy
import bmesh
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
import common
p=Path(__file__).resolve().parents[1]
source=Path(sys.argv[sys.argv.index('--')+1]).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
assert meshes
for o in bpy.data.objects:o.select_set(o in meshes)
bpy.context.view_layer.objects.active=meshes[0]
if len(meshes)>1:bpy.ops.object.join()
body=bpy.context.object;body.parent=None
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
co=np.array([tuple(v.co) for v in body.data.vertices]);scale=2.1/np.ptp(co[:,2])
body.scale=(scale,)*3
body.location=(-(co[:,0].max()+co[:,0].min())*scale/2,-(co[:,1].max()+co[:,1].min())*scale/2,-co[:,2].min()*scale)
bpy.ops.object.transform_apply(location=True,scale=True)
body.name=body.data.name='Body'
for o in list(bpy.data.objects):
 if o is not body:bpy.data.objects.remove(o,do_unlink=True)
# Label actual connected pieces; geometry is preserved for subsequent anatomy review.
me=body.data;adj=[[] for _ in me.vertices]
for e in me.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
seen=set();pieces=[]
for i in range(len(me.vertices)):
 if i in seen:continue
 stack=[i];part=[]
 while stack:
  v=stack.pop()
  if v in seen:continue
  seen.add(v);part.append(v);stack.extend(adj[v])
 pieces.append(part)
pieces.sort(key=len,reverse=True)
labels=np.zeros(len(me.vertices),dtype=np.int32);report=[]
for i,part in enumerate(pieces):
 labels[part]=i;c=np.array([tuple(me.vertices[v].co) for v in part])
 report.append({'piece':i,'vertices':len(part),'min':c.min(0).tolist(),'max':c.max(0).tolist()})
me.attributes.new('piece','INT','POINT').data.foreach_set('value',labels)
me.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',np.array([tuple(v.co) for v in me.vertices]).ravel())
bm=bmesh.new();bm.from_mesh(me)
stats={'source':str(source),'vertices':len(me.vertices),'triangles':sum(len(f.vertices)-2 for f in me.polygons),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold and not e.is_boundary for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'pieces':report};bm.free()
(p/'review/geometry').mkdir(parents=True,exist_ok=True)
(p/'review/geometry/static_inventory.json').write_text(json.dumps(stats,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/imported.blend'))
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/geometry/body'),1.05,2.5,views=('front','left','back','right','three_quarter'),resolution=(640,960))
common.render_views(str(p/'review/geometry/head'),1.83,0.72,views=('front','left','three_quarter'),resolution=(640,640))
for side,sign in [('left',1),('right',-1)]:
 co=np.array([tuple(v.co) for v in me.vertices]);band=co[(co[:,0]*sign>0.45)&(co[:,2]<1.3)&(co[:,2]>0.6)]
 if len(band):
  c=band.mean(0);common.render_views(str(p/'review/geometry'/('hand_'+side)),float(c[2]),0.55,views=('front','back'),resolution=(640,640),target=(float(c[0]),float(c[1])))
print(json.dumps({k:v for k,v in stats.items() if k!='pieces'}));print('PIECES',report[:12])
