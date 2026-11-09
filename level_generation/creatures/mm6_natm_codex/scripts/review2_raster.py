import bpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));me=bpy.data.objects['Body'].data;me.calc_loop_triangles();pv=np.array([p.value for p in me.attributes['piece'].data]);co=np.array([v.co[:]for v in me.vertices]);uv=me.uv_layers.active.data
 for material in range(len(me.materials)):
  mat=me.materials[material];bs=mat.node_tree.nodes.get('Principled BSDF');im=bs.inputs['Base Color'].links[0].from_node.image;N=im.size[0];piece=np.full((N,N),-1,np.int16);pos=np.zeros((N,N,3),np.float32)
  for tri in me.loop_triangles:
   if tri.material_index!=material:continue
   V=list(tri.vertices);U=np.array([uv[l].uv[:]for l in tri.loops])*N;lo=np.maximum(0,np.floor(U.min(0)).astype(int));hi=np.minimum(N-1,np.ceil(U.max(0)).astype(int));xs,ys=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);a,b,c=U;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
   if abs(den)<1e-12:continue
   w0=((b[1]-c[1])*(xs-c[0])+(c[0]-b[0])*(ys-c[1]))/den;w1=((c[1]-a[1])*(xs-c[0])+(a[0]-c[0])*(ys-c[1]))/den;w2=1-w0-w1;m=(w0>=0)&(w1>=0)&(w2>=0);ix=(xs[m]-.5).astype(int);iy=(N-.5-ys[m]).astype(int);piece[iy,ix]=pv[V[0]];pos[iy,ix]=w0[m,None]*co[V[0]]+w1[m,None]*co[V[1]]+w2[m,None]*co[V[2]]
  np.savez_compressed(P/f'work/round2_raster_{level}_{material}.npz',piece=piece,pos=pos);print('RASTER',level,material,N,int((piece==0).sum()),flush=True)
