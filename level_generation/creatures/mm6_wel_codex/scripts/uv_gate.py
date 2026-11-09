import bpy,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'));o=bpy.data.objects['Body'];me=o.data;me.calc_loop_triangles();uv=me.uv_layers.active;pa=np.array([a.value for a in me.attributes['part'].data]);out={}
for slot in [0,1]:
 count=np.zeros((1024,1024),np.uint16);density={}
 for tri in me.loop_triangles:
  if tri.material_index!=slot:continue
  u=np.array([uv.data[i].uv[:] for i in tri.loops]);assert u.min()>=-1e-5 and u.max()<=1.00001;xy=u*1024;lo=np.maximum(0,np.floor(xy.min(0)).astype(int));hi=np.minimum(1023,np.ceil(xy.max(0)).astype(int));xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);q=np.stack([xx,yy],axis=-1)-xy[0];m=np.column_stack([xy[1]-xy[0],xy[2]-xy[0]]);det=np.linalg.det(m)
  if abs(det)<1e-9:continue
  b=q@np.linalg.inv(m).T;inside=(b[...,0]>1e-4)&(b[...,1]>1e-4)&(b.sum(-1)<.9999);count[lo[1]:hi[1]+1,lo[0]:hi[0]+1]+=inside
  a=np.array([me.vertices[i].co[:] for i in tri.vertices]);world=np.linalg.norm(np.cross(a[1]-a[0],a[2]-a[0]))*.5;area=abs(det)*.5/1024**2;k=str(pa[tri.vertices[0]]);density.setdefault(k,[]).append([world,area])
 overlap=int(np.count_nonzero(count>1));assert overlap<25,overlap
 regions={k:round(math.sqrt(np.array(a)[:,1].sum()/np.array(a)[:,0].sum())*1024/100,2) for k,a in density.items()};assert min(regions.values())>2.,regions
 out[str(slot)]={'overlap_pixels':overlap,'coverage':float(np.mean(count>0)),'texels_per_cm_at_1k':regions}
(P/'work/uv_gate.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
