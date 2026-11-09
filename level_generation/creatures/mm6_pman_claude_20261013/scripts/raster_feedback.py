import bpy,json,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
body=bpy.data.objects['Body'];me=body.data
T=np.array([v.co[:] for v in me.vertices]);head=np.array([v.value for v in me.attributes['head'].data],bool);reports={'UVMap':{},'HeadUV':{}}
# Exact raster interior tests; adjacent triangles sharing an edge do not count as overlap.
for layer in ['UVMap','HeadUV']:
 N=1024;want=layer=='HeadUV';hits=np.zeros((N,N),np.uint16);pos=np.zeros((N,N,3),np.float32);density={};degenerate=0;piece_map=np.full((N,N),-1,np.int16);pieces=np.array([v.value for v in me.attributes['piece'].data])
 for f in me.polygons:
  if bool(head[f.index])!=want:continue
  uv=np.array([tuple(me.uv_layers[layer].data[i].uv) for i in f.loop_indices]);assert np.isfinite(uv).all() and uv.min()>-1e-5 and uv.max()<1.00001
  a,b,c=uv*N;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-10:degenerate+=1;continue
  area=abs(den)/2;names={g.index:g.name for g in body.vertex_groups};weights={}
  for vi in f.vertices:
   for g in me.vertices[vi].groups:weights[g.group]=weights.get(g.group,0)+g.weight
  group=names[max(weights,key=weights.get)];density.setdefault(group,[]).append(math.sqrt(area/max(f.area,1e-12)))
  x0,y0=np.maximum(np.floor(uv.min(0)*N).astype(int),0);x1,y1=np.minimum(np.ceil(uv.max(0)*N).astype(int),N-1)
  if x1<x0 or y1<y0:continue
  x,y=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
  w0=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
  w1=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;w2=1-w0-w1
  mask=(w0>1e-6)&(w1>1e-6)&(w2>1e-6);ix=(x[mask]-.5).astype(int);iy=N-1-(y[mask]-.5).astype(int)
  hits[iy,ix]+=1;piece_map[iy,ix]=int(pieces[f.vertices[0]])
  pos[iy,ix]=w0[mask,None]*T[f.vertices[0]]+w1[mask,None]*T[f.vertices[1]]+w2[mask,None]*T[f.vertices[2]]
 reports[layer].update(covered_pixels=int((hits>0).sum()),overlap_pixels=int((hits>1).sum()),degenerate_faces=degenerate,density_px_per_m={n:[float(np.percentile(v,5)),float(np.median(v))] for n,v in density.items()})
 np.savez_compressed(P/'work'/f'uvraster_{layer}.npz',coverage=hits>0,pos=pos,piece=piece_map)
 assert degenerate==0 and int((hits>1).sum())==0,reports[layer]

(P/'work/feedback_uv.json').write_text(json.dumps(reports,indent=2))
