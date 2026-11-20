import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));C.reset();C.activate('Standing',0);ob=bpy.data.objects['Body'];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());pv=[v.value for v in ob.data.attributes['piece'].data]
for px,py in [(640,350),(648,357),(630,353),(483,475),(483,489),(590,486),(231,540),(705,512),(710,495)]:
 p=Vector(((px-500)*.95/1000,-5,1.32+(425-py)*.95/1000));hit,loc,n,idx=ev.ray_cast(p,Vector((0,1,0)))
 if hit:
  f=ob.data.polygons[idx];print('PICK',px,py,'face',idx,'piece',[pv[i]for i in f.vertices],'point',list(loc),'rest',[list(ob.data.vertices[i].co)for i in f.vertices],flush=True)

for idx in [2806,2758,2960,496,4140]:
 f=ob.data.polygons[idx];uv=np.mean([ob.data.uv_layers.active.data[l].uv[:]for l in f.loop_indices],axis=0);mat=f.material_index;raster=np.load(P/f'work/round2_raster_0_{mat}.npz');N=raster['piece'].shape[0];x,y=int(uv[0]*N),int((1-uv[1])*N);print('RAW_UV',idx,mat,uv.tolist(),'piece',int(raster['piece'][y,x]),'pos',raster['pos'][y,x].tolist(),flush=True)
