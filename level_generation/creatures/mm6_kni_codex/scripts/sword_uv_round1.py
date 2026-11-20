import bpy,numpy as np,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1/sword_clay.blend'));me=bpy.data.objects['Sword'].data;me.calc_loop_triangles();uv=me.uv_layers.active.data;N=1024;hits=np.zeros((N,N),np.uint16);parts=np.full((N,N),-1,np.int16);classes=np.zeros((N,N),np.uint8);density={};collapsed=[]
for tri in me.loop_triangles:
 v=np.array([tuple(uv[i].uv)for i in tri.loops]);xyz=np.array([tuple(me.vertices[i].co)for i in tri.vertices]);a2=abs(np.linalg.det(np.stack([v[1]-v[0],v[2]-v[0]])))/2;a3=np.linalg.norm(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]))/2;part=me.attributes['sword_part'].data[tri.polygon_index].value;cl=me.attributes['material_class'].data[tri.polygon_index].value
 if a3>1e-12:
  density.setdefault(part,[]).append(math.sqrt(a2/a3)*N/100)
  if a2<1e-12:collapsed.append(tri.index)
 v[:,1]=1-v[:,1];v*=N;lo=np.maximum(np.floor(v.min(0)).astype(int),0);hi=np.minimum(np.ceil(v.max(0)).astype(int),N-1)
 if (hi<lo).any():continue
 x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);a,b,c=v;det=np.linalg.det(np.stack([b-a,c-a]))
 if abs(det)<1e-10:continue
 u=((x-a[0])*(c[1]-a[1])-(y-a[1])*(c[0]-a[0]))/det;w=((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/det;mask=(u>1e-6)&(w>1e-6)&(u+w<1-1e-6);sl=np.s_[lo[1]:hi[1]+1,lo[0]:hi[0]+1];hits[sl]+=mask;parts[sl][mask]=part;classes[sl][mask]=cl
report={'covered_texels':int((hits>0).sum()),'overlap_texels':int((hits>1).sum()),'collapsed_faces':collapsed,'density_px_per_cm':{str(k):np.percentile(v,[10,50,90]).tolist()for k,v in density.items()}}
assert not collapsed and report['overlap_texels']/max(report['covered_texels'],1)<.002,report
np.savez_compressed(P/'work/round1/sword_uv.npz',parts=parts,classes=classes);(P/'review/round1/uv_gate.json').write_text(json.dumps(report,indent=2));print('SWORD UV',report)
