"""Check the two used body UV sets for degenerate charts and overlapping texel interiors."""
import bpy,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_textured_uv.blend'));me=bpy.data.objects['Body'].data
pieces=np.array([a.value for a in me.attributes['piece'].data])
hd=np.array([a.value for a in me.attributes['head'].data]);me.calc_loop_triangles();report={};N=1024
for layer in ['UVMap','HeadUV']:
 uv=me.uv_layers[layer].data;count=np.zeros((N,N),np.uint16);density=[];degenerate=[];owner=np.full((N,N),-1);pairs={}
 for tri in me.loop_triangles:
  if bool(hd[tri.polygon_index])!=(layer=='HeadUV'):continue
  a,b,c=np.array([uv[i].uv[:] for i in tri.loops])*N
  den=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);area=tri.area
  if abs(den)<1e-7:degenerate.append(tri.polygon_index);continue
  if area>1e-12:density.append((abs(den)*.5/area)**.5)
  lo=np.maximum(np.floor(np.minimum(np.minimum(a,b),c)).astype(int),0);hi=np.minimum(np.ceil(np.maximum(np.maximum(a,b),c)).astype(int),N-1)
  x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
  w1=((x-a[0])*(c[1]-a[1])-(y-a[1])*(c[0]-a[0]))/den
  w2=((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/den
  m=(w1>.001)&(w2>.001)&(w1+w2<.999)
  iy,ix=(y[m]-.5).astype(int),(x[m]-.5).astype(int);part=int(pieces[tri.vertices[0]])
  for previous,n in zip(*np.unique(owner[iy,ix],return_counts=True)):
   if previous>=0:
    key=str((min(int(previous),part),max(int(previous),part)));pairs[key]=pairs.get(key,0)+int(n)
  owner[iy,ix]=part;count[iy,ix]+=1
 r={'overlap_piece_pairs':pairs,'degenerate_faces':degenerate,'covered_texels':int((count>0).sum()),'overlap_texels':int((count>1).sum()),'density_px_per_m_p10_p50_p90':np.percentile(density,[10,50,90]).tolist()};report[layer]=r
 assert len(degenerate)==0,(layer,degenerate)
 assert r['overlap_texels']<=4,(layer,r)  # Allow isolated raster boundary coincidences at 1K.
 assert r['covered_texels']>200000,(layer,r)
(P/'review/uv_quality.json').write_text(json.dumps(report,indent=1));print('UV_QUALITY',report)
