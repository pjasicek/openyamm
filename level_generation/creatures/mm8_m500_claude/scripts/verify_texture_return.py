"""Compare every returned texture triangle against the upload, including UV orientation."""
from pathlib import Path
import bpy,json,numpy as np
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
def load(path):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));result=[]
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active
  for t in me.loop_triangles:
   c=np.array([o.matrix_world@me.vertices[v].co for v in t.vertices]);u=np.array([uv.data[l].uv[:] for l in t.loops]);result.append((c,u))
 return result
report={}
for label in ['body','head']:
 a=load(P/'texturing'/f'm500_{label}_upload.glb');b=load(P/'meshy'/f'{label}_retexture_v1/model_urls_glb.glb');assert len(a)==len(b)
 ac=np.array([p for p,u in a]);bc=np.array([p for p,u in b]);scale=np.ptp(ac.reshape(-1,3),axis=0).max()/np.ptp(bc.reshape(-1,3),axis=0).max();offset=(ac.max((0,1))+ac.min((0,1)))/2-(bc.max((0,1))+bc.min((0,1)))/2*scale;bc=bc*scale+offset
 tree=KDTree(len(b))
 for i,p in enumerate(bc):tree.insert(p.mean(0),i)
 tree.balance();error=0;surface=0;matches=set()
 for pos,uv in a:
  _,i,d=tree.find(pos.mean(0));matches.add(i);other=bc[i];ou=b[i][1];order=np.linalg.norm(pos[:,None]-other,axis=2).argmin(1);error=max(error,float(abs(uv-ou[order]).max()));surface=max(surface,float(np.linalg.norm(pos-other[order],axis=1).max()))
 assert surface<1e-5 and error<1e-5,(label,surface,error)
 report[label]={'triangles':len(a),'matched_triangles':len(matches),'uniform_scale':float(scale),'offset':offset.tolist(),'maximum_geometry_error':surface,'max_uv_error':error}
(P/'work/texture_return_parity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
