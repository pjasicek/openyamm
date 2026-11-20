from pathlib import Path
import bpy,numpy as np,json
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_textured_uv.blend'));m=bpy.data.objects['Body'].data;m.calc_loop_triangles();hd=np.array([a.value for a in m.attributes['head'].data]);out={};N=1024;piece=np.array([a.value for a in m.attributes['piece'].data])
for name in ['UVMap','HeadUV']:
 uv=m.uv_layers[name].data;hits=np.zeros((N,N),np.int32);zero=[];bounds=[];areas=[];count=0;pairs={};owner=np.full((N,N),-1,np.int32)
 for t in m.loop_triangles:
  if bool(hd[t.polygon_index])!=(name=='HeadUV'):continue
  count+=1;P=np.array([tuple(uv[i].uv) for i in t.loops]);assert np.isfinite(P).all()
  if P.min()<0 or P.max()>1:bounds.append(t.polygon_index)
  a,b,c=P*N;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1]);areas.append(abs(den)/2)
  if abs(den)<1e-8:zero.append(t.polygon_index);continue
  lo=np.maximum(0,np.floor(np.min([a,b,c],0)).astype(int));hi=np.minimum(N-1,np.ceil(np.max([a,b,c],0)).astype(int));x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
  w0=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den;w1=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;mask=(w0>1e-6)&(w1>1e-6)&(1-w0-w1>1e-6)
  region=owner[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
  for other in np.unique(region[mask & (region>=0)]):
   overlap=int((mask & (region==other)).sum());pairs[(int(other),t.polygon_index)]=pairs.get((int(other),t.polygon_index),0)+overlap
  region[mask]=t.polygon_index
  hits[lo[1]:hi[1]+1,lo[0]:hi[0]+1]+=mask
 out[name]={'triangles':count,'degenerate_faces':zero,'out_of_bounds_faces':bounds,'covered_texels':int((hits>0).sum()),'overlap_texels':int((hits>1).sum()),'uv_area_px_quantiles':np.quantile(areas,[0,.5,1]).tolist()}
 assert not zero and not bounds,out[name]
 out[name]['overlap_pairs']=[{'faces':[a,b],'pixels':n,'pieces':[int(piece[m.polygons[i].vertices[0]]) for i in [a,b]],'centres':[list(m.polygons[i].center) for i in [a,b]]} for (a,b),n in sorted(pairs.items(),key=lambda x:-x[1])]
 print('OVERLAP',name,out[name]['overlap_pairs'][:12])
(p/'review/uv_diagnostic.json').write_text(json.dumps(out,indent=2));print('UV_CHECK',out)
