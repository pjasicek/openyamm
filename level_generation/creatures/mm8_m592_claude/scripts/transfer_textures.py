"""Verify body paint UV correspondence and retain the independently packed head UVs."""
from pathlib import Path
import sys,runpy,bpy,json,numpy as np
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1];tool=P.parent/'mm8_m540_claude/scripts/transfer_uv.py';sys.argv=[str(tool),'--',str(P/'work/rig_reduced.blend'),str(P/'meshy/body_retexture_v1'),str(P/'work/rig_uv.blend')];runpy.run_path(str(tool),run_name='__main__')
body=bpy.data.objects['Body'];me=body.data;polys=[f for f in me.polygons if me.attributes['head'].data[f.index].value];T=np.array([tuple(body.matrix_world@v.co) for v in me.vertices]);ids=sorted({i for f in polys for i in f.vertices});before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy/head_retexture_v1/model_urls_glb.glb'));src=max((o for o in set(bpy.data.objects)-before if o.type=='MESH'),key=lambda o:len(o.data.polygons));S=np.array([tuple(src.matrix_world@v.co) for v in src.data.vertices]);scale=np.ptp(T[ids],axis=0).max()/np.ptp(S,axis=0).max();S=S*scale+(T[ids].min(0)+T[ids].max(0))/2-(S.min(0)+S.max(0))/2*scale;tree=kdtree.KDTree(len(polys))
for i,f in enumerate(polys):tree.insert(Vector(T[list(f.vertices)].mean(0)),i)
tree.balance();worst=0;uvworst=0;seen=set()
for f in src.data.polygons:
 sc=S[list(f.vertices)];best=None
 for _,i,_ in tree.find_n(Vector(sc.mean(0)),12):
  p=polys[i];d=np.linalg.norm(sc[:,None,:]-T[list(p.vertices)][None,:,:],axis=2);corners=d.argmin(1);err=float(d[np.arange(3),corners].max())
  if best is None or err<best[0]:best=err,p,corners
 err,p,corners=best;assert err<1e-5 and p.index not in seen,(f.index,err);seen.add(p.index);worst=max(worst,err)
 for j,k in enumerate(corners):
  a=src.data.uv_layers.active.data[f.loop_indices[j]].uv;b=me.uv_layers['HeadUV'].data[p.loop_indices[k]].uv;uvworst=max(uvworst,(a-b).length)
assert uvworst<1e-4,uvworst
for ob in set(bpy.data.objects)-before:bpy.data.objects.remove(ob,do_unlink=True)
report={'head_faces':len(polys),'returned_faces':len(seen),'max_corner_error_m':worst,'max_uv_error':uvworst,'head_uv':'unchanged'};(P/'review/head_uv_transfer.json').write_text(json.dumps(report,indent=2)+'\n');print('HEAD_UV',report,flush=True)
# UV seam samples for luminance matching at the natural head/neck boundary.
import bmesh
bm=bmesh.new();bm.from_mesh(me);hd=bm.faces.layers.int['head'];bu=bm.loops.layers.uv['UVMap'];hu=bm.loops.layers.uv['HeadUV'];rows=[]
for e in bm.edges:
 if len(e.link_faces)!=2 or e.link_faces[0][hd]==e.link_faces[1][hd]:continue
 b,h=sorted(e.link_faces,key=lambda f:f[hd])
 for t in (0,.25,.5,.75,1):
  row={'pos':list(e.verts[0].co.lerp(e.verts[1].co,t))}
  for name,f,u in [('body',b,bu),('head',h,hu)]:
   ls=[next(l for l in f.loops if l.vert==v) for v in e.verts];centre=sum((l[u].uv for l in f.loops),Vector((0,0)))/len(f.loops);row[name]=list(ls[0][u].uv.lerp(ls[1][u].uv,t).lerp(centre,.025))
  rows.append(row)
bm.free();assert rows;(P/'work/seam_samples.json').write_text(json.dumps(rows)+'\n');bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_uv.blend'))
