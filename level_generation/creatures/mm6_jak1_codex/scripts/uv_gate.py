import bpy,json,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_master.blend'));me=bpy.data.objects['Jackalman'].data;me.calc_loop_triangles();uv=me.uv_layers.active.data;report={}
for mi,mat in enumerate(me.materials):
 hits=np.zeros((1024,1024),np.uint16);dens=[];collapsed=[]
 for t in me.loop_triangles:
  if me.polygons[t.polygon_index].material_index!=mi:continue
  p=np.array([tuple(uv[i].uv)for i in t.loops]);q=np.array([tuple(me.vertices[i].co)for i in t.vertices]);a2=abs(np.linalg.det(np.stack([p[1]-p[0],p[2]-p[0]])))/2;a3=np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))/2
  if a3>1e-10:
   dens.append(math.sqrt(a2/a3)*10.24)
   if a2<1e-12:collapsed.append(t.index)
  p*=1024;lo=np.maximum(np.floor(p.min(0)).astype(int),0);hi=np.minimum(np.ceil(p.max(0)).astype(int),1023)
  if (hi<lo).any():continue
  x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);a,b,c=p;det=np.linalg.det(np.stack([b-a,c-a]))
  if abs(det)<1e-10:continue
  u=((x-a[0])*(c[1]-a[1])-(y-a[1])*(c[0]-a[0]))/det;v=((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/det;mask=(u>1e-6)&(v>1e-6)&(u+v<1-1e-6);hits[lo[1]:hi[1]+1,lo[0]:hi[0]+1]+=mask
 entry={'triangles':len(dens),'density_px_per_cm_p10_p50_p90':np.percentile(dens,[10,50,90]).tolist(),'collapsed':collapsed,'overlap_texels':int((hits>1).sum()),'covered_texels':int((hits>0).sum())};report[mat.name]=entry
 assert not collapsed and entry['overlap_texels']/max(1,entry['covered_texels'])<.01,entry
(P/'review/uv_gate.json').write_text(json.dumps(report,indent=2));print('UV',report,flush=True)
