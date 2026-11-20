"""Exact UV density and raster overlap per texture set; no coloured faces may collapse."""
from pathlib import Path
import bpy,numpy as np,json,math
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_texturing.blend'))
me=bpy.data.objects['Body'].data;me.calc_loop_triangles();report={}
for layer,ishead in [('UVMap',False),('HeadUV',True)]:
 uv=me.uv_layers[layer].data;counts=np.zeros((1024,1024),np.uint16);regions={};zero=0
 for t in me.loop_triangles:
  if bool(me.attributes['head'].data[t.polygon_index].value)!=ishead:continue
  pts=np.array([tuple(uv[i].uv) for i in t.loops]);a,b,c=pts
  den=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);area=abs(den)/2
  co=[me.vertices[i].co for i in t.vertices];worldarea=(co[1]-co[0]).cross(co[2]-co[0]).length/2
  piece=me.attributes['piece'].data[t.vertices[0]].value
  r=regions.setdefault(str(piece),[0,0,0]);r[0]+=worldarea;r[1]+=area;r[2]+=1
  if worldarea>1e-7 and area<1e-12:zero+=1
  if abs(den)<1e-12:continue
  lo=np.maximum(0,np.floor(pts.min(0)*1024).astype(int));hi=np.minimum(1023,np.ceil(pts.max(0)*1024).astype(int))
  xs,ys=np.meshgrid((np.arange(lo[0],hi[0]+1)+.5)/1024,(np.arange(lo[1],hi[1]+1)+.5)/1024)
  v=(xs-a[0])*(c[1]-a[1])-(ys-a[1])*(c[0]-a[0]);v/=den
  w=(b[0]-a[0])*(ys-a[1])-(b[1]-a[1])*(xs-a[0]);w/=den
  counts[lo[1]:hi[1]+1,lo[0]:hi[0]+1]+=((v>1e-6)&(w>1e-6)&(v+w<1-1e-6))
 overlap=float((counts>1).sum()/max(1,(counts>0).sum()))
 density={k:{'px_per_cm':round(math.sqrt(v[1]/v[0])*10.24,2),'tris':v[2]} for k,v in regions.items() if v[0]>0}
 report[layer]={'collapsed_visible_triangles':zero,'overlap_fraction':overlap,'occupied_fraction':float((counts>0).mean()),'regions':density}
 assert zero==0,(layer,zero)
 assert overlap<.005,(layer,overlap)
 assert min(d['px_per_cm'] for d in density.values())>1,(layer,density)
print('UVGATE',json.dumps(report));(p/'work/uv_gate.json').write_text(json.dumps(report,indent=2)+'\n')
