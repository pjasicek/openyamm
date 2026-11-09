import bpy,sys,json
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
p=Path(__file__).resolve().parents[1];src,job,out,layer=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=src);r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];me=b.data;r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(Path(job)/'model_urls_glb.glb'));o=max((o for o in bpy.data.objects if o not in before and o.type=='MESH'),key=lambda o:len(o.data.polygons))
S=np.array([tuple(o.matrix_world@v.co) for v in o.data.vertices]);T=np.array([v.co[:] for v in me.vertices]);polys=[f for f in me.polygons if layer=='UVMap' or me.attributes['head'].data[f.index].value]
sub=T if layer=='UVMap' else T[sorted({v for f in polys for v in f.vertices})];scale=np.ptp(sub,axis=0).max()/np.ptp(S,axis=0).max();S=S*scale+(sub.min(0)+sub.max(0))/2-(S.min(0)+S.max(0))*scale/2
tr=kdtree.KDTree(len(o.data.polygons))
for f in o.data.polygons:tr.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
tr.balance();uv=me.uv_layers[layer].data;su=o.data.uv_layers.active.data;matches=[];corner=0.;centroid=0.;bad=[]
for f in polys:
 _,j,d=tr.find(Vector(T[list(f.vertices)].mean(0)));g=o.data.polygons[j];matches.append(j);centroid=max(centroid,d)
 for li,vi in zip(f.loop_indices,f.vertices):
  k=int(np.argmin(np.linalg.norm(S[list(g.vertices)]-T[vi],axis=1)));e=float(np.linalg.norm(S[g.vertices[k]]-T[vi]));
  if d>.0001:
   assert me.attributes['head'].data[f.index].value and f.area<.00004 and all(1.43<T[v,2]<1.48 and -.065<T[v,0]<-.04 for v in f.vertices),('unexpected geometry change',f.index,d)
   aa,bb,cc=S[list(g.vertices)];bc=np.linalg.lstsq(np.column_stack([bb-aa,cc-aa]),T[vi]-aa,rcond=None)[0];ua,ub,uc=[np.array(su[x].uv) for x in g.loop_indices];uv[li].uv=ua+bc[0]*(ub-ua)+bc[1]*(uc-ua)
  else:corner=max(corner,e);uv[li].uv=su[g.loop_indices[k]].uv
 if d>.0001 or len(f.vertices)!=len(g.vertices):bad.append([f.index,j,d])
report={'ours':len(polys),'returned':len(o.data.polygons),'unique_matches':len(set(matches)),'corner_max_mm':corner*1000,'centroid_max_mm':centroid*1000,'bad':bad};(p/f'work/uv_transfer_{layer}.json').write_text(json.dumps(report,indent=2));print('UV_TRANSFER',report,flush=True)
assert corner<.0001 and len(set(matches))>=len(polys)-len(bad) and (not bad or len(bad)<=4),'Retexture geometry correspondence failed'
for o in list(bpy.data.objects):
 if o not in before:bpy.data.objects.remove(o,do_unlink=True)
me.uv_layers.active=me.uv_layers['UVMap'];bpy.ops.wm.save_as_mainfile(filepath=out)
