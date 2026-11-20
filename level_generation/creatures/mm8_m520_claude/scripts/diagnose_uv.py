"""Carry Meshy's UVs by original polygon corners; match its triangulation while preserving rig weights and attributes."""
import bpy,bmesh,sys,os,numpy as np
from mathutils import Vector,kdtree
args=sys.argv[sys.argv.index('--')+1:];blend,job,out=args[:3];layer=args[3] if len(args)>3 else 'UVMap'
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(os.path.abspath(job),'model_urls_glb.glb'))
src=max((o for o in bpy.data.objects if o not in before and o.type=='MESH'),key=lambda o:len(o.data.polygons))
S=np.array([tuple(src.matrix_world@v.co) for v in src.data.vertices]);T=np.array([tuple(body.matrix_world@v.co) for v in me.vertices])
polys=[p for p in me.polygons if layer=='UVMap' or me.attributes['head'].data[p.index].value]
Tsub=T if layer=='UVMap' else T[sorted({v for p in polys for v in p.vertices})]
scale=(Tsub.max(0)-Tsub.min(0)).max()/(S.max(0)-S.min(0)).max();S=S*scale+((Tsub.max(0)+Tsub.min(0))/2-(S.max(0)+S.min(0))/2*scale)
tree=kdtree.KDTree(len(T))
for i,v in enumerate(T):tree.insert(v,i)
tree.balance();hits=[tree.find(v) for v in S];ds=np.array([h[2] for h in hits]);print('COORD',len(S),len(T),'worst',ds.max(),'quantiles',np.quantile(ds,[.5,.99,.999]),'changed',(ds>1e-5).sum(),flush=True)
for i in np.where(ds>1e-5)[0][:30]:print('CHANGED',i,S[i],hits[i][1:],T[hits[i][1]],flush=True)
sp=src.data.polygons[16341];print('FACE',list(sp.vertices),[S[i].tolist() for i in sp.vertices],flush=True)
print('CLOSEST',[(i,hits[i][1],hits[i][2]) for i in sp.vertices],flush=True)
print('COUNTS',len(src.data.polygons),sum(len(f.vertices)-2 for f in polys),flush=True)
