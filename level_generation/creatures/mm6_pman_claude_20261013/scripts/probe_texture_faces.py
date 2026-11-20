from pathlib import Path
import bpy,numpy as np,json
from mathutils import Vector
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/texture_ready.blend'));body=bpy.data.objects['Body'];me=body.data
T=np.array([v.co[:] for v in me.vertices]);flags=np.array([e.value for e in me.attributes['head'].data])
for job in ['body_texture_v1','head_texture_v1']:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy'/job/'model_urls_glb.glb'));new=set(bpy.data.objects)-before
 src=next(o for o in new if o.type=='MESH');S=np.array([tuple(src.matrix_world@v.co) for v in src.data.vertices])
 polys=[f for f in me.polygons if job.startswith('body') or flags[f.index]];sub=T[sorted({i for f in polys for i in f.vertices})]
 k=np.ptp(sub,axis=0).mean()/np.ptp(S,axis=0).mean();S=S*k+(sub.min(0)+sub.max(0))/2-(S.min(0)+S.max(0))/2*k
 tree=KDTree(len(src.data.polygons))
 for f in src.data.polygons:tree.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
 tree.balance();used={};bad=[]
 for f in polys:
  _,i,d=tree.find(Vector(T[list(f.vertices)].mean(0)));used.setdefault(i,[]).append(f.index)
  sf=src.data.polygons[i];dist=np.linalg.norm(T[list(f.vertices)][:,None,:]-S[list(sf.vertices)][None,:,:],axis=2)
  if d>.0001 or dist.min(1).max()>.0001:bad.append({'face':f.index,'src':i,'area':f.area,'piece':me.attributes['piece'].data[f.vertices[0]].value,'positions':T[list(f.vertices)].tolist(),'d':d,'corner_error':float(dist.min(1).max())})
 print(job,'counts',len(polys),len(src.data.polygons),'BAD',json.dumps(bad),'DUPLICATE',json.dumps({k:v for k,v in used.items() if len(v)>1}))
 for o in new:bpy.data.objects.remove(o,do_unlink=True)
