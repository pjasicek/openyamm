import bpy,sys,json,numpy as np,math
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v9h.blend'))
b=bpy.data.objects['Body'];me=b.data;hd=np.zeros(len(me.polygons),np.int32);me.attributes['head'].data.foreach_get('value',hd);me.calc_loop_triangles()
report={}
for layer in ['HeadUV']:
 uv=me.uv_layers[layer].data;counts=np.zeros((1024,1024),np.int16);areaUV=area3D=0.
 for tri in me.loop_triangles:
  if bool(hd[tri.polygon_index])!=(layer=='HeadUV'):continue
  ps=np.array([tuple(uv[l].uv) for l in tri.loops]);assert np.isfinite(ps).all() and ps.min()>-1e-5 and ps.max()<1.00001
  areaUV+=abs(float(np.cross(ps[1]-ps[0],ps[2]-ps[0])))*.5;area3D+=tri.area
  ps*=1024;x0,y0=np.maximum(0,np.floor(ps.min(0)).astype(int));x1,y1=np.minimum(1023,np.ceil(ps.max(0)).astype(int))
  if x1<x0 or y1<y0:continue
  xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5);a,bb,c=ps
  den=(bb[1]-c[1])*(a[0]-c[0])+(c[0]-bb[0])*(a[1]-c[1])
  if abs(den)<1e-12:continue
  w0=((bb[1]-c[1])*(xx-c[0])+(c[0]-bb[0])*(yy-c[1]))/den
  w1=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den
  inside=(w0>1e-7)&(w1>1e-7)&((1-w0-w1)>1e-7)
  counts[y0:y1+1,x0:x1+1]+=inside
 overlap=int((counts>1).sum());report[layer]={'overlap_pixels':overlap,'covered_pixels':int((counts>0).sum()),'texels_per_meter':1024*math.sqrt(areaUV/area3D),'surface_m2':area3D}
 print('UV_RAW',layer,overlap)
(p/'work/uv_audit.json').write_text(json.dumps(report,indent=1));print('UV_AUDIT',report)
