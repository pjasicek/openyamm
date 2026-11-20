"""Verify one-to-one face/corner correspondence before copying the returned Meshy UVs."""
import bpy,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/texture_ready.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
T=np.array([tuple(body.matrix_world@v.co) for v in me.vertices])
head=np.array([x.value for x in me.attributes['head'].data],bool)
reports={}
for job,layer in [('body_texture_v1','UVMap'),('head_texture_v1','HeadUV')]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy'/job/'model_urls_glb.glb'))
 imported=set(bpy.data.objects)-before;src=max((o for o in imported if o.type=='MESH'),key=lambda o:len(o.data.polygons))
 polys=list(me.polygons) if layer=='UVMap' else [f for f in me.polygons if head[f.index]]
 S=np.array([tuple(src.matrix_world@v.co) for v in src.data.vertices]);sub=T[sorted({i for f in polys for i in f.vertices})]
 scale=np.ptp(sub,axis=0).max()/np.ptp(S,axis=0).max();S=S*scale+(sub.min(0)+sub.max(0))/2-(S.min(0)+S.max(0))/2*scale
 tree=KDTree(len(src.data.polygons))
 for f in src.data.polygons:tree.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
 tree.balance();used=set();bad=[]
 for f in polys:
  _,i,d=tree.find(Vector(T[list(f.vertices)].mean(0)));sf=src.data.polygons[i];dist=np.linalg.norm(T[list(f.vertices)][:,None,:]-S[list(sf.vertices)][None,:,:],axis=2)
  if i in used or d>.0001 or dist.min(1).max()>.0001:bad.append(dict(face=f.index,area=f.area,center=list(f.center),head=bool(head[f.index]),piece=[me.attributes['piece'].data[v].value for v in f.vertices],vertices=list(f.vertices),coords=[list(me.vertices[v].co) for v in f.vertices],normal=list(f.normal),error=d,corner_error=float(dist.min(1).max()),duplicate=i in used))
  used.add(i)
 print('CORRESPONDENCE',job,'face counts',len(polys),len(src.data.polygons),'bad',json.dumps(bad),flush=True)
 for o in imported:bpy.data.objects.remove(o,do_unlink=True)
