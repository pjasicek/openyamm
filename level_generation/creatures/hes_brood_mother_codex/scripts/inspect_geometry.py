import bpy, json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/brood_mother_geometry_v2/model_urls_glb.glb'))
for o in bpy.context.scene.objects:
 if o.type!='MESH': continue
 me=o.data
 co=np.array([tuple(o.matrix_world@v.co) for v in me.vertices])
 print('MESH',o.name,'verts',len(co),'triangles',sum(len(f.vertices)-2 for f in me.polygons),'bounds',co.min(0),co.max(0),'matrix',o.matrix_world)
 print('UV',len(me.uv_layers),'materials',[m.name for m in me.materials])
 adj=[[] for v in me.vertices]
 for e in me.edges:
  a,b=e.vertices;adj[a].append(b);adj[b].append(a)
 seen=set();pieces=[]
 for i in range(len(co)):
  if i in seen: continue
  part=[];stack=[i];seen.add(i)
  while stack:
   k=stack.pop();part.append(k)
   for j in adj[k]:
    if j not in seen:seen.add(j);stack.append(j)
  pieces.append(part)
 print('PIECES',len(pieces),[(len(part),co[part].min(0).tolist(),co[part].max(0).tolist()) for part in sorted(pieces,key=lambda p:-len(p))[:20]])
 (P/'work').mkdir(exist_ok=True)
 np.savez(P/'work/raw_mesh.npz',vertices=co,faces=np.array([tuple(f.vertices) for f in me.polygons]))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/raw_geometry.blend'))
